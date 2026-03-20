import os
import sys
import site
import cv2
import time
import re
import json
import base64
import pickle
import logging
import threading
import numpy as np
import face_recognition

from pathlib import Path
from collections import deque
from flask import Flask, request, jsonify, Response, stream_with_context
from flask_cors import CORS

# =========================================================
# FIX SITE FOR PYINSTALLER
# =========================================================
if site.USER_SITE is None:
    site.USER_SITE = os.path.dirname(sys.executable) if getattr(sys, "frozen", False) else os.getcwd()

# =========================================================
# ENV / LOG
# =========================================================
os.environ["OPENCV_FFMPEG_LOGLEVEL"] = "8"
logging.disable(logging.WARNING)

# =========================================================
# CONFIG
# =========================================================
if getattr(sys, "frozen", False):
    base_path = sys._MEIPASS
else:
    base_path = os.path.dirname(os.path.abspath(__file__))

API_PORT = int(os.getenv("PORT", 5001))
WINDOW_NAME = "FACEID SINGLE-READ LOCK MODE"

THRESHOLD = 0.35
CONFIRM_FRAMES = 5
LOST_TIMEOUT = 2.0
ENCODE_INTERVAL = 0.7
FRAME_WIDTH = 480
ROTATE_MODE = -90

RECOGNIZE_TIMEOUT = 5.0
ALERT_TIMEOUT = 8.0

STREAM_WIDTH = 640
STREAM_HEIGHT = 360
JPEG_QUALITY = 80

MAX_READ_FAILS_BEFORE_WARN = 20
RECONNECT_DELAY_SEC = 1.0

# =========================================================
# ROOT PATH / FACE MODEL PATH
# =========================================================
current_path = Path(__file__).resolve()

ROOT = None
for parent in current_path.parents:
    if parent.name == "V-Shield":
        ROOT = parent
        break

if ROOT is None:
    ROOT = current_path.parent

FACE_MODEL_DIR = ROOT / "API/API/API/wwwroot/uploads/VideoFace/FaceID"

# =========================================================
# APP
# =========================================================
app = Flask(__name__)
CORS(
    app,
    resources={r"/api/*": {"origins": "*"}},
    supports_credentials=False
)

# =========================================================
# GLOBAL STATE
# =========================================================
camera_enabled = False
current_ip = ""
camera_connected = False

stop_event = threading.Event()

latest_raw_frame = None
latest_raw_frame_ts = 0.0
latest_jpeg = None
latest_display_frame = None

# face recognition state
tracking_active = False
identity_confirmed = False
confirm_count = 0
last_seen_time = 0.0
last_encode_time = 0.0
tracking_start_time = 0.0
alert_triggered = False
distance_buffer = deque(maxlen=5)

last_face_box = None
last_distance = None
last_employee_id = None
last_face_match = False
last_timeout = False
last_alert = False

# lock mode
scan_locked = False
lock_reason = None
locked_frame_jpeg = None
locked_snapshot_b64 = None
locked_face_crop_b64 = None

# last live images
last_snapshot_b64 = None
last_face_crop_b64 = None

fps = 0

camera_thread = None
face_thread = None
api_thread = None

api_lock = threading.Lock()
state_lock = threading.Lock()
frame_lock = threading.Lock()
camera_state_lock = threading.RLock()

recognition_state = {
    "success": True,
    "camera_enabled": False,
    "camera_connected": False,
    "ip": "",
    "face_model_dir": str(FACE_MODEL_DIR),
    "models_loaded": 0,
    "total_encodings": 0,

    "tracking_active": False,
    "identity_confirmed": False,
    "face_match": False,
    "employee_id": None,
    "confirm_count": 0,
    "distance": None,
    "last_seen": None,
    "bbox": None,
    "timeout": False,
    "alert": False,

    "scan_locked": False,
    "lock_reason": None,

    "fps": 0,
    "last_snapshot": None,
    "last_face_crop": None,
    "locked_snapshot": None,
    "locked_face_crop": None,
    "last_update": None,
    "message": "System initialized"
}

# =========================================================
# LOAD FACE MODELS
# =========================================================
print("Loading face models...")
print("Face model directory:", FACE_MODEL_DIR)

known_encodings = []
known_ids = []

if FACE_MODEL_DIR.exists():
    model_files = list(FACE_MODEL_DIR.glob("*.pkl"))
else:
    model_files = []

for model_file in model_files:
    try:
        with open(model_file, "rb") as f:
            encodings = pickle.load(f)

        # ví dụ: emp_2_20260315020708.pkl -> 2
        parts = model_file.stem.split("_")
        emp_id = f"{parts[1]}" if len(parts) > 1 else model_file.stem

        for enc in encodings:
            known_encodings.append(enc)
            known_ids.append(emp_id)

    except Exception as e:
        print(f"Load model failed: {model_file.name} -> {e}")

print("Loaded models:", len(model_files))
print("Total encodings:", len(known_encodings))
print("Face models loaded")

if len(known_encodings) == 0:
    print("WARNING: No face models found")

recognition_state["models_loaded"] = len(model_files)
recognition_state["total_encodings"] = len(known_encodings)

# =========================================================
# JSON SAFE HELPERS
# =========================================================
def make_json_safe(obj):
    if isinstance(obj, dict):
        return {str(k): make_json_safe(v) for k, v in obj.items()}
    if isinstance(obj, list):
        return [make_json_safe(v) for v in obj]
    if isinstance(obj, tuple):
        return [make_json_safe(v) for v in obj]

    if isinstance(obj, np.bool_):
        return bool(obj)
    if isinstance(obj, (np.int8, np.int16, np.int32, np.int64,
                        np.uint8, np.uint16, np.uint32, np.uint64)):
        return int(obj)
    if isinstance(obj, (np.float16, np.float32, np.float64)):
        return float(obj)
    if isinstance(obj, np.ndarray):
        return obj.tolist()

    return obj

# =========================================================
# STATE HELPERS
# =========================================================
def now_ts():
    return time.strftime("%Y-%m-%d %H:%M:%S")

def update_recognition_state(**kwargs):
    safe_kwargs = make_json_safe(kwargs)
    with state_lock:
        recognition_state.update(safe_kwargs)
        recognition_state["last_update"] = now_ts()

def get_recognition_snapshot(include_images=True):
    with state_lock:
        snapshot = {
            "success": recognition_state.get("success", True),
            "camera_enabled": recognition_state.get("camera_enabled", False),
            "camera_connected": recognition_state.get("camera_connected", False),
            "ip": recognition_state.get("ip", ""),
            "face_model_dir": recognition_state.get("face_model_dir"),
            "models_loaded": recognition_state.get("models_loaded", 0),
            "total_encodings": recognition_state.get("total_encodings", 0),

            "tracking_active": recognition_state.get("tracking_active", False),
            "identity_confirmed": recognition_state.get("identity_confirmed", False),
            "face_match": recognition_state.get("face_match", False),
            "employee_id": recognition_state.get("employee_id"),
            "confirm_count": recognition_state.get("confirm_count", 0),
            "distance": recognition_state.get("distance"),
            "last_seen": recognition_state.get("last_seen"),
            "bbox": recognition_state.get("bbox"),
            "timeout": recognition_state.get("timeout", False),
            "alert": recognition_state.get("alert", False),

            "scan_locked": recognition_state.get("scan_locked", False),
            "lock_reason": recognition_state.get("lock_reason"),

            "fps": recognition_state.get("fps", 0),
            "last_snapshot": recognition_state.get("last_snapshot") if include_images else None,
            "last_face_crop": recognition_state.get("last_face_crop") if include_images else None,
            "locked_snapshot": recognition_state.get("locked_snapshot") if include_images else None,
            "locked_face_crop": recognition_state.get("locked_face_crop") if include_images else None,
            "last_update": recognition_state.get("last_update"),
            "message": recognition_state.get("message", "")
        }
    return make_json_safe(snapshot)

# =========================================================
# CAMERA STATE HELPERS
# =========================================================
def set_camera_flags(enabled=None, ip=None, connected=None):
    global camera_enabled, current_ip, camera_connected
    with camera_state_lock:
        if enabled is not None:
            camera_enabled = bool(enabled)
        if ip is not None:
            current_ip = str(ip)
        if connected is not None:
            camera_connected = bool(connected)

def get_camera_flags():
    with camera_state_lock:
        return bool(camera_enabled), str(current_ip), bool(camera_connected)

def get_latest_frame_copy():
    global latest_raw_frame, latest_raw_frame_ts
    with frame_lock:
        if latest_raw_frame is None:
            return None, 0.0
        return latest_raw_frame.copy(), float(latest_raw_frame_ts)

# =========================================================
# IMAGE HELPERS
# =========================================================
def encode_frame_to_jpeg(frame):
    ok, jpeg = cv2.imencode(
        ".jpg",
        frame,
        [int(cv2.IMWRITE_JPEG_QUALITY), JPEG_QUALITY]
    )
    if ok:
        return jpeg.tobytes()
    return None

def image_to_base64(frame):
    if frame is None or frame.size == 0:
        return None
    ok, buf = cv2.imencode(".jpg", frame, [int(cv2.IMWRITE_JPEG_QUALITY), 90])
    if not ok:
        return None
    return "data:image/jpeg;base64," + base64.b64encode(buf.tobytes()).decode("utf-8")

def offline_frame():
    frame = np.zeros((STREAM_HEIGHT, STREAM_WIDTH, 3), dtype=np.uint8)
    cv2.putText(
        frame,
        "Camera Offline",
        (190, 180),
        cv2.FONT_HERSHEY_SIMPLEX,
        1,
        (255, 255, 255),
        2
    )
    return frame

# =========================================================
# RESET STATE
# =========================================================
def reset_recognition_state(reason="Recognition state reset"):
    global tracking_active, identity_confirmed, confirm_count
    global last_seen_time, last_encode_time, tracking_start_time
    global alert_triggered, last_face_box, last_distance
    global last_employee_id, last_face_match, last_timeout, last_alert
    global scan_locked, lock_reason
    global locked_frame_jpeg, locked_snapshot_b64, locked_face_crop_b64
    global last_snapshot_b64, last_face_crop_b64
    global fps

    tracking_active = False
    identity_confirmed = False
    confirm_count = 0
    last_seen_time = 0.0
    last_encode_time = 0.0
    tracking_start_time = 0.0
    alert_triggered = False

    last_face_box = None
    last_distance = None
    last_employee_id = None
    last_face_match = False
    last_timeout = False
    last_alert = False

    scan_locked = False
    lock_reason = None
    locked_frame_jpeg = None
    locked_snapshot_b64 = None
    locked_face_crop_b64 = None

    last_snapshot_b64 = None
    last_face_crop_b64 = None

    fps = 0
    distance_buffer.clear()

    enabled, ip, connected = get_camera_flags()

    update_recognition_state(
        success=True,
        camera_enabled=enabled,
        camera_connected=connected,
        ip=ip,
        tracking_active=False,
        identity_confirmed=False,
        face_match=False,
        employee_id=None,
        confirm_count=0,
        distance=None,
        last_seen=None,
        bbox=None,
        timeout=False,
        alert=False,
        scan_locked=False,
        lock_reason=None,
        fps=0,
        last_snapshot=None,
        last_face_crop=None,
        locked_snapshot=None,
        locked_face_crop=None,
        message=reason
    )

# =========================================================
# LOCK RESULT
# =========================================================
def lock_scan_result(reason, frame=None, face_crop=None):
    global scan_locked, lock_reason
    global locked_frame_jpeg, locked_snapshot_b64, locked_face_crop_b64

    if scan_locked:
        return

    scan_locked = True
    lock_reason = str(reason)

    if frame is not None:
        locked_frame_jpeg = encode_frame_to_jpeg(frame)
        locked_snapshot_b64 = image_to_base64(frame)

    if face_crop is not None and getattr(face_crop, "size", 0) > 0:
        locked_face_crop_b64 = image_to_base64(face_crop)

    update_recognition_state(
        scan_locked=True,
        lock_reason=lock_reason,
        locked_snapshot=locked_snapshot_b64,
        locked_face_crop=locked_face_crop_b64,
        message=f"Face scan locked: {lock_reason}"
    )

# =========================================================
# DRAW OVERLAY
# =========================================================
def get_display_text():
    if scan_locked:
        if lock_reason == "confirmed" and last_employee_id:
            return f"LOCKED: Employee {last_employee_id}"
        if lock_reason == "timeout":
            return "LOCKED: TIMEOUT"
        if lock_reason == "alert":
            return "LOCKED: ALERT"
        return "LOCKED"

    if identity_confirmed and last_employee_id:
        return f"Confirmed: Employee {last_employee_id}"
    if tracking_active and last_employee_id and last_face_match:
        return f"Recognizing: Employee {last_employee_id}"
    if tracking_active:
        return "Face detected"
    return "Waiting face..."

def draw_overlay(frame):
    display = frame.copy()

    if last_face_box is not None:
        x1 = int(last_face_box["left"])
        y1 = int(last_face_box["top"])
        x2 = int(last_face_box["right"])
        y2 = int(last_face_box["bottom"])

        if scan_locked:
            color = (0, 255, 255)
        else:
            color = (0, 255, 0) if identity_confirmed else (0, 255, 255)

        cv2.rectangle(display, (x1, y1), (x2, y2), color, 2)

    cv2.putText(
        display,
        f"FPS: {fps}",
        (20, 40),
        cv2.FONT_HERSHEY_SIMPLEX,
        1,
        (255, 0, 0),
        2
    )

    cv2.putText(
        display,
        get_display_text(),
        (20, 80),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.8,
        (0, 255, 0),
        2
    )

    enabled, ip, connected = get_camera_flags()
    cv2.putText(
        display,
        f"IP: {ip or '-----'}",
        (20, 120),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.6,
        (200, 200, 200),
        2
    )

    dist_text = f"Distance: {last_distance:.4f}" if last_distance is not None else "Distance: ---"
    cv2.putText(
        display,
        dist_text,
        (20, 160),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.6,
        (180, 180, 0),
        2
    )

    employee_text = f"Employee ID: {last_employee_id}" if last_employee_id else "Employee ID: ---"
    cv2.putText(
        display,
        employee_text,
        (20, 200),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.7,
        (255, 255, 0),
        2
    )

    if last_timeout:
        cv2.putText(
            display,
            "TIMEOUT: Unknown / not confirmed",
            (20, 240),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.7,
            (0, 165, 255),
            2
        )

    if last_alert:
        cv2.putText(
            display,
            "ALERT: Call security",
            (20, 280),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.8,
            (0, 0, 255),
            2
        )

    if scan_locked:
        cv2.putText(
            display,
            f"SCAN LOCKED: {lock_reason}",
            (20, 320),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.8,
            (0, 255, 255),
            2
        )
    elif enabled and not connected:
        cv2.putText(
            display,
            "RECONNECTING...",
            (20, 320),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.8,
            (0, 165, 255),
            2
        )

    return display

# =========================================================
# CAMERA READER WORKER
# =========================================================
def camera_reader_worker():
    global latest_raw_frame, latest_raw_frame_ts

    local_cap = None
    local_ip = ""
    read_fail_count = 0

    while not stop_event.is_set():
        enabled, ip, _ = get_camera_flags()

        if not enabled or not ip:
            if local_cap is not None:
                try:
                    local_cap.release()
                except Exception:
                    pass
                local_cap = None

            local_ip = ""
            set_camera_flags(connected=False)
            time.sleep(0.1)
            continue

        if local_cap is None or local_ip != ip:
            if local_cap is not None:
                try:
                    local_cap.release()
                except Exception:
                    pass
                local_cap = None

            local_ip = ip
            print(f"Opening camera: {ip}")

            try:
                temp_cap = cv2.VideoCapture(ip, cv2.CAP_FFMPEG)
                temp_cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)

                if not temp_cap.isOpened():
                    print("Cannot open camera")
                    try:
                        temp_cap.release()
                    except Exception:
                        pass

                    set_camera_flags(connected=False)
                    update_recognition_state(
                        camera_enabled=True,
                        camera_connected=False,
                        ip=ip,
                        message="Cannot open camera stream"
                    )
                    time.sleep(RECONNECT_DELAY_SEC)
                    continue

                local_cap = temp_cap
                read_fail_count = 0
                set_camera_flags(connected=True)
                update_recognition_state(
                    camera_enabled=True,
                    camera_connected=True,
                    ip=ip,
                    message="Camera opened successfully"
                )
                print("Camera opened successfully")

            except Exception as e:
                print("Open camera worker error:", e)
                set_camera_flags(connected=False)
                time.sleep(RECONNECT_DELAY_SEC)
                continue

        try:
            ret, frame = local_cap.read()
        except cv2.error as e:
            print("Camera read cv2 error:", e)
            ret, frame = False, None
        except Exception as e:
            print("Camera read error:", e)
            ret, frame = False, None

        if not ret or frame is None:
            read_fail_count += 1

            if read_fail_count >= MAX_READ_FAILS_BEFORE_WARN:
                set_camera_flags(connected=False)
                update_recognition_state(
                    camera_enabled=True,
                    camera_connected=False,
                    ip=ip,
                    message="Camera stream unstable, reconnecting..."
                )

                try:
                    local_cap.release()
                except Exception:
                    pass

                local_cap = None
                time.sleep(RECONNECT_DELAY_SEC)
            else:
                time.sleep(0.02)
            continue

        read_fail_count = 0
        set_camera_flags(connected=True)

        frame = cv2.resize(frame, (STREAM_WIDTH, STREAM_HEIGHT))

        with frame_lock:
            latest_raw_frame = frame.copy()
            latest_raw_frame_ts = time.time()

    if local_cap is not None:
        try:
            local_cap.release()
        except Exception:
            pass

# =========================================================
# FACE HELPERS
# =========================================================
def preprocess_frame(local_frame):
    h, w = local_frame.shape[:2]
    if w == 0:
        return None

    scale = FRAME_WIDTH / w
    resized = cv2.resize(local_frame, (FRAME_WIDTH, int(h * scale)))

    if ROTATE_MODE == 90:
        resized = cv2.rotate(resized, cv2.ROTATE_90_CLOCKWISE)
    elif ROTATE_MODE == -90:
        resized = cv2.rotate(resized, cv2.ROTATE_90_COUNTERCLOCKWISE)
    elif ROTATE_MODE == 180:
        resized = cv2.rotate(resized, cv2.ROTATE_180)

    return resized

def crop_face_safe(frame, face_location):
    top, right, bottom, left = face_location
    h, w = frame.shape[:2]

    top = max(0, top)
    left = max(0, left)
    bottom = min(h, bottom)
    right = min(w, right)

    if right <= left or bottom <= top:
        return None

    crop = frame[top:bottom, left:right]
    if crop.size == 0:
        return None
    return crop

def update_face_state_no_face(current_time):
    global tracking_active, identity_confirmed, confirm_count
    global last_face_match, last_employee_id, last_distance
    global last_face_box, last_timeout, last_alert

    if tracking_active and not scan_locked and current_time - last_seen_time > LOST_TIMEOUT:
        print("Person left")
        reset_recognition_state(reason="Face lost. State reset")
    else:
        enabled, ip, connected = get_camera_flags()
        update_recognition_state(
            camera_enabled=enabled,
            camera_connected=connected,
            ip=ip,
            tracking_active=tracking_active,
            identity_confirmed=identity_confirmed,
            face_match=last_face_match,
            employee_id=last_employee_id,
            confirm_count=confirm_count,
            distance=last_distance,
            last_seen=last_seen_time if last_seen_time > 0 else None,
            bbox=last_face_box,
            timeout=last_timeout,
            alert=last_alert,
            scan_locked=scan_locked,
            lock_reason=lock_reason,
            message="No face detected" if not scan_locked else f"Face scan locked: {lock_reason}"
        )

# =========================================================
# FACE PROCESSING WORKER
# =========================================================
def face_processing_worker():
    global tracking_active, identity_confirmed, confirm_count
    global last_seen_time, last_encode_time, tracking_start_time
    global alert_triggered, last_face_box, last_distance
    global last_employee_id, last_face_match, last_timeout, last_alert
    global last_snapshot_b64, last_face_crop_b64
    global fps, latest_display_frame, latest_jpeg

    print("Face processing worker started")

    fps_counter = 0
    fps_start = time.time()
    last_frame_ts_seen = 0.0

    while not stop_event.is_set():
        enabled, ip, connected = get_camera_flags()

        if not enabled:
            frame = np.zeros((STREAM_HEIGHT, STREAM_WIDTH, 3), dtype=np.uint8)
            cv2.putText(frame, "HE THONG DA KHOI DONG", (130, 100),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.9, (0, 255, 0), 2)
            cv2.putText(frame, "Camera dang tat", (210, 150),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 255, 255), 2)
            cv2.putText(frame, "Nhan I de nhap IP", (190, 200),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
            cv2.putText(frame, "Nhan O de mo camera", (170, 235),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
            cv2.putText(frame, "Nhan R de reset", (190, 270),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
            cv2.putText(frame, "Nhan Q de thoat", (210, 305),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)

            if current_ip:
                cv2.putText(frame, f"IP hien tai: {current_ip}", (120, 340),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.6, (180, 180, 180), 2)

            with frame_lock:
                latest_display_frame = frame.copy()
                latest_jpeg = encode_frame_to_jpeg(frame)

            update_recognition_state(
                camera_enabled=False,
                camera_connected=False,
                ip=current_ip,
                bbox=None,
                tracking_active=False,
                identity_confirmed=False,
                face_match=False,
                employee_id=None,
                confirm_count=0,
                distance=None,
                last_seen=None,
                timeout=False,
                alert=False,
                scan_locked=False,
                lock_reason=None,
                fps=0,
                message="Camera is off"
            )

            time.sleep(0.03)
            continue

        frame, frame_ts = get_latest_frame_copy()

        if frame is None:
            placeholder = np.zeros((STREAM_HEIGHT, STREAM_WIDTH, 3), dtype=np.uint8)
            if connected:
                cv2.putText(placeholder, "Dang cho frame...", (200, 180),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.9, (255, 255, 255), 2)
            else:
                cv2.putText(placeholder, "Dang ket noi lai camera...", (120, 180),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 165, 255), 2)

            with frame_lock:
                latest_display_frame = placeholder.copy()
                latest_jpeg = encode_frame_to_jpeg(placeholder)

            update_recognition_state(
                camera_enabled=enabled,
                camera_connected=connected,
                ip=ip,
                bbox=None,
                fps=int(fps),
                message="Waiting live frame"
            )

            time.sleep(0.03)
            continue

        if frame_ts != last_frame_ts_seen:
            last_frame_ts_seen = frame_ts
            fps_counter += 1

        processed = preprocess_frame(frame)
        if processed is None:
            time.sleep(0.01)
            continue

        # nếu đã lock thì dừng nhận diện tiếp, chỉ giữ ảnh lock
        if scan_locked:
            display_frame = draw_overlay(processed)

            with frame_lock:
                latest_display_frame = display_frame.copy()
                if locked_frame_jpeg is None:
                    latest_jpeg = encode_frame_to_jpeg(display_frame)
                else:
                    latest_jpeg = locked_frame_jpeg

            update_recognition_state(
                camera_enabled=enabled,
                camera_connected=connected,
                ip=ip,
                tracking_active=tracking_active,
                identity_confirmed=identity_confirmed,
                face_match=last_face_match,
                employee_id=last_employee_id,
                confirm_count=confirm_count,
                distance=last_distance,
                last_seen=last_seen_time if last_seen_time > 0 else None,
                bbox=last_face_box,
                timeout=last_timeout,
                alert=last_alert,
                scan_locked=True,
                lock_reason=lock_reason,
                locked_snapshot=locked_snapshot_b64,
                locked_face_crop=locked_face_crop_b64,
                fps=int(fps),
                message=f"Face scan locked: {lock_reason}"
            )

            if time.time() - fps_start >= 1:
                fps = fps_counter
                fps_counter = 0
                fps_start = time.time()

            time.sleep(0.03)
            continue

        rgb = cv2.cvtColor(processed, cv2.COLOR_BGR2RGB)
        current_time = time.time()
        face_locations = face_recognition.face_locations(rgb, model="hog")

        if face_locations:
            top, right, bottom, left = face_locations[0]

            face_box = {
                "top": int(top),
                "right": int(right),
                "bottom": int(bottom),
                "left": int(left),
                "width": int(right - left),
                "height": int(bottom - top)
            }
            last_face_box = face_box

            face_crop = crop_face_safe(processed, face_locations[0])
            if face_crop is not None:
                last_face_crop_b64 = image_to_base64(face_crop)

            last_snapshot_b64 = image_to_base64(processed)

            need_encode = current_time - last_encode_time > ENCODE_INTERVAL

            if need_encode:
                enc = face_recognition.face_encodings(rgb, [face_locations[0]])

                if enc and len(known_encodings) > 0:
                    distances = face_recognition.face_distance(known_encodings, enc[0])

                    best_index = np.argmin(distances)
                    distance = float(distances[best_index])
                    employee_id = known_ids[best_index]
                    is_match = distance < THRESHOLD

                    if not tracking_active:
                        print("Face detected")
                        tracking_active = True
                        identity_confirmed = False
                        confirm_count = 0
                        distance_buffer.clear()
                        tracking_start_time = current_time
                        alert_triggered = False
                        last_timeout = False
                        last_alert = False

                    distance_buffer.append(distance)
                    avg_distance = sum(distance_buffer) / len(distance_buffer)

                    last_seen_time = current_time
                    last_distance = float(avg_distance)
                    last_face_match = bool(is_match)

                    if is_match:
                        confirm_count += 1
                        last_employee_id = employee_id
                    else:
                        confirm_count = 0
                        identity_confirmed = False
                        last_employee_id = None

                    if confirm_count >= CONFIRM_FRAMES and not identity_confirmed:
                        identity_confirmed = True
                        print("Identity confirmed")
                        lock_scan_result(
                            reason="confirmed",
                            frame=processed,
                            face_crop=face_crop
                        )

                    last_encode_time = current_time

                elif len(known_encodings) == 0:
                    if not tracking_active:
                        tracking_active = True
                        identity_confirmed = False
                        confirm_count = 0
                        tracking_start_time = current_time
                        alert_triggered = False
                        last_timeout = False
                        last_alert = False

                    last_seen_time = current_time
                    last_face_match = False
                    last_employee_id = None
                    last_distance = None

            if tracking_active and not identity_confirmed and not scan_locked:
                elapsed = current_time - tracking_start_time

                # timeout trước
                if elapsed > RECOGNIZE_TIMEOUT and not last_timeout:
                    print("Recognition timeout - cannot recognize")
                    confirm_count = 0
                    identity_confirmed = False
                    last_face_match = False
                    last_employee_id = None
                    last_timeout = True

                    lock_scan_result(
                        reason="timeout",
                        frame=processed,
                        face_crop=face_crop
                    )

                # alert chỉ chạy nếu chưa lock
                if elapsed > ALERT_TIMEOUT and not alert_triggered and not scan_locked:
                    alert_triggered = True
                    last_alert = True
                    print("ALERT: Unknown person - call security!")

                    lock_scan_result(
                        reason="alert",
                        frame=processed,
                        face_crop=face_crop
                    )

            enabled2, ip2, connected2 = get_camera_flags()
            update_recognition_state(
                camera_enabled=enabled2,
                camera_connected=connected2,
                ip=ip2,
                tracking_active=tracking_active,
                identity_confirmed=identity_confirmed,
                face_match=last_face_match,
                employee_id=last_employee_id,
                confirm_count=confirm_count,
                distance=last_distance,
                last_seen=last_seen_time,
                bbox=last_face_box,
                timeout=last_timeout,
                alert=last_alert,
                scan_locked=scan_locked,
                lock_reason=lock_reason,
                last_snapshot=last_snapshot_b64,
                last_face_crop=last_face_crop_b64,
                locked_snapshot=locked_snapshot_b64,
                locked_face_crop=locked_face_crop_b64,
                fps=int(fps),
                message="Face detection running" if not scan_locked else f"Face scan locked: {lock_reason}"
            )

        else:
            update_face_state_no_face(current_time)

        display_frame = draw_overlay(processed)

        with frame_lock:
            latest_display_frame = display_frame.copy()
            if scan_locked and locked_frame_jpeg is not None:
                latest_jpeg = locked_frame_jpeg
            else:
                latest_jpeg = encode_frame_to_jpeg(display_frame)

        if time.time() - fps_start >= 1:
            fps = fps_counter
            fps_counter = 0
            fps_start = time.time()

        time.sleep(0.01)

    print("Face processing worker stopped")

# =========================================================
# STREAM
# =========================================================
def mjpeg_generator():
    while not stop_event.is_set():
        try:
            enabled, _, connected = get_camera_flags()

            if not enabled:
                payload = encode_frame_to_jpeg(offline_frame())
                if payload:
                    yield (
                        b"--frame\r\n"
                        b"Content-Type: image/jpeg\r\n\r\n" + payload + b"\r\n"
                    )
                time.sleep(0.3)
                continue

            with frame_lock:
                if scan_locked and locked_frame_jpeg is not None:
                    payload = locked_frame_jpeg
                else:
                    payload = latest_jpeg

            if payload is None:
                placeholder = offline_frame()
                if enabled and not connected:
                    cv2.putText(
                        placeholder,
                        "Dang ket noi lai camera...",
                        (130, 220),
                        cv2.FONT_HERSHEY_SIMPLEX,
                        0.7,
                        (0, 165, 255),
                        2
                    )
                payload = encode_frame_to_jpeg(placeholder)

            if payload is not None:
                yield (
                    b"--frame\r\n"
                    b"Content-Type: image/jpeg\r\n\r\n" + payload + b"\r\n"
                )

            time.sleep(0.02)

        except GeneratorExit:
            break
        except Exception as e:
            print("MJPEG generator error:", e)
            time.sleep(0.1)

# =========================================================
# CAMERA CONTROL
# =========================================================
def open_camera(ip):
    global current_ip

    if not ip:
        update_recognition_state(success=False, message="Missing camera IP")
        return False

    set_camera_flags(enabled=True, ip=ip, connected=False)
    current_ip = ip

    reset_recognition_state(reason="Waiting camera worker to connect...")

    update_recognition_state(
        success=True,
        camera_enabled=True,
        camera_connected=False,
        ip=ip,
        message="Waiting camera worker to connect..."
    )

    return True

def close_camera():
    global current_ip, latest_raw_frame, latest_raw_frame_ts, latest_jpeg, latest_display_frame

    set_camera_flags(enabled=False, connected=False)
    current_ip = ""

    with frame_lock:
        latest_raw_frame = None
        latest_raw_frame_ts = 0.0
        latest_jpeg = None
        latest_display_frame = None

    reset_recognition_state(reason="Camera closed")

    update_recognition_state(
        success=True,
        camera_enabled=False,
        camera_connected=False,
        ip="",
        bbox=None,
        message="Camera closed"
    )

    print("Camera closed")

# =========================================================
# API
# =========================================================
@app.route("/api/camera/on", methods=["POST"])
def api_camera_on():
    try:
        data = request.get_json(silent=True) or {}
        ip = str(data.get("ip", "")).strip()

        if not ip:
            return jsonify({
                "success": False,
                "message": "Thiếu IP camera"
            }), 400

        with api_lock:
            ok = open_camera(ip)

        if ok:
            return jsonify({
                "success": True,
                "message": "Đang kết nối camera",
                "ip": ip,
                "stream_url": "/api/camera/stream"
            }), 200

        return jsonify({
            "success": False,
            "message": "Không thể mở camera",
            "ip": ip
        }), 500

    except Exception as e:
        return jsonify({
            "success": False,
            "message": f"Lỗi bật camera: {str(e)}"
        }), 500

@app.route("/api/camera/off", methods=["POST"])
def api_camera_off():
    try:
        with api_lock:
            close_camera()

        return jsonify({
            "success": True,
            "message": "Đã tắt camera"
        }), 200

    except Exception as e:
        return jsonify({
            "success": False,
            "message": f"Lỗi tắt camera: {str(e)}"
        }), 500

@app.route("/api/camera/reset", methods=["POST"])
def api_camera_reset():
    try:
        with api_lock:
            reset_recognition_state(reason="Đã reset trạng thái nhận diện")
            enabled, ip, connected = get_camera_flags()
            update_recognition_state(
                success=True,
                camera_enabled=enabled,
                camera_connected=connected,
                ip=ip,
                message="Đã reset trạng thái nhận diện"
            )

        return jsonify({
            "success": True,
            "message": "Đã reset trạng thái nhận diện"
        }), 200

    except Exception as e:
        return jsonify({
            "success": False,
            "message": f"Lỗi reset trạng thái: {str(e)}"
        }), 500

@app.route("/api/camera/status", methods=["GET"])
def api_camera_status():
    try:
        snapshot = get_recognition_snapshot(include_images=False)
        return jsonify({
            "success": True,
            "camera_enabled": snapshot["camera_enabled"],
            "camera_connected": snapshot["camera_connected"],
            "ip": snapshot["ip"],
            "tracking_active": snapshot["tracking_active"],
            "identity_confirmed": snapshot["identity_confirmed"],
            "face_match": snapshot["face_match"],
            "employee_id": snapshot["employee_id"],
            "confirm_count": snapshot["confirm_count"],
            "distance": snapshot["distance"],
            "last_seen": snapshot["last_seen"],
            "bbox": snapshot["bbox"],
            "timeout": snapshot["timeout"],
            "alert": snapshot["alert"],
            "scan_locked": snapshot["scan_locked"],
            "lock_reason": snapshot["lock_reason"],
            "fps": snapshot["fps"],
            "models_loaded": snapshot["models_loaded"],
            "total_encodings": snapshot["total_encodings"],
            "message": snapshot["message"],
            "last_update": snapshot["last_update"],
            "stream_url": "/api/camera/stream" if snapshot["camera_enabled"] else ""
        }), 200
    except Exception as e:
        return jsonify({
            "success": False,
            "message": f"Lỗi lấy trạng thái camera: {str(e)}"
        }), 500

@app.route("/api/camera/result", methods=["GET"])
def api_camera_result():
    try:
        return jsonify(get_recognition_snapshot(include_images=True)), 200
    except Exception as e:
        return jsonify({
            "success": False,
            "message": f"Lỗi lấy kết quả nhận diện: {str(e)}"
        }), 500

@app.route("/api/camera/locked-images", methods=["GET"])
def api_camera_locked_images():
    try:
        snapshot = get_recognition_snapshot(include_images=True)
        return jsonify({
            "success": True,
            "identity_confirmed": snapshot["identity_confirmed"],
            "employee_id": snapshot["employee_id"],
            "scan_locked": snapshot["scan_locked"],
            "lock_reason": snapshot["lock_reason"],
            "locked_snapshot": snapshot["locked_snapshot"],
            "locked_face_crop": snapshot["locked_face_crop"]
        }), 200
    except Exception as e:
        return jsonify({
            "success": False,
            "message": f"Lỗi lấy ảnh lock: {str(e)}"
        }), 500

@app.route("/api/camera/stream", methods=["GET"])
def api_camera_stream():
    response = Response(
        stream_with_context(mjpeg_generator()),
        mimetype="multipart/x-mixed-replace; boundary=frame"
    )
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    response.headers["Pragma"] = "no-cache"
    response.headers["Expires"] = "0"
    response.headers["Access-Control-Allow-Origin"] = "*"
    return response

@app.route("/api/camera/events", methods=["GET"])
def api_camera_events():
    def event_stream():
        last_payload = None

        while not stop_event.is_set():
            try:
                snapshot = get_recognition_snapshot(include_images=False)

                lite_snapshot = {
                    "success": snapshot["success"],
                    "camera_enabled": snapshot["camera_enabled"],
                    "camera_connected": snapshot["camera_connected"],
                    "ip": snapshot["ip"],
                    "tracking_active": snapshot["tracking_active"],
                    "identity_confirmed": snapshot["identity_confirmed"],
                    "face_match": snapshot["face_match"],
                    "employee_id": snapshot["employee_id"],
                    "confirm_count": snapshot["confirm_count"],
                    "distance": snapshot["distance"],
                    "last_seen": snapshot["last_seen"],
                    "bbox": snapshot["bbox"],
                    "timeout": snapshot["timeout"],
                    "alert": snapshot["alert"],
                    "scan_locked": snapshot["scan_locked"],
                    "lock_reason": snapshot["lock_reason"],
                    "fps": snapshot["fps"],
                    "message": snapshot["message"],
                    "last_update": snapshot["last_update"]
                }

                payload = json.dumps(make_json_safe(lite_snapshot), ensure_ascii=False)

                if payload != last_payload:
                    yield f"event: state\ndata: {payload}\n\n"
                    last_payload = payload
                else:
                    yield "event: ping\ndata: {\"ok\":true}\n\n"

                time.sleep(0.2)

            except GeneratorExit:
                print("SSE client disconnected")
                break
            except Exception as e:
                print("SSE error:", e)
                time.sleep(1)

    resp = Response(
        stream_with_context(event_stream()),
        mimetype="text/event-stream"
    )
    resp.headers["Cache-Control"] = "no-cache"
    resp.headers["X-Accel-Buffering"] = "no"
    resp.headers["Connection"] = "keep-alive"
    resp.headers["Access-Control-Allow-Origin"] = "*"
    return resp

@app.route("/api/health", methods=["GET"])
def api_health():
    enabled, ip, connected = get_camera_flags()
    return jsonify({
        "success": True,
        "message": "FaceID API is running",
        "camera_enabled": enabled,
        "camera_connected": connected,
        "ip": ip,
        "models_loaded": len(model_files),
        "total_encodings": len(known_encodings),
        "last_update": now_ts()
    }), 200

# =========================================================
# API SERVER
# =========================================================
def run_api_server():
    print(f"API running at: http://127.0.0.1:{API_PORT}")
    app.run(host="0.0.0.0", port=API_PORT, debug=False, use_reloader=False, threaded=True)

# =========================================================
# DEBUG VIEW LOOP - MAIN THREAD
# =========================================================
def debug_view_loop():
    global current_ip

    try:
        cv2.namedWindow(WINDOW_NAME, cv2.WINDOW_NORMAL)
    except Exception as e:
        print("namedWindow error:", e)

    while not stop_event.is_set():
        with frame_lock:
            display = None if latest_display_frame is None else latest_display_frame.copy()

        if display is None:
            display = np.zeros((STREAM_HEIGHT, STREAM_WIDTH, 3), dtype=np.uint8)
            cv2.putText(
                display,
                "Khoi dong...",
                (220, 180),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.9,
                (255, 255, 255),
                2
            )

        try:
            cv2.imshow(WINDOW_NAME, display)
        except cv2.error as e:
            print("imshow error:", e)
            time.sleep(0.1)
            continue

        key = cv2.waitKey(1) & 0xFF

        if key == ord("i"):
            new_ip = input("\nNhap IP Webcam: ").strip()
            if new_ip:
                set_camera_flags(ip=new_ip)
                current_ip = new_ip
                update_recognition_state(
                    ip=current_ip,
                    message="IP updated manually"
                )
                print("Da luu IP:", current_ip)
            else:
                print("IP khong hop le.")

        elif key == ord("o"):
            if not current_ip:
                print("Chua co IP. Nhan 'i' de nhap IP truoc.")
            else:
                with api_lock:
                    open_camera(current_ip)

        elif key == ord("c"):
            with api_lock:
                close_camera()

        elif key == ord("r"):
            with api_lock:
                reset_recognition_state(
                    reason="Manual reset done. Ready to scan again."
                )
                enabled2, ip2, connected2 = get_camera_flags()
                update_recognition_state(
                    camera_enabled=enabled2,
                    camera_connected=connected2,
                    ip=ip2,
                    message="Manual reset done. Ready to scan again."
                )

        elif key == ord("q"):
            stop_event.set()
            break

        time.sleep(0.01)

# =========================================================
# MAIN
# =========================================================
def main():
    global camera_thread, face_thread, api_thread

    print("\n===== FACEID SINGLE-READ LOCK MODE =====")
    print("Phím điều khiển:")
    print("  i = nhập IP webcam")
    print("  o = mở camera")
    print("  c = tắt camera")
    print("  r = reset trạng thái nhận diện")
    print("  q = thoát chương trình\n")

    camera_thread = threading.Thread(target=camera_reader_worker, daemon=True)
    camera_thread.start()

    face_thread = threading.Thread(target=face_processing_worker, daemon=True)
    face_thread.start()

    api_thread = threading.Thread(target=run_api_server, daemon=True)
    api_thread.start()

    debug_view_loop()

    with api_lock:
        close_camera()

    try:
        cv2.destroyAllWindows()
    except Exception:
        pass

    print("Da giai phong tai nguyen.")

# =========================================================
# ENTRY
# =========================================================
if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("Thoat an toan...")
        stop_event.set()
        try:
            with api_lock:
                close_camera()
        except Exception as e:
            print("Close camera on exit error:", e)

        try:
            cv2.destroyAllWindows()
        except Exception:
            pass

    except Exception as e:
        print("Fatal error:", e)
        stop_event.set()
        try:
            with api_lock:
                close_camera()
        except Exception:
            pass
        try:
            cv2.destroyAllWindows()
        except Exception:
            pass

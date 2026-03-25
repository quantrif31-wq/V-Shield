import os
import sys
import site
import cv2
import torch
import time
import re
import json
import base64
import numpy as np
import logging
import threading

from ultralytics import YOLO
from paddleocr import PaddleOCR
from collections import Counter
from queue import Queue, Full, Empty
from flask import Flask, request, jsonify, Response, stream_with_context
from flasgger import Swagger
from flask_cors import CORS

# =========================================================
# FIX SITE FOR PYINSTALLER
# =========================================================
if site.USER_SITE is None:
    site.USER_SITE = os.path.dirname(sys.executable) if getattr(sys, "frozen", False) else os.getcwd()

# =========================================================
# FIX PADDLE FOR PYINSTALLER
# =========================================================
os.environ["FLAGS_enable_pir_api"] = "0"
os.environ["FLAGS_use_mkldnn"] = "0"
os.environ["FLAGS_enable_parallel_graph"] = "0"
os.environ["FLAGS_use_cinn"] = "0"
os.environ["FLAGS_log_level"] = "3"
os.environ["GLOG_minloglevel"] = "3"
os.environ["OPENCV_FFMPEG_LOGLEVEL"] = "8"

sys.modules["Cython"] = None

# =========================================================
# FIX IMPORT WHEN RUN AS EXE
# =========================================================
if getattr(sys, "frozen", False):
    exe_dir = os.path.dirname(sys.executable)
    sys.path.insert(0, exe_dir)

import paddle
try:
    paddle.utils.cpp_extension.extension_utils._jit_compile = False
except Exception:
    pass

# =========================================================
# SILENT LOG
# =========================================================
logging.disable(logging.WARNING)
logging.getLogger("ppocr").setLevel(logging.ERROR)

# =========================================================
# CONFIG
# =========================================================
if getattr(sys, "frozen", False):
    base_path = sys._MEIPASS
else:
    base_path = os.path.dirname(os.path.abspath(__file__))

MODEL_PATH = os.path.join(base_path, "best.pt")

CONF_THRES = 0.7
IOU_THRES = 0.6
IMG_SIZE = 416

STABLE_FRAMES = 2
DETECT_EVERY_N_FRAMES = 4
PADDING = 20

CONFIRM_MIN_VOTES = 2
CONFIRM_RATIO = 0.5
OCR_COOLDOWN = 0.2

JPEG_QUALITY = 80
STREAM_WIDTH = 640
STREAM_HEIGHT = 360
MOVE_THRESHOLD = 20

LOCK_AFTER_CONFIRM = True
API_PORT = int(os.getenv("PORT", 5002))

MAX_READ_FAILS_BEFORE_WARN = 20
RECONNECT_DELAY_SEC = 1.0

# =========================================================
# APP
# =========================================================
app = Flask(__name__)
app.config["SWAGGER"] = {
    "title": "LPR Camera API",
    "uiversion": 3,
    "openapi": "3.0.2",
    "specs_route": "/docs/"
}

swagger_template = {
    "openapi": "3.0.2",
    "info": {
        "title": "LPR Camera API",
        "description": "API điều khiển camera, stream, OCR biển số, trạng thái realtime",
        "version": "1.0.0"
    },
    "servers": [
        {
            "url": f"http://127.0.0.1:{API_PORT}"
        }
    ]
}

Swagger(app, template=swagger_template)

CORS(
    app,
    resources={r"/api/*": {"origins": "*"}},
    supports_credentials=False
)

# =========================================================
# TORCH / MODEL
# =========================================================
torch.set_grad_enabled(False)
torch.set_num_threads(4)

device = "cuda" if torch.cuda.is_available() else "cpu"
print("Device:", device)

print("Loading YOLO...")
model = YOLO(MODEL_PATH)
model.to(device)
model.fuse()
if device == "cuda":
    model.half()

print("Loading PaddleOCR...")
ocr = PaddleOCR(
    use_angle_cls=False,
    lang="en",
    show_log=False,
    use_gpu=(device == "cuda")
)

# =========================================================
# GLOBAL STATE
# =========================================================
camera_enabled = False
current_ip = ""
camera_connected = False

frame_id = 0
stable_count = 0
last_box = None
last_box_center = None
last_ocr_time = 0.0
fps = 0

ocr_queue = Queue(maxsize=1)
ocr_running = False

plate_votes = Counter()
confirmed_plate = None
last_raw_plate = None
live_candidates = []

latest_jpeg = None
latest_raw_frame = None
latest_raw_frame_ts = 0.0

scan_locked = False
locked_frame_jpeg = None
locked_snapshot_b64 = None
locked_plate_crop_b64 = None

stop_event = threading.Event()

api_lock = threading.Lock()
state_lock = threading.Lock()
frame_lock = threading.Lock()
camera_state_lock = threading.RLock()
session_lock = threading.Lock()

camera_thread = None
ocr_thread = None
api_thread = None

session_id = 0

recognition_state = {
    "success": True,
    "session_id": 0,
    "camera_enabled": False,
    "camera_connected": False,
    "ip": "",
    "device": device,
    "model_path": MODEL_PATH,
    "bbox": None,
    "stable_count": 0,
    "confirmed_plate": None,
    "last_raw_plate": None,
    "plate_votes": {},
    "live_candidates": [],
    "ocr_running": False,
    "moving_fast": False,
    "fps": 0,
    "scan_locked": False,
    "locked_snapshot": None,
    "locked_plate_crop": None,
    "last_update": None,
    "message": "System initialized"
}

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

def safe_counter_to_dict(counter_obj):
    return {str(k): int(v) for k, v in counter_obj.items()}

def next_session_id():
    global session_id
    with session_lock:
        session_id += 1
        return session_id

def get_session_id():
    with session_lock:
        return int(session_id)

def update_recognition_state(**kwargs):
    safe_kwargs = make_json_safe(kwargs)
    with state_lock:
        recognition_state.update(safe_kwargs)
        recognition_state["last_update"] = now_ts()

def get_recognition_snapshot(include_images=True):
    with state_lock:
        snapshot = {
            "success": True,
            "session_id": recognition_state.get("session_id", 0),
            "camera_enabled": recognition_state.get("camera_enabled", False),
            "camera_connected": recognition_state.get("camera_connected", False),
            "ip": recognition_state.get("ip", ""),
            "device": recognition_state.get("device"),
            "model_path": recognition_state.get("model_path"),
            "bbox": recognition_state.get("bbox"),
            "stable_count": recognition_state.get("stable_count", 0),
            "confirmed_plate": recognition_state.get("confirmed_plate"),
            "last_raw_plate": recognition_state.get("last_raw_plate"),
            "plate_votes": recognition_state.get("plate_votes", {}),
            "live_candidates": recognition_state.get("live_candidates", []),
            "ocr_running": recognition_state.get("ocr_running", False),
            "moving_fast": recognition_state.get("moving_fast", False),
            "fps": recognition_state.get("fps", 0),
            "scan_locked": recognition_state.get("scan_locked", False),
            "locked_snapshot": recognition_state.get("locked_snapshot") if include_images else None,
            "locked_plate_crop": recognition_state.get("locked_plate_crop") if include_images else None,
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
# UTILS
# =========================================================
def is_box_moving_fast(box, prev_center, threshold=MOVE_THRESHOLD):
    x1, y1, x2, y2 = box
    center = ((x1 + x2) // 2, (y1 + y2) // 2)

    if prev_center is None:
        return False, center

    dist = np.linalg.norm(np.array(center) - np.array(prev_center))
    return bool(dist > threshold), center

def is_similar_box(box1, box2, threshold=15):
    if box1 is None or box2 is None:
        return False
    return bool(np.all(np.abs(box1 - box2) < threshold))

def normalize_plate_text(text: str) -> str:
    return text.replace(" ", "").replace("-", "").replace(".", "").upper()

def validate_plate(text):
    text = normalize_plate_text(text)
    patterns = [
        r"^\d{2}[A-Z]{1,2}\d{4,6}$",
    ]
    for pattern in patterns:
        if re.match(pattern, text):
            return True, "vn_plate"
    return False, None

def clear_ocr_queue():
    while True:
        try:
            _ = ocr_queue.get_nowait()
            try:
                ocr_queue.task_done()
            except Exception:
                pass
        except Empty:
            break

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

def reset_recognition_state(reason="Recognition state reset", new_session=True):
    global frame_id, stable_count, last_box, last_box_center
    global last_ocr_time, ocr_running
    global plate_votes, confirmed_plate, last_raw_plate
    global latest_jpeg, latest_raw_frame, latest_raw_frame_ts, live_candidates
    global scan_locked, locked_frame_jpeg, locked_snapshot_b64, locked_plate_crop_b64
    global fps

    sid = get_session_id()
    if new_session:
        sid = next_session_id()

    frame_id = 0
    stable_count = 0
    last_box = None
    last_box_center = None
    last_ocr_time = 0.0
    fps = 0

    ocr_running = False

    plate_votes.clear()
    confirmed_plate = None
    last_raw_plate = None
    live_candidates = []

    scan_locked = False
    locked_frame_jpeg = None
    locked_snapshot_b64 = None
    locked_plate_crop_b64 = None

    clear_ocr_queue()

    with frame_lock:
        latest_jpeg = None
        latest_raw_frame = None
        latest_raw_frame_ts = 0.0

    enabled, ip, connected = get_camera_flags()
    update_recognition_state(
        success=True,
        session_id=sid,
        camera_enabled=enabled,
        camera_connected=connected,
        ip=ip,
        bbox=None,
        stable_count=0,
        confirmed_plate=None,
        last_raw_plate=None,
        plate_votes={},
        live_candidates=[],
        ocr_running=False,
        moving_fast=False,
        fps=0,
        scan_locked=False,
        locked_snapshot=None,
        locked_plate_crop=None,
        message=reason
    )

# =========================================================
# IMAGE ENHANCE
# =========================================================
def auto_brightness_contrast(image):
    lab = cv2.cvtColor(image, cv2.COLOR_BGR2LAB)
    l, a, b = cv2.split(lab)
    clahe = cv2.createCLAHE(clipLimit=3.0, tileGridSize=(8, 8))
    l = clahe.apply(l)
    lab = cv2.merge((l, a, b))
    return cv2.cvtColor(lab, cv2.COLOR_LAB2BGR)

def sharpen_image(img):
    kernel = np.array([[0, -1, 0], [-1, 5, -1], [0, -1, 0]])
    return cv2.filter2D(img, -1, kernel)

def deskew_plate(img):
    h, w = img.shape[:2]

    if h > w * 1.2:
        img = cv2.rotate(img, cv2.ROTATE_90_CLOCKWISE)

    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    edges = cv2.Canny(gray, 50, 150)
    coords = np.column_stack(np.where(edges > 0))

    if len(coords) < 50:
        return img

    rect = cv2.minAreaRect(coords)
    angle = rect[-1]

    if angle < -45:
        angle = -(90 + angle)
    else:
        angle = -angle

    if abs(angle) < 45:
        h, w = img.shape[:2]
        M = cv2.getRotationMatrix2D((w // 2, h // 2), angle, 1.0)
        img = cv2.warpAffine(
            img,
            M,
            (w, h),
            flags=cv2.INTER_LINEAR,
            borderMode=cv2.BORDER_REPLICATE
        )

    return img

def normalize_plate_size(gray):
    h, w = gray.shape
    target_height = 80
    scale = target_height / max(h, 1)
    return cv2.resize(gray, (max(int(w * scale), 1), target_height))

def is_bad_lighting(gray):
    mean_val = np.mean(gray)
    return bool(mean_val < 40 or mean_val > 220)

def enhance_plate(crop):
    gray = cv2.cvtColor(crop, cv2.COLOR_BGR2GRAY)

    if is_bad_lighting(gray):
        crop = auto_brightness_contrast(crop)
        crop = sharpen_image(crop)

    crop = deskew_plate(crop)
    gray = cv2.cvtColor(crop, cv2.COLOR_BGR2GRAY)
    gray = normalize_plate_size(gray)

    return cv2.cvtColor(gray, cv2.COLOR_GRAY2BGR)

# =========================================================
# OCR
# =========================================================
def extract_text_from_ocr(result):
    lines = []
    confidences = []

    if not result:
        return "", 0.0

    for res in result:
        if isinstance(res, list):
            for item in res:
                if isinstance(item, (list, tuple)) and len(item) >= 2:
                    text_part = item[1]
                    if isinstance(text_part, (list, tuple)) and len(text_part) >= 2:
                        lines.append(str(text_part[0]))
                        confidences.append(float(text_part[1]))

    if not lines:
        return "", 0.0

    text = "".join(lines).upper()
    text = re.sub(r"[^A-Z0-9]", "", text)
    avg_conf = sum(confidences) / len(confidences)
    return text, avg_conf

def smart_rotate_ocr_candidates(crop):
    rotations = [
        crop,
        cv2.rotate(crop, cv2.ROTATE_90_CLOCKWISE),
        cv2.rotate(crop, cv2.ROTATE_90_COUNTERCLOCKWISE),
        cv2.rotate(crop, cv2.ROTATE_180),
    ]

    candidates = []

    for img in rotations:
        try:
            processed = enhance_plate(img)
            result = ocr.ocr(processed)
            text, conf = extract_text_from_ocr(result)

            if text and conf > 0.45:
                normalized = normalize_plate_text(text)
                is_valid, _ = validate_plate(normalized)
                score = conf * len(normalized)
                if is_valid:
                    score += 5

                candidates.append({
                    "text": str(normalized),
                    "conf": float(round(float(conf), 4)),
                    "valid": bool(is_valid),
                    "score": float(round(float(score), 4))
                })
        except Exception as e:
            print("Rotate OCR error:", e)

    dedup = {}
    for item in candidates:
        text = item["text"]
        if text not in dedup or item["score"] > dedup[text]["score"]:
            dedup[text] = item

    final_candidates = list(dedup.values())
    final_candidates.sort(key=lambda x: x["score"], reverse=True)
    return final_candidates[:5]

def lock_scan_result(frame, plate_crop):
    global scan_locked, locked_frame_jpeg, locked_snapshot_b64, locked_plate_crop_b64

    if scan_locked:
        return

    scan_locked = True
    locked_frame_jpeg = encode_frame_to_jpeg(frame)
    locked_snapshot_b64 = image_to_base64(frame)
    locked_plate_crop_b64 = image_to_base64(plate_crop)

    update_recognition_state(
        session_id=get_session_id(),
        scan_locked=True,
        locked_snapshot=locked_snapshot_b64,
        locked_plate_crop=locked_plate_crop_b64,
        message="Plate confirmed. Scan locked."
    )

def ocr_worker():
    global ocr_running
    global last_raw_plate, confirmed_plate, live_candidates, scan_locked

    while not stop_event.is_set():
        try:
            payload = ocr_queue.get(timeout=0.2)
        except Empty:
            continue

        done_called = False
        try:
            if payload is None:
                ocr_queue.task_done()
                done_called = True
                break

            payload_session = int(payload.get("session_id", -1))
            current_session = get_session_id()

            if payload_session != current_session:
                ocr_queue.task_done()
                done_called = True
                continue

            crop = payload["crop"]
            full_frame = payload["frame"]

            if scan_locked or stop_event.is_set():
                update_recognition_state(
                    session_id=current_session,
                    ocr_running=False,
                    message="Scan already locked"
                )
                ocr_queue.task_done()
                done_called = True
                continue

            candidates = smart_rotate_ocr_candidates(crop)

            if payload_session != get_session_id():
                ocr_queue.task_done()
                done_called = True
                continue

            live_candidates = candidates

            if candidates:
                best = candidates[0]
                best_text = best["text"]
                last_raw_plate = best_text

                if best["valid"]:
                    if not scan_locked:
                        plate_votes[best_text] += 1

                    total = sum(plate_votes.values())
                    best_plate, best_count = plate_votes.most_common(1)[0]

                    if (
                        not scan_locked
                        and best_count >= CONFIRM_MIN_VOTES
                        and (best_count / max(total, 1)) >= CONFIRM_RATIO
                    ):
                        if confirmed_plate != best_plate:
                            confirmed_plate = best_plate
                            print("Plate confirmed:", confirmed_plate)

                        if LOCK_AFTER_CONFIRM:
                            lock_scan_result(full_frame, crop)

                    update_recognition_state(
                        session_id=current_session,
                        last_raw_plate=last_raw_plate,
                        confirmed_plate=confirmed_plate,
                        plate_votes=safe_counter_to_dict(plate_votes),
                        live_candidates=live_candidates,
                        ocr_running=True,
                        scan_locked=scan_locked,
                        locked_snapshot=locked_snapshot_b64,
                        locked_plate_crop=locked_plate_crop_b64,
                        message="OCR reading realtime"
                    )
                else:
                    update_recognition_state(
                        session_id=current_session,
                        last_raw_plate=last_raw_plate,
                        confirmed_plate=confirmed_plate,
                        plate_votes=safe_counter_to_dict(plate_votes),
                        live_candidates=live_candidates,
                        ocr_running=True,
                        scan_locked=scan_locked,
                        locked_snapshot=locked_snapshot_b64,
                        locked_plate_crop=locked_plate_crop_b64,
                        message="OCR read text but format not confirmed"
                    )
            else:
                live_candidates = []
                update_recognition_state(
                    session_id=current_session,
                    live_candidates=[],
                    ocr_running=True,
                    scan_locked=scan_locked,
                    locked_snapshot=locked_snapshot_b64,
                    locked_plate_crop=locked_plate_crop_b64,
                    message="OCR running but no text"
                )

        except Exception as e:
            print("OCR worker error:", e)
        finally:
            ocr_running = False
            update_recognition_state(
                session_id=get_session_id(),
                ocr_running=False,
                last_raw_plate=last_raw_plate,
                confirmed_plate=confirmed_plate,
                plate_votes=safe_counter_to_dict(plate_votes),
                live_candidates=live_candidates,
                scan_locked=scan_locked,
                locked_snapshot=locked_snapshot_b64,
                locked_plate_crop=locked_plate_crop_b64
            )
            if not done_called:
                try:
                    ocr_queue.task_done()
                except ValueError:
                    pass

# =========================================================
# CAMERA READER WORKER
# =========================================================
def camera_reader_worker():
    global latest_raw_frame, latest_raw_frame_ts

    local_cap = None
    local_ip = ""
    local_session = -1
    read_fail_count = 0

    while not stop_event.is_set():
        enabled, ip, _ = get_camera_flags()
        current_session = get_session_id()

        if not enabled or not ip:
            if local_cap is not None:
                try:
                    local_cap.release()
                except Exception:
                    pass
                local_cap = None

            local_ip = ""
            local_session = current_session
            set_camera_flags(connected=False)
            time.sleep(0.1)
            continue

        if local_cap is None or local_ip != ip or local_session != current_session:
            if local_cap is not None:
                try:
                    local_cap.release()
                except Exception:
                    pass
                local_cap = None

            local_ip = ip
            local_session = current_session
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
                        session_id=current_session,
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
                    session_id=current_session,
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
                    session_id=current_session,
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

        if current_session != get_session_id():
            continue

        with frame_lock:
            latest_raw_frame = frame.copy()
            latest_raw_frame_ts = time.time()

    if local_cap is not None:
        try:
            local_cap.release()
        except Exception:
            pass

# =========================================================
# STREAM
# =========================================================
def get_display_text():
    if scan_locked and confirmed_plate:
        return f"LOCKED: {confirmed_plate}"
    if confirmed_plate:
        return f"Confirmed: {confirmed_plate}"
    if last_raw_plate:
        return f"Reading: {last_raw_plate}"
    return "Waiting plate..."

def draw_overlay(frame, moving_fast=False):
    display = frame.copy()

    if last_box is not None and not scan_locked:
        x1, y1, x2, y2 = [int(v) for v in last_box]
        cv2.rectangle(
            display,
            (x1, y1),
            (x2, y2),
            (0, 255, 0) if not moving_fast else (0, 255, 255),
            2
        )

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

    if scan_locked:
        cv2.putText(
            display,
            "SCAN LOCKED",
            (20, 160),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.8,
            (0, 255, 255),
            2
        )
    elif enabled and not connected:
        cv2.putText(
            display,
            "RECONNECTING...",
            (20, 160),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.8,
            (0, 165, 255),
            2
        )

    return display

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

            if scan_locked and locked_frame_jpeg is not None:
                payload = locked_frame_jpeg
            else:
                with frame_lock:
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

    reset_recognition_state(reason="Waiting camera worker to connect...", new_session=True)

    update_recognition_state(
        success=True,
        session_id=get_session_id(),
        camera_enabled=True,
        camera_connected=False,
        ip=ip,
        message="Waiting camera worker to connect..."
    )

    return True

def close_camera():
    global current_ip

    set_camera_flags(enabled=False, connected=False)
    current_ip = ""

    reset_recognition_state(reason="Camera closed", new_session=True)

    update_recognition_state(
        success=True,
        session_id=get_session_id(),
        camera_enabled=False,
        camera_connected=False,
        ip="",
        bbox=None,
        moving_fast=False,
        message="Camera closed"
    )

    print("Camera closed")

# =========================================================
# API
# =========================================================
@app.route("/api/camera/on", methods=["POST"])
def api_camera_on():
    """
    Camera status
    ---
    tags:
      - Camera
    responses:
      200:
        description: OK
        content:
          application/json:
            example:
              success: true
              message: running
    """
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
                "session_id": get_session_id(),
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
    """
    Camera status
    ---
    tags:
      - Camera
    responses:
      200:
        description: OK
        content:
          application/json:
            example:
              success: true
              message: running
    """
    try:
        with api_lock:
            close_camera()

        return jsonify({
            "success": True,
            "session_id": get_session_id(),
            "message": "Đã tắt camera"
        }), 200

    except Exception as e:
        return jsonify({
            "success": False,
            "message": f"Lỗi tắt camera: {str(e)}"
        }), 500

@app.route("/api/camera/reset", methods=["POST"])
def api_camera_reset():
    """
    Camera status
    ---
    tags:
      - Camera
    responses:
      200:
        description: OK
        content:
          application/json:
            example:
              success: true
              message: running
    """
    try:
        with api_lock:
            reset_recognition_state(
                reason="Đã reset trạng thái nhận diện",
                new_session=True
            )
            enabled, ip, connected = get_camera_flags()
            update_recognition_state(
                success=True,
                session_id=get_session_id(),
                camera_enabled=enabled,
                camera_connected=connected,
                ip=ip,
                message="Đã reset trạng thái nhận diện"
            )

        return jsonify({
            "success": True,
            "session_id": get_session_id(),
            "message": "Đã reset trạng thái nhận diện"
        }), 200

    except Exception as e:
        return jsonify({
            "success": False,
            "message": f"Lỗi reset trạng thái: {str(e)}"
        }), 500

@app.route("/api/camera/status", methods=["GET"])
def api_camera_status():
    """
    Camera status
    ---
    tags:
      - Camera
    responses:
      200:
        description: OK
        content:
          application/json:
            example:
              success: true
              message: running
    """
    try:
        snapshot = get_recognition_snapshot(include_images=False)
        return jsonify({
            "success": True,
            "session_id": snapshot["session_id"],
            "camera_enabled": snapshot["camera_enabled"],
            "camera_connected": snapshot["camera_connected"],
            "ip": snapshot["ip"],
            "confirmed_plate": snapshot["confirmed_plate"],
            "last_raw_plate": snapshot["last_raw_plate"],
            "ocr_running": snapshot["ocr_running"],
            "fps": snapshot["fps"],
            "stable_count": snapshot["stable_count"],
            "moving_fast": snapshot["moving_fast"],
            "bbox": snapshot["bbox"],
            "plate_votes": snapshot["plate_votes"],
            "live_candidates": snapshot["live_candidates"],
            "scan_locked": snapshot["scan_locked"],
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
    """
    Camera status
    ---
    tags:
      - Camera
    responses:
      200:
        description: OK
        content:
          application/json:
            example:
              success: true
              message: running
    """
    try:
        return jsonify(get_recognition_snapshot(include_images=True)), 200
    except Exception as e:
        return jsonify({
            "success": False,
            "message": f"Lỗi lấy kết quả nhận diện: {str(e)}"
        }), 500

@app.route("/api/camera/locked-images", methods=["GET"])
def api_camera_locked_images():
    """
    Camera status
    ---
    tags:
      - Camera
    responses:
      200:
        description: OK
        content:
          application/json:
            example:
              success: true
              message: running
    """
    try:
        snapshot = get_recognition_snapshot(include_images=True)
        return jsonify({
            "success": True,
            "session_id": snapshot["session_id"],
            "scan_locked": snapshot["scan_locked"],
            "locked_snapshot": snapshot["locked_snapshot"],
            "locked_plate_crop": snapshot["locked_plate_crop"]
        }), 200
    except Exception as e:
        return jsonify({
            "success": False,
            "message": f"Lỗi lấy ảnh lock: {str(e)}"
        }), 500

@app.route("/api/camera/stream", methods=["GET"])
def api_camera_stream():
    """
    Camera status
    ---
    tags:
      - Camera
    responses:
      200:
        description: OK
        content:
          application/json:
            example:
              success: true
              message: running
    """
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
    """
    Camera status
    ---
    tags:
      - Camera
    responses:
      200:
        description: OK
        content:
          application/json:
            example:
              success: true
              message: running
    """
    def event_stream():
        last_payload = None

        while not stop_event.is_set():
            try:
                snapshot = get_recognition_snapshot(include_images=False)

                lite_snapshot = {
                    "success": snapshot["success"],
                    "session_id": snapshot["session_id"],
                    "camera_enabled": snapshot["camera_enabled"],
                    "camera_connected": snapshot["camera_connected"],
                    "ip": snapshot["ip"],
                    "bbox": snapshot["bbox"],
                    "stable_count": snapshot["stable_count"],
                    "confirmed_plate": snapshot["confirmed_plate"],
                    "last_raw_plate": snapshot["last_raw_plate"],
                    "plate_votes": snapshot["plate_votes"],
                    "live_candidates": snapshot["live_candidates"],
                    "ocr_running": snapshot["ocr_running"],
                    "moving_fast": snapshot["moving_fast"],
                    "fps": snapshot["fps"],
                    "scan_locked": snapshot["scan_locked"],
                    "last_update": snapshot["last_update"],
                    "message": snapshot["message"]
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
    """
    Health check API
    ---
    tags:
      - System
    responses:
      200:
        description: API is running
        content:
          application/json:
            example:
              success: true
              message: LPR API is running
    """
    enabled, ip, connected = get_camera_flags()
    return jsonify({
        "success": True,
        "message": "LPR API is running",
        "device": device,
        "session_id": get_session_id(),
        "camera_enabled": enabled,
        "camera_connected": connected,
        "ip": ip,
        "last_update": now_ts()
    }), 200

def run_api_server():
    print(f"API running at: http://127.0.0.1:{API_PORT}")
    app.run(host="0.0.0.0", port=API_PORT, debug=False, use_reloader=False, threaded=True)

# =========================================================
# MAIN LOOP
# =========================================================
def main():
    global current_ip
    global frame_id, stable_count, last_box, last_box_center
    global ocr_running, confirmed_plate, plate_votes
    global last_raw_plate, last_ocr_time, fps, latest_jpeg, live_candidates
    global scan_locked, camera_thread, ocr_thread, api_thread

    print("\n===== LPR SINGLE-READ LOCK MODE =====")
    print("Phím điều khiển:")
    print("  i = nhập IP webcam")
    print("  o = mở camera")
    print("  c = tắt camera")
    print("  r = reset phiên quét")
    print("  q = thoát chương trình\n")

    ocr_thread = threading.Thread(target=ocr_worker, daemon=True)
    ocr_thread.start()

    api_thread = threading.Thread(target=run_api_server, daemon=True)
    api_thread.start()

    camera_thread = threading.Thread(target=camera_reader_worker, daemon=True)
    camera_thread.start()

    fps_counter = 0
    fps_start = time.time()
    last_frame_ts_seen = 0.0

    while not stop_event.is_set():
        moving_fast = False

        enabled, ip, connected = get_camera_flags()

        if enabled:
            frame, frame_ts = get_latest_frame_copy()

            if frame is None:
                placeholder = np.zeros((STREAM_HEIGHT, STREAM_WIDTH, 3), dtype=np.uint8)
                if connected:
                    cv2.putText(
                        placeholder,
                        "Dang cho frame...",
                        (200, 180),
                        cv2.FONT_HERSHEY_SIMPLEX,
                        0.9,
                        (255, 255, 255),
                        2
                    )
                else:
                    cv2.putText(
                        placeholder,
                        "Dang ket noi lai camera...",
                        (120, 180),
                        cv2.FONT_HERSHEY_SIMPLEX,
                        0.8,
                        (0, 165, 255),
                        2
                    )

                update_recognition_state(
                    session_id=get_session_id(),
                    camera_enabled=enabled,
                    camera_connected=connected,
                    ip=ip,
                    bbox=None,
                    moving_fast=False,
                    fps=int(fps),
                    live_candidates=live_candidates,
                    scan_locked=scan_locked,
                    locked_snapshot=locked_snapshot_b64,
                    locked_plate_crop=locked_plate_crop_b64,
                    message="Waiting live frame"
                )
                display_frame = draw_overlay(placeholder, moving_fast=False)

            else:
                if frame_ts != last_frame_ts_seen:
                    last_frame_ts_seen = frame_ts
                    frame_id += 1
                    fps_counter += 1

                if not scan_locked and connected:
                    detect_interval = 1 if stable_count < STABLE_FRAMES else DETECT_EVERY_N_FRAMES

                    if frame_id % detect_interval == 0:
                        try:
                            results = model(
                                frame,
                                imgsz=IMG_SIZE,
                                conf=CONF_THRES,
                                iou=IOU_THRES,
                                max_det=1,
                                verbose=False
                            )

                            if len(results[0].boxes) > 0:
                                conf = float(results[0].boxes.conf[0])

                                if conf > 0.75:
                                    new_box = results[0].boxes.xyxy[0].cpu().numpy().astype(int)

                                    if is_similar_box(last_box, new_box):
                                        stable_count += 1
                                    else:
                                        stable_count = 0

                                    last_box = new_box
                                else:
                                    last_box = None
                                    stable_count = 0
                            else:
                                last_box = None
                                stable_count = 0

                        except Exception as e:
                            print("YOLO detect error:", e)
                            last_box = None
                            stable_count = 0

                    if last_box is not None:
                        x1, y1, x2, y2 = [int(v) for v in last_box]
                        moving_fast, last_box_center = is_box_moving_fast(last_box, last_box_center)

                        enough_time = (time.time() - last_ocr_time) >= OCR_COOLDOWN

                        if (
                            stable_count >= STABLE_FRAMES
                            and not moving_fast
                            and not ocr_running
                            and ocr_queue.empty()
                            and enough_time
                        ):
                            x1p = max(0, x1 - PADDING)
                            y1p = max(0, y1 - PADDING)
                            x2p = min(frame.shape[1], x2 + PADDING)
                            y2p = min(frame.shape[0], y2 + PADDING)

                            crop = frame[y1p:y2p, x1p:x2p]

                            if crop.size > 0:
                                try:
                                    ocr_running = True
                                    last_ocr_time = time.time()
                                    payload = {
                                        "session_id": get_session_id(),
                                        "crop": crop.copy(),
                                        "frame": frame.copy()
                                    }
                                    ocr_queue.put_nowait(payload)
                                    update_recognition_state(
                                        session_id=get_session_id(),
                                        ocr_running=True
                                    )
                                except Full:
                                    ocr_running = False

                        update_recognition_state(
                            session_id=get_session_id(),
                            camera_enabled=enabled,
                            camera_connected=connected,
                            ip=ip,
                            bbox={
                                "x1": int(x1),
                                "y1": int(y1),
                                "x2": int(x2),
                                "y2": int(y2)
                            },
                            stable_count=int(stable_count),
                            moving_fast=bool(moving_fast),
                            ocr_running=bool(ocr_running),
                            confirmed_plate=confirmed_plate,
                            last_raw_plate=last_raw_plate,
                            plate_votes=safe_counter_to_dict(plate_votes),
                            live_candidates=live_candidates,
                            fps=int(fps),
                            scan_locked=bool(scan_locked),
                            locked_snapshot=locked_snapshot_b64,
                            locked_plate_crop=locked_plate_crop_b64,
                            message="Detection running"
                        )
                    else:
                        update_recognition_state(
                            session_id=get_session_id(),
                            camera_enabled=enabled,
                            camera_connected=connected,
                            ip=ip,
                            bbox=None,
                            stable_count=int(stable_count),
                            moving_fast=False,
                            ocr_running=bool(ocr_running),
                            confirmed_plate=confirmed_plate,
                            last_raw_plate=last_raw_plate,
                            plate_votes=safe_counter_to_dict(plate_votes),
                            live_candidates=live_candidates,
                            fps=int(fps),
                            scan_locked=bool(scan_locked),
                            locked_snapshot=locked_snapshot_b64,
                            locked_plate_crop=locked_plate_crop_b64,
                            message="No plate detected"
                        )
                else:
                    update_recognition_state(
                        session_id=get_session_id(),
                        camera_enabled=enabled,
                        camera_connected=connected,
                        ip=ip,
                        bbox=None,
                        stable_count=int(stable_count),
                        moving_fast=False,
                        ocr_running=False,
                        confirmed_plate=confirmed_plate,
                        last_raw_plate=last_raw_plate,
                        plate_votes=safe_counter_to_dict(plate_votes),
                        live_candidates=live_candidates,
                        fps=int(fps),
                        scan_locked=bool(scan_locked),
                        locked_snapshot=locked_snapshot_b64,
                        locked_plate_crop=locked_plate_crop_b64,
                        message="Scan locked with confirmed result" if scan_locked else "Camera connected"
                    )

                display_frame = draw_overlay(frame, moving_fast=moving_fast)

            if time.time() - fps_start >= 1:
                fps = fps_counter
                fps_counter = 0
                fps_start = time.time()

            if not scan_locked:
                with frame_lock:
                    latest_jpeg = encode_frame_to_jpeg(display_frame)

            try:
                cv2.imshow("LPR SINGLE-READ LOCK MODE", display_frame)
            except cv2.error as e:
                print("imshow error:", e)

        else:
            frame = np.zeros((STREAM_HEIGHT, STREAM_WIDTH, 3), dtype=np.uint8)
            cv2.putText(
                frame,
                "HE THONG DA KHOI DONG",
                (130, 100),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.9,
                (0, 255, 0),
                2
            )
            cv2.putText(
                frame,
                "Camera dang tat",
                (210, 150),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.8,
                (0, 255, 255),
                2
            )
            cv2.putText(
                frame,
                "Nhan I de nhap IP",
                (190, 200),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.7,
                (255, 255, 255),
                2
            )
            cv2.putText(
                frame,
                "Nhan O de mo camera",
                (170, 235),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.7,
                (255, 255, 255),
                2
            )
            cv2.putText(
                frame,
                "Nhan R de reset",
                (190, 270),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.7,
                (255, 255, 255),
                2
            )
            cv2.putText(
                frame,
                "Nhan Q de thoat",
                (210, 305),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.7,
                (255, 255, 255),
                2
            )

            if current_ip:
                cv2.putText(
                    frame,
                    f"IP hien tai: {current_ip}",
                    (120, 340),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    0.6,
                    (180, 180, 180),
                    2
                )

            with frame_lock:
                latest_jpeg = encode_frame_to_jpeg(frame)

            update_recognition_state(
                session_id=get_session_id(),
                camera_enabled=False,
                camera_connected=False,
                ip=current_ip,
                bbox=None,
                stable_count=int(stable_count),
                moving_fast=False,
                confirmed_plate=confirmed_plate,
                last_raw_plate=last_raw_plate,
                plate_votes=safe_counter_to_dict(plate_votes),
                live_candidates=live_candidates,
                ocr_running=bool(ocr_running),
                fps=0,
                scan_locked=bool(scan_locked),
                locked_snapshot=locked_snapshot_b64,
                locked_plate_crop=locked_plate_crop_b64,
                message="Camera is off"
            )

            try:
                cv2.imshow("LPR SINGLE-READ LOCK MODE", frame)
            except cv2.error as e:
                print("imshow error:", e)

        key = cv2.waitKey(1) & 0xFF

        if key == ord("i"):
            new_ip = input("\nNhap IP Webcam: ").strip()
            if new_ip:
                set_camera_flags(ip=new_ip)
                current_ip = new_ip
                update_recognition_state(
                    session_id=get_session_id(),
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
                    reason="Manual reset done. Ready to scan again.",
                    new_session=True
                )
                enabled2, ip2, connected2 = get_camera_flags()
                update_recognition_state(
                    session_id=get_session_id(),
                    camera_enabled=enabled2,
                    camera_connected=connected2,
                    ip=ip2,
                    message="Manual reset done. Ready to scan again."
                )

        elif key == ord("q"):
            break

    stop_event.set()

    with api_lock:
        close_camera()

    try:
        ocr_queue.put_nowait(None)
    except Full:
        pass

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
            ocr_queue.put_nowait(None)
        except Full:
            pass

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
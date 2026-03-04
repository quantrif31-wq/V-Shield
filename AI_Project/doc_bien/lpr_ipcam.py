import os
import sys
import site

# ===== FIX SITE FOR PYINSTALLER =====
if site.USER_SITE is None:
    site.USER_SITE = os.path.dirname(sys.executable) if getattr(sys, 'frozen', False) else os.getcwd()

# ===== FIX PADDLE FOR PYINSTALLER =====
os.environ["FLAGS_enable_pir_api"] = "0"
os.environ["FLAGS_use_mkldnn"] = "0"
os.environ["FLAGS_enable_parallel_graph"] = "0"
os.environ["FLAGS_use_cinn"] = "0"
os.environ["FLAGS_log_level"] = "3"
os.environ["GLOG_minloglevel"] = "3"

sys.modules['Cython'] = None

# ===== FIX IMPORT WHEN RUN AS EXE =====
if getattr(sys, 'frozen', False):
    exe_dir = os.path.dirname(sys.executable)
    sys.path.insert(0, exe_dir)
import paddle
try:
    paddle.utils.cpp_extension.extension_utils._jit_compile = False
except:
    pass

# ===== NORMAL IMPORTS =====
import cv2
import torch
import time
import re
import numpy as np
from ultralytics import YOLO
from paddleocr import PaddleOCR
from collections import Counter
import logging
import threading
from queue import Queue
# ================== SILENT ==================
os.environ["FLAGS_log_level"] = "3"
os.environ["GLOG_minloglevel"] = "3"
logging.disable(logging.WARNING)
logging.getLogger("ppocr").setLevel(logging.ERROR)

# ================== CAMERA INPUT ==================
ip_input = input("Nhập IP Webcam: ").strip()
if not ip_input:
    print("Không nhập IP. Thoát.")
    sys.exit()

IP_STREAM = ip_input

# ================== CONFIG ==================
if getattr(sys, 'frozen', False):
    base_path = sys._MEIPASS
else:
    base_path = os.path.dirname(os.path.abspath(__file__))

MODEL_PATH = os.path.join(base_path, "best.pt")
CONF_THRES = 0.7
IOU_THRES = 0.6
IMG_SIZE = 416

STABLE_FRAMES = 3
DETECT_EVERY_N_FRAMES = 5
PADDING = 20

WAIT_TIMEOUT = 2
CONFIRM_MIN_VOTES = 3
CONFIRM_RATIO = 0.6

# ================== GLOBAL ==================
last_box_center = None

ocr_queue = Queue(maxsize=1)
ocr_result = None
ocr_running = False

# ===== Session State Machine =====
session_active = False
session_votes = Counter()
session_confirmed = False
confirmed_plate = None
last_seen_time = 0

# ================== UTILS ==================

def is_box_moving_fast(box, prev_center, threshold=20):
    x1, y1, x2, y2 = box
    center = ((x1+x2)//2, (y1+y2)//2)
    if prev_center is None:
        return False, center
    dist = np.linalg.norm(np.array(center) - np.array(prev_center))
    return dist > threshold, center

def is_similar_box(box1, box2, threshold=15):
    if box1 is None or box2 is None:
        return False
    return np.all(np.abs(box1 - box2) < threshold)

# ================== DEVICE ==================
torch.set_grad_enabled(False)
torch.set_num_threads(4)
device = "cuda" if torch.cuda.is_available() else "cpu"
print("Device:", device)

# ================== LOAD MODEL ==================
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

# ================== VALIDATION ==================

def validate_plate(text):
    text = text.replace(" ", "").replace("-", "")

    pattern = r'^(\d{2})([A-Z]{1,2})(\d{5})$'
    match = re.match(pattern, text)

    if not match:
        return False, None

    province = match.group(1)
    series = match.group(2)
    number = match.group(3)

    # Ví dụ: nếu series có 2 chữ -> thường là ô tô mới
    if len(series) == 2:
        vehicle_type = "car"
    else:
        vehicle_type = "bike_or_car"

    return True, vehicle_type

# ================== ENHANCE ==================

def auto_brightness_contrast(image):
    lab = cv2.cvtColor(image, cv2.COLOR_BGR2LAB)
    l, a, b = cv2.split(lab)
    clahe = cv2.createCLAHE(clipLimit=3.0, tileGridSize=(8,8))
    l = clahe.apply(l)
    lab = cv2.merge((l, a, b))
    return cv2.cvtColor(lab, cv2.COLOR_LAB2BGR)

def sharpen_image(img):
    kernel = np.array([[0,-1,0],[-1,5,-1],[0,-1,0]])
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
        (h, w) = img.shape[:2]
        M = cv2.getRotationMatrix2D((w//2, h//2), angle, 1.0)
        img = cv2.warpAffine(img, M, (w, h),
                             flags=cv2.INTER_LINEAR,
                             borderMode=cv2.BORDER_REPLICATE)
    return img

def normalize_plate_size(gray):
    h, w = gray.shape
    target_height = 80
    scale = target_height / h
    return cv2.resize(gray, (int(w * scale), target_height))

def is_bad_lighting(gray):
    mean_val = np.mean(gray)
    return mean_val < 40 or mean_val > 220

def enhance_plate(crop):
    gray = cv2.cvtColor(crop, cv2.COLOR_BGR2GRAY)
    if is_bad_lighting(gray):
        crop = auto_brightness_contrast(crop)
        crop = sharpen_image(crop)
    crop = deskew_plate(crop)
    gray = cv2.cvtColor(crop, cv2.COLOR_BGR2GRAY)
    gray = normalize_plate_size(gray)
    return cv2.cvtColor(gray, cv2.COLOR_GRAY2BGR)

# ================== OCR ==================

def extract_text_from_ocr(result):
    lines = []
    confidences = []
    if not result:
        return "", 0
    for res in result:
        if isinstance(res, list):
            for item in res:
                if isinstance(item, (list, tuple)) and len(item) >= 2:
                    text_part = item[1]
                    if isinstance(text_part, (list, tuple)) and len(text_part) >= 2:
                        lines.append(str(text_part[0]))
                        confidences.append(float(text_part[1]))
    if not lines:
        return "", 0
    text = "".join(lines).upper()
    text = re.sub(r'[^A-Z0-9]', '', text)
    avg_conf = sum(confidences) / len(confidences)
    return text, avg_conf

def smart_rotate_ocr(crop):
    rotations = [
        crop,
        cv2.rotate(crop, cv2.ROTATE_90_CLOCKWISE),
        cv2.rotate(crop, cv2.ROTATE_90_COUNTERCLOCKWISE),
        cv2.rotate(crop, cv2.ROTATE_180),
    ]
    best_text = ""
    best_score = 0
    for img in rotations:
        processed = enhance_plate(img)
        result = ocr.ocr(processed)
        text, conf = extract_text_from_ocr(result)
        if text and validate_plate(text) and conf > 0.7:
            score = conf * len(text)
            if score > best_score:
                best_score = score
                best_text = text
    return best_text

def ocr_worker():
    global ocr_result, ocr_running
    while True:
        crop = ocr_queue.get()
        if crop is None:
            break
        text = smart_rotate_ocr(crop)
        if text:
            ocr_result = text
        ocr_running = False
        ocr_queue.task_done()

# ================== MAIN ==================

try:
    cap = cv2.VideoCapture(IP_STREAM, cv2.CAP_FFMPEG)
    cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)

    if not cap.isOpened():
        print("Không thể mở camera.")
        sys.exit()

    print("System started")

    threading.Thread(target=ocr_worker, daemon=True).start()

    stable_count = 0
    last_box = None
    frame_id = 0

    fps_counter = 0
    fps_start = time.time()
    fps = 0

    while True:
        ret, frame = cap.read()
        if not ret:
            continue

        frame_id += 1
        frame = cv2.resize(frame, (640, 360))

        detect_interval = 1 if stable_count < STABLE_FRAMES else DETECT_EVERY_N_FRAMES

        if frame_id % detect_interval == 0:
            results = model(frame, imgsz=IMG_SIZE,
                            conf=CONF_THRES, iou=IOU_THRES,
                            max_det=1, verbose=False)

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

        # ================= SESSION LOGIC =================
        if last_box is not None:
            x1, y1, x2, y2 = last_box
            moving_fast, globals()['last_box_center'] = is_box_moving_fast(
                last_box, globals()['last_box_center']
            )

            if not session_active:
                session_active = True
                session_votes.clear()
                session_confirmed = False
                confirmed_plate = None
                print("New vehicle detected")

            last_seen_time = time.time()

            if (stable_count >= STABLE_FRAMES
                and not ocr_running
                and ocr_queue.empty()
                and not session_confirmed):

                x1p = max(0, x1 - PADDING)
                y1p = max(0, y1 - PADDING)
                x2p = min(frame.shape[1], x2 + PADDING)
                y2p = min(frame.shape[0], y2 + PADDING)

                crop = frame[y1p:y2p, x1p:x2p]
                if crop.size > 0:
                    ocr_running = True
                    ocr_queue.put(crop.copy())

            cv2.rectangle(frame, (x1,y1), (x2,y2),
                          (0,255,0) if not moving_fast else (0,255,255), 2)

        # ===== OCR RESULT =====
        if ocr_result:
            detected = ocr_result
            ocr_result = None

            if session_active and not session_confirmed:
                session_votes[detected] += 1

                total = sum(session_votes.values())
                best_plate, best_count = session_votes.most_common(1)[0]

                if (best_count >= CONFIRM_MIN_VOTES and
                    best_count / total >= CONFIRM_RATIO):

                    confirmed_plate = best_plate
                    session_confirmed = True
                    print("Plate confirmed:", confirmed_plate)

        # ===== SESSION END =====
        if session_active:
            if time.time() - last_seen_time > WAIT_TIMEOUT:
                print("Vehicle exited")
                session_active = False
                session_votes.clear()
                session_confirmed = False
                confirmed_plate = None

        # ===== DISPLAY =====
        display_status = "Dang cho bien..."
        if session_active:
            if session_confirmed:
                display_status = f"Da xac nhan: {confirmed_plate}"
            else:
                display_status = "Dang doc..."

        fps_counter += 1
        if time.time() - fps_start >= 1:
            fps = fps_counter
            fps_counter = 0
            fps_start = time.time()

        cv2.putText(frame, f"FPS: {fps}",
                    (20,40), cv2.FONT_HERSHEY_SIMPLEX,
                    1, (255,0,0), 2)

        cv2.putText(frame, display_status,
                    (20,80), cv2.FONT_HERSHEY_SIMPLEX,
                    0.8, (0,255,0), 2)

        cv2.imshow("LPR SYSTEM PRO MAX", frame)

        if cv2.waitKey(1) & 0xFF == ord("q"):
            break

except KeyboardInterrupt:
    print("Thoát an toàn...")

finally:
    ocr_queue.put(None)
    cap.release()
    cv2.destroyAllWindows()
    print("Đã giải phóng tài nguyên.")
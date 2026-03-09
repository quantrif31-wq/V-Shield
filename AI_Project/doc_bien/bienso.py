import os
import sys
import site
import cv2
import torch
import time
import re
import numpy as np
import logging
import threading

from ultralytics import YOLO
from paddleocr import PaddleOCR
from collections import Counter
from queue import Queue

from fastapi import FastAPI
from pydantic import BaseModel
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
# ================== FIX ENV ==================
if site.USER_SITE is None:
    site.USER_SITE = os.getcwd()

os.environ["FLAGS_enable_pir_api"] = "0"
os.environ["FLAGS_use_mkldnn"] = "0"
os.environ["FLAGS_enable_parallel_graph"] = "0"
os.environ["FLAGS_use_cinn"] = "0"
os.environ["FLAGS_log_level"] = "3"
os.environ["GLOG_minloglevel"] = "3"

logging.disable(logging.WARNING)
logging.getLogger("ppocr").setLevel(logging.ERROR)

# ================== FASTAPI ==================
app = FastAPI(title="License Plate Recognition API")

# ================== CONFIG ==================
MODEL_PATH = "best.pt"

CONF_THRES = 0.7
IOU_THRES = 0.6
IMG_SIZE = 416

STABLE_FRAMES = 3
DETECT_EVERY_N_FRAMES = 5
PADDING = 20

WAIT_TIMEOUT = 2
CONFIRM_MIN_VOTES = 3
CONFIRM_RATIO = 0.6

# ================== DEVICE ==================
torch.set_grad_enabled(False)
torch.set_num_threads(4)
device = "cuda" if torch.cuda.is_available() else "cpu"

# ================== LOAD MODEL ==================
print("Loading YOLO...")
model = YOLO(MODEL_PATH)
model.to(device)
model.fuse()

if device == "cuda":
    model.half()

print("Loading OCR...")
ocr = PaddleOCR(
    use_angle_cls=False,
    lang="en",
    show_log=False,
    use_gpu=(device == "cuda")
)

# ================== GLOBAL ==================
cap = None
frame = None
lock = threading.Lock()

last_box = None
last_box_center = None

stable_count = 0
frame_id = 0

fps = 0
fps_counter = 0
fps_start = time.time()

ocr_queue = Queue(maxsize=1)
ocr_running = False
ocr_result = None

session_active = False
session_votes = Counter()
session_confirmed = False
confirmed_plate = None
last_seen_time = 0


# ================== REQUEST MODEL ==================

class CameraInput(BaseModel):
    ip: str


# ================== UTILS ==================

def is_box_moving_fast(box, prev_center, threshold=20):
    x1,y1,x2,y2 = box
    center = ((x1+x2)//2,(y1+y2)//2)

    if prev_center is None:
        return False,center

    dist = np.linalg.norm(np.array(center)-np.array(prev_center))
    return dist>threshold,center


def is_similar_box(box1,box2,threshold=15):

    if box1 is None or box2 is None:
        return False

    return np.all(np.abs(box1-box2)<threshold)


def validate_plate(text):

    text=text.replace(" ","").replace("-","")

    pattern=r'^\d{2}[A-Z]{1,2}\d{4,6}$'
    match=re.match(pattern,text)

    if not match:
        return False

    return True


# ================== IMAGE ENHANCE ==================

def auto_brightness_contrast(image):

    lab=cv2.cvtColor(image,cv2.COLOR_BGR2LAB)

    l,a,b=cv2.split(lab)

    clahe=cv2.createCLAHE(clipLimit=3.0,tileGridSize=(8,8))

    l=clahe.apply(l)

    lab=cv2.merge((l,a,b))

    return cv2.cvtColor(lab,cv2.COLOR_LAB2BGR)


def sharpen_image(img):

    kernel=np.array([[0,-1,0],[-1,5,-1],[0,-1,0]])

    return cv2.filter2D(img,-1,kernel)

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

        img = cv2.warpAffine(
            img,
            M,
            (w, h),
            flags=cv2.INTER_LINEAR,
            borderMode=cv2.BORDER_REPLICATE
        )

    return img

def enhance_plate(crop):

    gray=cv2.cvtColor(crop,cv2.COLOR_BGR2GRAY)

    mean_val=np.mean(gray)

    if mean_val<40 or mean_val>220:

        crop=auto_brightness_contrast(crop)

        crop=sharpen_image(crop)
    crop = deskew_plate(crop)

    gray=cv2.cvtColor(crop,cv2.COLOR_BGR2GRAY)

    gray = cv2.resize(gray, (320, 160))

    return cv2.cvtColor(gray,cv2.COLOR_GRAY2BGR)


# ================== OCR ==================

def extract_text_from_ocr(result):

    lines=[]
    confs=[]

    if not result:
        return "",0

    for res in result:

        if isinstance(res,list):

            for item in res:

                if isinstance(item,(list,tuple)) and len(item)>=2:

                    text_part=item[1]

                    lines.append(text_part[0])
                    confs.append(text_part[1])

    if not lines:
        return "",0

    text="".join(lines).upper()

    text=re.sub(r'[^A-Z0-9]','',text)

    avg=sum(confs)/len(confs)

    return text,avg


def smart_rotate_ocr(crop):

    crop = deskew_plate(crop)

    rotations = [
        crop,
        cv2.rotate(crop, cv2.ROTATE_90_CLOCKWISE),
        cv2.rotate(crop, cv2.ROTATE_180),
        cv2.rotate(crop, cv2.ROTATE_90_COUNTERCLOCKWISE)
    ]

    for img in rotations:

        processed = enhance_plate(img)

        result = ocr.ocr(processed)

        text, conf = extract_text_from_ocr(result)

        if text and validate_plate(text) and conf > 0.7:
            return text

    return ""


def ocr_worker():

    global ocr_running,ocr_result

    while True:

        crop=ocr_queue.get()

        if crop is None:
            break

        text=smart_rotate_ocr(crop)

        if text:
            ocr_result=text

        ocr_running=False

        ocr_queue.task_done()


# ================== CAMERA LOOP ==================

def camera_loop():

    global frame,stable_count,last_box,frame_id,fps_counter,fps_start,fps
    global session_active,session_votes,session_confirmed,confirmed_plate,last_seen_time
    global ocr_running,ocr_result,last_box_center

    while True:

        ret,img=cap.read()

        if not ret:
            continue

        frame_id+=1

        img=cv2.resize(img,(640,360))

        detect_interval=1 if stable_count<STABLE_FRAMES else DETECT_EVERY_N_FRAMES

        if frame_id%detect_interval==0:

            results=model(img,imgsz=IMG_SIZE,conf=CONF_THRES,iou=IOU_THRES,max_det=1,verbose=False)

            if len(results[0].boxes)>0:

                conf=float(results[0].boxes.conf[0])

                if conf>0.75:

                    new_box=results[0].boxes.xyxy[0].cpu().numpy().astype(int)

                    if is_similar_box(last_box,new_box):

                        stable_count+=1

                    else:

                        stable_count=0

                    last_box=new_box

                else:

                    last_box=None
                    stable_count=0

            else:

                last_box=None
                stable_count=0

        if last_box is not None:

            x1,y1,x2,y2=last_box

            moving_fast,last_box_center=is_box_moving_fast(last_box,last_box_center)

            if not session_active:

                session_active=True
                session_votes.clear()
                session_confirmed=False
                confirmed_plate=None

            last_seen_time=time.time()

            if stable_count>=STABLE_FRAMES and not ocr_running and ocr_queue.empty() and not session_confirmed:

                x1p = max(0, x1 - PADDING)
                y1p = max(0, y1 - PADDING)
                x2p = min(img.shape[1], x2 + PADDING)
                y2p = min(img.shape[0], y2 + PADDING)

                crop = img[y1p:y2p, x1p:x2p]
                #cv2.imwrite("debug_plate.jpg", crop)

                

                if crop.size>0:

                    ocr_running=True

                    ocr_queue.put(crop.copy())

        if ocr_result:

            detected=ocr_result

            ocr_result=None

            if session_active and not session_confirmed:

                session_votes[detected]+=1

                total=sum(session_votes.values())

                best_plate,best_count=session_votes.most_common(1)[0]

                if best_count>=CONFIRM_MIN_VOTES and best_count/total>=CONFIRM_RATIO:

                    confirmed_plate=best_plate

                    session_confirmed=True

        if session_active:

            if time.time()-last_seen_time>WAIT_TIMEOUT:

                session_active=False
                session_votes.clear()
                session_confirmed=False
                confirmed_plate=None

        fps_counter+=1

        if time.time()-fps_start>=1:

            fps=fps_counter
            fps_counter=0
            fps_start=time.time()

        with lock:
            frame=img.copy()


# ================== API ==================

@app.post("/start_camera")
def start_camera(data:CameraInput):

    global cap

    cap=cv2.VideoCapture(data.ip)

    if not cap.isOpened():

        return {"status":"error","message":"cannot open camera"}

    threading.Thread(target=ocr_worker,daemon=True).start()
    threading.Thread(target=camera_loop,daemon=True).start()

    return {"status":"camera started"}


@app.get("/plate")

def get_plate():

    global frame,last_box,confirmed_plate,session_active,session_confirmed,fps

    with lock:

        box=None

        if last_box is not None:

            x1,y1,x2,y2=[int(v) for v in last_box]

            box={
                "x1":x1,
                "y1":y1,
                "x2":x2,
                "y2":y2
            }

    return {

        "plate":confirmed_plate,

        "session_active":session_active,

        "confirmed":session_confirmed,

        "box":box,

        "fps":fps
    }

@app.get("/status")
def status():
    return {"status": "running"}
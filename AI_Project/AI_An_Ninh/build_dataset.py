import cv2
import numpy as np
from ultralytics import YOLO
from collections import deque
import os

# ===== CONFIG =====
DATA_PATH = "hanh_vi/ngat/data"
SEQ_LEN = 30

yolo = YOLO("yolov8n.pt")

def extract_feature(prev, box):
    x1,y1,x2,y2 = box
    w = x2-x1
    h = y2-y1
    cx = x1 + w/2
    cy = y1 + h/2
    aspect = w/(h+1e-6)

    if prev is None:
        dx,dy = 0,0
    else:
        dx = cx-prev[0]
        dy = cy-prev[1]

    speed = (dx**2+dy**2)**0.5
    return np.array([cx,cy,w,h,aspect,dx,dy,speed],dtype=np.float32),(cx,cy)


def process_video(path, label):
    cap = cv2.VideoCapture(path)
    prev=None
    seq=deque(maxlen=SEQ_LEN)
    X=[]
    y=[]

    while True:
        ret,frame=cap.read()
        if not ret:
            break

        res = yolo(frame)[0]

        if res.boxes is None or len(res.boxes) == 0:
            continue

        box = res.boxes.xyxy[0].cpu().numpy()
        feat, prev = extract_feature(prev, box)

        seq.append(feat)

        if len(seq) == SEQ_LEN:
            X.append(np.array(seq))
            y.append(label)

    return X, y


X=[]
y=[]

# ===== FALL =====
fall_path = os.path.join(DATA_PATH, "fall")

for file in os.listdir(fall_path):
    if file.endswith(".avi") or file.endswith(".mp4"):
        full_path = os.path.join(fall_path, file)
        print("Processing FALL:", full_path)

        x1, y1 = process_video(full_path, 1)
        X += x1
        y += y1


# ===== NORMAL =====
normal_path = os.path.join(DATA_PATH, "normal")

for file in os.listdir(normal_path):
    if file.endswith(".avi") or file.endswith(".mp4"):
        full_path = os.path.join(normal_path, file)
        print("Processing NORMAL:", full_path)

        x1, y1 = process_video(full_path, 0)
        X += x1
        y += y1


# ===== SAVE =====
X = np.array(X)
y = np.array(y)

print("Dataset shape:", X.shape)

os.makedirs("hanh_vi/ngat/data", exist_ok=True)
np.savez("hanh_vi/ngat/data/dataset.npz", X=X, y=y)

print("DONE BUILD DATASET")
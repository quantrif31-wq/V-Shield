import face_recognition
import cv2
import pickle
import numpy as np

VIDEO_PATH = "me.mp4"
OUTPUT = "face_model.pkl"

encodings = []

cap = cv2.VideoCapture(VIDEO_PATH)

frame_id = 0

print("Start training from video...")

while True:

    ret, frame = cap.read()

    if not ret:
        break

    frame_id += 1

    # lấy mỗi 5 frame
    if frame_id % 5 != 0:
        continue

    rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

    faces = face_recognition.face_locations(rgb, model="hog")

    if not faces:
        continue

    face_enc = face_recognition.face_encodings(rgb, faces)

    for enc in face_enc:
        encodings.append(enc)

    print("Collected encodings:", len(encodings))

cap.release()

print("Total encodings:", len(encodings))

# lưu model
with open(OUTPUT, "wb") as f:
    pickle.dump(encodings, f)

print("Model saved to", OUTPUT)

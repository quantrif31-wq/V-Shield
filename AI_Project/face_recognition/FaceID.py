from fastapi import FastAPI
import face_recognition
import cv2
import time
import threading
from collections import deque

app = FastAPI()

# ================= CONFIG =================
THRESHOLD = 0.4
CONFIRM_FRAMES = 3
LOST_TIMEOUT = 2.0
ENCODE_INTERVAL = 0.7
FRAME_WIDTH = 480
ROTATE_MODE = -90

# ================= GLOBAL STATE =================
running = False
cap = None

frame = None
frame_lock = threading.Lock()

# face state
session_active = False
session_confirmed = False
confirm_count = 0
last_seen_time = 0
last_encode_time = 0

distance_buffer = deque(maxlen=5)

# API result
result_state = {
    "camera_running": False,
    "session_active": False,
    "session_confirmed": False,
    "confirm_count": 0,
    "distance": None,
    "last_seen": None
}

# ================= LOAD FACE =================
print("Loading face model...")

known_image = face_recognition.load_image_file("me.jpg")
encodings = face_recognition.face_encodings(known_image)

if not encodings:
    raise Exception("No face found in me.jpg")

known_encoding = encodings[0]

print("Face model loaded")


# ================= CAMERA THREAD =================
def camera_thread(ip_url):

    global frame
    global cap
    global running

    cap = cv2.VideoCapture(ip_url, cv2.CAP_FFMPEG)
    cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)

    if not cap.isOpened():
        print("Cannot open camera")
        running = False
        return

    while running:

        ret, f = cap.read()

        if ret:
            with frame_lock:
                frame = f


# ================= FACE PROCESS THREAD =================
def face_processing():

    global session_active
    global session_confirmed
    global confirm_count
    global last_seen_time
    global last_encode_time
    global result_state

    while running:

        if frame is None:
            time.sleep(0.01)
            continue

        with frame_lock:
            local_frame = frame.copy()

        # resize
        h, w = local_frame.shape[:2]
        scale = FRAME_WIDTH / w
        local_frame = cv2.resize(local_frame, (FRAME_WIDTH, int(h * scale)))

        # rotate
        if ROTATE_MODE == 90:
            local_frame = cv2.rotate(local_frame, cv2.ROTATE_90_CLOCKWISE)
        elif ROTATE_MODE == -90:
            local_frame = cv2.rotate(local_frame, cv2.ROTATE_90_COUNTERCLOCKWISE)
        elif ROTATE_MODE == 180:
            local_frame = cv2.rotate(local_frame, cv2.ROTATE_180)

        rgb = cv2.cvtColor(local_frame, cv2.COLOR_BGR2RGB)

        face_locations = face_recognition.face_locations(rgb, model="hog")

        current_time = time.time()

        if face_locations:

            if current_time - last_encode_time > ENCODE_INTERVAL:

                enc = face_recognition.face_encodings(rgb, [face_locations[0]])

                if enc:

                    distance = face_recognition.face_distance(
                        [known_encoding],
                        enc[0]
                    )[0]

                    distance_buffer.append(distance)

                    avg_distance = sum(distance_buffer) / len(distance_buffer)

                    if not session_active:
                        session_active = True
                        session_confirmed = False
                        confirm_count = 0
                        print("New person detected")

                    last_seen_time = current_time

                    if avg_distance < THRESHOLD:
                        confirm_count += 1
                    else:
                        confirm_count = 0

                    if confirm_count >= CONFIRM_FRAMES and not session_confirmed:
                        session_confirmed = True
                        print("Identity confirmed")

                    last_encode_time = current_time

                    result_state = {
                        "camera_running": True,
                        "session_active": session_active,
                        "session_confirmed": session_confirmed,
                        "confirm_count": confirm_count,
                        "distance": float(avg_distance),
                        "last_seen": last_seen_time
                    }

        # face lost
        if session_active and current_time - last_seen_time > LOST_TIMEOUT:

            print("Person left")

            session_active = False
            session_confirmed = False
            confirm_count = 0
            distance_buffer.clear()

            result_state = {
                "camera_running": True,
                "session_active": False,
                "session_confirmed": False,
                "confirm_count": 0,
                "distance": None,
                "last_seen": None
            }

        time.sleep(0.01)


# ================= API =================

@app.get("/")
def root():
    return {"service": "face-ai-running"}


@app.post("/camera/start")
def start_camera(ip_url: str):

    global running

    if running:
        return {"status": "already_running"}

    running = True

    threading.Thread(
        target=camera_thread,
        args=(ip_url,),
        daemon=True
    ).start()

    threading.Thread(
        target=face_processing,
        daemon=True
    ).start()

    result_state["camera_running"] = True

    return {"status": "camera_started"}


@app.post("/camera/stop")
def stop_camera():

    global running
    global cap

    running = False

    if cap:
        cap.release()

    result_state["camera_running"] = False

    return {"status": "camera_stopped"}


@app.get("/camera/status")
def camera_status():
    return result_state

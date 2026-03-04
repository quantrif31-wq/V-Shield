import face_recognition
import cv2
import time
import threading
import signal
import sys
from collections import deque

# ================= CONFIG =================
THRESHOLD = 0.4
CONFIRM_FRAMES = 3
LOST_TIMEOUT = 2.0
ENCODE_INTERVAL = 0.7
FRAME_WIDTH = 480
ROTATE_MODE = -90  # 0, 90, -90, 180

# ================= SAFE EXIT =================
running = True
def signal_handler(sig, frame):
    global running
    running = False
signal.signal(signal.SIGINT, signal_handler)

# ================= INPUT =================
ip_url = input("Nhập IP camera: ").strip()
if not ip_url:
    sys.exit()

print("Load me.jpg...")
known_image = face_recognition.load_image_file("me.jpg")
encodings = face_recognition.face_encodings(known_image)

if not encodings:
    print("Không có mặt trong me.jpg")
    sys.exit()

known_encoding = encodings[0]
print("Load thành công.")

# ================= CAMERA =================
cap = cv2.VideoCapture(ip_url, cv2.CAP_FFMPEG)
cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)

if not cap.isOpened():
    print("Không mở được camera.")
    sys.exit()

frame = None
frame_lock = threading.Lock()

def camera_thread():
    global frame
    while running:
        ret, f = cap.read()
        if ret:
            with frame_lock:
                frame = f

threading.Thread(target=camera_thread, daemon=True).start()

# ================= FACE STATE =================
session_active = False
session_confirmed = False
confirm_count = 0
last_seen_time = 0
last_encode_time = 0
distance_buffer = deque(maxlen=5)
face_box = None

# ================= FACE PROCESS THREAD =================
def face_processing():
    global session_active, session_confirmed
    global confirm_count, last_seen_time
    global last_encode_time, distance_buffer
    global face_box

    while running:

        if frame is None:
            continue

        with frame_lock:
            local_frame = frame.copy()

        # Resize
        h, w = local_frame.shape[:2]
        scale = FRAME_WIDTH / w
        local_frame = cv2.resize(local_frame, (FRAME_WIDTH, int(h * scale)))

        # Rotate
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
            top, right, bottom, left = face_locations[0]
            face_box = (top, right, bottom, left)

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
                        print("Phát hiện người mới.")

                    last_seen_time = current_time

                    if avg_distance < THRESHOLD:
                        confirm_count += 1
                    else:
                        confirm_count = 0

                    if confirm_count >= CONFIRM_FRAMES and not session_confirmed:
                        session_confirmed = True
                        print(f"XÁC NHẬN DANH TÍNH (distance={round(avg_distance,3)})")

                    last_encode_time = current_time
        else:
            face_box = None

        if session_active and current_time - last_seen_time > LOST_TIMEOUT:
            print("Người đã rời đi.")
            session_active = False
            session_confirmed = False
            confirm_count = 0
            distance_buffer.clear()

        time.sleep(0.01)  # tránh ăn 100% CPU

threading.Thread(target=face_processing, daemon=True).start()

# ================= DISPLAY LOOP =================
prev_time = time.time()
fps_smooth = 0

print("Hệ thống FACE ID FINAL bắt đầu...")

while running:

    with frame_lock:
        if frame is None:
            continue
        display_frame = frame.copy()

    h, w = display_frame.shape[:2]
    scale = FRAME_WIDTH / w
    display_frame = cv2.resize(display_frame, (FRAME_WIDTH, int(h * scale)))

    if ROTATE_MODE == 90:
        display_frame = cv2.rotate(display_frame, cv2.ROTATE_90_CLOCKWISE)
    elif ROTATE_MODE == -90:
        display_frame = cv2.rotate(display_frame, cv2.ROTATE_90_COUNTERCLOCKWISE)
    elif ROTATE_MODE == 180:
        display_frame = cv2.rotate(display_frame, cv2.ROTATE_180)

    # Draw face box
    if face_box:
        top, right, bottom, left = face_box
        color = (0,255,0) if session_confirmed else (0,255,255)
        cv2.rectangle(display_frame, (left, top), (right, bottom), color, 2)

    # FPS
    now = time.time()
    delta = now - prev_time
    prev_time = now

    if delta > 0:
        fps = 1/delta
        fps_smooth = fps_smooth*0.9 + fps*0.1

    cv2.putText(display_frame, f"FPS: {int(fps_smooth)}",
                (20,30),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.7,
                (255,255,0),2)

    cv2.imshow("FACE ID FINAL PRO", display_frame)

    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

running = False
cap.release()
cv2.destroyAllWindows()
print("Đã thoát.")

import cv2
import time
import base64
import numpy as np
from pyzbar import pyzbar
from threading import Thread, Lock
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import uvicorn

# ================= STATE =================
state = {
    "running": False,
    "scan_enabled": False,
    "locked": False,
    "qr": "",
    "rtsp": "",
    "connected": False
}

lock = Lock()
frame_lock = Lock()
locked_frame_lock = Lock()

latest_frame = None
locked_frame = None   # frame tại thời điểm quét được QR
stop_flag = False

# ================= FASTAPI =================
app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ================= IMAGE ENHANCE =================
def enhance(img):
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    gray = cv2.equalizeHist(gray)
    return gray

# ================= CAMERA =================
def camera_worker():
    global latest_frame

    cap = None
    current_rtsp = ""

    while not stop_flag:
        with lock:
            running = state["running"]
            rtsp = state["rtsp"]

        if not running:
            time.sleep(0.05)
            continue

        if rtsp != current_rtsp:
            current_rtsp = rtsp
            if cap:
                cap.release()

            print("🔁 connect:", rtsp)
            cap = cv2.VideoCapture(rtsp)
            cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)

        if not cap or not cap.isOpened():
            with lock:
                state["connected"] = False
            time.sleep(0.2)
            continue

        with lock:
            state["connected"] = True

        ret, frame = cap.read()
        if not ret:
            continue

        frame = cv2.resize(frame, (480, 270))

        with frame_lock:
            latest_frame = frame.copy()

        time.sleep(0.01)

    if cap:
        cap.release()

# ================= QR DECODE =================
def decode_qr(frame):
    h, w, _ = frame.shape

    rois = [
        frame,
        frame[h//4:3*h//4, w//4:3*w//4],
        frame[0:h//2, :]
    ]

    for roi in rois:
        gray = enhance(roi)

        for scale in [1.0, 1.5, 2.0]:
            if scale != 1.0:
                resized = cv2.resize(gray, None, fx=scale, fy=scale)
            else:
                resized = gray

            barcodes = pyzbar.decode(resized)

            if barcodes:
                return barcodes[0].data.decode()

    return None

# ================= SCAN =================
def scan_worker():
    global latest_frame, locked_frame

    print("🚀 Scan thread ready")

    while not stop_flag:
        with lock:
            scan = state["scan_enabled"]
            locked_state = state["locked"]

        if not scan or locked_state:
            time.sleep(0.02)
            continue

        with frame_lock:
            frame = None if latest_frame is None else latest_frame.copy()

        if frame is None:
            continue

        qr = decode_qr(frame)

        if qr:
            # 📸 Lưu frame tại đúng thời điểm quét được QR
            with locked_frame_lock:
                locked_frame = frame.copy()

            with lock:
                state["qr"] = qr
                state["locked"] = True
                state["scan_enabled"] = False

            print("🔒 QR LOCKED:", qr)

        time.sleep(0.02)

# ================= API =================
@app.post("/qr/start")
def api_start(data: dict):
    rtsp = data.get("rtsp")

    with lock:
        state["rtsp"] = rtsp
        state["running"] = True
        state["locked"] = False
        state["qr"] = ""
        state["scan_enabled"] = False  # chỉ mở cam

    return {"success": True}


@app.post("/qr/scan")
def api_scan():
    global locked_frame
    with lock:
        state["locked"] = False
        state["qr"] = ""
        state["scan_enabled"] = True
    with locked_frame_lock:
        locked_frame = None

    return {"success": True}


@app.post("/qr/reset")
def api_reset():
    global locked_frame
    with lock:
        state["locked"] = False
        state["qr"] = ""
        state["scan_enabled"] = True
    with locked_frame_lock:
        locked_frame = None

    return {"success": True}


@app.post("/qr/stop")
def api_stop():
    with lock:
        state["running"] = False
        state["scan_enabled"] = False
        state["locked"] = False

    return {"success": True}


@app.get("/qr/result")
def api_result():
    return state


@app.get("/qr/locked-image")
def api_locked_image():
    """Trả về ảnh frame tại thời điểm quét được QR, encode base64 JPEG."""
    with locked_frame_lock:
        frame = None if locked_frame is None else locked_frame.copy()

    if frame is None:
        return {"success": False, "image": ""}

    _, buf = cv2.imencode(".jpg", frame, [cv2.IMWRITE_JPEG_QUALITY, 92])
    b64 = base64.b64encode(buf).decode("utf-8")
    return {"success": True, "image": f"data:image/jpeg;base64,{b64}"}

# ================= MAIN =================
def main():
    global stop_flag

    Thread(target=camera_worker, daemon=True).start()
    Thread(target=scan_worker, daemon=True).start()
    Thread(target=lambda: uvicorn.run(app, host="0.0.0.0", port=8001), daemon=True).start()

    print("\n=== QR FINAL PRO ===")
    print("i = nhập RTSP")
    print("o = mở cam")
    print("r = scan")
    print("q = thoát\n")

    current_rtsp = ""

    while True:
        frame = None

        with frame_lock:
            if latest_frame is not None:
                frame = latest_frame.copy()

        if frame is None:
            frame = np.zeros((270, 480, 3), dtype=np.uint8)
            cv2.putText(frame, "NO CAMERA", (150, 140),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.8, (255,255,255), 2)

        with lock:
            qr = state["qr"]
            locked = state["locked"]
            scan = state["scan_enabled"]

        if scan:
            cv2.putText(frame, "SCANNING...", (10, 30),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0,165,255), 2)

        if locked:
            cv2.putText(frame, f"LOCKED: {qr}", (10, 60),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0,255,0), 2)

        cv2.imshow("QR FINAL", frame)

        key = cv2.waitKey(1) & 0xFF

        if key == ord("i"):
            current_rtsp = input("RTSP: ").strip()
            with lock:
                state["rtsp"] = current_rtsp

        elif key == ord("o"):
            with lock:
                state["running"] = True

        elif key == ord("r"):
            with lock:
                state["locked"] = False
                state["qr"] = ""
                state["scan_enabled"] = True

            print("🔍 scanning...")

        elif key == ord("q"):
            break

    stop_flag = True
    cv2.destroyAllWindows()


if __name__ == "__main__":
    main()
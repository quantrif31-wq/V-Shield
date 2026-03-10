import cv2
import time
import re
from ultralytics import YOLO
from paddleocr import PaddleOCR

# =============================
# LOAD MODEL
# =============================

model = YOLO("plate_yolov8n.pt")

ocr = PaddleOCR(
    use_angle_cls=True,
    lang="en",
    show_log=False
)

# =============================
# CAMERA
# =============================

ip_camera = "http://214.212.6.129:8080/video"

cap = cv2.VideoCapture(ip_camera)

plate_text = ""
last_read_time = 0

# regex biển VN
plate_regex = re.compile(r"[0-9]{2}[A-Z][0-9]{5}")

# =============================
# MAIN LOOP
# =============================

while True:

    ret, frame = cap.read()

    if not ret:
        break

    # giảm độ phân giải cho nhẹ CPU
    frame = cv2.resize(frame,(640,360))

    results = model(frame, conf=0.4, verbose=False)[0]

    for box in results.boxes.xyxy:

        x1,y1,x2,y2 = map(int,box)

        plate = frame[y1:y2, x1:x2]

        if plate.size == 0:
            continue

        # resize biển
        plate = cv2.resize(plate,(320,160))

        # =============================
        # XỬ LÝ ẢNH CHO OCR
        # =============================

        gray = cv2.cvtColor(plate, cv2.COLOR_BGR2GRAY)

        plate_bin = cv2.adaptiveThreshold(
            gray,
            255,
            cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
            cv2.THRESH_BINARY,
            11,
            2
        )

        # =============================
        # OCR MỖI 3 GIÂY
        # =============================

        if time.time() - last_read_time > 3:

            result = ocr.ocr(plate_bin)

            text = ""

            if result and result[0]:

                for line in result[0]:

                    if line is None:
                        continue

                    text += line[1][0]

            text = text.replace(" ", "").upper()

            # lọc format biển VN
            match = plate_regex.search(text)

            if match:

                plate_text = match.group()

                print("PLATE:", plate_text)

                last_read_time = time.time()

        # =============================
        # VẼ KHUNG
        # =============================

        cv2.rectangle(
            frame,
            (x1,y1),
            (x2,y2),
            (0,255,0),
            2
        )

        if plate_text:

            cv2.putText(
                frame,
                plate_text,
                (x1,y1-10),
                cv2.FONT_HERSHEY_SIMPLEX,
                1,
                (0,255,0),
                2
            )

    # thu nhỏ màn hình
    display = cv2.resize(frame,None,fx=0.7,fy=0.7)

    cv2.imshow("Plate Reader",display)

    if cv2.waitKey(1) == 27:
        break

cap.release()
cv2.destroyAllWindows()
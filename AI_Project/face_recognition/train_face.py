import face_recognition
import cv2
import pickle
import os
import shutil
import numpy as np
import pyodbc

from pathlib import Path

print("=== FACE TRAINING SYSTEM START ===")
# ================== DATABASE ==================
DB_CONN_STR = r"DRIVER={ODBC Driver 17 for SQL Server};SERVER=(localdb)\MSSQLLocalDB;DATABASE=AccessControlDB;Trusted_Connection=yes;TrustServerCertificate=yes"


# ==============================
# XÁC ĐỊNH ROOT V-SHIELD
# ==============================

current_path = Path(__file__).resolve()

# tìm thư mục V-Shield
for parent in current_path.parents:
    if parent.name == "V-Shield":
        ROOT = parent
        break

print("Project root:", ROOT)
# ================== CONNECT DATABASE ==================
conn = pyodbc.connect(DB_CONN_STR)
cursor = conn.cursor()

print("Database connected")


# ==============================
# CÁC ĐƯỜNG DẪN
# ==============================

VIDEO_NOTOK = ROOT / "API/API/API/wwwroot/uploads/VideoFace/video_notok"
VIDEO_OK = ROOT / "API/API/API/wwwroot/uploads/VideoFace/video_ok"
FACE_MODEL = ROOT / "API/API/API/wwwroot/uploads/VideoFace/FaceID"

# tạo folder nếu chưa có
VIDEO_OK.mkdir(parents=True, exist_ok=True)
FACE_MODEL.mkdir(parents=True, exist_ok=True)

# ==============================
# LẤY DANH SÁCH VIDEO MP4
# ==============================

video_files = list(VIDEO_NOTOK.glob("*.mp4"))

if not video_files:
    print("No mp4 files found.")
    exit()

print("Found", len(video_files), "videos")

# ==============================
# TRAIN TỪNG VIDEO
# ==============================

for video_path in video_files:

    print("\n=============================")
    print("Processing:", video_path.name)

    video_name = video_path.stem
    # ==========================
# LẤY EMPLOYEE ID TỪ TÊN FILE
# ==========================

    parts = video_name.split("_")

    if len(parts) < 2:
        raise Exception("Invalid video name format")

    employee_id = int(parts[1])

    model_path = FACE_MODEL / f"{video_name}.pkl"
    temp_model = FACE_MODEL / f"{video_name}.tmp"

    encodings = []

    try:

        cap = cv2.VideoCapture(str(video_path))

        frame_id = 0

        print("Start training...")

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

        if len(encodings) == 0:
            raise Exception("No face found in video")

        print("Total encodings:", len(encodings))

        # ==========================
        # LƯU MODEL TẠM
        # ==========================

        with open(temp_model, "wb") as f:
            pickle.dump(encodings, f)

        # rename thành file chính
        os.rename(temp_model, model_path)

        print("Model saved:", model_path.name)
        # ==========================
        # SAVE MODEL INFO TO DATABASE
        # ==========================

        cursor.execute("""
        INSERT INTO EmployeeFaceModels
        (EmployeeId, ModelFileName, ModelPath, CreatedAt)
        VALUES (?, ?, ?, GETDATE())
        """,
        employee_id,
        model_path.name,
        str(model_path)
        )

        conn.commit()

        print("Model saved to database for employee:", employee_id)


        # ==========================
        # MOVE VIDEO -> VIDEO_OK
        # ==========================

        shutil.move(str(video_path), str(VIDEO_OK / video_path.name))

        print("Video moved to video_ok")

    except KeyboardInterrupt:

        print("\nTraining interrupted!")

        # xóa file tạm
        if temp_model.exists():
            temp_model.unlink()

        print("Temporary model deleted.")
        print("Video kept in video_notok")

        break

    except Exception as e:

        print("Error:", e)

        # xóa file tạm nếu có
        if temp_model.exists():
            temp_model.unlink()

        print("Training failed. Video kept in video_notok.")

cursor.close()
conn.close()
print("Database connection closed")


print("\n=== TRAINING FINISHED ===")

import cv2
import time
import requests
from ultralytics import YOLO

# ---------------------------
# Tapo RTSP DETAILS
# ---------------------------
CAMERA_IP = "192.168.1.125"
USERNAME = "macaque"
PASSWORD = "macaque47"

RTSP_URL = f"rtsp://{USERNAME}:{PASSWORD}@{CAMERA_IP}:554/stream2"

# ---------------------------
# LOAD YOLO MODEL
# ---------------------------
model = YOLO("my_model.pt")

# Open RTSP stream
cap = cv2.VideoCapture(RTSP_URL, cv2.CAP_FFMPEG)

if not cap.isOpened():
    print("❌ Failed to connect to Tapo camera")
    exit()

# Render backend
SERVER_URL = "https://YOUR-APP.onrender.com/upload"

print("✅ Tapo camera connected. Streaming...")

while True:
    ret, frame = cap.read()
    if not ret:
        continue

    # YOLO detection
    results = model(frame, verbose=False)
    macaque_count = 0

    for box in results[0].boxes.data:
        *_, conf, cls = box.tolist()
        if model.names[int(cls)] == "macaque" and conf > 0.5:
            macaque_count += 1

    # Encode frame
    _, jpeg = cv2.imencode(".jpg", frame)

    # Send to Render
    try:
        requests.post(
            SERVER_URL,
            files={"frame": jpeg.tobytes()},
            data={"count": macaque_count},
            timeout=2
        )
    except:
        print("⚠ Render server unreachable")

    time.sleep(0.2)

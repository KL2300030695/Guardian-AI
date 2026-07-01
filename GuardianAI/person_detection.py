import cv2
from ultralytics import YOLO
from datetime import datetime
import os
import time

# -----------------------------
# Load YOLO Model
# -----------------------------
model = YOLO("yolov8n.pt")

# -----------------------------
# IP Webcam URL
# -----------------------------
url = "http://10.123.34.14:8080/video"

cap = cv2.VideoCapture(url)

if not cap.isOpened():
    print("Error: Cannot open camera stream.")
    exit()

# -----------------------------
# Create folders
# -----------------------------
os.makedirs("recordings", exist_ok=True)
os.makedirs("screenshots", exist_ok=True)

# -----------------------------
# Variables
# -----------------------------
recording = False
event_started = False
writer = None
last_detection = 0

# -----------------------------
# Main Loop
# -----------------------------
while True:

    ret, frame = cap.read()

    if not ret:
        print("Failed to receive frame")
        break

    person_found = False

    # Run YOLO
    results = model(frame, verbose=False)

    # Check detections
    for result in results:

        for box in result.boxes:

            cls = int(box.cls[0])
            conf = float(box.conf[0])

            # Person Class = 0
            if cls == 0 and conf > 0.5:

                person_found = True

                x1, y1, x2, y2 = map(int, box.xyxy[0])

                # Green rectangle
                cv2.rectangle(
                    frame,
                    (x1, y1),
                    (x2, y2),
                    (0, 255, 0),
                    2,
                )

                # Label
                cv2.putText(
                    frame,
                    f"Person {conf:.2f}",
                    (x1, y1 - 10),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    0.6,
                    (0, 255, 0),
                    2,
                )

    # ---------------------------------------
    # Event Started
    # ---------------------------------------
    if person_found:

        last_detection = time.time()

        # Save ONE screenshot per event
        if not event_started:

            screenshot_name = datetime.now().strftime(
                "screenshots/%Y-%m-%d_%H-%M-%S.jpg"
            )

            cv2.imwrite(screenshot_name, frame)

            print(f"Screenshot Saved : {screenshot_name}")

            event_started = True

        # Start Recording
        if not recording:

            filename = datetime.now().strftime(
                "recordings/%Y-%m-%d_%H-%M-%S.mp4"
            )

            fourcc = cv2.VideoWriter_fourcc(*"mp4v")

            writer = cv2.VideoWriter(
                filename,
                fourcc,
                20,
                (frame.shape[1], frame.shape[0]),
            )

            recording = True

            print("Started Recording")

    # ---------------------------------------
    # Recording
    # ---------------------------------------
    if recording:

        writer.write(frame)

        cv2.putText(
            frame,
            "RECORDING",
            (20, 40),
            cv2.FONT_HERSHEY_SIMPLEX,
            1,
            (0, 0, 255),
            3,
        )

        # Stop after 10 sec of no person
        if time.time() - last_detection > 10:

            recording = False
            event_started = False

            writer.release()
            writer = None

            print("Stopped Recording")

    # ---------------------------------------
    # Display
    # ---------------------------------------
    cv2.imshow("Guardian AI", frame)

    if cv2.waitKey(1) & 0xFF == ord("q"):
        break

# -----------------------------
# Cleanup
# -----------------------------
if writer is not None:
    writer.release()

cap.release()
cv2.destroyAllWindows()
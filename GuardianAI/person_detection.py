import cv2
from ultralytics import YOLO
from datetime import datetime
import os
import time
from backend.notifier import send_alert
from backend.database import init_db, insert_event, update_event

# -----------------------------
# Initialise Database
# -----------------------------
init_db()

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
os.makedirs("recordings",  exist_ok=True)
os.makedirs("screenshots", exist_ok=True)
os.makedirs("database",    exist_ok=True)

# -----------------------------
# Variables
# -----------------------------
recording       = False
event_started   = False
writer          = None
last_detection  = 0

# Per-event tracking (reset each event)
event_id          = None       # database row id
event_start_time  = None       # to compute duration
peak_persons      = 0          # highest person count seen
peak_confidence   = 0.0        # highest confidence seen
current_recording = ""         # path of the active recording file

# HUD metrics
fps_time    = time.time()
fps         = 0
total_events = 0

# -----------------------------
# Main Loop
# -----------------------------
while True:

    ret, frame = cap.read()

    if not ret:
        print("Failed to receive frame")
        break

    person_found  = False
    person_count  = 0
    max_conf      = 0.0

    # Run YOLO
    results = model(frame, verbose=False)

    # Check detections
    for result in results:

        for box in result.boxes:

            cls  = int(box.cls[0])
            conf = float(box.conf[0])

            # Person Class = 0
            if cls == 0 and conf > 0.5:

                person_found  = True
                person_count += 1
                max_conf      = max(max_conf, conf)

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

        # Track peak stats during the event
        peak_persons    = max(peak_persons, person_count)
        peak_confidence = max(peak_confidence, max_conf)

        # First frame of a new event
        if not event_started:

            screenshot_name = datetime.now().strftime(
                "screenshots/%Y-%m-%d_%H-%M-%S.jpg"
            )

            cv2.imwrite(screenshot_name, frame)
            print(f"Screenshot Saved : {screenshot_name}")

            # Send Telegram and capture delivery status
            telegram_ok = send_alert(screenshot_name, person_count)

            # ── Database: insert new event row ──
            event_id = insert_event(
                persons    = person_count,
                confidence = max_conf,
                screenshot = screenshot_name,
                telegram   = telegram_ok,
            )

            event_started = True
            total_events += 1

        # Start recording
        if not recording:

            current_recording = datetime.now().strftime(
                "recordings/%Y-%m-%d_%H-%M-%S.mp4"
            )

            fourcc = cv2.VideoWriter_fourcc(*"mp4v")

            writer = cv2.VideoWriter(
                current_recording,
                fourcc,
                20,
                (frame.shape[1], frame.shape[0]),
            )

            recording        = True
            event_start_time = time.time()

            print("Started Recording")

    # ---------------------------------------
    # Recording
    # ---------------------------------------
    if recording:

        writer.write(frame)

        # Stop after 10 sec of no person
        if time.time() - last_detection > 10:

            duration  = time.time() - event_start_time
            recording = False
            event_started = False

            writer.release()
            writer = None

            print(f"Stopped Recording  (duration={duration:.1f}s)")

            # ── Database: update event with recording details ──
            if event_id is not None:
                update_event(
                    event_id  = event_id,
                    recording = current_recording,
                    duration  = duration,
                    persons   = peak_persons,
                )

            # Reset per-event state
            event_id          = None
            event_start_time  = None
            current_recording = ""
            peak_persons      = 0
            peak_confidence   = 0.0

    # ---------------------------------------
    # Display
    # ---------------------------------------
    # Calculate FPS
    current_time = time.time()
    fps = 1 / (current_time - fps_time) if (current_time - fps_time) > 0 else 0
    fps_time = current_time

    # Draw HUD Dashboard
    # Black dashboard background
    cv2.rectangle(frame, (0, 0), (340, 170), (40, 40, 40), -1)

    # Title
    cv2.putText(frame,
                "Guardian AI",
                (15, 30),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.8,
                (0, 255, 255),
                2)

    # Date & Time
    cv2.putText(frame,
                datetime.now().strftime("%d-%m-%Y %H:%M:%S"),
                (15, 55),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.5,
                (255, 255, 255),
                1)

    # Monitoring status
    cv2.putText(frame,
                "Status : Monitoring",
                (15, 80),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.55,
                (0, 255, 0),
                2)

    # Recording indicator
    recording_text  = "YES" if recording else "NO"
    recording_color = (0, 0, 255) if recording else (255, 255, 255)
    cv2.putText(frame,
                f"Recording : {recording_text}",
                (15, 105),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.55,
                recording_color,
                2)

    # FPS
    cv2.putText(frame,
                f"FPS : {fps:.1f}",
                (170, 105),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.55,
                (0, 255, 255),
                2)

    # Person count
    cv2.putText(frame,
                f"Persons : {person_count}",
                (15, 130),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.55,
                (255, 255, 255),
                2)

    # Total events
    cv2.putText(frame,
                f"Events : {total_events}",
                (170, 130),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.55,
                (255, 255, 255),
                2)

    # Display
    cv2.imshow("Guardian AI", frame)

    if cv2.waitKey(1) & 0xFF == ord("q"):
        break

# -----------------------------
# Cleanup
# -----------------------------
if writer is not None:
    # Save whatever was recorded up to now
    duration = time.time() - (event_start_time or time.time())
    writer.release()
    if event_id is not None:
        update_event(
            event_id  = event_id,
            recording = current_recording,
            duration  = duration,
            persons   = peak_persons,
        )

cap.release()
cv2.destroyAllWindows()
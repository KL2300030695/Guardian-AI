"""
detector.py — Guardian AI YOLO Detector (Phase 8)
────────────────────────────────────────────────────
Wraps the YOLO model into a stateless helper that processes
a single frame and returns structured detection results.
"""

from ultralytics import YOLO
import cv2
import numpy as np
from config import CONFIDENCE


class Detector:
    """Loads the YOLO model once and runs inference per frame."""

    def __init__(self, model_path: str = "yolov8n.pt"):
        self.model = YOLO(model_path)
        print(f"[Detector] YOLO model loaded: {model_path}")

    # ------------------------------------------------------------------
    def detect(self, frame: np.ndarray) -> tuple[np.ndarray, int, float]:
        """
        Run inference on a single frame.

        Draws bounding boxes directly onto the frame (in-place).

        Returns:
            annotated_frame : np.ndarray  — frame with boxes drawn
            person_count    : int         — number of persons detected
            max_confidence  : float       — highest confidence score seen
        """
        results      = self.model(frame, verbose=False)
        person_count = 0
        max_conf     = 0.0

        for result in results:
            for box in result.boxes:
                cls  = int(box.cls[0])
                conf = float(box.conf[0])

                if cls == 0 and conf > CONFIDENCE:          # class 0 = person
                    person_count += 1
                    max_conf      = max(max_conf, conf)

                    x1, y1, x2, y2 = map(int, box.xyxy[0])

                    cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 255, 0), 2)
                    cv2.putText(
                        frame,
                        f"Person {conf:.2f}",
                        (x1, y1 - 10),
                        cv2.FONT_HERSHEY_SIMPLEX,
                        0.6,
                        (0, 255, 0),
                        2,
                    )

        return frame, person_count, max_conf

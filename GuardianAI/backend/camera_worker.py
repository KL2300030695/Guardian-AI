"""
camera_worker.py — Guardian AI Per-Camera Detection Worker (Phase 11)
───────────────────────────────────────────────────────────────────────
One CameraWorker per physical camera. Each runs its own background
thread with YOLO + face recognition + recording + Telegram alerts.

Usage
─────
    worker = CameraWorker(camera_id=1, name="Main Door",
                          url="http://10.0.0.1:8080/video",
                          location="Entrance")
    worker.start()
    worker.stop()
    frame_bytes = worker.get_frame_jpeg()
    status_dict = worker.status()

Registration
────────────
    worker.start_registration("Subhash")   # begin face capture
    worker.registration_status()           # poll progress
    worker.cancel_registration()           # abort
"""

import cv2
import os
import time
import threading
from datetime import datetime

from config            import CONFIDENCE, RECORD_TIMEOUT
from backend.detector  import Detector
from backend.recorder  import Recorder
from backend.notifier  import send_alert
from backend.database  import init_db, insert_event, update_event
from backend.face_database import init_face_db, save_face
from backend.face_matcher  import matcher as face_matcher

try:
    import face_recognition as fr
    _FR = True
except ImportError:
    _FR = False
    print("[CameraWorker] face_recognition not available — identity disabled.")

os.makedirs("recordings",  exist_ok=True)
os.makedirs("screenshots", exist_ok=True)
os.makedirs("database",    exist_ok=True)
os.makedirs("faces",       exist_ok=True)

_FACE_EVERY_N = 3
_FACE_SCALE   = 0.5
_REG_TOTAL    = 20


class CameraWorker:
    """
    Thread-safe detection worker for a single camera.
    """

    def __init__(
        self,
        camera_id: int,
        name:      str,
        url:       str,
        location:  str = "",
    ):
        self._camera_id = camera_id
        self._name      = name
        self._url       = url
        self._location  = location

        self._thread:   threading.Thread | None = None
        self._stop_evt: threading.Event         = threading.Event()
        self._lock      = threading.Lock()

        # Live state
        self._running      = False
        self._recording    = False
        self._person_count = 0
        self._fps          = 0.0
        self._total_events = 0
        self._frame_jpeg: bytes | None = None
        self._last_identities: list[dict] = []

        # Registration state
        self._registering      = False
        self._reg_name         = ""
        self._reg_encodings    = []
        self._reg_sample_frame = None
        self._reg_completed    = False

    # ──────────────────────────────────────────────────────
    # Public: camera control
    # ──────────────────────────────────────────────────────
    def start(self) -> dict:
        with self._lock:
            if self._running:
                return {"ok": False, "message": f"[{self._name}] Already running"}
            self._stop_evt.clear()
            self._thread = threading.Thread(
                target=self._loop,
                daemon=True,
                name=f"guardian-cam-{self._camera_id}",
            )
            self._thread.start()
            self._running = True
            return {"ok": True, "message": f"[{self._name}] Started"}

    def stop(self) -> dict:
        with self._lock:
            if not self._running:
                return {"ok": False, "message": f"[{self._name}] Not running"}
            self._stop_evt.set()
        if self._thread:
            self._thread.join(timeout=15)
        with self._lock:
            self._running = False
        return {"ok": True, "message": f"[{self._name}] Stopped"}

    def status(self) -> dict:
        with self._lock:
            return {
                "camera_id":    self._camera_id,
                "name":         self._name,
                "location":     self._location,
                "url":          self._url,
                "running":      self._running,
                "recording":    self._recording,
                "person_count": self._person_count,
                "fps":          round(self._fps, 1),
                "total_events": self._total_events,
                "identities":   list(self._last_identities),
                "fr_available": _FR,
            }

    def get_frame_jpeg(self) -> bytes | None:
        with self._lock:
            return self._frame_jpeg

    # ──────────────────────────────────────────────────────
    # Public: face registration
    # ──────────────────────────────────────────────────────
    def start_registration(self, name: str) -> dict:
        name = name.strip()
        if not name:
            return {"ok": False, "message": "Name cannot be empty"}
        with self._lock:
            if not self._running:
                return {"ok": False, "message": f"[{self._name}] Camera must be running first"}
            if self._registering:
                return {"ok": False, "message": f"Already registering: {self._reg_name}"}
            self._registering      = True
            self._reg_name         = name
            self._reg_encodings    = []
            self._reg_sample_frame = None
            self._reg_completed    = False
        print(f"[{self._name}] Registration started for: {name}")
        return {"ok": True, "camera_id": self._camera_id,
                "message": f"Capturing {_REG_TOTAL} frames for '{name}'"}

    def cancel_registration(self) -> dict:
        with self._lock:
            if not self._registering:
                return {"ok": False, "message": "No registration in progress"}
            self._registering = False
            self._reg_name    = ""
            self._reg_encodings.clear()
        return {"ok": True, "message": "Registration cancelled"}

    def registration_status(self) -> dict:
        with self._lock:
            return {
                "active":      self._registering,
                "camera_id":   self._camera_id,
                "camera_name": self._name,
                "name":        self._reg_name,
                "progress":    len(self._reg_encodings),
                "total":       _REG_TOTAL,
                "completed":   self._reg_completed,
            }

    # ──────────────────────────────────────────────────────
    # Internal: finalize face registration
    # ──────────────────────────────────────────────────────
    def _finalize_registration(self):
        import numpy as np
        name      = self._reg_name
        encodings = self._reg_encodings.copy()
        sample    = self._reg_sample_frame

        mean_enc = np.mean(encodings, axis=0)

        sample_path = ""
        if sample is not None:
            sample_path = f"faces/{name.lower().replace(' ', '_')}.jpg"
            cv2.imwrite(sample_path, sample)

        save_face(
            name         = name,
            encoding     = mean_enc,
            sample_image = sample_path,
            image_count  = len(encodings),
        )
        face_matcher.reload()

        with self._lock:
            self._registering   = False
            self._reg_completed = True
            self._reg_encodings = []

        print(f"[{self._name}] Registration complete: {name} ({len(encodings)} frames)")

    # ──────────────────────────────────────────────────────
    # Internal: main detection loop
    # ──────────────────────────────────────────────────────
    def _loop(self):
        detector = Detector()
        recorder = Recorder()

        cap = cv2.VideoCapture(self._url)
        if not cap.isOpened():
            print(f"[{self._name}] ERROR: Cannot open camera: {self._url}")
            with self._lock:
                self._running = False
            return

        print(f"[{self._name}] Stream opened. Detection loop running.")

        # Per-event state
        event_started    = False
        last_detection   = 0.0
        event_id         = None
        peak_persons     = 0
        peak_confidence  = 0.0
        event_identity   = "Unknown"
        event_is_known   = False

        frame_n  = 0
        fps_time = time.time()
        cached_face_data: list = []

        try:
            while not self._stop_evt.is_set():

                ret, frame = cap.read()
                if not ret:
                    print(f"[{self._name}] Failed to read frame — reconnecting…")
                    time.sleep(1)
                    continue

                frame_raw = frame.copy()
                frame, person_count, max_conf = detector.detect(frame)

                now      = time.time()
                fps      = 1.0 / max(now - fps_time, 1e-6)
                fps_time = now
                frame_n += 1

                # ── Face recognition every N frames ──────────
                if _FR and frame_n % _FACE_EVERY_N == 0:
                    small = cv2.resize(frame_raw, (0, 0), fx=_FACE_SCALE, fy=_FACE_SCALE)
                    rgb   = cv2.cvtColor(small, cv2.COLOR_BGR2RGB)
                    face_locs = fr.face_locations(rgb, model="hog")
                    face_encs = fr.face_encodings(rgb, face_locs)

                    cached_face_data = []
                    sc = int(1 / _FACE_SCALE)

                    for (top, right, bot, left), enc in zip(face_locs, face_encs):
                        t2, r2, b2, l2 = top*sc, right*sc, bot*sc, left*sc

                        with self._lock:
                            reg_active = self._registering
                            reg_count  = len(self._reg_encodings)

                        if reg_active and reg_count < _REG_TOTAL:
                            with self._lock:
                                self._reg_encodings.append(enc)
                                if self._reg_sample_frame is None:
                                    self._reg_sample_frame = frame_raw[t2:b2, l2:r2].copy()
                            if reg_count + 1 >= _REG_TOTAL:
                                self._finalize_registration()
                            continue

                        name_id, conf, is_known = face_matcher.match(enc)
                        cached_face_data.append(((t2, r2, b2, l2), name_id, conf, is_known))

                # ── Draw face overlays ────────────────────────
                for (t, r, b, l), name_id, conf, is_known in cached_face_data:
                    color = (0, 220, 130) if is_known else (0, 80, 255)
                    icon  = ":)" if is_known else "??"
                    label = f"{icon} {name_id}  {conf:.0%}"
                    cv2.rectangle(frame, (l, t), (r, b), color, 2)
                    (tw, th), _ = cv2.getTextSize(label, cv2.FONT_HERSHEY_SIMPLEX, 0.5, 1)
                    cv2.rectangle(frame, (l, t - th - 8), (l + tw + 6, t), color, -1)
                    cv2.putText(frame, label, (l + 3, t - 5),
                                cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 0), 1)

                identities_now = [
                    {"name": d[1], "conf": d[2], "is_known": d[3]}
                    for d in cached_face_data
                ]
                unknown_ids = [x for x in identities_now if not x["is_known"]]
                known_ids   = [x for x in identities_now if x["is_known"]]
                top_id = (unknown_ids or known_ids or [None])[0]

                with self._lock:
                    self._person_count    = person_count
                    self._fps             = fps
                    self._recording       = recorder.is_recording
                    self._last_identities = identities_now

                person_found = person_count > 0

                # ── Event Start ───────────────────────────────
                if person_found:
                    last_detection  = time.time()
                    peak_persons    = max(peak_persons,   person_count)
                    peak_confidence = max(peak_confidence, max_conf)

                    if not event_started:
                        # Screenshot path includes camera id
                        shot_path = datetime.now().strftime(
                            f"screenshots/cam{self._camera_id}_%Y-%m-%d_%H-%M-%S.jpg"
                        )
                        cv2.imwrite(shot_path, frame)

                        # Smart alert: only for unknowns
                        any_unknown = bool(unknown_ids) or (not _FR and person_found)
                        telegram_ok = send_alert(
                            image_path      = shot_path,
                            person_count    = person_count,
                            camera_name     = self._name,
                            camera_location = self._location,
                        ) if any_unknown else False

                        event_identity = top_id["name"]    if top_id else "Unknown"
                        event_is_known = top_id["is_known"] if top_id else False

                        event_id = insert_event(
                            persons    = person_count,
                            confidence = max_conf,
                            screenshot = shot_path,
                            telegram   = telegram_ok,
                            identity   = event_identity,
                            is_known   = event_is_known,
                            camera_id  = self._camera_id,
                        )

                        event_started = True
                        with self._lock:
                            self._total_events += 1

                    if not recorder.is_recording:
                        h, w = frame.shape[:2]
                        recorder.start(w, h)
                        print(f"[{self._name}] Recording started.")

                # ── Recording / Stop ──────────────────────────
                if recorder.is_recording:
                    recorder.write(frame)

                    if time.time() - last_detection > RECORD_TIMEOUT:
                        rec_path, duration = recorder.stop()
                        event_started = False
                        print(f"[{self._name}] Recording stopped. {duration:.1f}s")

                        if event_id is not None:
                            update_event(
                                event_id  = event_id,
                                recording = rec_path,
                                duration  = duration,
                                persons   = peak_persons,
                            )

                        event_id        = None
                        peak_persons    = 0
                        peak_confidence = 0.0
                        event_identity  = "Unknown"
                        event_is_known  = False

                        with self._lock:
                            self._recording = False

                # ── HUD ───────────────────────────────────────
                self._draw_hud(frame, person_count, recorder.is_recording,
                               fps, identities_now)

                # ── Buffer for MJPEG ──────────────────────────
                _, jpeg_buf = cv2.imencode(
                    '.jpg', frame, [cv2.IMWRITE_JPEG_QUALITY, 75]
                )
                with self._lock:
                    self._frame_jpeg = jpeg_buf.tobytes()

                # Optional local window (disabled in multi-camera mode to save resources)
                # cv2.imshow(f"Guardian AI — {self._name}", frame)
                # if cv2.waitKey(1) & 0xFF == ord("q"):
                #     break

        finally:
            if recorder.is_recording:
                rec_path, duration = recorder.stop()
                if event_id is not None:
                    update_event(event_id=event_id, recording=rec_path,
                                 duration=duration, persons=peak_persons)
            cap.release()
            print(f"[{self._name}] Loop exited cleanly.")
            with self._lock:
                self._running   = False
                self._recording = False

    # ──────────────────────────────────────────────────────
    # HUD
    # ──────────────────────────────────────────────────────
    def _draw_hud(self, frame, person_count, recording, fps, identities):
        cv2.rectangle(frame, (0, 0), (370, 190), (30, 30, 30), -1)
        cv2.putText(frame, f"Guardian AI | {self._name}",
                    (12, 28), cv2.FONT_HERSHEY_SIMPLEX, 0.65, (0, 255, 255), 2)
        cv2.putText(frame, datetime.now().strftime("%d-%m-%Y %H:%M:%S"),
                    (12, 52), cv2.FONT_HERSHEY_SIMPLEX, 0.48, (200, 200, 200), 1)
        cv2.putText(frame, f"Location : {self._location}",
                    (12, 76), cv2.FONT_HERSHEY_SIMPLEX, 0.48, (180, 180, 180), 1)

        rec_text  = "YES" if recording else "NO"
        rec_color = (0, 0, 255) if recording else (255, 255, 255)
        cv2.putText(frame, f"Recording : {rec_text}",
                    (12, 100), cv2.FONT_HERSHEY_SIMPLEX, 0.52, rec_color, 2)
        cv2.putText(frame, f"FPS : {fps:.1f}",
                    (210, 100), cv2.FONT_HERSHEY_SIMPLEX, 0.52, (0, 255, 255), 2)
        cv2.putText(frame, f"Persons : {person_count}",
                    (12, 124), cv2.FONT_HERSHEY_SIMPLEX, 0.52, (255, 255, 255), 2)

        if identities:
            top = identities[0]
            id_color = (0, 220, 130) if top["is_known"] else (80, 80, 255)
            cv2.putText(frame, f"ID: {top['name']}  {top['conf']:.0%}",
                        (12, 152), cv2.FONT_HERSHEY_SIMPLEX, 0.52, id_color, 2)

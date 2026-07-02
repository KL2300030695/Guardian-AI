"""
camera.py — Guardian AI Camera Engine (Phase 10)
─────────────────────────────────────────────────
Now includes:
  • Face recognition + identity overlay on each frame
  • Smart alerts: Telegram only sent for UNKNOWN persons
  • Registration mode: captures N frames to enroll a new face

Public interface
────────────────
    engine.start()                     — POST /camera/start
    engine.stop()                      — POST /camera/stop
    engine.status()                    — GET  /camera/status
    engine.get_frame_jpeg()            — GET  /video_feed
    engine.start_registration(name)    — POST /faces/register/start
    engine.cancel_registration()       — POST /faces/register/cancel
    engine.registration_status()       — GET  /faces/register/status
"""

import cv2
import os
import time
import threading
from datetime import datetime

from config            import CAMERA_URL, CONFIDENCE, RECORD_TIMEOUT
from backend.detector  import Detector
from backend.recorder  import Recorder
from backend.notifier  import send_alert
from backend.database  import init_db, insert_event, update_event
from backend.face_database import init_face_db, save_face
from backend.face_matcher  import matcher as face_matcher

# Graceful fallback if face_recognition is not installed
try:
    import face_recognition as fr
    _FR = True
except ImportError:
    _FR = False
    print("[Camera] WARNING: face_recognition not installed — identity detection disabled.")

os.makedirs("recordings",  exist_ok=True)
os.makedirs("screenshots", exist_ok=True)
os.makedirs("database",    exist_ok=True)
os.makedirs("faces",       exist_ok=True)

# ── How many frames to process face recognition (skip intermediate frames) ──
_FACE_EVERY_N = 3       # run face_recognition on every 3rd frame (CPU saver)
_FACE_SCALE   = 0.5     # shrink frame before detection (faster)
_REG_TOTAL    = 20      # frames needed to register a face


class CameraEngine:
    """Thread-safe camera engine with face recognition and registration support."""

    def __init__(self):
        init_db()
        init_face_db()

        self._thread:   threading.Thread | None = None
        self._stop_evt: threading.Event         = threading.Event()
        self._lock           = threading.Lock()

        # Live status
        self._running        = False
        self._recording      = False
        self._person_count   = 0
        self._fps            = 0.0
        self._total_events   = 0
        self._last_event_id  = None
        self._frame_jpeg: bytes | None = None

        # Face recognition live state
        self._last_identities: list[dict] = []     # [{name, conf, is_known}, ...]

        # Registration state
        self._registering      = False
        self._reg_name         = ""
        self._reg_encodings    = []          # accumulated face encodings
        self._reg_sample_frame = None        # first captured face crop (numpy)
        self._reg_completed    = False

    # ──────────────────────────────────────────────────────
    # Public: Camera
    # ──────────────────────────────────────────────────────
    def start(self) -> dict:
        with self._lock:
            if self._running:
                return {"ok": False, "message": "Camera is already running"}
            self._stop_evt.clear()
            self._thread = threading.Thread(
                target=self._loop, daemon=True, name="guardian-camera"
            )
            self._thread.start()
            self._running = True
            return {"ok": True, "message": "Camera started"}

    def stop(self) -> dict:
        with self._lock:
            if not self._running:
                return {"ok": False, "message": "Camera is not running"}
            self._stop_evt.set()
        if self._thread:
            self._thread.join(timeout=15)
        with self._lock:
            self._running = False
        return {"ok": True, "message": "Camera stopped"}

    def status(self) -> dict:
        with self._lock:
            return {
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
    # Public: Face Registration
    # ──────────────────────────────────────────────────────
    def start_registration(self, name: str) -> dict:
        name = name.strip()
        if not name:
            return {"ok": False, "message": "Name cannot be empty"}
        with self._lock:
            if not self._running:
                return {"ok": False, "message": "Camera must be running to register a face"}
            if self._registering:
                return {"ok": False, "message": f"Already registering: {self._reg_name}"}
            self._registering      = True
            self._reg_name         = name
            self._reg_encodings    = []
            self._reg_sample_frame = None
            self._reg_completed    = False
        print(f"[Camera] Registration started for: {name}")
        return {"ok": True, "message": f"Capturing {_REG_TOTAL} frames for '{name}'"}

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
                "active":    self._registering,
                "name":      self._reg_name,
                "progress":  len(self._reg_encodings),
                "total":     _REG_TOTAL,
                "completed": self._reg_completed,
            }

    # ──────────────────────────────────────────────────────
    # Internal: Registration finalization
    # ──────────────────────────────────────────────────────
    def _finalize_registration(self):
        import numpy as np
        name      = self._reg_name
        encodings = self._reg_encodings.copy()
        sample    = self._reg_sample_frame

        # Compute mean encoding
        mean_enc = np.mean(encodings, axis=0)

        # Save sample face image
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

        print(f"[Camera] Registration complete: {name} ({len(encodings)} frames)")

    # ──────────────────────────────────────────────────────
    # Internal: Main detection loop
    # ──────────────────────────────────────────────────────
    def _loop(self):
        detector   = Detector()
        recorder   = Recorder()

        cap = cv2.VideoCapture(CAMERA_URL)
        if not cap.isOpened():
            print("[Camera] ERROR: Cannot open camera stream.")
            with self._lock:
                self._running = False
            return

        print("[Camera] Stream opened. Detection loop running.")

        # Per-event state
        event_started     = False
        last_detection    = 0.0
        event_id          = None
        event_start_time  = None
        peak_persons      = 0
        peak_confidence   = 0.0
        event_identity    = "Unknown"
        event_is_known    = False

        # Frame counter for skipping face recognition
        frame_n = 0
        fps_time = time.time()

        # Cached identities (updated every _FACE_EVERY_N frames)
        cached_face_data: list[tuple] = []   # [(top,right,bot,left), name, conf, is_known]

        try:
            while not self._stop_evt.is_set():

                ret, frame = cap.read()
                if not ret:
                    print("[Camera] Failed to read frame — reconnecting…")
                    time.sleep(1)
                    continue

                frame_raw = frame.copy()       # clean copy for face detection

                # ── YOLO person detection ──────────────────────
                frame, person_count, max_conf = detector.detect(frame)

                # ── FPS ────────────────────────────────────────
                now      = time.time()
                fps      = 1.0 / max(now - fps_time, 1e-6)
                fps_time = now
                frame_n += 1

                # ── Face recognition (every N frames) ─────────
                if _FR and frame_n % _FACE_EVERY_N == 0:
                    small = cv2.resize(frame_raw, (0, 0), fx=_FACE_SCALE, fy=_FACE_SCALE)
                    rgb   = cv2.cvtColor(small, cv2.COLOR_BGR2RGB)

                    face_locs = fr.face_locations(rgb, model="hog")
                    face_encs = fr.face_encodings(rgb, face_locs)

                    cached_face_data = []
                    for (top, right, bot, left), enc in zip(face_locs, face_encs):
                        # Scale coords back to full size
                        sc = int(1 / _FACE_SCALE)
                        t2, r2, b2, l2 = top*sc, right*sc, bot*sc, left*sc

                        # Registration mode: accumulate encodings
                        with self._lock:
                            reg_active = self._registering
                            reg_count  = len(self._reg_encodings)

                        if reg_active and reg_count < _REG_TOTAL:
                            with self._lock:
                                self._reg_encodings.append(enc)
                                if self._reg_sample_frame is None:
                                    # Save face crop as sample
                                    self._reg_sample_frame = frame_raw[t2:b2, l2:r2].copy()
                            if reg_count + 1 >= _REG_TOTAL:
                                self._finalize_registration()
                            continue         # don't match while registering

                        # Normal matching
                        name, conf, is_known = face_matcher.match(enc)
                        cached_face_data.append(((t2, r2, b2, l2), name, conf, is_known))

                # ── Draw face identity boxes ───────────────────
                for (t, r, b, l), name, conf, is_known in cached_face_data:
                    color = (0, 220, 130) if is_known else (0, 80, 255)
                    icon  = ":)" if is_known else "??"
                    label = f"{icon} {name}  {conf:.0%}"
                    cv2.rectangle(frame, (l, t), (r, b), color, 2)
                    # Label background
                    (tw, th), _ = cv2.getTextSize(label, cv2.FONT_HERSHEY_SIMPLEX, 0.5, 1)
                    cv2.rectangle(frame, (l, t - th - 8), (l + tw + 6, t), color, -1)
                    cv2.putText(frame, label, (l + 3, t - 5),
                                cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 0), 1)

                # ── Derive event identity from face data ───────
                identities_now = [
                    {"name": d[1], "conf": d[2], "is_known": d[3]}
                    for d in cached_face_data
                ]
                # Pick the dominant identity (first unknown, else first known)
                unknown_ids = [x for x in identities_now if not x["is_known"]]
                known_ids   = [x for x in identities_now if x["is_known"]]
                if unknown_ids:
                    top_id = unknown_ids[0]
                elif known_ids:
                    top_id = known_ids[0]
                else:
                    top_id = None

                # ── Share live state ───────────────────────────
                with self._lock:
                    self._person_count    = person_count
                    self._fps             = fps
                    self._recording       = recorder.is_recording
                    self._last_identities = identities_now

                person_found = person_count > 0

                # ── Event Start ────────────────────────────────
                if person_found:
                    last_detection  = time.time()
                    peak_persons    = max(peak_persons,   person_count)
                    peak_confidence = max(peak_confidence, max_conf)

                    if not event_started:
                        shot_path = datetime.now().strftime(
                            "screenshots/%Y-%m-%d_%H-%M-%S.jpg"
                        )
                        cv2.imwrite(shot_path, frame)
                        print(f"[Camera] Screenshot saved: {shot_path}")

                        # ── Smart alert: only for unknown persons ──
                        any_unknown = bool(unknown_ids) or (not _FR and person_found)
                        telegram_ok = send_alert(shot_path, person_count) if any_unknown else False

                        # Identity for this event
                        event_identity = top_id["name"]   if top_id else "Unknown"
                        event_is_known = top_id["is_known"] if top_id else False

                        event_id = insert_event(
                            persons    = person_count,
                            confidence = max_conf,
                            screenshot = shot_path,
                            telegram   = telegram_ok,
                            identity   = event_identity,
                            is_known   = event_is_known,
                        )

                        event_started = True
                        with self._lock:
                            self._total_events  += 1
                            self._last_event_id  = event_id

                    if not recorder.is_recording:
                        h, w = frame.shape[:2]
                        recorder.start(w, h)
                        event_start_time = time.time()
                        print("[Camera] Recording started.")

                # ── Recording / Stop ───────────────────────────
                if recorder.is_recording:
                    recorder.write(frame)

                    if time.time() - last_detection > RECORD_TIMEOUT:
                        rec_path, duration = recorder.stop()
                        event_started      = False
                        print(f"[Camera] Recording stopped. Duration={duration}s")

                        if event_id is not None:
                            update_event(
                                event_id  = event_id,
                                recording = rec_path,
                                duration  = duration,
                                persons   = peak_persons,
                            )

                        event_id          = None
                        event_start_time  = None
                        peak_persons      = 0
                        peak_confidence   = 0.0
                        event_identity    = "Unknown"
                        event_is_known    = False

                        with self._lock:
                            self._recording = False

                # ── HUD ────────────────────────────────────────
                self._draw_hud(frame, person_count, recorder.is_recording, fps,
                               identities_now)

                # ── Buffer for MJPEG stream ────────────────────
                _, jpeg_buf = cv2.imencode('.jpg', frame, [cv2.IMWRITE_JPEG_QUALITY, 75])
                with self._lock:
                    self._frame_jpeg = jpeg_buf.tobytes()

                cv2.imshow("Guardian AI", frame)
                if cv2.waitKey(1) & 0xFF == ord("q"):
                    break

        finally:
            if recorder.is_recording:
                rec_path, duration = recorder.stop()
                if event_id is not None:
                    update_event(event_id=event_id, recording=rec_path,
                                 duration=duration, persons=peak_persons)
            cap.release()
            cv2.destroyAllWindows()
            print("[Camera] Loop exited cleanly.")
            with self._lock:
                self._running   = False
                self._recording = False

    # ──────────────────────────────────────────────────────
    # HUD (Phase 10 — includes identity info)
    # ──────────────────────────────────────────────────────
    @staticmethod
    def _draw_hud(frame, person_count: int, recording: bool, fps: float,
                  identities: list):
        cv2.rectangle(frame, (0, 0), (360, 185), (30, 30, 30), -1)

        cv2.putText(frame, "Guardian AI",
                    (15, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 255, 255), 2)
        cv2.putText(frame, datetime.now().strftime("%d-%m-%Y %H:%M:%S"),
                    (15, 55), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)
        cv2.putText(frame, "Status : Monitoring",
                    (15, 80), cv2.FONT_HERSHEY_SIMPLEX, 0.55, (0, 255, 0), 2)

        rec_text  = "YES" if recording else "NO"
        rec_color = (0, 0, 255) if recording else (255, 255, 255)
        cv2.putText(frame, f"Recording : {rec_text}",
                    (15, 105), cv2.FONT_HERSHEY_SIMPLEX, 0.55, rec_color, 2)
        cv2.putText(frame, f"FPS : {fps:.1f}",
                    (200, 105), cv2.FONT_HERSHEY_SIMPLEX, 0.55, (0, 255, 255), 2)
        cv2.putText(frame, f"Persons : {person_count}",
                    (15, 130), cv2.FONT_HERSHEY_SIMPLEX, 0.55, (255, 255, 255), 2)

        # Show first identity on HUD
        if identities:
            top = identities[0]
            id_color = (0, 220, 130) if top["is_known"] else (80, 80, 255)
            id_text  = f"ID: {top['name']}  {top['conf']:.0%}"
            cv2.putText(frame, id_text, (15, 158),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.55, id_color, 2)
        else:
            cv2.putText(frame, "ID: --",
                        (15, 158), cv2.FONT_HERSHEY_SIMPLEX, 0.55, (100, 100, 100), 1)

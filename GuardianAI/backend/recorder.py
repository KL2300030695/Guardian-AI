"""
recorder.py — Guardian AI Video Recorder (Phase 8)
────────────────────────────────────────────────────
Wraps cv2.VideoWriter into a small, clean helper.
"""

import cv2
import os
import time
from datetime import datetime


class Recorder:
    """Handles opening, writing, and closing a single mp4 recording."""

    def __init__(self, output_dir: str = "recordings", fps: int = 20):
        os.makedirs(output_dir, exist_ok=True)
        self.output_dir   = output_dir
        self.fps          = fps
        self._writer      = None
        self.filepath     = ""
        self.start_time   = None

    # ------------------------------------------------------------------
    def start(self, frame_width: int, frame_height: int) -> str:
        """Open a new recording file.  Returns the relative filepath."""
        self.filepath   = datetime.now().strftime(
            f"{self.output_dir}/%Y-%m-%d_%H-%M-%S.mp4"
        )
        fourcc          = cv2.VideoWriter_fourcc(*"mp4v")
        self._writer    = cv2.VideoWriter(
            self.filepath, fourcc, self.fps, (frame_width, frame_height)
        )
        self.start_time = time.time()
        return self.filepath

    # ------------------------------------------------------------------
    def write(self, frame) -> None:
        if self._writer:
            self._writer.write(frame)

    # ------------------------------------------------------------------
    def stop(self) -> tuple[str, float]:
        """
        Stop recording.
        Returns (filepath, duration_seconds).
        """
        duration = time.time() - self.start_time if self.start_time else 0.0
        if self._writer:
            self._writer.release()
            self._writer = None
        path           = self.filepath
        self.filepath  = ""
        self.start_time = None
        return path, round(duration, 2)

    # ------------------------------------------------------------------
    @property
    def is_recording(self) -> bool:
        return self._writer is not None

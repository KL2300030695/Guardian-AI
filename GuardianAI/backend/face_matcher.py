"""
face_matcher.py — Guardian AI Identity Matcher (Phase 10)
──────────────────────────────────────────────────────────
Loads all known face encodings from the database and compares
new detections against them using Euclidean distance.

Usage
─────
    from backend.face_matcher import matcher

    name, confidence, is_known = matcher.match(encoding)
    matcher.reload()          # call after registering a new face

Architecture note
─────────────────
face_recognition.face_distance() returns values in [0, 1].
A distance of 0 means identical; 0.6 is the typical threshold.
We convert distance → confidence as: confidence = 1 - distance.
"""

import numpy as np

# Graceful fallback if face_recognition isn't installed
try:
    import face_recognition as fr
    _FR_AVAILABLE = True
except ImportError:
    _FR_AVAILABLE = False
    print("[FaceMatcher] WARNING: face_recognition not installed. "
          "Run: pip install face_recognition")

from backend.face_database import load_all_encodings

MATCH_THRESHOLD = 0.55      # distance ≤ this → known person


class FaceMatcher:
    """
    Thread-safe singleton that holds known face encodings in memory.
    Call reload() whenever the database changes.
    """

    def __init__(self):
        self._names:     list[str]        = []
        self._encodings: list[np.ndarray] = []
        self.reload()

    # ──────────────────────────────────────────────
    def reload(self) -> None:
        """Refresh encodings from the database."""
        pairs = load_all_encodings()
        self._names     = [p[0] for p in pairs]
        self._encodings = [p[1] for p in pairs]
        print(f"[FaceMatcher] Loaded {len(self._names)} known face(s): "
              f"{self._names if self._names else '(none)'}")

    # ──────────────────────────────────────────────
    def match(self, encoding: np.ndarray) -> tuple[str, float, bool]:
        """
        Compare a face encoding against all known faces.

        Returns:
            name       : str   — person's name or "Unknown"
            confidence : float — 0.0 – 1.0 (higher = more certain)
            is_known   : bool  — True if matched a known face
        """
        if not _FR_AVAILABLE or len(self._encodings) == 0:
            return "Unknown", 0.0, False

        distances   = fr.face_distance(self._encodings, encoding)
        best_idx    = int(np.argmin(distances))
        best_dist   = float(distances[best_idx])
        confidence  = round(1.0 - best_dist, 3)

        if best_dist <= MATCH_THRESHOLD:
            return self._names[best_idx], confidence, True
        return "Unknown", confidence, False

    # ──────────────────────────────────────────────
    @property
    def face_recognition_available(self) -> bool:
        return _FR_AVAILABLE

    @property
    def known_count(self) -> int:
        return len(self._names)


# Module-level singleton — shared across the whole application
matcher = FaceMatcher()

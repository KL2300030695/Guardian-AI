"""
face_database.py — Guardian AI Face Identity Storage (Phase 10)
────────────────────────────────────────────────────────────────
Manages the known_faces table in the same guardian.db SQLite database.

Table: known_faces
  id           INTEGER  PRIMARY KEY AUTOINCREMENT
  name         TEXT     UNIQUE NOT NULL
  encoding     BLOB     NOT NULL   — mean 128-d numpy array (numpy binary format)
  sample_image TEXT     DEFAULT '' — path to a representative face crop
  created_at   TEXT     NOT NULL
  image_count  INTEGER  DEFAULT 0  — number of training frames used
"""

import sqlite3
import os
import io
import numpy as np
from datetime import datetime

# ── Paths ──────────────────────────────────────────
DB_PATH  = os.path.join("database", "guardian.db")
FACE_DIR = "faces"          # sample face crops stored here


def _conn() -> sqlite3.Connection:
    os.makedirs("database", exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def _enc_to_bytes(encoding: np.ndarray) -> bytes:
    """Serialize a numpy array to bytes using numpy's own format."""
    buf = io.BytesIO()
    np.save(buf, encoding)
    return buf.getvalue()


def _bytes_to_enc(blob: bytes) -> np.ndarray:
    """Deserialize numpy array from bytes."""
    buf = io.BytesIO(blob)
    return np.load(buf)


# ── Initialise ─────────────────────────────────────
def init_face_db() -> None:
    """Create the known_faces table if it doesn't exist."""
    os.makedirs(FACE_DIR, exist_ok=True)
    conn = _conn()
    conn.execute("""
        CREATE TABLE IF NOT EXISTS known_faces (
            id           INTEGER PRIMARY KEY AUTOINCREMENT,
            name         TEXT    UNIQUE NOT NULL,
            encoding     BLOB    NOT NULL,
            sample_image TEXT    DEFAULT '',
            created_at   TEXT    NOT NULL,
            image_count  INTEGER DEFAULT 0
        )
    """)
    conn.commit()
    conn.close()
    print("[FaceDB] known_faces table ready.")


# ── Save / upsert a known face ──────────────────────
def save_face(
    name:         str,
    encoding:     np.ndarray,
    sample_image: str = "",
    image_count:  int = 0,
) -> int:
    """
    Insert a new known face or replace if the name already exists.
    Returns the row id.
    """
    blob = _enc_to_bytes(encoding)
    now  = datetime.now().strftime("%d-%b-%Y %H:%M:%S")

    conn = _conn()
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO known_faces (name, encoding, sample_image, created_at, image_count)
        VALUES (?, ?, ?, ?, ?)
        ON CONFLICT(name) DO UPDATE SET
            encoding    = excluded.encoding,
            sample_image = excluded.sample_image,
            created_at  = excluded.created_at,
            image_count = excluded.image_count
    """, (name, blob, sample_image, now, image_count))
    conn.commit()
    face_id = cursor.lastrowid or cursor.execute(
        "SELECT id FROM known_faces WHERE name=?", (name,)
    ).fetchone()[0]
    conn.close()
    print(f"[FaceDB] Face saved: {name} ({image_count} frames)")
    return face_id


# ── Read helpers ────────────────────────────────────
def get_all_faces() -> list[dict]:
    """Return all known faces (without the encoding blob — use load_all_encodings() for that)."""
    conn = _conn()
    rows = conn.execute("""
        SELECT id, name, sample_image, created_at, image_count
        FROM known_faces ORDER BY name
    """).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def load_all_encodings() -> list[tuple[str, np.ndarray]]:
    """Load (name, encoding) pairs for the FaceMatcher."""
    try:
        conn = _conn()
        rows = conn.execute("SELECT name, encoding FROM known_faces").fetchall()
        conn.close()
        return [(r["name"], _bytes_to_enc(r["encoding"])) for r in rows]
    except Exception:
        return []   # table not yet created — return empty list


# ── Delete ──────────────────────────────────────────
def delete_face(face_id: int) -> None:
    conn = _conn()
    # Also grab sample image to clean up the file
    row = conn.execute("SELECT sample_image FROM known_faces WHERE id=?", (face_id,)).fetchone()
    conn.execute("DELETE FROM known_faces WHERE id=?", (face_id,))
    conn.commit()
    conn.close()
    if row and row["sample_image"] and os.path.exists(row["sample_image"]):
        os.remove(row["sample_image"])
    print(f"[FaceDB] Face #{face_id} deleted.")

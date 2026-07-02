"""
cameras_db.py — Guardian AI Camera Registry (Phase 11)
────────────────────────────────────────────────────────
Manages the cameras table in guardian.db.

Table: cameras
  id         INTEGER  PRIMARY KEY AUTOINCREMENT
  name       TEXT     e.g. "Main Door"
  url        TEXT     IP Webcam / RTSP URL
  location   TEXT     e.g. "Entrance"
  enabled    INTEGER  1 = active, 0 = disabled
  created_at TEXT     Timestamp string
"""

import sqlite3
import os
from datetime import datetime

DB_PATH = os.path.join("database", "guardian.db")


def _conn() -> sqlite3.Connection:
    os.makedirs("database", exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


# ── Initialise ─────────────────────────────────────
def init_cameras_db() -> None:
    """Create the cameras table if it doesn't exist."""
    conn = _conn()
    conn.execute("""
        CREATE TABLE IF NOT EXISTS cameras (
            id         INTEGER PRIMARY KEY AUTOINCREMENT,
            name       TEXT    NOT NULL,
            url        TEXT    NOT NULL,
            location   TEXT    DEFAULT '',
            enabled    INTEGER DEFAULT 1,
            created_at TEXT    NOT NULL
        )
    """)
    conn.commit()
    conn.close()
    print("[CamerasDB] cameras table ready.")


# ── Seed default camera from config.py ─────────────
def seed_default_camera() -> None:
    """
    If the cameras table is empty, seed it with a Camera 1
    entry read from config.py CAMERA_URL so existing setups
    continue to work without manual configuration.
    """
    conn = _conn()
    count = conn.execute("SELECT COUNT(*) FROM cameras").fetchone()[0]
    if count == 0:
        from config import CAMERA_URL
        now = datetime.now().strftime("%d-%b-%Y %H:%M:%S")
        conn.execute("""
            INSERT INTO cameras (name, url, location, enabled, created_at)
            VALUES (?, ?, ?, ?, ?)
        """, ("Camera 1", CAMERA_URL, "Main Entrance", 1, now))
        conn.commit()
        print("[CamerasDB] Seeded Camera 1 from config.py")
    conn.close()


# ── CRUD ───────────────────────────────────────────
def get_all_cameras() -> list[dict]:
    conn = _conn()
    rows = conn.execute("SELECT * FROM cameras ORDER BY id").fetchall()
    conn.close()
    return [dict(r) for r in rows]


def get_camera(camera_id: int) -> dict | None:
    conn = _conn()
    row = conn.execute(
        "SELECT * FROM cameras WHERE id=?", (camera_id,)
    ).fetchone()
    conn.close()
    return dict(row) if row else None


def add_camera(
    name: str,
    url: str,
    location: str = "",
    enabled: bool = True,
) -> int:
    now = datetime.now().strftime("%d-%b-%Y %H:%M:%S")
    conn = _conn()
    cur = conn.cursor()
    cur.execute("""
        INSERT INTO cameras (name, url, location, enabled, created_at)
        VALUES (?, ?, ?, ?, ?)
    """, (name, url, location, 1 if enabled else 0, now))
    conn.commit()
    cam_id = cur.lastrowid
    conn.close()
    print(f"[CamerasDB] Added camera #{cam_id}: {name} @ {url}")
    return cam_id


def update_camera(camera_id: int, **kwargs) -> None:
    allowed = {"name", "url", "location", "enabled"}
    updates = {k: v for k, v in kwargs.items() if k in allowed}
    if not updates:
        return
    set_clause = ", ".join(f"{k}=?" for k in updates)
    vals = list(updates.values()) + [camera_id]
    conn = _conn()
    conn.execute(f"UPDATE cameras SET {set_clause} WHERE id=?", vals)
    conn.commit()
    conn.close()
    print(f"[CamerasDB] Updated camera #{camera_id}: {updates}")


def delete_camera(camera_id: int) -> None:
    conn = _conn()
    conn.execute("DELETE FROM cameras WHERE id=?", (camera_id,))
    conn.commit()
    conn.close()
    print(f"[CamerasDB] Deleted camera #{camera_id}")

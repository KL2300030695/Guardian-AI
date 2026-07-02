"""
database.py — Guardian AI Event Database (Phase 11)
────────────────────────────────────────────────────
Phase 11 additions:
  • events.camera_id  — which camera triggered this event
  • insert_event()    — accepts camera_id parameter
  • get_events_by_camera() — filter events by camera
  • get_camera_event_counts() — analytics: events per camera
  • get_daily_counts() / get_hourly_counts() — optional camera_id filter
"""

import sqlite3
import os
from datetime import datetime

DB_DIR  = "database"
DB_PATH = os.path.join(DB_DIR, "guardian.db")


def _get_connection() -> sqlite3.Connection:
    os.makedirs(DB_DIR, exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


# ──────────────────────────────────────────────────
# Initialise + migrate
# ──────────────────────────────────────────────────
def init_db() -> None:
    """Create the events table and run any pending column migrations."""
    conn = _get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS events (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            date        TEXT    NOT NULL,
            time        TEXT    NOT NULL,
            persons     INTEGER NOT NULL DEFAULT 1,
            confidence  REAL    NOT NULL DEFAULT 0.0,
            screenshot  TEXT    DEFAULT '',
            recording   TEXT    DEFAULT '',
            telegram    INTEGER NOT NULL DEFAULT 0,
            duration    REAL    NOT NULL DEFAULT 0.0,
            identity    TEXT    DEFAULT 'Unknown',
            is_known    INTEGER DEFAULT 0,
            camera_id   INTEGER DEFAULT 1
        )
    """)
    # Safe migrations — catch errors for columns that already exist
    for col, definition in [
        ("identity",  "TEXT    DEFAULT 'Unknown'"),
        ("is_known",  "INTEGER DEFAULT 0"),
        ("camera_id", "INTEGER DEFAULT 1"),
    ]:
        try:
            cursor.execute(f"ALTER TABLE events ADD COLUMN {col} {definition}")
            print(f"[DB] Migration: added column '{col}'")
        except Exception:
            pass
    conn.commit()
    conn.close()
    print(f"[DB] Database ready > {DB_PATH}")


# ──────────────────────────────────────────────────
# Insert
# ──────────────────────────────────────────────────
def insert_event(
    persons:    int,
    confidence: float,
    screenshot: str,
    telegram:   bool,
    identity:   str  = "Unknown",
    is_known:   bool = False,
    camera_id:  int  = 1,
) -> int:
    now = datetime.now()
    conn = _get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO events
            (date, time, persons, confidence, screenshot, telegram,
             identity, is_known, camera_id)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        now.strftime("%d-%b-%Y"),
        now.strftime("%H:%M:%S"),
        persons,
        round(confidence, 4),
        screenshot,
        1 if telegram else 0,
        identity,
        1 if is_known else 0,
        camera_id,
    ))
    event_id = cursor.lastrowid
    conn.commit()
    conn.close()
    print(f"[DB] Event #{event_id} — cam#{camera_id} | {persons} person(s) | {identity}")
    return event_id


# ──────────────────────────────────────────────────
# Update
# ──────────────────────────────────────────────────
def update_event(
    event_id:  int,
    recording: str,
    duration:  float,
    persons:   int = None,
) -> None:
    conn = _get_connection()
    cursor = conn.cursor()
    if persons is not None:
        cursor.execute("""
            UPDATE events SET recording=?, duration=?, persons=? WHERE id=?
        """, (recording, round(duration, 2), persons, event_id))
    else:
        cursor.execute("""
            UPDATE events SET recording=?, duration=? WHERE id=?
        """, (recording, round(duration, 2), event_id))
    conn.commit()
    conn.close()
    print(f"[DB] Event #{event_id} updated — {recording} | {duration:.1f}s")


# ──────────────────────────────────────────────────
# Query helpers
# ──────────────────────────────────────────────────
def get_all_events() -> list[dict]:
    conn = _get_connection()
    rows = [dict(r) for r in conn.execute(
        "SELECT * FROM events ORDER BY id DESC"
    ).fetchall()]
    conn.close()
    return rows


def get_recent_events(limit: int = 10) -> list[dict]:
    conn = _get_connection()
    rows = [dict(r) for r in conn.execute(
        "SELECT * FROM events ORDER BY id DESC LIMIT ?", (limit,)
    ).fetchall()]
    conn.close()
    return rows


def get_events_by_date(date_str: str) -> list[dict]:
    conn = _get_connection()
    rows = [dict(r) for r in conn.execute(
        "SELECT * FROM events WHERE date=? ORDER BY id DESC", (date_str,)
    ).fetchall()]
    conn.close()
    return rows


def get_events_by_camera(camera_id: int, limit: int = None) -> list[dict]:
    conn = _get_connection()
    sql = "SELECT * FROM events WHERE camera_id=? ORDER BY id DESC"
    params = [camera_id]
    if limit:
        sql += " LIMIT ?"
        params.append(limit)
    rows = [dict(r) for r in conn.execute(sql, params).fetchall()]
    conn.close()
    return rows


def get_stats(camera_id: int = None) -> dict:
    conn = _get_connection()
    where = f"WHERE camera_id={camera_id}" if camera_id else ""
    row = dict(conn.execute(f"""
        SELECT
            COUNT(*)       AS total_events,
            SUM(persons)   AS total_persons,
            SUM(telegram)  AS telegram_sent,
            SUM(duration)  AS total_duration
        FROM events {where}
    """).fetchone())
    conn.close()
    return {k: (v or 0) for k, v in row.items()}


def get_daily_counts(camera_id: int = None) -> list[dict]:
    where = f"WHERE camera_id={camera_id}" if camera_id else ""
    conn = _get_connection()
    rows = [dict(r) for r in conn.execute(f"""
        SELECT date, COUNT(*) AS count
        FROM events {where}
        GROUP BY date ORDER BY id DESC LIMIT 30
    """).fetchall()]
    conn.close()
    return rows


def get_hourly_counts(camera_id: int = None) -> list[dict]:
    where = f"WHERE camera_id={camera_id}" if camera_id else ""
    conn = _get_connection()
    rows = [dict(r) for r in conn.execute(f"""
        SELECT CAST(substr(time, 1, 2) AS INTEGER) AS hour,
               COUNT(*) AS count
        FROM events {where}
        GROUP BY hour ORDER BY hour
    """).fetchall()]
    conn.close()
    hour_map = {r["hour"]: r["count"] for r in rows}
    return [{"hour": h, "count": hour_map.get(h, 0)} for h in range(24)]


def get_camera_event_counts() -> list[dict]:
    """
    Returns event counts per camera_id for the Analytics page.
    Each item: {camera_id, count}
    """
    conn = _get_connection()
    rows = [dict(r) for r in conn.execute("""
        SELECT camera_id, COUNT(*) AS count
        FROM events
        GROUP BY camera_id
        ORDER BY count DESC
    """).fetchall()]
    conn.close()
    return rows

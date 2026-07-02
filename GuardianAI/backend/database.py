"""
database.py — Guardian AI Event Database (Phase 12 — AI Analytics)
───────────────────────────────────────────────────────────────────
Manages an SQLite database at database/guardian.db.

Table: events
  id          INTEGER  PRIMARY KEY AUTOINCREMENT
  date        TEXT     e.g. "02-Jul-2026"
  time        TEXT     e.g. "00:42:15"
  persons     INTEGER  Peak person count for the event
  confidence  REAL     Highest confidence score seen
  screenshot  TEXT     Relative path to screenshot file
  recording   TEXT     Relative path to recording file
  telegram    INTEGER  1 = sent, 0 = failed / not sent
  duration    REAL     Recording duration in seconds
  identity    TEXT     Identified person name or 'Unknown'
  is_known    INTEGER  1 = known person, 0 = unknown
  camera_id   INTEGER  Camera identifier
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
    conn = _get_connection()
    rows = [dict(r) for r in conn.execute("""
        SELECT camera_id, COUNT(*) AS count
        FROM events
        GROUP BY camera_id
        ORDER BY count DESC
    """).fetchall()]
    conn.close()
    return rows


# ──────────────────────────────────────────────────
# Phase 12: AI Analytics Detailed Queries
# ──────────────────────────────────────────────────
def get_analytics_overview(camera_id: int = None, days: int = None) -> dict:
    """
    Returns rich analytics metrics:
    - total_events, total_persons, telegram_sent, total_duration, avg_duration
    - known_count, unknown_count, known_percentage, avg_confidence
    - peak_hour, peak_hour_count, most_active_camera
    """
    conn = _get_connection()

    where_clauses = []
    params = []
    if camera_id is not None:
        where_clauses.append("camera_id = ?")
        params.append(camera_id)
    if days is not None:
        where_clauses.append("id >= (SELECT id FROM events ORDER BY id DESC LIMIT 1 OFFSET ?)")
        params.append(max(0, days * 50)) # approximate frame window or limit

    where_str = ("WHERE " + " AND ".join(where_clauses)) if where_clauses else ""

    # Aggregate stats
    agg = dict(conn.execute(f"""
        SELECT
            COUNT(*)                              AS total_events,
            COALESCE(SUM(persons), 0)            AS total_persons,
            COALESCE(SUM(telegram), 0)           AS telegram_sent,
            COALESCE(SUM(duration), 0.0)         AS total_duration,
            COALESCE(AVG(duration), 0.0)         AS avg_duration,
            COALESCE(AVG(confidence), 0.0)       AS avg_confidence,
            COALESCE(SUM(CASE WHEN is_known = 1 THEN 1 ELSE 0 END), 0) AS known_count,
            COALESCE(SUM(CASE WHEN is_known = 0 THEN 1 ELSE 0 END), 0) AS unknown_count
        FROM events {where_str}
    """, params).fetchone())

    total = agg["total_events"]
    known = agg["known_count"]
    agg["known_ratio"] = round((known / total * 100), 1) if total > 0 else 0.0
    agg["avg_duration"] = round(agg["avg_duration"], 1)
    agg["avg_confidence_pct"] = round(agg["avg_confidence"] * 100, 1)

    # Peak Hour
    peak_row = conn.execute(f"""
        SELECT CAST(substr(time, 1, 2) AS INTEGER) AS hour, COUNT(*) AS count
        FROM events {where_str}
        GROUP BY hour ORDER BY count DESC LIMIT 1
    """, params).fetchone()

    if peak_row:
        agg["peak_hour"] = peak_row["hour"]
        agg["peak_hour_count"] = peak_row["count"]
    else:
        agg["peak_hour"] = 0
        agg["peak_hour_count"] = 0

    # Most Active Camera
    most_active_cam = conn.execute(f"""
        SELECT camera_id, COUNT(*) as count
        FROM events {where_str}
        GROUP BY camera_id ORDER BY count DESC LIMIT 1
    """, params).fetchone()

    if most_active_cam:
        cam_id = most_active_cam["camera_id"]
        cam_info = conn.execute("SELECT name, location FROM cameras WHERE id=?", (cam_id,)).fetchone()
        agg["most_active_camera"] = {
            "id": cam_id,
            "name": cam_info["name"] if cam_info else f"Camera {cam_id}",
            "location": cam_info["location"] if cam_info else "",
            "count": most_active_cam["count"]
        }
    else:
        agg["most_active_camera"] = {"id": 1, "name": "None", "location": "", "count": 0}

    conn.close()
    return agg


def get_analytics_trends(camera_id: int = None, limit_days: int = 30) -> list[dict]:
    """
    Returns daily event trends with known vs unknown breakdown per day.
    """
    conn = _get_connection()
    where = f"WHERE camera_id={camera_id}" if camera_id else ""
    rows = [dict(r) for r in conn.execute(f"""
        SELECT
            date,
            COUNT(*) AS total,
            SUM(CASE WHEN is_known = 1 THEN 1 ELSE 0 END) AS known,
            SUM(CASE WHEN is_known = 0 THEN 1 ELSE 0 END) AS unknown,
            ROUND(AVG(confidence) * 100, 1) AS avg_confidence
        FROM events {where}
        GROUP BY date
        ORDER BY id DESC
        LIMIT ?
    """, (limit_days,)).fetchall()]
    conn.close()
    return rows


def get_analytics_hourly_breakdown(camera_id: int = None) -> list[dict]:
    """
    Returns 24-hour distribution with known vs unknown breakdown for each hour.
    """
    conn = _get_connection()
    where = f"WHERE camera_id={camera_id}" if camera_id else ""
    rows = [dict(r) for r in conn.execute(f"""
        SELECT
            CAST(substr(time, 1, 2) AS INTEGER) AS hour,
            COUNT(*) AS total,
            SUM(CASE WHEN is_known = 1 THEN 1 ELSE 0 END) AS known,
            SUM(CASE WHEN is_known = 0 THEN 1 ELSE 0 END) AS unknown
        FROM events {where}
        GROUP BY hour
        ORDER BY hour
    """).fetchall()]
    conn.close()

    hour_map = {r["hour"]: r for r in rows}
    result = []
    for h in range(24):
        item = hour_map.get(h, {"hour": h, "total": 0, "known": 0, "unknown": 0})
        item["hour_label"] = f"{h:02d}:00"
        result.append(item)
    return result


def get_analytics_cameras_comparison() -> list[dict]:
    """
    Compares activity across all registered cameras (joins cameras + events).
    """
    conn = _get_connection()
    rows = [dict(r) for r in conn.execute("""
        SELECT
            c.id AS camera_id,
            c.name AS name,
            c.location AS location,
            c.enabled AS enabled,
            COUNT(e.id) AS total_events,
            COALESCE(SUM(e.persons), 0) AS total_persons,
            COALESCE(SUM(CASE WHEN e.is_known = 1 THEN 1 ELSE 0 END), 0) AS known_events,
            COALESCE(SUM(CASE WHEN e.is_known = 0 THEN 1 ELSE 0 END), 0) AS unknown_events,
            ROUND(COALESCE(AVG(e.duration), 0), 1) AS avg_duration
        FROM cameras c
        LEFT JOIN events e ON c.id = e.camera_id
        GROUP BY c.id
        ORDER BY total_events DESC
    """).fetchall()]
    conn.close()
    return rows


def get_analytics_identities() -> list[dict]:
    """
    Returns breakdown by identified person.
    """
    conn = _get_connection()
    rows = [dict(r) for r in conn.execute("""
        SELECT
            identity,
            is_known,
            COUNT(*) AS count,
            ROUND(AVG(confidence) * 100, 1) AS avg_confidence,
            MAX(date || ' ' || time) AS last_seen
        FROM events
        GROUP BY identity
        ORDER BY count DESC
    """).fetchall()]
    conn.close()
    return rows

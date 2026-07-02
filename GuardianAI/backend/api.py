"""
api.py — Guardian AI FastAPI Router (Phase 11 — Multi-Camera)
──────────────────────────────────────────────────────────────
Endpoints
─────────
Health:
  GET /health

Cameras (Multi-Camera Management):
  GET    /cameras                    — list all cameras + live status
  POST   /cameras                    — add a new camera
  PUT    /cameras/{id}               — update camera details
  DELETE /cameras/{id}               — remove camera
  POST   /cameras/{id}/start         — start camera worker
  POST   /cameras/{id}/stop          — stop camera worker
  GET    /cameras/{id}/status        — status of specific camera
  GET    /video_feed                 — MJPEG live stream (default / camera 1)
  GET    /video_feed/{id}            — MJPEG live stream for camera {id}

Events:
  GET    /events                     — all events
  GET    /events/recent              — recent 10 events
  GET    /events/stats               — system / camera stats
  GET    /events/date/{date}         — events by date
  GET    /events/camera/{camera_id}  — events for specific camera

Analytics:
  GET    /events/analytics/daily     — daily count
  GET    /events/analytics/hourly    — hourly distribution
  GET    /events/analytics/cameras   — event counts per camera

Face Recognition:
  GET    /faces                      — list known faces
  POST   /faces/register/start       — begin face registration
  GET    /faces/register/status      — registration status
  POST   /faces/register/cancel      — cancel registration
  DELETE /faces/{face_id}            — delete face
  GET    /faces/{face_id}/image      — serve face photo
  GET    /faces/{name}/history       — event history for identity

Settings:
  GET    /settings                   — read-only system config
"""

import asyncio
from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse, FileResponse
from pydantic import BaseModel
from datetime import datetime
import os

from backend.database import (
    get_all_events, get_recent_events, get_stats,
    get_events_by_date, get_events_by_camera,
    get_daily_counts, get_hourly_counts, get_camera_event_counts,
)
from backend.cameras_db import get_all_cameras, get_camera
from backend.face_database import get_all_faces, delete_face
from config import CAMERA_URL, CONFIDENCE, RECORD_TIMEOUT

# CameraManager singleton — injected by main.py
_manager = None


def set_manager(manager) -> None:
    global _manager
    _manager = manager


# Legacy compatibility alias
def set_engine(engine) -> None:
    pass


router = APIRouter()


# ── Health ────────────────────────────────────────
@router.get("/health")
def health():
    return {"status": "running"}


# ── MJPEG Stream ──────────────────────────────────
async def _frame_generator(camera_id: int = 1):
    while True:
        frame = _manager.get_frame(camera_id) if _manager else None
        if frame:
            yield (
                b"--frame\r\n"
                b"Content-Type: image/jpeg\r\n\r\n"
                + frame + b"\r\n"
            )
        else:
            await asyncio.sleep(0.1)
            continue
        await asyncio.sleep(0.04)


@router.get("/video_feed")
async def video_feed_default():
    """Default MJPEG live stream (Camera 1)."""
    return StreamingResponse(
        _frame_generator(1),
        media_type="multipart/x-mixed-replace; boundary=frame",
    )


@router.get("/video_feed/{camera_id}")
async def video_feed_by_id(camera_id: int):
    """MJPEG live stream for a specific camera ID."""
    return StreamingResponse(
        _frame_generator(camera_id),
        media_type="multipart/x-mixed-replace; boundary=frame",
    )


# ── Multi-Camera Management Endpoints ─────────────
@router.get("/cameras")
def list_cameras():
    """List all cameras along with their live operational status."""
    if _manager is None:
        return get_all_cameras()
    return _manager.get_all_status()


class AddCameraRequest(BaseModel):
    name: str
    url: str
    location: str = ""
    enabled: bool = True


@router.post("/cameras")
def add_camera_endpoint(body: AddCameraRequest):
    if _manager is None:
        raise HTTPException(503, "Manager not initialized")
    return _manager.add_camera(
        name=body.name,
        url=body.url,
        location=body.location,
        enabled=body.enabled,
    )


class UpdateCameraRequest(BaseModel):
    name: str | None = None
    url: str | None = None
    location: str | None = None
    enabled: bool | None = None


@router.put("/cameras/{camera_id}")
def update_camera_endpoint(camera_id: int, body: UpdateCameraRequest):
    if _manager is None:
        raise HTTPException(503, "Manager not initialized")
    updates = {k: v for k, v in body.dict().items() if v is not None}
    return _manager.update_camera(camera_id, **updates)


@router.delete("/cameras/{camera_id}")
def remove_camera_endpoint(camera_id: int):
    if _manager is None:
        raise HTTPException(503, "Manager not initialized")
    return _manager.remove_camera(camera_id)


@router.post("/cameras/{camera_id}/start")
def camera_start(camera_id: int):
    if _manager is None:
        raise HTTPException(503, "Manager not initialized")
    return _manager.start_camera(camera_id)


@router.post("/cameras/{camera_id}/stop")
def camera_stop(camera_id: int):
    if _manager is None:
        raise HTTPException(503, "Manager not initialized")
    return _manager.stop_camera(camera_id)


@router.get("/cameras/{camera_id}/status")
def camera_status_by_id(camera_id: int):
    if _manager is None:
        raise HTTPException(503, "Manager not initialized")
    st = _manager.get_status(camera_id)
    if st is None:
        raise HTTPException(404, f"Camera {camera_id} not found")
    return st


# Legacy camera endpoints for backward compatibility
@router.post("/camera/start")
def camera_start_legacy():
    if _manager is None:
        raise HTTPException(503, "Manager not initialized")
    return _manager.start_camera(1)


@router.post("/camera/stop")
def camera_stop_legacy():
    if _manager is None:
        raise HTTPException(503, "Manager not initialized")
    return _manager.stop_camera(1)


@router.get("/camera/status")
def camera_status_legacy():
    if _manager is None:
        raise HTTPException(503, "Manager not initialized")
    st = _manager.get_status(1)
    if st is None:
        # Fallback summary
        statuses = _manager.get_all_status()
        if statuses:
            st = statuses[0]
        else:
            return {"running": False, "recording": False, "person_count": 0, "fps": 0, "total_events": 0}
    return st


# ── Events ────────────────────────────────────────
@router.get("/events")
def events_all():
    return get_all_events()


@router.get("/events/recent")
def events_recent():
    return get_recent_events(limit=10)


@router.get("/events/stats")
def events_stats(camera_id: int | None = None):
    return get_stats(camera_id=camera_id)


@router.get("/events/date/{date}")
def events_by_date(date: str):
    try:
        parsed  = datetime.strptime(date, "%Y-%m-%d")
        db_date = parsed.strftime("%d-%b-%Y")
    except ValueError:
        raise HTTPException(400, f"Invalid date '{date}'. Use YYYY-MM-DD.")
    return get_events_by_date(db_date)


@router.get("/events/camera/{camera_id}")
def events_by_camera_route(camera_id: int, limit: int | None = None):
    return get_events_by_camera(camera_id=camera_id, limit=limit)


@router.get("/events/analytics/daily")
def analytics_daily(camera_id: int | None = None):
    return get_daily_counts(camera_id=camera_id)


@router.get("/events/analytics/hourly")
def analytics_hourly(camera_id: int | None = None):
    return get_hourly_counts(camera_id=camera_id)


@router.get("/events/analytics/cameras")
def analytics_cameras():
    return get_camera_event_counts()


# ── Settings ──────────────────────────────────────
@router.get("/settings")
def settings():
    return {
        "camera_url":     CAMERA_URL,
        "confidence":     CONFIDENCE,
        "record_timeout": RECORD_TIMEOUT,
    }


# ── Face Recognition: Known Faces ─────────────────
@router.get("/faces")
def faces_list():
    return get_all_faces()


@router.delete("/faces/{face_id}")
def faces_delete(face_id: int):
    delete_face(face_id)
    from backend.face_matcher import matcher
    matcher.reload()
    return {"ok": True, "message": f"Face #{face_id} deleted"}


@router.get("/faces/{face_id}/image")
def faces_image(face_id: int):
    faces = {f["id"]: f for f in get_all_faces()}
    if face_id not in faces:
        raise HTTPException(404, "Face not found")
    img_path = faces[face_id].get("sample_image", "")
    if not img_path or not os.path.exists(img_path):
        raise HTTPException(404, "Sample image not available")
    return FileResponse(img_path, media_type="image/jpeg")


@router.get("/faces/{name}/history")
def faces_history(name: str):
    import sqlite3
    from backend.database import _get_connection
    conn = _get_connection()
    rows = conn.execute(
        "SELECT * FROM events WHERE identity = ? ORDER BY id DESC",
        (name,)
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]


# ── Face Recognition: Registration ────────────────
class RegisterRequest(BaseModel):
    name: str
    camera_id: int | None = None


@router.post("/faces/register/start")
def register_start(body: RegisterRequest):
    if _manager is None:
        raise HTTPException(503, "Manager not initialized")
    return _manager.start_registration(body.name, camera_id=body.camera_id)


@router.get("/faces/register/status")
def register_status(camera_id: int | None = None):
    if _manager is None:
        raise HTTPException(503, "Manager not initialized")
    return _manager.registration_status(camera_id=camera_id)


@router.post("/faces/register/cancel")
def register_cancel(camera_id: int | None = None):
    if _manager is None:
        raise HTTPException(503, "Manager not initialized")
    return _manager.cancel_registration(camera_id=camera_id)

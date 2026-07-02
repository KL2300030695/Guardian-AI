"""
camera_manager.py — Guardian AI Multi-Camera Manager (Phase 11)
────────────────────────────────────────────────────────────────
Owns every CameraWorker. Reads camera definitions from the database
and exposes a single API for start/stop/status/stream/add/remove.

Usage (from main.py)
─────────────────────
    from backend.camera_manager import CameraManager
    manager = CameraManager()      # loads all cameras from DB
    manager.start_all()            # starts enabled cameras
"""

import threading
from backend.cameras_db   import (
    init_cameras_db, seed_default_camera,
    get_all_cameras, get_camera,
    add_camera as db_add_camera,
    update_camera as db_update_camera,
    delete_camera as db_delete_camera,
)
from backend.camera_worker import CameraWorker
from backend.database      import init_db
from backend.face_database import init_face_db


class CameraManager:
    """Thread-safe manager for all CameraWorker instances."""

    def __init__(self):
        # Initialise all databases
        init_db()
        init_cameras_db()
        init_face_db()
        seed_default_camera()

        self._lock:    threading.Lock              = threading.Lock()
        self._workers: dict[int, CameraWorker]    = {}

        # Create (but don't start) a worker for every camera in the DB
        for cam in get_all_cameras():
            self._workers[cam["id"]] = CameraWorker(
                camera_id = cam["id"],
                name      = cam["name"],
                url       = cam["url"],
                location  = cam["location"],
            )

        print(f"[Manager] {len(self._workers)} camera(s) loaded.")

    # ──────────────────────────────────────────────────────
    # Bulk operations
    # ──────────────────────────────────────────────────────
    def start_all(self) -> dict:
        """Start every enabled camera."""
        results = {}
        cameras = get_all_cameras()
        for cam in cameras:
            if cam["enabled"] and cam["id"] in self._workers:
                results[cam["id"]] = self._workers[cam["id"]].start()
        return results

    def stop_all(self) -> dict:
        results = {}
        for cid, w in self._workers.items():
            results[cid] = w.stop()
        return results

    # ──────────────────────────────────────────────────────
    # Per-camera control
    # ──────────────────────────────────────────────────────
    def start_camera(self, camera_id: int) -> dict:
        w = self._workers.get(camera_id)
        if w is None:
            return {"ok": False, "message": f"Camera {camera_id} not found"}
        return w.start()

    def stop_camera(self, camera_id: int) -> dict:
        w = self._workers.get(camera_id)
        if w is None:
            return {"ok": False, "message": f"Camera {camera_id} not found"}
        return w.stop()

    def get_status(self, camera_id: int) -> dict | None:
        w = self._workers.get(camera_id)
        return w.status() if w else None

    def get_all_status(self) -> list[dict]:
        return [w.status() for w in self._workers.values()]

    def get_frame(self, camera_id: int) -> bytes | None:
        w = self._workers.get(camera_id)
        return w.get_frame_jpeg() if w else None

    # ──────────────────────────────────────────────────────
    # Camera management (add / update / remove)
    # ──────────────────────────────────────────────────────
    def add_camera(
        self,
        name:     str,
        url:      str,
        location: str  = "",
        enabled:  bool = True,
    ) -> dict:
        cam_id = db_add_camera(name=name, url=url, location=location, enabled=enabled)
        worker = CameraWorker(camera_id=cam_id, name=name, url=url, location=location)
        with self._lock:
            self._workers[cam_id] = worker
        if enabled:
            worker.start()
        return {"ok": True, "camera_id": cam_id, "message": f"Camera '{name}' added"}

    def update_camera(self, camera_id: int, **kwargs) -> dict:
        db_update_camera(camera_id, **kwargs)

        # Restart worker if URL or enabled state changed
        url_changed     = "url"     in kwargs
        enabled_changed = "enabled" in kwargs
        if url_changed or enabled_changed:
            if camera_id in self._workers:
                self._workers[camera_id].stop()

            cam = get_camera(camera_id)
            if cam is None:
                return {"ok": False, "message": "Camera not found after update"}

            new_worker = CameraWorker(
                camera_id = cam["id"],
                name      = cam["name"],
                url       = cam["url"],
                location  = cam["location"],
            )
            with self._lock:
                self._workers[cam["id"]] = new_worker
            if cam["enabled"]:
                new_worker.start()
        elif "name" in kwargs or "location" in kwargs:
            # Just update the in-memory worker's metadata without restart
            w = self._workers.get(camera_id)
            if w:
                if "name" in kwargs:
                    w._name = kwargs["name"]
                if "location" in kwargs:
                    w._location = kwargs["location"]

        return {"ok": True, "message": "Camera updated"}

    def remove_camera(self, camera_id: int) -> dict:
        if camera_id in self._workers:
            self._workers[camera_id].stop()
            with self._lock:
                del self._workers[camera_id]
        db_delete_camera(camera_id)
        return {"ok": True, "message": f"Camera {camera_id} removed"}

    # ──────────────────────────────────────────────────────
    # Face registration — routed to a specific camera worker
    # ──────────────────────────────────────────────────────
    def start_registration(self, name: str, camera_id: int | None = None) -> dict:
        """
        Begin face registration on the given camera (or the first running one).
        """
        if camera_id is None:
            # Pick first running camera
            for cid, w in self._workers.items():
                if w.status()["running"]:
                    camera_id = cid
                    break
        if camera_id is None:
            return {"ok": False, "message": "No camera is running — start a camera first"}
        w = self._workers.get(camera_id)
        if w is None:
            return {"ok": False, "message": f"Camera {camera_id} not found"}
        return w.start_registration(name)

    def cancel_registration(self, camera_id: int | None = None) -> dict:
        if camera_id is not None:
            w = self._workers.get(camera_id)
            return w.cancel_registration() if w else {"ok": False, "message": "Camera not found"}
        for w in self._workers.values():
            st = w.registration_status()
            if st["active"]:
                return w.cancel_registration()
        return {"ok": False, "message": "No active registration"}

    def registration_status(self, camera_id: int | None = None) -> dict:
        if camera_id is not None:
            w = self._workers.get(camera_id)
            return w.registration_status() if w else {
                "active": False, "name": "", "progress": 0, "total": 20, "completed": False
            }
        for w in self._workers.values():
            st = w.registration_status()
            if st["active"]:
                return st
        return {"active": False, "camera_id": None, "name": "",
                "progress": 0, "total": 20, "completed": False}

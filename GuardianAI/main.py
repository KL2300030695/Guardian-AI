"""
main.py — Guardian AI Server (Phase 11 — Multi-Camera)
──────────────────────────────────────────────────────
Run with:   python main.py
      or:   uvicorn main:app --host 0.0.0.0 --port 8000

Endpoints available at http://localhost:8000/docs
Frontend dashboard at  http://localhost:5173   (Vite dev)
Production UI at      http://localhost:8000/ui
"""

import uvicorn
import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from backend.camera_manager import CameraManager
from backend import api as api_module
from backend.api import router

# ── App ────────────────────────────────────────────────────────
app = FastAPI(
    title       = "Guardian AI",
    description = "AI-powered security camera — Phase 11 Multi-Camera",
    version     = "11.0.0",
    docs_url    = "/docs",
    redoc_url   = "/redoc",
)

# ── CORS ───────────────────────────────────────────────────────
app.add_middleware(
    CORSMiddleware,
    allow_origins     = ["*"],
    allow_credentials = True,
    allow_methods     = ["*"],
    allow_headers     = ["*"],
)

# ── Camera Manager Singleton ───────────────────────────────────
manager = CameraManager()
api_module.set_manager(manager)

# Automatically start enabled cameras on server boot
manager.start_all()

# ── API routes ──────────────────────────────────────────────────
app.include_router(router)

# ── Static file mounts ──────────────────────────────────────────
for folder in ("recordings", "screenshots", "database", "frontend", "faces"):
    os.makedirs(folder, exist_ok=True)

app.mount("/screenshots", StaticFiles(directory="screenshots"), name="screenshots")
app.mount("/recordings",  StaticFiles(directory="recordings"),  name="recordings")
app.mount("/faces",       StaticFiles(directory="faces"),       name="face_images")

# Serve built React app at /ui
FRONTEND_DIST = os.path.join("frontend", "dist")
if os.path.isdir(FRONTEND_DIST):
    app.mount("/ui", StaticFiles(directory=FRONTEND_DIST, html=True), name="frontend")

# ── Dev runner ──────────────────────────────────────────────────
if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=False, log_level="info")

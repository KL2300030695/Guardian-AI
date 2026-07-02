"""
start_production.py — One-Click Production Launcher
───────────────────────────────────────────────────────
Builds the React frontend (if needed) and launches the Guardian AI
unified server on http://localhost:8000/ui.
"""

import os
import sys
import subprocess
import webbrowser
import time

PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))
GUARDIAN_DIR = os.path.join(PROJECT_ROOT, "GuardianAI")
FRONTEND_DIR = os.path.join(GUARDIAN_DIR, "frontend")
DIST_DIR     = os.path.join(FRONTEND_DIR, "dist")


def main():
    print("==================================================")
    print(" 🛡️ Guardian AI — Production Launcher")
    print("==================================================")

    # 1. Build React Frontend if dist directory is missing
    if not os.path.isdir(DIST_DIR):
        print("\n[Launcher] React frontend build missing. Compiling frontend...")
        npm_cmd = "npm.cmd" if sys.platform == "win32" else "npm"
        try:
            subprocess.run([npm_cmd, "run", "build"], cwd=FRONTEND_DIR, check=True)
            print("[Launcher] React frontend build complete ✅")
        except Exception as e:
            print(f"[Launcher] ERROR building frontend: {e}")
            print("Please run 'npm run build' inside GuardianAI/frontend manually.")
    else:
        print("[Launcher] Compiled React dashboard dist/ verified ✅")

    # 2. Add GuardianAI directory to sys.path
    sys.path.insert(0, GUARDIAN_DIR)
    os.chdir(GUARDIAN_DIR)

    # 3. Launch Server
    print("\n[Launcher] Launching Guardian AI Unified Production Server...")
    print("--------------------------------------------------")
    print(" 🌐 Dashboard UI:   http://localhost:8000/ui")
    print(" 📚 API Docs:       http://localhost:8000/docs")
    print(" 📹 Stream Feed:    http://localhost:8000/video_feed")
    print("--------------------------------------------------")

    # Open browser automatically after 2 seconds
    def open_browser():
        time.sleep(2)
        webbrowser.open("http://localhost:8000/ui")

    import threading
    threading.Thread(target=open_browser, daemon=True).start()

    # Run Uvicorn directly
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=False, log_level="info")


if __name__ == "__main__":
    main()

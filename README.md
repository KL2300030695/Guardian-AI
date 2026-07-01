<div align="center">
  <h1>🛡️ Guardian AI</h1>
  <p><strong>Intelligent AI-Powered Security & Person Detection System</strong></p>

  <p>
    <img src="https://img.shields.io/badge/Python-3.8+-blue.svg" alt="Python Version" />
    <img src="https://img.shields.io/badge/OpenCV-4.x-green.svg" alt="OpenCV" />
    <img src="https://img.shields.io/badge/YOLOv8-Ultralytics-orange.svg" alt="YOLOv8" />
    <img src="https://img.shields.io/badge/Telegram-Bot%20Alerts-26A5E4.svg" alt="Telegram" />
    <img src="https://img.shields.io/badge/HUD-Live%20Dashboard-purple.svg" alt="HUD" />
  </p>
</div>

<hr/>

## 📖 Overview

**Guardian AI** is a smart surveillance system built using Python, OpenCV, and Ultralytics YOLOv8. It connects to an IP webcam and actively monitors the video feed in real-time. When a person is detected, Guardian AI instantly captures a screenshot, begins recording the event, and sends a **real-time Telegram alert** with the snapshot attached — all while displaying a live **Heads-Up Display (HUD)** on screen.

---

## ✨ Features

- 👤 **Real-Time Person Detection:** Utilizes state-of-the-art YOLOv8 object detection to accurately identify people in the video feed.
- 📸 **Automatic Screenshots:** Instantly snaps and saves a high-quality photo when an event is triggered.
- 🎥 **Smart Video Recording:** Automatically starts recording video when a person enters the frame and gracefully stops 10 seconds after they leave.
- ⚡ **IP Camera Support:** Seamlessly connects to external network cameras (like your mobile phone via IP Webcam).
- 📲 **Telegram Alerts:** Sends an instant Telegram message with a snapshot and person count every time a new detection event begins.
- 🖥️ **Live HUD Dashboard:** On-screen overlay showing real-time system stats — monitoring status, recording state, person count, total events, FPS, and live date/time.

---

## 🖥️ Live HUD Preview

```
+--------------------------------------------------+
| Guardian AI                  02-07-2026 00:43:00 |
| Status : Monitoring                              |
| Recording : YES              FPS : 24.3          |
| Persons : 1                  Events : 4          |
+--------------------------------------------------+
|                                                  |
|         🟩 Person 0.97                           |
|                                                  |
+--------------------------------------------------+
```

| Element | Color | Meaning |
|---------|-------|---------|
| Title & FPS | 🟦 Cyan | System branding & performance |
| Status | 🟩 Green | Always monitoring |
| Recording YES | 🟥 Red | Active recording |
| Recording NO | ⬜ White | Idle |
| Persons / Events | ⬜ White | Live detection counts |

---

## 📲 Telegram Alert Preview

```
🚨 Guardian AI Alert

👤 Persons Detected : 1

📅 Time : 02-07-2026 00:43:00
[📷 Screenshot attached]
```

---

## 🛠️ Installation

### 1. Clone the repository
```bash
git clone https://github.com/KL2300030695/Guardian-AI.git
cd Guardian-AI
```

### 2. Create a Virtual Environment (recommended)
```bash
python -m venv venv
# On Windows
venv\Scripts\activate
# On macOS/Linux
source venv/bin/activate
```

### 3. Install Dependencies
```bash
pip install -r GuardianAI/requirements.txt
```

---

## ⚙️ Configuration

Edit **`GuardianAI/config.py`** before running:

```python
BOT_TOKEN     = "YOUR_TELEGRAM_BOT_TOKEN"   # From @BotFather
CHAT_ID       = "YOUR_CHAT_ID"              # Your Telegram chat ID

CAMERA_URL    = "http://YOUR_IP:8080/video" # IP Webcam stream URL

CONFIDENCE    = 0.5    # Detection confidence threshold (0–1)
RECORD_TIMEOUT = 10    # Seconds to keep recording after person leaves
```

> **Get your Bot Token:** Message [@BotFather](https://t.me/BotFather) on Telegram → `/newbot`  
> **Get your Chat ID:** Message [@userinfobot](https://t.me/userinfobot) on Telegram

---

## 🚀 Usage

### 🔗 Step 1 — Start IP Webcam on your phone
- Install **IP Webcam** (Android) or **EpocCam** (iOS)
- Tap **Start Server** — note the IP shown (e.g. `http://192.168.x.x:8080`)
- Update `CAMERA_URL` in `config.py`

### 🧪 Step 2 — Test your camera connection
```bash
python GuardianAI/camera_test.py
```
*(Press `q` to quit)*

### 🛡️ Step 3 — Start Guardian AI
```bash
python GuardianAI/person_detection.py
```

When a person is detected:
1. 📸 Screenshot saved → `GuardianAI/screenshots/`
2. 📲 Telegram alert sent with photo
3. 🎥 Recording started → `GuardianAI/recordings/`
4. 🖥️ HUD updates live on screen

*(Press `q` to quit Guardian AI)*

---

## 📂 Project Structure

```text
Guardian-AI/
├── GuardianAI/
│   ├── config.py               # 🔧 Central configuration (tokens, URL, thresholds)
│   ├── person_detection.py     # 🤖 Core AI detection, HUD & recording engine
│   ├── camera_test.py          # 📷 Verify IP camera stream
│   ├── main.py                 # Placeholder for future enhancements
│   ├── requirements.txt        # 📦 Project dependencies
│   └── backend/
│       └── notifier.py         # 📲 Telegram alert module
├── recordings/                 # 🎥 Auto-generated event video clips
├── screenshots/                # 📸 Auto-generated event snapshots
├── yolov8n.pt                  # 🧠 Pre-trained YOLOv8 Nano model weights
└── README.md                   # 📖 Project documentation
```

---

## 📦 Dependencies

| Package | Purpose |
|---------|---------|
| `ultralytics` | YOLOv8 person detection |
| `opencv-python` | Video capture, frame processing & HUD rendering |
| `requests` | Telegram Bot API communication |

---

## 🗺️ Roadmap

- [x] Phase 1 — IP Camera connection
- [x] Phase 2 — YOLOv8 person detection
- [x] Phase 3 — Auto screenshot & recording
- [x] Phase 4 — Event-based logic (start/stop recording)
- [x] Phase 5 — Live HUD & Telegram alerts
- [ ] Phase 6 — Web dashboard (Flask/FastAPI)
- [ ] Phase 7 — Multi-camera support
- [ ] Phase 8 — Face recognition

---

## 📝 License

Distributed under the MIT License.

<br />
<div align="center">
  <i>Built with ❤️ using Python & AI</i>
</div>

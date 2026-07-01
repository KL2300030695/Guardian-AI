<div align="center">
  <h1>🛡️ Guardian AI</h1>
  <p><strong>Intelligent AI-Powered Security & Person Detection System</strong></p>

  <p>
    <img src="https://img.shields.io/badge/Python-3.8+-blue.svg" alt="Python Version" />
    <img src="https://img.shields.io/badge/OpenCV-4.x-green.svg" alt="OpenCV" />
    <img src="https://img.shields.io/badge/YOLOv8-Ultralytics-orange.svg" alt="YOLOv8" />
  </p>
</div>

<hr/>

## 📖 Overview

**Guardian AI** is a smart surveillance system built using Python, OpenCV, and Ultralytics YOLOv8. It connects to an IP webcam and actively monitors the video feed in real-time. When a person is detected, Guardian AI instantly captures a screenshot and begins recording the event until the area is clear. 

## ✨ Features

- 👤 **Real-Time Person Detection:** Utilizes state-of-the-art YOLOv8 object detection to accurately identify people in the video feed.
- 📸 **Automatic Screenshots:** Instantly snaps and saves a high-quality photo when an event is triggered.
- 🎥 **Smart Video Recording:** Automatically starts recording video when a person enters the frame and gracefully stops 10 seconds after they leave.
- ⚡ **IP Camera Support:** Seamlessly connects to external network cameras (like your mobile phone via IP Webcam).
- 🖥️ **Live UI:** On-screen visual indicators (bounding boxes, confidence scores, and a flashing `RECORDING` tag).

---

## 🛠️ Installation

### 1. Clone the repository
```bash
git clone https://github.com/KL2300030695/Guardian-AI.git
cd Guardian-AI
```

### 2. Create a Virtual Environment (Optional but recommended)
```bash
python -m venv venv
# On Windows
venv\Scripts\activate
# On macOS/Linux
source venv/bin/activate
```

### 3. Install Dependencies
Make sure you have Python installed. Then run:
```bash
pip install -r GuardianAI/requirements.txt
```

---

## 🚀 Usage

### 🔗 Configure your camera
Guardian AI is configured to use an IP Webcam URL. You can use apps like **IP Webcam (Android)** to turn your phone into a network camera.
Update the `url` variable in both Python scripts to match your IP camera address:
```python
url = "http://YOUR_IP_HERE:8080/video"
```

### 🧪 Test your connection
Before running the AI, ensure your camera feed is accessible:
```bash
python GuardianAI/camera_test.py
```
*(Press `q` to quit the video window)*

### 🛡️ Start Guardian AI
Run the main detection script:
```bash
python GuardianAI/person_detection.py
```

The system will start analyzing the feed. If a person is detected:
- A screenshot will be saved in the `screenshots/` directory.
- A video of the event will be saved in the `recordings/` directory.

*(Press `q` to quit Guardian AI)*

---

## 📂 Project Structure

```text
Guardian-AI/
├── GuardianAI/
│   ├── main.py                 # Placeholder for future enhancements
│   ├── person_detection.py     # Core AI detection & recording script
│   ├── camera_test.py          # Script to verify IP camera stream
│   └── requirements.txt        # Project dependencies
├── recordings/                 # Auto-generated video clips of events
├── screenshots/                # Auto-generated snapshot images
├── yolov8n.pt                  # Pre-trained YOLOv8 Nano model weights
└── README.md                   # Project documentation
```

---

## 📝 License

Distributed under the MIT License.

<br />
<div align="center">
  <i>Built with ❤️ using Python & AI</i>
</div>

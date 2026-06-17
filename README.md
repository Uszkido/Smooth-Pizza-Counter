# Pizza & Ice Cream Club — AI Counting System

> Computer-vision production tracking for Pizza & Ice Cream Club, built and deployed by **Vexel Innovations**.

---

## What it does

Staff at Pizza & Ice Cream Club needed a reliable way to track daily production in real time without manual tallying. This system mounts a camera above the production line and uses a YOLOv8 object-detection model to count items crossing a configurable threshold line — automatically, continuously, and without any specialist hardware.

**Key capabilities:**

- Live camera feed with AI detection overlay and crossing-line counter
- Real-time dashboard: today's count, hourly breakdown, daily goal progress
- Role-based access (manager and viewer accounts)
- Analytics page with weekly trend data and shift summaries
- Telegram and WhatsApp notification integrations
- CSV export of production records and full audit log
- Windows service with watchdog — survives reboots and crashes automatically
- ngrok-based remote access for off-site monitoring
- Native desktop UI (PyQt6) as an alternative to the web dashboard

---

## Screenshots

**Staff portal login**

![Login page](docs/images/login_page_clean.png)

**Live detection dashboard — AI counting in action**

![Live detection](docs/images/live_detection_clean.png)

---

## Tech stack

| Layer | Technology |
|---|---|
| Backend | Python 3.11, FastAPI, Uvicorn |
| Computer vision | YOLOv8n (Ultralytics), OpenCV, ONNX Runtime |
| Desktop UI | PyQt6 |
| Frontend | Jinja2 templates, vanilla JS |
| Packaging | PyInstaller (Windows .exe + installer via Inno Setup) |
| Service management | NSSM-style Windows service with watchdog |
| Remote access | ngrok |
| Notifications | Telegram Bot API, WhatsApp (via external API) |

---

## Project structure

```
├── main.py                   # FastAPI backend — detection, API routes, session management
├── vms_ui.py                 # Native PyQt6 desktop client
├── launcher.py               # System-tray launcher (starts server, opens browser)
├── scaffold_android.py       # Android client scaffold (in progress)
├── templates/                # Jinja2 HTML templates (login, dashboard, analytics, calibration)
├── static/                   # Brand assets and logo files
├── yolov8n.pt                # YOLOv8 nano model weights
├── yolov8n.onnx              # ONNX export for production inference
├── config.example.json       # Configuration template (copy to config.json and fill in)
├── requirements.txt          # Python dependencies
├── scripts/                  # Build, install, and service management scripts
│   ├── INSTALL_SERVICE.bat   # Register as Windows service
│   ├── WATCHDOG.bat          # Watchdog process
│   ├── STATUS.bat            # Check service status
│   ├── BUILD_*.bat/.ps1      # PyInstaller build scripts
│   └── PizzaInstaller.iss    # Inno Setup installer configuration
└── docs/                     # Operational documentation
    ├── OPERATIONS_GUIDE.html
    ├── SERVER_SETUP_GUIDE.html
    ├── TECHNICAL_ARCHITECTURE.html
    └── ...
```

---

## Getting started

**1. Clone and set up a virtual environment**

```bash
git clone https://github.com/Uszkido/Smooth-Pizza-Counter.git
cd Smooth-Pizza-Counter
python -m venv venv_311
venv_311\Scripts\activate
pip install -r requirements.txt
```

**2. Configure**

```bash
copy config.example.json config.json
```

Edit `config.json` with your camera IP, credentials, and branch name. See `docs/SERVER_SETUP_GUIDE.html` for full details.

**3. Run**

```bash
python launcher.py
```

On first run, the app generates random admin and viewer passwords and prints them to the console — note them down before the window closes.

**4. Deploy as a Windows service**

Run `scripts\INSTALL_SERVICE.bat` as Administrator to register the app as a persistent Windows service with automatic restart on failure.

---

## Build

To produce a standalone `.exe` for deployment on a machine without Python:

```bash
scripts\BUILD_FINAL.bat
```

The packaged build includes all dependencies and can be distributed as a single folder. Use `scripts\PizzaInstaller.iss` with Inno Setup to produce an installer `.exe`.

> Note: `PizzaVMS_Final.spec` is required by the build scripts but is not included in this repo (machine-specific). Generate it with `pyinstaller --name PizzaVMS_Final main.py` before running the build scripts.

---

## Configuration reference

| Key | Description |
|---|---|
| `cam_ip` | Camera IP address (`"0"` for built-in webcam) |
| `cam_brand` | `"HIKVISION"` or `"DAHUA"` (sets RTSP URL format) |
| `line_y` | Vertical pixel position of the counting line |
| `confidence` | YOLOv8 detection confidence threshold (0–1) |
| `daily_target` | Target item count for the day (used in goal ring) |
| `app_port` | Web server port (default 8040) |
| `telegram_bot_token` | Telegram bot token for shift notifications |
| `branch_name` | Display name shown in the dashboard header |

---

## License

Copyright © 2026 Vexel Innovations. All rights reserved.

This software is proprietary. Unauthorized copying, distribution, or modification is prohibited.

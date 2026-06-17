import sys
import os
import traceback

# â”€â”€â”€â”€â”€â”€ GLOBAL DEBUGGER / CRASH LOGGER â”€â”€â”€â”€â”€â”€
log_path = os.path.join(os.path.dirname(sys.executable if getattr(sys, 'frozen', False) else __file__), "pizza_crash_log.txt")
open(log_path, "a").write(f"\n--- APP STARTED {os.getpid()} ---\n")

def crash_handler(exc_type, exc_value, exc_tb):
    with open(log_path, "a") as f:
        f.write("FATAL ERROR:\n")
        traceback.print_exception(exc_type, exc_value, exc_tb, file=f)
sys.excepthook = crash_handler

import cv2
import json
import time
import threading
import secrets
import csv
import io
import numpy as np
import uvicorn
import requests
from datetime import datetime, timedelta
from fastapi import FastAPI, Request, Response, Form
from fastapi.responses import StreamingResponse, HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from ultralytics import YOLO

app = FastAPI()

def get_base_path():
    if getattr(sys, 'frozen', False):
        return sys._MEIPASS
    return os.path.dirname(os.path.abspath(__file__))

BASE_DIR = get_base_path()
USER_DATA_DIR = os.path.dirname(sys.executable) if getattr(sys, 'frozen', False) else BASE_DIR

os.makedirs(os.path.join(BASE_DIR, "static"), exist_ok=True)
os.makedirs(os.path.join(BASE_DIR, "templates"), exist_ok=True)

app.mount("/static", StaticFiles(directory=os.path.join(BASE_DIR, "static")), name="static")
templates = Jinja2Templates(directory=os.path.join(BASE_DIR, "templates"))

CONFIG_FILE = os.path.join(USER_DATA_DIR, "config.json")
LOG_FILE    = os.path.join(USER_DATA_DIR, "pizza_logs.json")
AUDIT_FILE  = os.path.join(USER_DATA_DIR, "audit_log.json")

# â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
# CONFIG
# â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
DEFAULT_CONFIG = {
    "branch_name": "Main Branch",
    "app_port": 8040,
    "cam_ip": "", "cam_user": "admin", "cam_pass": "",
    "cam_port": "554", "cam_brand": "HIKVISION",
    "line_y": 360, "confidence": 0.5, "yolo_model": "yolov8n.pt",
    "daily_target": 500,
    "telegram_bot_token": "", "telegram_chat_id": "",
    "whatsapp_phone": "", "whatsapp_apikey": "",
}

def _generate_first_run_users():
    admin_pw = secrets.token_urlsafe(9)
    viewer_pw = secrets.token_urlsafe(9)
    print("=" * 60)
    print("FIRST RUN: generated login credentials (save these now)")
    print(f"  admin  / {admin_pw}")
    print(f"  viewer / {viewer_pw}")
    print("These will not be shown again. Change them in config.json.")
    print("=" * 60)
    return {
        "admin": {"password": admin_pw, "role": "manager"},
        "viewer": {"password": viewer_pw, "role": "viewer"}
    }

def load_config():
    if not os.path.exists(CONFIG_FILE):
        cfg = DEFAULT_CONFIG.copy()
        cfg["users"] = _generate_first_run_users()
        with open(CONFIG_FILE, "w") as f:
            json.dump(cfg, f, indent=4)
        return cfg
    with open(CONFIG_FILE, "r") as f:
        cfg = json.load(f)
    # merge missing keys from default
    changed = False
    for k, v in DEFAULT_CONFIG.items():
        if k not in cfg:
            cfg[k] = v
            changed = True
    if changed:
        save_config(cfg)
    return cfg
def save_config(cfg):
    with open(CONFIG_FILE, "w") as f:
        json.dump(cfg, f, indent=4)

def load_logs():
    if not os.path.exists(LOG_FILE):
        return {}
    with open(LOG_FILE, "r") as f:
        try: return json.load(f)
        except: return {}

def save_logs(logs):
    with open(LOG_FILE, "w") as f:
        json.dump(logs, f, indent=4)

# â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
# AUDIT LOG
# â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
def write_audit(action: str, user: str = "system"):
    entries = []
    if os.path.exists(AUDIT_FILE):
        try:
            with open(AUDIT_FILE, "r") as f:
                entries = json.load(f)
        except: pass
    entries.append({
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "user": user,
        "action": action
    })
    # Keep last 500 entries only
    entries = entries[-500:]
    with open(AUDIT_FILE, "w") as f:
        json.dump(entries, f, indent=2)

# â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
# NOTIFICATIONS
# â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
def send_telegram(message):
    cfg = load_config()
    token = cfg.get("telegram_bot_token", "")
    chat  = cfg.get("telegram_chat_id", "")
    if not token or not chat: return
    try:
        requests.post(f"https://api.telegram.org/bot{token}/sendMessage",
                      json={"chat_id": chat, "text": message}, timeout=3)
    except: pass

def send_whatsapp(message):
    cfg = load_config()
    phone  = cfg.get("whatsapp_phone", "").strip()
    apikey = cfg.get("whatsapp_apikey", "").strip()
    if not phone or not apikey: return
    try:
        requests.get(
            f"https://api.callmebot.com/whatsapp.php",
            params={"phone": phone, "text": message, "apikey": apikey},
            timeout=3
        )
    except: pass

def notify(message):
    """Send to both Telegram and WhatsApp."""
    threading.Thread(target=send_telegram, args=(message,), daemon=True).start()
    threading.Thread(target=send_whatsapp, args=(message,), daemon=True).start()

# â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
# SESSION / AUTH
# â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
# token -> {"username": str, "role": str}
ACTIVE_SESSIONS = {}

def get_session(request: Request):
    token = request.cookies.get("session_token", "")
    return ACTIVE_SESSIONS.get(token)

def is_logged_in(request: Request) -> bool:
    return get_session(request) is not None

def is_manager(request: Request) -> bool:
    s = get_session(request)
    return s is not None and s.get("role") == "manager"

def require_login(request: Request):
    if not is_logged_in(request):
        return RedirectResponse(url="/login", status_code=302)
    return None

def require_manager(request: Request):
    if not is_manager(request):
        return RedirectResponse(url="/", status_code=302)
    return None

# â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
# VIDEO STREAM
# â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
class VideoStream:
    def __init__(self, src=0):
        self.stopped = False
        self.src = int(src) if str(src).isdigit() else src
        os.environ["OPENCV_FFMPEG_READ_ATTEMPTS"] = "20"
        os.environ["OPENCV_FFMPEG_CAPTURE_OPTIONS"] = "rtsp_transport;tcp|fflags;nobuffer|flags;low_delay"
        self.cap = cv2.VideoCapture(self.src, cv2.CAP_FFMPEG)
        self.cap.set(cv2.CAP_PROP_BUFFERSIZE, 0)
        self.ret  = False
        self.frame = None
        if self.cap.isOpened():
            self.ret, self.frame = self.cap.read()
        self.lock = threading.Lock()
        threading.Thread(target=self.update, daemon=True).start()

    def update(self):
        while not self.stopped:
            if not self.cap or not self.cap.isOpened():
                time.sleep(1)
                self.cap = cv2.VideoCapture(self.src)
                self.cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)
                continue
            ret, frame = self.cap.read()
            if not ret:
                time.sleep(0.5)
                self.cap.release()
                continue
            with self.lock:
                self.ret   = ret
                self.frame = frame

    def read(self):
        with self.lock:
            if self.frame is not None:
                return self.ret, self.frame.copy()
            return False, None

    def stop(self):
        self.stopped = True
        if self.cap: self.cap.release()

def get_camera_source():
    cfg = load_config()
    ip  = cfg.get("cam_ip", "").strip()
    if not ip or ip == "0": return 0
    user  = cfg.get("cam_user", "admin")
    pwd   = cfg.get("cam_pass", "")
    port  = cfg.get("cam_port", "554")
    brand = cfg.get("cam_brand", "HIKVISION").upper()
    if brand == "DAHUA":
        return f"rtsp://{user}:{pwd}@{ip}:{port}/cam/realmonitor?channel=1&subtype=1"
    elif brand == "TIANDY":
        return f"rtsp://{user}:{pwd}@{ip}:{port}/live/ch1_sub"
    elif brand == "GENERIC":
        return f"rtsp://{user}:{pwd}@{ip}:{port}/stream2"
    else:
        return f"rtsp://{user}:{pwd}@{ip}:{port}/Streaming/Channels/102"

stream = None
def get_stream():
    global stream
    curr_src = get_camera_source()
    if stream is None or str(stream.src) != str(curr_src):
        if stream: stream.stop()
        stream = VideoStream(curr_src)
    return stream

model = None
last_model_path = ""
def get_model():
    global model, last_model_path
    cfg    = load_config()
    m_path = cfg.get("yolo_model", "yolov8n.pt")
    full_path = m_path
    if not os.path.isabs(m_path):
        test = os.path.join(USER_DATA_DIR, m_path)
        full_path = test if os.path.exists(test) else os.path.join(BASE_DIR, m_path)
    if model is None or last_model_path != full_path:
        try:
            model = YOLO(full_path); last_model_path = full_path
        except:
            try:
                model = YOLO(os.path.join(BASE_DIR, "yolov8n.pt"))
                last_model_path = os.path.join(BASE_DIR, "yolov8n.pt")
            except:
                model = YOLO("yolov8n.pt"); last_model_path = "yolov8n.pt"
    return model

# â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
# PIZZA RATE (pizzas in last 60 minutes)
# â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
pizza_timestamps = []   # list of epoch times when each pizza was counted
sparkline_buffer = []   # list of {"t": epoch, "v": cumulative_count}
SPARKLINE_MAX   = 30    # keep last 30 data-points

def get_pizza_rate():
    """Return pizzas counted in the last 60 minutes."""
    now    = time.time()
    cutoff = now - 3600
    global pizza_timestamps
    pizza_timestamps = [t for t in pizza_timestamps if t > cutoff]
    return len(pizza_timestamps)

def push_sparkline(count: int):
    global sparkline_buffer
    sparkline_buffer.append({"t": round(time.time()), "v": count})
    if len(sparkline_buffer) > SPARKLINE_MAX:
        sparkline_buffer.pop(0)

# â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
# FRAME GENERATION
# â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
total_count          = 0
counted_ids          = set()
history              = {}
last_pizza_time      = time.time()
downtime_alert_sent  = False
nightly_brief_sent   = ""

# â”€â”€â”€ Log read cache â€” avoid hitting disk every frame â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
_log_cache: dict = {}
_log_cache_ts: float = 0.0
LOG_CACHE_TTL = 1.0  # seconds

def load_logs_cached() -> dict:
    global _log_cache, _log_cache_ts
    if time.time() - _log_cache_ts < LOG_CACHE_TTL:
        return _log_cache
    _log_cache = load_logs()
    _log_cache_ts = time.time()
    return _log_cache

# â”€â”€â”€ Save-logs debounce â€” only write if dirty â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
_logs_dirty = False
_last_save_ts: float = 0.0
SAVE_INTERVAL = 2.0  # seconds between disk writes

def mark_logs_dirty(logs: dict):
    """Update cache and mark for save; actual write happens every SAVE_INTERVAL."""
    global _log_cache, _log_cache_ts, _logs_dirty
    _log_cache    = logs
    _log_cache_ts = time.time()
    _logs_dirty   = True

def flush_logs_if_dirty(logs: dict):
    global _logs_dirty, _last_save_ts
    if _logs_dirty and (time.time() - _last_save_ts) >= SAVE_INTERVAL:
        save_logs(logs)
        _logs_dirty   = False
        _last_save_ts = time.time()

def generate_frames():
    global total_count, counted_ids, history, last_pizza_time
    global downtime_alert_sent, nightly_brief_sent, pizza_timestamps
    last_processed = 0

    date_str = datetime.now().strftime("%Y-%m-%d")
    logs = load_logs()
    if date_str in logs:
        total_count = logs[date_str].get("total", 0)

    while True:
        cfg = load_config()
        vs  = get_stream()
        ret, frame = vs.read()

        if not ret or frame is None:
            time.sleep(0.1); continue

        now = time.time()
        if now - last_processed < 0.02:
            time.sleep(0.005); continue
        last_processed = now

        dt_now   = datetime.now()
        date_str = dt_now.strftime("%Y-%m-%d")
        hour_str = dt_now.strftime("%H")

        logs = load_logs_cached()
        if date_str not in logs:
            logs[date_str] = {"total": 0, "hourly": {}}
        if hour_str not in logs[date_str]["hourly"]:
            logs[date_str]["hourly"][hour_str] = 0
        total_count = logs[date_str]["total"]

        branch = cfg.get("branch_name", "Pizza & Ice Cream Club")

        # Downtime (30 min)
        if (now - last_pizza_time) > 1800 and not downtime_alert_sent and total_count > 0:
            downtime_alert_sent = True
            notify(f"âš ï¸ [{branch}] No pizzas from the oven in 30 minutes! Please check the kitchen staff and oven.")

        # Nightly brief at 23:xx
        if hour_str == "23" and nightly_brief_sent != date_str:
            nightly_brief_sent = date_str
            rate = get_pizza_rate()
            notify(
                f"ðŸŒ™ {branch} Nightly Brief â€” {date_str}\n"
                f"ðŸ• Total Pizzas Today: {total_count}\n"
                f"ðŸ“Š Current Rate: {rate} pizzas/hr"
            )

        # Resize â€” 960 px wide: faster YOLO inference + quicker JPEG encode
        h, w = frame.shape[:2]
        target_w = 960
        frame    = cv2.resize(frame, (target_w, int(h * (target_w / w))))
        new_h    = frame.shape[0]

        m = get_model()
        # Class 53 = 'apple' in standard COCO (closest proxy for pizza in yolov8n).
        # If you loaded a custom pizza model trained on class 0, change this to [0].
        yolo_model_name = cfg.get("yolo_model", "").lower()
        classes_to_track = [53] if "yolov8n" in yolo_model_name and "pizza" not in yolo_model_name else [0]
        results = m.track(source=frame, imgsz=480, persist=True,
                          conf=float(cfg.get("confidence", 0.5)),
                          classes=classes_to_track, verbose=False,
                          tracker="bytetrack.yaml")

        line_y = max(10, min(new_h - 10, int(cfg.get("line_y", 360))))
        cv2.line(frame, (0, line_y), (target_w, line_y), (0, 255, 0), 3)
        cv2.putText(frame, "Counting Line", (20, line_y - 15),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 255, 0), 2)

        res = results[0]
        if res.boxes is not None and res.boxes.id is not None:
            for tid, box in zip(res.boxes.id.cpu().tolist(),
                                res.boxes.xyxy.cpu().tolist()):
                x1, y1, x2, y2 = map(int, box)
                cx = (x1 + x2) // 2
                cy = (y1 + y2) // 2
                tid = int(tid)

                history.setdefault(tid, []).append(cy)
                if len(history[tid]) > 10: history[tid].pop(0)

                if len(history[tid]) >= 2:
                    if history[tid][0] < line_y <= history[tid][-1]:
                        if tid not in counted_ids:
                            counted_ids.add(tid)
                            logs[date_str]["total"] += 1
                            logs[date_str]["hourly"][hour_str] += 1
                            mark_logs_dirty(logs)      # debounced disk write
                            pizza_timestamps.append(time.time())
                            push_sparkline(logs[date_str]["total"])
                            last_pizza_time     = time.time()
                            downtime_alert_sent = False
                            cv2.rectangle(frame, (0, 0), (target_w, new_h), (0, 255, 0), 20)

                color = (0, 0, 255) if tid in counted_ids else (255, 100, 0)
                cv2.rectangle(frame, (x1, y1), (x2, y2), color, 2)
                cv2.putText(frame, f"ID:{tid}", (x1, y1-10),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.7, color, 2)
                cv2.circle(frame, (cx, cy), 6, (0, 255, 255), -1)

        # Overlay counter
        ov = frame.copy()
        cv2.rectangle(ov, (10, 10), (340, 110), (0, 0, 0), -1)
        cv2.addWeighted(ov, 0.6, frame, 0.4, 0, frame)
        cv2.putText(frame, f"PIZZAS: {logs[date_str]['total']}", (25, 75),
                    cv2.FONT_HERSHEY_SIMPLEX, 1.5, (0, 255, 0), 4)

        rate_now = get_pizza_rate()
        cv2.putText(frame, f"{rate_now}/hr", (25, 105),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 200, 200), 2)

        if downtime_alert_sent:
            cv2.putText(frame, "NO PIZZA IN 30 MIN - CHECK OVEN",
                        (20, new_h - 20), cv2.FONT_HERSHEY_SIMPLEX, 0.9, (0, 0, 255), 3)

        flush_logs_if_dirty(logs)   # write to disk at most every 2 seconds
        _, buf = cv2.imencode(".jpg", frame, [int(cv2.IMWRITE_JPEG_QUALITY), 85])
        yield (b"--frame\r\nContent-Type: image/jpeg\r\n\r\n" + buf.tobytes() + b"\r\n")

# â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
# ANALYTICS HELPERS
# â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
def build_weekly_data():
    logs  = load_logs()
    today = datetime.now().date()
    labels = []
    values = []
    for i in range(6, -1, -1):
        d = (today - timedelta(days=i)).strftime("%Y-%m-%d")
        labels.append(d)
        values.append(logs.get(d, {}).get("total", 0))
    return {"labels": labels, "values": values}

def build_records(logs):
    best_day   = max(logs, key=lambda d: logs[d].get("total", 0), default=None)
    worst_day  = min(logs, key=lambda d: logs[d].get("total", 0), default=None)
    totals     = [logs[d]["total"] for d in logs if logs[d].get("total", 0) > 0]
    avg        = round(sum(totals) / len(totals), 1) if totals else 0
    best_val   = logs[best_day]["total"] if best_day else 0
    worst_val  = logs[worst_day]["total"] if worst_day else 0
    return {
        "best_day": best_day, "best_val": best_val,
        "worst_day": worst_day, "worst_val": worst_val,
        "daily_avg": avg
    }

# â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
# ROUTES â€” AUTH
# â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
@app.get("/login")
def login_page(request: Request):
    if is_logged_in(request):
        return RedirectResponse(url="/", status_code=302)
    return templates.TemplateResponse(request=request, name="login.html", context={"error": ""})

@app.post("/login")
async def login_submit(request: Request,
                       username: str = Form(...),
                       password: str = Form(...)):
    cfg   = load_config()
    users = cfg.get("users", {})
    user  = users.get(username)
    if user and user.get("password") == password:
        token = secrets.token_hex(32)
        ACTIVE_SESSIONS[token] = {"username": username, "role": user.get("role", "viewer")}
        write_audit(f"Login by '{username}'", username)
        redirect = RedirectResponse(url="/", status_code=302)
        redirect.set_cookie("session_token", token, httponly=True, samesite="lax")
        return redirect
    return templates.TemplateResponse(request=request, name="login.html",
        context={"error": "Invalid username or password."})

@app.get("/logout")
def logout(request: Request):
    token = request.cookies.get("session_token", "")
    sess  = ACTIVE_SESSIONS.pop(token, {})
    write_audit(f"Logout by '{sess.get('username','?')}'", sess.get("username","?"))
    r = RedirectResponse(url="/login", status_code=302)
    r.delete_cookie("session_token")
    return r

# â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
# ROUTES â€” PAGES
# â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
@app.get("/")
def index(request: Request):
    g = require_login(request)
    if g: return g
    sess = get_session(request)
    return templates.TemplateResponse(request=request, name="index.html",
        context={"role": sess["role"], "username": sess["username"]})

@app.get("/calibration")
def calibration(request: Request):
    g = require_manager(request)
    if g: return g
    sess = get_session(request)
    return templates.TemplateResponse(request=request, name="calibration.html",
        context={"role": sess["role"], "username": sess["username"]})

@app.get("/analytics")
def analytics(request: Request):
    g = require_login(request)
    if g: return g
    sess = get_session(request)
    return templates.TemplateResponse(request=request, name="analytics.html",
        context={"role": sess["role"], "username": sess["username"]})

@app.get("/video_feed")
def video_feed(request: Request):
    g = require_login(request)
    if g: return g
    return StreamingResponse(generate_frames(),
                             media_type="multipart/x-mixed-replace; boundary=frame")

# â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
# ROUTES â€” API
# â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
@app.get("/api/config")
def get_config_api(request: Request):
    g = require_login(request)
    if g: return g
    return load_config()

@app.post("/api/config")
async def update_config_api(request: Request):
    g = require_manager(request)
    if g: return {"error": "Unauthorized"}
    data = await request.json()
    cfg  = load_config()
    cfg.update(data)
    save_config(cfg)
    sess = get_session(request)
    write_audit("Config updated", sess["username"] if sess else "unknown")
    return {"status": "success"}

@app.get("/api/stats")
def get_stats(request: Request):
    g = require_login(request)
    if g: return {"error": "Unauthorized"}
    today    = datetime.now().strftime("%Y-%m-%d")
    logs     = load_logs()
    cfg      = load_config()
    records  = build_records(logs)
    weekly   = build_weekly_data()
    global last_pizza_time, sparkline_buffer
    idle_mins = int((time.time() - last_pizza_time) / 60)
    # Build shift sub-totals from hourly data
    hourly = logs.get(today, {}).get("hourly", {})
    shifts = {"morning": 0, "afternoon": 0, "night": 0}
    for h, v in hourly.items():
        hi = int(h)
        if 6 <= hi < 12:  shifts["morning"]   += v
        elif 12 <= hi < 18: shifts["afternoon"] += v
        else:               shifts["night"]     += v
    return {
        "branch_name":  cfg.get("branch_name", "Main Branch"),
        "total_pizzas": logs.get(today, {}).get("total", 0),
        "daily_target": cfg.get("daily_target", 500),
        "hourly_data":  hourly,
        "pizza_rate":   get_pizza_rate(),
        "idle_minutes": idle_mins if logs.get(today, {}).get("total", 0) > 0 else 0,
        "full_history": logs,
        "weekly":       weekly,
        "records":      records,
        "shifts":       shifts,
        "sparkline":    list(sparkline_buffer),
    }

@app.post("/api/reset")
def reset_counter(request: Request):
    g = require_manager(request)
    if g: return {"error": "Unauthorized"}
    global counted_ids, history, last_pizza_time, pizza_timestamps
    counted_ids.clear(); history.clear(); pizza_timestamps.clear()
    last_pizza_time = time.time()
    today = datetime.now().strftime("%Y-%m-%d")
    logs  = load_logs()
    if today in logs:
        logs[today]["total"]  = 0
        logs[today]["hourly"] = {}
        save_logs(logs)
    sess = get_session(request)
    write_audit("Counter reset", sess["username"] if sess else "unknown")
    sparkline_buffer.clear()
    return {"status": "success"}

@app.get("/api/export_csv")
def export_csv(request: Request):
    g = require_login(request)
    if g: return g
    logs = load_logs()
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(["Date", "Hour", "Pizzas"])
    for date in sorted(logs.keys()):
        hourly = logs[date].get("hourly", {})
        for h in sorted(hourly.keys()):
            writer.writerow([date, f"{h}:00", hourly[h]])
    output.seek(0)
    return StreamingResponse(iter([output.getvalue()]),
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=pizza_history.csv"})

@app.get("/api/audit_log")
def get_audit_log(request: Request):
    g = require_manager(request)
    if g: return {"error": "Unauthorized"}
    if not os.path.exists(AUDIT_FILE): return []
    with open(AUDIT_FILE, "r") as f:
        try: return json.load(f)
        except: return []

@app.post("/api/shift_summary")
def shift_summary(request: Request):
    g = require_login(request)
    if g: return {"error": "Unauthorized"}
    today = datetime.now().strftime("%Y-%m-%d")
    logs  = load_logs()
    cfg   = load_config()
    branch = cfg.get("branch_name", "Pizza & Ice Cream Club")
    total  = logs.get(today, {}).get("total", 0)
    hourly = logs.get(today, {}).get("hourly", {})
    peak_h = max(hourly, key=lambda h: hourly[h], default="N/A")
    peak_v = hourly.get(peak_h, 0)
    sess   = get_session(request)
    user   = sess["username"] if sess else "unknown"
    hour   = datetime.now().strftime("%H:%M")
    msg = (
        f"ðŸ“‹ {branch} â€” Shift Summary ({hour})\n"
        f"ðŸ‘¤ Submitted by: {user}\n"
        f"ðŸ• Pizzas so far today: {total}\n"
        f"â° Peak hour: {peak_h}:00 ({peak_v} pizzas)\n"
        f"ðŸ“ˆ Rate: {get_pizza_rate()} pizzas/hr"
    )
    notify(msg)
    write_audit(f"Shift summary sent by '{user}'", user)
    return {"status": "success", "message": msg}

@app.post("/api/manual_adjust")
async def manual_adjust(request: Request):
    """Add or subtract from today's count. Body: {delta: int, reason: str}"""
    g = require_manager(request)
    if g: return {"error": "Unauthorized"}
    data   = await request.json()
    delta  = int(data.get("delta", 0))
    reason = str(data.get("reason", "Manual adjustment"))[:120]
    if delta == 0:
        return {"error": "delta must be non-zero"}
    today  = datetime.now().strftime("%Y-%m-%d")
    hour   = datetime.now().strftime("%H")
    logs   = load_logs()
    if today not in logs:
        logs[today] = {"total": 0, "hourly": {}}
    if hour not in logs[today]["hourly"]:
        logs[today]["hourly"][hour] = 0
    logs[today]["total"]          = max(0, logs[today]["total"] + delta)
    logs[today]["hourly"][hour]   = max(0, logs[today]["hourly"][hour] + delta)
    save_logs(logs)
    push_sparkline(logs[today]["total"])
    sess = get_session(request)
    user = sess["username"] if sess else "unknown"
    sign = f"+{delta}" if delta > 0 else str(delta)
    write_audit(f"Manual adjust {sign} â€” {reason}", user)
    notify(f"âœï¸ [{load_config().get('branch_name','Branch')}] Manual adjust {sign} by {user}: {reason}")
    return {"status": "success", "new_total": logs[today]["total"]}

@app.get("/api/remote")
def get_remote(request: Request):
    g = require_login(request)
    if g: return {"error": "Unauthorized"}
    try:
        r = requests.get("http://localhost:4040/api/tunnels", timeout=1)
        if r.status_code == 200:
            tunnels = r.json().get("tunnels", [])
            if tunnels:
                return {"status": "success", "url": tunnels[0]["public_url"]}
    except: pass
    return {"status": "error", "message": "Remote not running. Start START_REMOTE_ACCESS.bat"}

@app.post("/api/test_telegram")
def test_telegram(request: Request):
    g = require_login(request)
    if g: return {"error": "Unauthorized"}
    notify("ðŸ• Test OK! Nightly briefs and downtime alerts are active.")
    return {"status": "success"}

# â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
if __name__ == "__main__":
    # Bind 0.0.0.0 so the dashboard is reachable from LAN devices too
    cfg = load_config()
    uvicorn.run(app, host="0.0.0.0", port=cfg.get("app_port", 8040), log_level="info")

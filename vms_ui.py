"""
Pizza & Ice Cream Club — Native VMS GUI
Full-featured replacement for the Chromium/WebEngine embed.
All screens: Login, Live Dashboard, Analytics, Settings/Calibration.
"""
import sys
import time
import os
import cv2
import numpy as np
import requests as _req
import json

def _asset(name: str) -> str:
    """Return absolute path to a static asset. Works both frozen (PyInstaller) and in dev."""
    if getattr(sys, "frozen", False):
        # PyInstaller bundles ('static','static') → files land at sys._MEIPASS/static/<name>
        return os.path.join(sys._MEIPASS, "static", name)
    else:
        return os.path.join(os.path.dirname(os.path.abspath(__file__)), "static", name)

def get_app_port():
    try:
        cfg_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "config.json")
        if getattr(sys, "frozen", False):
            cfg_path = os.path.join(os.path.dirname(sys.executable), "config.json")
        with open(cfg_path, "r") as f:
            return int(json.load(f).get("app_port", 8040))
    except:
        return 8040

from PyQt6.QtWidgets import (
    QApplication, QSystemTrayIcon, QMenu, QMainWindow, QWidget,
    QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QFrame, QSizePolicy,
    QStackedWidget, QScrollArea, QLineEdit, QComboBox, QSlider,
    QMessageBox, QInputDialog, QTableWidget, QTableWidgetItem,
    QHeaderView, QProgressBar, QFormLayout, QGroupBox,
)
from PyQt6.QtGui import (
    QAction, QImage, QPixmap, QFont, QColor, QPainter, QPen
)
from PyQt6.QtCore import Qt, QThread, pyqtSignal, QTimer

# ── SESSION STATE ──────────────────────────────────────────────────────────
BASE_URL       = f"http://127.0.0.1:{get_app_port()}"
SESSION_COOKIE = {"session_token": ""}
SESSION_ROLE   = {"role": "viewer"}
SESSION_USER   = {"user": ""}

# ── DESIGN TOKENS ──────────────────────────────────────────────────────────
DARK       = "#0b0c10"
SIDEBAR_BG = "#0d0e14"
CARD_BG    = "#1a1d27"
ACCENT     = "#66fcf1"
ACCENT2    = "#45a29e"
TEXT       = "#c5c6c7"
PURE       = "#ffffff"
GREEN      = "#4ade80"
ORANGE     = "#fb923c"
RED        = "#ff4b2b"
YELLOW     = "#fbbf24"

GLOBAL_STYLE = f"""
    QWidget   {{ background-color:{DARK}; color:{TEXT}; font-family:'Segoe UI'; }}
    QLabel    {{ color:{TEXT}; background:transparent; }}
    QScrollBar:vertical   {{ width:6px; background:transparent; }}
    QScrollBar::handle:vertical {{ background:rgba(255,255,255,0.12); border-radius:3px; }}
    QScrollBar::add-line:vertical,
    QScrollBar::sub-line:vertical {{ height:0; }}
    QLineEdit, QComboBox {{
        background:rgba(0,0,0,0.45); border:1px solid rgba(255,255,255,0.1);
        border-radius:6px; padding:7px 10px; color:{PURE};
        font-size:13px; font-family:'Segoe UI';
    }}
    QLineEdit:focus, QComboBox:focus {{ border:1px solid {ACCENT}; }}
    QComboBox QAbstractItemView {{ background:#1a1d27; color:{PURE};
        selection-background-color:{ACCENT2}; }}
    QGroupBox {{
        border:1px solid rgba(255,255,255,0.07); border-radius:10px;
        margin-top:10px; padding:14px;
    }}
    QGroupBox::title {{
        color:{PURE}; font-weight:bold; subcontrol-origin:margin;
        subcontrol-position:top left; padding:0 6px; left:12px;
    }}
    QTableWidget {{ background:transparent; border:none;
        gridline-color:rgba(255,255,255,0.05); }}
    QTableWidget::item {{ padding:6px; border:none; }}
    QHeaderView::section {{
        background:rgba(0,0,0,0.4); color:{ACCENT}; font-size:9px;
        text-transform:uppercase; letter-spacing:1px; border:none; padding:6px;
    }}
    QSlider::groove:horizontal {{
        height:5px; background:rgba(255,255,255,0.1); border-radius:3px;
    }}
    QSlider::handle:horizontal {{
        width:16px; height:16px; border-radius:8px;
        background:{ACCENT}; margin:-5px 0;
    }}
    QSlider::sub-page:horizontal {{ background:{ACCENT}; border-radius:3px; }}
"""

# ── HELPERS ────────────────────────────────────────────────────────────────
def card_frame():
    f = QFrame()
    f.setStyleSheet(f"QFrame{{background:{CARD_BG}; border-radius:14px;"
                    f"border:1px solid rgba(255,255,255,0.06);}}")
    return f

def styled_btn(text, color="accent", small=False):
    pad = "7px 14px" if small else "10px 18px"
    fs  = "11px"    if small else "13px"
    styles = {
        "accent": f"background:qlineargradient(x1:0,y1:0,x2:1,y2:1,"
                  f"stop:0 {ACCENT},stop:1 {ACCENT2}); color:#000;",
        "green":  f"background:qlineargradient(x1:0,y1:0,x2:1,y2:1,"
                  f"stop:0 {GREEN},stop:1 #22c55e); color:#000;",
        "orange": f"background:qlineargradient(x1:0,y1:0,x2:1,y2:1,"
                  f"stop:0 {ORANGE},stop:1 #f97316); color:#000;",
        "red":    f"background:qlineargradient(x1:0,y1:0,x2:1,y2:1,"
                  f"stop:0 {RED},stop:1 #ff416c); color:#fff;",
        "ghost":  "background:rgba(255,255,255,0.07); color:#fff;"
                  "border:1px solid rgba(255,255,255,0.15);",
    }
    bg = styles.get(color, "background:#313244; color:#fff;")
    btn = QPushButton(text)
    btn.setStyleSheet(f"""
        QPushButton{{
            {bg} border-radius:8px; padding:{pad};
            font-weight:bold; font-size:{fs};
            font-family:'Segoe UI'; border:none;
        }}
        QPushButton:hover{{opacity:0.85;}}
        QPushButton:disabled{{opacity:0.4;}}
    """)
    return btn

def api_get(path):
    try:
        r = _req.get(f"{BASE_URL}{path}",
                     cookies=SESSION_COOKIE, timeout=3)
        return r.json() if r.ok else None
    except:
        return None

def api_post(path, payload=None):
    try:
        r = _req.post(f"{BASE_URL}{path}", json=payload,
                      cookies=SESSION_COOKIE, timeout=4)
        return r.json() if r.ok else None
    except:
        return None


# ══════════════════════════════════════════════════════════════════════════
# VIDEO WORKER THREAD
# ══════════════════════════════════════════════════════════════════════════
class VideoWorker(QThread):
    frame_ready = pyqtSignal(np.ndarray)

    def run(self):
        while True:
            cap = cv2.VideoCapture(f"{BASE_URL}/video_feed",
                                   cv2.CAP_FFMPEG)
            while cap.isOpened():
                ret, frame = cap.read()
                if ret:
                    self.frame_ready.emit(frame)
                else:
                    break
            cap.release()
            time.sleep(2)


# ══════════════════════════════════════════════════════════════════════════
# PURE-PYTHON BAR CHART WIDGET
# ══════════════════════════════════════════════════════════════════════════
class BarChart(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.labels = []
        self.values = []
        self.setMinimumHeight(170)

    def set_data(self, labels, values):
        self.labels = labels
        self.values = values
        self.update()

    def paintEvent(self, _):
        if not self.values:
            return
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        W, H = self.width(), self.height()
        pl, pr, pt, pb = 44, 10, 10, 28
        cw = W - pl - pr
        ch = H - pt - pb
        mx = max(self.values) or 1
        n  = len(self.values)
        bar_w = max(4, cw // n - 3)
        step  = cw / n

        # grid lines
        p.setPen(QPen(QColor(255, 255, 255, 18), 1))
        for i in range(5):
            y = pt + i * ch // 4
            p.drawLine(pl, y, W - pr, y)

        # bars
        for i, (lbl, val) in enumerate(zip(self.labels, self.values)):
            x = int(pl + i * step + (step - bar_w) / 2)
            bh = int(val / mx * ch)
            y  = pt + ch - bh
            c  = QColor(ACCENT)
            c.setAlphaF(0.82)
            p.setBrush(c)
            p.setPen(Qt.PenStyle.NoPen)
            p.drawRoundedRect(x, y, bar_w, bh, 3, 3)
            if n <= 24 and i % max(1, n // 12) == 0:
                p.setPen(QColor(TEXT))
                p.setFont(QFont("Segoe UI", 7))
                p.drawText(x - 2, H - 4, lbl[:5])
        p.end()


class LineChart(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.labels = []
        self.values = []
        self.setMinimumHeight(170)

    def set_data(self, labels, values):
        self.labels = labels
        self.values = values
        self.update()

    def paintEvent(self, _):
        if len(self.values) < 2:
            return
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        W, H = self.width(), self.height()
        pl, pr, pt, pb = 44, 10, 10, 28
        cw = W - pl - pr
        ch = H - pt - pb
        mx = max(self.values) or 1

        p.setPen(QPen(QColor(255, 255, 255, 18), 1))
        for i in range(5):
            y = pt + i * ch // 4
            p.drawLine(pl, y, W - pr, y)

        spacing = cw / max(len(self.values) - 1, 1)
        pts = []
        for i, v in enumerate(self.values):
            x = int(pl + i * spacing)
            y = int(pt + ch - v / mx * ch)
            pts.append((x, y))

        p.setPen(QPen(QColor(ACCENT), 2))
        for i in range(len(pts) - 1):
            p.drawLine(*pts[i], *pts[i + 1])

        p.setBrush(QColor(ACCENT))
        p.setPen(Qt.PenStyle.NoPen)
        for x, y in pts:
            p.drawEllipse(x - 4, y - 4, 8, 8)

        p.setPen(QColor(TEXT))
        p.setFont(QFont("Segoe UI", 7))
        for lbl, (x, _) in zip(self.labels, pts):
            p.drawText(x - 14, H - 4, lbl[-5:])
        p.end()


# ══════════════════════════════════════════════════════════════════════════
# LOGIN PAGE
# ══════════════════════════════════════════════════════════════════════════
class LoginPage(QWidget):
    login_success = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        outer = QVBoxLayout(self)
        outer.setAlignment(Qt.AlignmentFlag.AlignCenter)

        box = card_frame()
        box.setFixedWidth(420)
        bl = QVBoxLayout(box)
        bl.setSpacing(14)
        bl.setContentsMargins(36, 36, 36, 36)

        # Branding logo
        logo_lbl = QLabel()
        logo_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        logo_path = _asset("pizza_club_logo.png")
        if os.path.exists(logo_path):
            pix = QPixmap(logo_path).scaledToHeight(
                56, Qt.TransformationMode.SmoothTransformation
            )
            logo_lbl.setPixmap(pix)
        else:
            logo_lbl.setText("🍕 Pizza & Ice Cream Club")
            logo_lbl.setStyleSheet(f"font-size:22px; font-weight:900; color:{PURE};")

        sub = QLabel("AI VMS Terminal — Secure Login")
        sub.setStyleSheet(f"font-size:12px; color:{TEXT};")
        sub.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.inp_user = QLineEdit()
        self.inp_user.setPlaceholderText("Username")

        self.inp_pass = QLineEdit()
        self.inp_pass.setPlaceholderText("Password")
        self.inp_pass.setEchoMode(QLineEdit.EchoMode.Password)
        self.inp_pass.returnPressed.connect(self.do_login)

        self.err = QLabel("")
        self.err.setStyleSheet("color:#ff4b2b; font-size:12px;")
        self.err.setAlignment(Qt.AlignmentFlag.AlignCenter)

        btn = styled_btn("🔐 Login", "accent")
        btn.clicked.connect(self.do_login)

        for w in [logo_lbl, sub, self.inp_user, self.inp_pass, self.err, btn]:
            bl.addWidget(w)

        # Vexel footer on login screen
        vexel_row = QHBoxLayout()
        vexel_row.setAlignment(Qt.AlignmentFlag.AlignCenter)
        vexel_logo = QLabel()
        vxl_path = _asset("logo_white.png")
        if os.path.exists(vxl_path):
            vpix = QPixmap(vxl_path).scaledToHeight(
                18, Qt.TransformationMode.SmoothTransformation
            )
            vexel_logo.setPixmap(vpix)
        vexel_txt = QLabel("Developed by Vexel Innovations")
        vexel_txt.setStyleSheet("font-size:10px; opacity:0.45; color:#888;")
        vexel_row.addWidget(vexel_logo)
        vexel_row.addWidget(vexel_txt)

        outer.addWidget(box, alignment=Qt.AlignmentFlag.AlignCenter)
        outer.addSpacing(12)
        outer.addLayout(vexel_row)

    def do_login(self):
        u = self.inp_user.text().strip()
        pw = self.inp_pass.text().strip()
        try:
            resp = _req.post(
                f"{BASE_URL}/login",
                data={"username": u, "password": pw},
                allow_redirects=False, timeout=4
            )
            token = resp.cookies.get("session_token", "")
            if token:
                SESSION_COOKIE["session_token"] = token
                SESSION_USER["user"] = u
                # Detect role: audit_log endpoint only works for managers
                test = _req.get(f"{BASE_URL}/api/audit_log",
                                cookies=SESSION_COOKIE, timeout=3)
                SESSION_ROLE["role"] = (
                    "manager" if test.ok and isinstance(test.json(), list)
                    else "viewer"
                )
                self.err.setText("")
                self.login_success.emit()
                return
        except Exception:
            pass
        self.err.setText("❌ Invalid username or password")


# ══════════════════════════════════════════════════════════════════════════
# DASHBOARD PAGE
# ══════════════════════════════════════════════════════════════════════════
class DashboardPage(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.vid = VideoWorker()
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # ── Camera (left) ─────────────────────────────────────────────────
        cam_area = QWidget()
        cl = QVBoxLayout(cam_area)
        cl.setContentsMargins(14, 14, 8, 14)

        live_row = QHBoxLayout()
        self.live_dot = QLabel("● LIVE AI TRACKING")
        self.live_dot.setStyleSheet(f"color:{RED}; font-weight:bold; font-size:12px;")
        self.branch_lbl = QLabel("")
        self.branch_lbl.setStyleSheet(f"color:{TEXT}; font-size:12px;")
        live_row.addWidget(self.live_dot)
        live_row.addStretch()
        live_row.addWidget(self.branch_lbl)
        cl.addLayout(live_row)

        self.cam = QLabel("INITIALIZING NEURAL ENGINE…")
        self.cam.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.cam.setStyleSheet(f"background:#000; border-radius:12px;"
                               f"border:2px solid rgba(255,255,255,0.07);"
                               f"font-size:16px; color:#6c7086;")
        self.cam.setSizePolicy(QSizePolicy.Policy.Expanding,
                               QSizePolicy.Policy.Expanding)
        cl.addWidget(self.cam)

        # ── Right sidebar ──────────────────────────────────────────────────
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFixedWidth(275)
        scroll.setStyleSheet("border:none; background:transparent;")
        sc_inner = QWidget()
        scroll.setWidget(sc_inner)
        rl = QVBoxLayout(sc_inner)
        rl.setContentsMargins(0, 14, 14, 14)
        rl.setSpacing(10)

        # Goal progress
        cg = card_frame()
        cgl = QVBoxLayout(cg)
        cgl.setContentsMargins(14, 12, 14, 12)
        lbl_g = QLabel("DAILY GOAL PROGRESS")
        lbl_g.setStyleSheet("font-size:9px; letter-spacing:2px;")
        self.goal_bar = QProgressBar()
        self.goal_bar.setRange(0, 100)
        self.goal_bar.setValue(0)
        self.goal_bar.setFixedHeight(13)
        self.goal_bar.setTextVisible(False)
        self.goal_bar.setStyleSheet(f"""
            QProgressBar{{background:rgba(255,255,255,0.07);border-radius:6px;border:none;}}
            QProgressBar::chunk{{background:qlineargradient(x1:0,y1:0,x2:1,y2:0,
                stop:0 {ACCENT},stop:1 {ACCENT2});border-radius:6px;}}
        """)
        self.goal_lbl = QLabel("0% of 500 target")
        self.goal_lbl.setStyleSheet(f"font-size:11px; color:{ACCENT};")
        cgl.addWidget(lbl_g)
        cgl.addWidget(self.goal_bar)
        cgl.addWidget(self.goal_lbl)
        rl.addWidget(cg)

        # Pizzas today + rate
        ct = card_frame()
        ctl = QVBoxLayout(ct)
        ctl.setContentsMargins(14, 12, 14, 12)
        QLabel("PIZZAS TODAY").also(
            lambda l: l.setStyleSheet("font-size:9px; letter-spacing:2px;")
        ).setParent(ct)
        ctl.addWidget(
            QLabel("PIZZAS TODAY").also(
                lambda l: l.setStyleSheet("font-size:9px; letter-spacing:2px;")
            )
        )
        self.total = QLabel("0")
        self.total.setStyleSheet(
            f"font-size:52px; font-weight:900; color:{ACCENT}; line-height:1;"
        )
        self.rate = QLabel("0/hr")
        self.rate.setStyleSheet(
            f"background:rgba(102,252,241,0.12); color:{ACCENT};"
            f"border:1px solid rgba(102,252,241,0.2); border-radius:12px;"
            f"padding:3px 10px; font-weight:bold; font-size:13px;"
        )
        self.idle = QLabel("✅ OVEN RUNNING")
        self.idle.setStyleSheet(
            f"color:{GREEN}; border:1px solid {GREEN}; border-radius:12px;"
            f"padding:4px 10px; font-size:11px; font-weight:bold;"
        )
        ctl.addWidget(self.total)
        ctl.addWidget(self.rate)
        ctl.addWidget(self.idle)
        rl.addWidget(ct)

        # Hourly breakdown table
        ch_ = card_frame()
        chl = QVBoxLayout(ch_)
        chl.setContentsMargins(14, 12, 14, 12)
        hdr_lbl = QLabel("Hourly Breakdown")
        hdr_lbl.setStyleSheet(f"font-size:11px; color:{PURE}; font-weight:bold;")
        chl.addWidget(hdr_lbl)
        self.hourly = QTableWidget(0, 2)
        self.hourly.setHorizontalHeaderLabels(["Hour", "Pizzas"])
        self.hourly.horizontalHeader().setSectionResizeMode(
            QHeaderView.ResizeMode.Stretch
        )
        self.hourly.verticalHeader().setVisible(False)
        self.hourly.setFixedHeight(130)
        self.hourly.setStyleSheet("font-size:11px;")
        chl.addWidget(self.hourly)
        rl.addWidget(ch_)

        # Action buttons
        self.btn_remote = styled_btn("🌐 Get Remote Link", "green", small=True)
        self.btn_shift  = styled_btn("📋 Send Shift Summary", "orange", small=True)
        self.btn_reset  = styled_btn("⚠️ Reset Counter", "red", small=True)
        self.btn_remote.clicked.connect(self.get_remote)
        self.btn_shift.clicked.connect(self.send_shift_summary)
        self.btn_reset.clicked.connect(self.reset_counter)
        rl.addWidget(self.btn_remote)
        rl.addWidget(self.btn_shift)
        rl.addWidget(self.btn_reset)
        rl.addStretch()

        layout.addWidget(cam_area, 1)
        layout.addWidget(scroll, 0)

        # Timers
        self.timer = QTimer()
        self.timer.timeout.connect(self.refresh)
        self.timer.start(2000)
        self.vid.frame_ready.connect(self._update_frame)

    def start_video(self):
        if not self.vid.isRunning():
            self.vid.start()

    def _update_frame(self, frame):
        rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        h, w, ch = rgb.shape
        qi = QImage(rgb.data, w, h, ch * w, QImage.Format.Format_RGB888)
        pix = QPixmap.fromImage(qi).scaled(
            self.cam.width(), self.cam.height(),
            Qt.AspectRatioMode.KeepAspectRatio,
            Qt.TransformationMode.SmoothTransformation,
        )
        self.cam.setPixmap(pix)

    def refresh(self):
        d = api_get("/api/stats")
        if not d:
            return
        total  = d.get("total_pizzas", 0)
        target = d.get("daily_target", 500)
        rate   = d.get("pizza_rate", 0)
        idle_m = d.get("idle_minutes", 0)
        self.total.setText(str(total))
        self.rate.setText(f"{rate}/hr")
        self.branch_lbl.setText(d.get("branch_name", ""))
        pct = min(100, int(total / target * 100)) if target else 0
        self.goal_bar.setValue(pct)
        self.goal_lbl.setText(f"{pct}% of {target} target")
        if idle_m >= 30 and total > 0:
            self.idle.setText(f"⚠️ NO PIZZA FOR {idle_m} MINS")
            self.idle.setStyleSheet(
                f"color:{RED}; border:1px solid {RED}; border-radius:12px;"
                f"padding:4px 10px; font-size:11px; font-weight:bold;"
            )
        else:
            self.idle.setText("✅ OVEN RUNNING")
            self.idle.setStyleSheet(
                f"color:{GREEN}; border:1px solid {GREEN}; border-radius:12px;"
                f"padding:4px 10px; font-size:11px; font-weight:bold;"
            )
        hourly = d.get("hourly_data", {})
        rows   = sorted(
            [h for h in hourly if hourly[h] > 0],
            reverse=True
        )[:6]
        self.hourly.setRowCount(len(rows))
        for i, h in enumerate(rows):
            self.hourly.setItem(i, 0, QTableWidgetItem(
                f"{h}:00 – {str(int(h)+1).zfill(2)}:00"
            ))
            it = QTableWidgetItem(str(hourly[h]))
            it.setForeground(QColor(ACCENT))
            self.hourly.setItem(i, 1, it)

    def get_remote(self):
        d = api_get("/api/remote")
        if d and d.get("status") == "success":
            dlg = QInputDialog(self)
            dlg.setWindowTitle("Remote Access Link")
            dlg.setLabelText("Your remote link (copy it):")
            dlg.setTextValue(d.get("url", ""))
            dlg.exec()
        else:
            msg = d.get("message", "Start START_REMOTE_ACCESS.bat first.") if d else "Not available."
            QMessageBox.warning(self, "Remote", msg)

    def send_shift_summary(self):
        self.btn_shift.setEnabled(False)
        self.btn_shift.setText("Sending…")
        d = api_post("/api/shift_summary")
        self.btn_shift.setEnabled(True)
        self.btn_shift.setText("📋 Send Shift Summary")
        if d:
            QMessageBox.information(self, "Shift Summary", d.get("message", "Sent!"))

    def reset_counter(self):
        if SESSION_ROLE["role"] != "manager":
            QMessageBox.warning(self, "Unauthorized", "Only managers can reset the counter.")
            return
        if QMessageBox.question(
            self, "Confirm Reset", "Reset today's counter to zero?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        ) == QMessageBox.StandardButton.Yes:
            api_post("/api/reset")
            self.refresh()


# ══════════════════════════════════════════════════════════════════════════
# ANALYTICS PAGE
# ══════════════════════════════════════════════════════════════════════════
class AnalyticsPage(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        layout = QHBoxLayout(self)
        layout.setContentsMargins(14, 14, 14, 14)
        layout.setSpacing(12)
        self.all_logs = {}

        # Left: date calendar
        left = card_frame()
        left.setFixedWidth(230)
        ll = QVBoxLayout(left)
        ll.setContentsMargins(12, 12, 12, 12)
        hdr = QLabel("📅 Historical Calendar")
        hdr.setStyleSheet(f"font-weight:bold; font-size:13px; color:{PURE};")
        ll.addWidget(hdr)
        self.date_tbl = QTableWidget(0, 2)
        self.date_tbl.setHorizontalHeaderLabels(["Date", "Total"])
        self.date_tbl.horizontalHeader().setSectionResizeMode(
            QHeaderView.ResizeMode.Stretch
        )
        self.date_tbl.verticalHeader().setVisible(False)
        self.date_tbl.setSelectionBehavior(
            QTableWidget.SelectionBehavior.SelectRows
        )
        self.date_tbl.cellClicked.connect(self._date_clicked)
        ll.addWidget(self.date_tbl)

        # Right: charts scroll
        right = QScrollArea()
        right.setWidgetResizable(True)
        right.setStyleSheet("border:none; background:transparent;")
        ri = QWidget()
        right.setWidget(ri)
        rl = QVBoxLayout(ri)
        rl.setSpacing(12)
        rl.setContentsMargins(0, 0, 0, 0)

        # KPI row
        kpi_row = QWidget()
        kr = QHBoxLayout(kpi_row)
        kr.setSpacing(10)
        kr.setContentsMargins(0, 0, 0, 0)

        def kpi_card(label, color=ACCENT):
            f = card_frame()
            bl = QVBoxLayout(f)
            bl.setContentsMargins(14, 12, 14, 12)
            v = QLabel("—")
            v.setStyleSheet(f"font-size:26px; font-weight:900; color:{color};")
            lb = QLabel(label)
            lb.setStyleSheet("font-size:9px; letter-spacing:1.5px;")
            bl.addWidget(v); bl.addWidget(lb)
            return f, v

        cf1, self.kpi_total = kpi_card("Selected Total")
        cf2, self.kpi_avg   = kpi_card("Daily Average")
        cf3, self.kpi_peak  = kpi_card("🏆 Best Hour", YELLOW)
        cf4, self.kpi_rate  = kpi_card("Live Rate/hr", GREEN)
        for c in [cf1, cf2, cf3, cf4]:
            kr.addWidget(c)
        rl.addWidget(kpi_row)

        # Records banner
        rec = card_frame()
        recl = QHBoxLayout(rec)
        recl.setContentsMargins(16, 14, 16, 14)

        def rec_col(label, color=YELLOW):
            w = QWidget()
            bl = QVBoxLayout(w)
            lb = QLabel(label)
            lb.setStyleSheet("font-size:9px; letter-spacing:1.5px;")
            val = QLabel("—")
            val.setStyleSheet(f"font-size:15px; font-weight:900; color:{color};")
            dt = QLabel("—")
            dt.setStyleSheet("font-size:10px; opacity:0.5;")
            bl.addWidget(lb); bl.addWidget(val); bl.addWidget(dt)
            return w, val, dt

        bw, self.best_val, self.best_date   = rec_col("🏆 Best Day Ever")
        ww, self.worst_val, self.worst_date = rec_col("📉 Quietest Day", TEXT)
        recl.addWidget(bw); recl.addWidget(ww)
        rl.addWidget(rec)

        # Hourly bar chart
        hc = card_frame()
        hcl = QVBoxLayout(hc)
        hcl.setContentsMargins(14, 12, 14, 12)
        hc_hdr = QHBoxLayout()
        hc_hdr.addWidget(
            QLabel("📈 Hourly Breakdown").also(
                lambda l: l.setStyleSheet(f"font-weight:bold; font-size:13px; color:{PURE};")
            )
        )
        hc_hdr.addStretch()
        btn_csv = styled_btn("⬇ Export CSV", "ghost", small=True)
        btn_csv.clicked.connect(self._export_csv)
        hc_hdr.addWidget(btn_csv)
        hcl.addLayout(hc_hdr)
        self.bar = BarChart()
        hcl.addWidget(self.bar)
        rl.addWidget(hc)

        # Weekly line chart
        wc = card_frame()
        wcl = QVBoxLayout(wc)
        wcl.setContentsMargins(14, 12, 14, 12)
        wcl.addWidget(
            QLabel("📆 Last 7 Days").also(
                lambda l: l.setStyleSheet(f"font-weight:bold; font-size:13px; color:{PURE};")
            )
        )
        self.line = LineChart()
        wcl.addWidget(self.line)
        rl.addWidget(wc)
        rl.addStretch()

        layout.addWidget(left, 0)
        layout.addWidget(right, 1)

    def load(self):
        d = api_get("/api/stats")
        if not d:
            return
        self.all_logs = d.get("full_history", {})
        rec = d.get("records", {})
        self.kpi_avg.setText(str(rec.get("daily_avg", "—")))
        self.kpi_rate.setText(f"{d.get('pizza_rate', 0)}/hr")
        self.best_val.setText(f"{rec.get('best_val', '—')} 🍕")
        self.best_date.setText(rec.get("best_day", "—"))
        self.worst_val.setText(f"{rec.get('worst_val', '—')} 🍕")
        self.worst_date.setText(rec.get("worst_day", "—"))
        wl = d.get("weekly", {}).get("labels", [])
        wv = d.get("weekly", {}).get("values", [])
        self.line.set_data([l[5:] for l in wl], wv)
        dates = sorted(self.all_logs.keys(), reverse=True)
        self.date_tbl.setRowCount(len(dates))
        for i, dt in enumerate(dates):
            self.date_tbl.setItem(i, 0, QTableWidgetItem(dt))
            it = QTableWidgetItem(str(self.all_logs[dt].get("total", 0)))
            it.setForeground(QColor(ACCENT))
            self.date_tbl.setItem(i, 1, it)
        if dates:
            self.date_tbl.selectRow(0)
            self._show_date(dates[0])

    def _date_clicked(self, row, _col):
        dates = sorted(self.all_logs.keys(), reverse=True)
        if row < len(dates):
            self._show_date(dates[row])

    def _show_date(self, date):
        day    = self.all_logs.get(date, {})
        hourly = day.get("hourly", {})
        total  = day.get("total", 0)
        self.kpi_total.setText(str(total))
        labels, values, max_h, max_v = [], [], "—", 0
        for i in range(24):
            h = str(i).zfill(2)
            v = hourly.get(h, 0)
            labels.append(f"{h}:00")
            values.append(v)
            if v > max_v:
                max_v = v; max_h = f"{h}:00"
        self.kpi_peak.setText(max_h)
        self.bar.set_data(labels, values)

    def _export_csv(self):
        import webbrowser
        webbrowser.open(f"{BASE_URL}/api/export_csv")


# ══════════════════════════════════════════════════════════════════════════
# SETTINGS PAGE
# ══════════════════════════════════════════════════════════════════════════
class SettingsPage(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.vid = VideoWorker()
        layout = QHBoxLayout(self)
        layout.setContentsMargins(14, 14, 14, 14)
        layout.setSpacing(12)

        # Camera preview (left)
        cam_f = card_frame()
        cam_l = QVBoxLayout(cam_f)
        cam_l.setContentsMargins(12, 12, 12, 12)
        cam_l.addWidget(
            QLabel("📷 Live Preview / Counting Line").also(
                lambda l: l.setStyleSheet(f"font-weight:bold; font-size:12px; color:{PURE};")
            )
        )
        self.cam = QLabel("Loading…")
        self.cam.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.cam.setStyleSheet("background:#000; border-radius:8px; font-size:13px; color:#6c7086;")
        self.cam.setMinimumHeight(280)
        cam_l.addWidget(self.cam)
        layout.addWidget(cam_f, 1)
        self.vid.frame_ready.connect(self._update_frame)

        # Settings scroll (right)
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFixedWidth(350)
        scroll.setStyleSheet("border:none; background:transparent;")
        si = QWidget()
        scroll.setWidget(si)
        sl = QVBoxLayout(si)
        sl.setSpacing(10)
        sl.setContentsMargins(0, 0, 4, 0)

        # Branch
        g1 = QGroupBox("🏪 Branch Identity")
        f1 = QFormLayout(g1)
        self.inp_branch = QLineEdit(); f1.addRow("Branch Name:", self.inp_branch)
        sl.addWidget(g1)

        # Camera config
        g2 = QGroupBox("📷 Camera Config")
        f2 = QFormLayout(g2)
        self.inp_ip   = QLineEdit(); f2.addRow("Camera IP ('0'=Webcam):", self.inp_ip)
        self.inp_user = QLineEdit(); f2.addRow("Username:", self.inp_user)
        self.inp_pass = QLineEdit()
        self.inp_pass.setEchoMode(QLineEdit.EchoMode.Password)
        f2.addRow("Password:", self.inp_pass)
        self.inp_port = QLineEdit(); f2.addRow("RTSP Port:", self.inp_port)
        self.cmb_brand = QComboBox()
        self.cmb_brand.addItems(["HIKVISION", "DAHUA", "TIANDY", "GENERIC"])
        f2.addRow("Brand:", self.cmb_brand)
        sl.addWidget(g2)

        # AI & counting
        g3 = QGroupBox("🧠 AI & Counting")
        f3 = QFormLayout(g3)
        self.inp_target = QLineEdit(); f3.addRow("Daily Pizza Target:", self.inp_target)
        self.inp_model  = QLineEdit(); f3.addRow("YOLO Model File:", self.inp_model)
        conf_row = QWidget(); cr = QHBoxLayout(conf_row); cr.setContentsMargins(0,0,0,0)
        self.sld_conf = QSlider(Qt.Orientation.Horizontal)
        self.sld_conf.setRange(10, 100); self.sld_conf.setValue(50)
        self.lbl_conf = QLabel("0.50"); self.lbl_conf.setFixedWidth(36)
        self.sld_conf.valueChanged.connect(lambda v: self.lbl_conf.setText(f"{v/100:.2f}"))
        cr.addWidget(self.sld_conf); cr.addWidget(self.lbl_conf)
        f3.addRow("Confidence:", conf_row)
        line_row = QWidget(); lr = QHBoxLayout(line_row); lr.setContentsMargins(0,0,0,0)
        self.sld_line = QSlider(Qt.Orientation.Horizontal)
        self.sld_line.setRange(10, 710); self.sld_line.setValue(360)
        self.lbl_line = QLabel("360"); self.lbl_line.setFixedWidth(36)
        self.sld_line.valueChanged.connect(lambda v: self.lbl_line.setText(str(v)))
        lr.addWidget(self.sld_line); lr.addWidget(self.lbl_line)
        f3.addRow("Counting Line Y:", line_row)
        sl.addWidget(g3)

        # Notifications
        g4 = QGroupBox("🔔 Notifications")
        f4 = QFormLayout(g4)
        self.inp_tg_tok = QLineEdit()
        self.inp_tg_tok.setEchoMode(QLineEdit.EchoMode.Password)
        f4.addRow("Telegram Token:", self.inp_tg_tok)
        self.inp_tg_id  = QLineEdit(); f4.addRow("Telegram Chat ID:", self.inp_tg_id)
        self.inp_wa_ph  = QLineEdit(); f4.addRow("WhatsApp Phone:", self.inp_wa_ph)
        self.inp_wa_key = QLineEdit()
        self.inp_wa_key.setEchoMode(QLineEdit.EchoMode.Password)
        f4.addRow("CallMeBot API Key:", self.inp_wa_key)
        btn_test = styled_btn("📩 Send Test Notification", "ghost", small=True)
        btn_test.clicked.connect(self._test_notify)
        f4.addRow(btn_test)
        sl.addWidget(g4)

        # User accounts
        g5 = QGroupBox("👥 User Accounts")
        f5 = QFormLayout(g5)
        self.inp_mgr_u  = QLineEdit(); f5.addRow("Manager Username:", self.inp_mgr_u)
        self.inp_mgr_p  = QLineEdit()
        self.inp_mgr_p.setEchoMode(QLineEdit.EchoMode.Password)
        f5.addRow("Manager Password:", self.inp_mgr_p)
        self.inp_view_u = QLineEdit(); f5.addRow("Viewer Username:", self.inp_view_u)
        self.inp_view_p = QLineEdit()
        self.inp_view_p.setEchoMode(QLineEdit.EchoMode.Password)
        f5.addRow("Viewer Password:", self.inp_view_p)
        note = QLabel("Manager can reset counter & change settings. Viewer = read-only.")
        note.setStyleSheet("font-size:10px; opacity:0.5;")
        note.setWordWrap(True)
        f5.addRow(note)
        sl.addWidget(g5)

        btn_save = styled_btn("💾 Save All Settings", "accent")
        btn_save.clicked.connect(self._save_all)
        sl.addWidget(btn_save)

        # Audit log
        g6 = QGroupBox("📋 Audit Log")
        g6l = QVBoxLayout(g6)
        self.audit = QTableWidget(0, 3)
        self.audit.setHorizontalHeaderLabels(["Time", "User", "Action"])
        self.audit.horizontalHeader().setSectionResizeMode(
            QHeaderView.ResizeMode.ResizeToContents
        )
        self.audit.horizontalHeader().setStretchLastSection(True)
        self.audit.verticalHeader().setVisible(False)
        self.audit.setFixedHeight(160)
        self.audit.setStyleSheet("font-size:10px;")
        g6l.addWidget(self.audit)
        sl.addWidget(g6)
        sl.addStretch()

        layout.addWidget(scroll, 0)

    def start_video(self):
        if not self.vid.isRunning():
            self.vid.start()

    def _update_frame(self, frame):
        rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        h, w, ch_ = rgb.shape
        qi  = QImage(rgb.data, w, h, ch_ * w, QImage.Format.Format_RGB888)
        pix = QPixmap.fromImage(qi).scaled(
            self.cam.width(), self.cam.height(),
            Qt.AspectRatioMode.KeepAspectRatio,
            Qt.TransformationMode.SmoothTransformation,
        )
        self.cam.setPixmap(pix)

    def load(self):
        d = api_get("/api/config")
        if not d:
            return
        self.inp_branch.setText(d.get("branch_name", ""))
        self.inp_ip.setText(d.get("cam_ip", "0"))
        self.inp_user.setText(d.get("cam_user", "admin"))
        self.inp_pass.setText(d.get("cam_pass", ""))
        self.inp_port.setText(d.get("cam_port", "554"))
        self.cmb_brand.setCurrentText(d.get("cam_brand", "HIKVISION"))
        self.inp_target.setText(str(d.get("daily_target", 500)))
        self.inp_model.setText(d.get("yolo_model", "yolov8n.pt"))
        self.sld_conf.setValue(int(float(d.get("confidence", 0.5)) * 100))
        self.sld_line.setValue(int(d.get("line_y", 360)))
        self.inp_tg_tok.setText(d.get("telegram_bot_token", ""))
        self.inp_tg_id.setText(d.get("telegram_chat_id", ""))
        self.inp_wa_ph.setText(d.get("whatsapp_phone", ""))
        self.inp_wa_key.setText(d.get("whatsapp_apikey", ""))
        users = d.get("users", {})
        mgr  = next((u for u in users if users[u].get("role") == "manager"), "admin")
        view = next((u for u in users if users[u].get("role") == "viewer"),  "viewer")
        self.inp_mgr_u.setText(mgr)
        self.inp_view_u.setText(view)
        # Audit
        rows = api_get("/api/audit_log")
        if rows:
            rows = list(reversed(rows))[:40]
            self.audit.setRowCount(len(rows))
            for i, row in enumerate(rows):
                self.audit.setItem(i, 0, QTableWidgetItem(row.get("timestamp", "")))
                self.audit.setItem(i, 1, QTableWidgetItem(row.get("user", "")))
                self.audit.setItem(i, 2, QTableWidgetItem(row.get("action", "")))

    def _save_all(self):
        cfg   = api_get("/api/config") or {}
        users = cfg.get("users", {})
        new_m = self.inp_mgr_u.text().strip()
        new_v = self.inp_view_u.text().strip()
        old_m = next((u for u in users if users[u].get("role") == "manager"), "admin")
        old_v = next((u for u in users if users[u].get("role") == "viewer"),  "viewer")
        if new_m and new_m != old_m:
            users[new_m] = {**users.get(old_m, {}), "role": "manager"}
            users.pop(old_m, None)
        if new_v and new_v != old_v:
            users[new_v] = {**users.get(old_v, {}), "role": "viewer"}
            users.pop(old_v, None)
        act_m = new_m or old_m
        act_v = new_v or old_v
        if self.inp_mgr_p.text():
            users.setdefault(act_m, {"role": "manager"})["password"] = self.inp_mgr_p.text()
        if self.inp_view_p.text():
            users.setdefault(act_v, {"role": "viewer"})["password"] = self.inp_view_p.text()
        payload = {
            "branch_name":        self.inp_branch.text(),
            "cam_ip":             self.inp_ip.text(),
            "cam_user":           self.inp_user.text(),
            "cam_pass":           self.inp_pass.text(),
            "cam_port":           self.inp_port.text(),
            "cam_brand":          self.cmb_brand.currentText(),
            "daily_target":       int(self.inp_target.text() or 500),
            "yolo_model":         self.inp_model.text(),
            "confidence":         round(self.sld_conf.value() / 100, 2),
            "line_y":             self.sld_line.value(),
            "telegram_bot_token": self.inp_tg_tok.text(),
            "telegram_chat_id":   self.inp_tg_id.text(),
            "whatsapp_phone":     self.inp_wa_ph.text(),
            "whatsapp_apikey":    self.inp_wa_key.text(),
            "users":              users,
        }
        api_post("/api/config", payload)
        QMessageBox.information(self, "Saved", "✅ All settings saved!")
        self.load()

    def _test_notify(self):
        api_post("/api/test_telegram")
        QMessageBox.information(self, "Sent", "📩 Test notification dispatched!")


# ══════════════════════════════════════════════════════════════════════════
# MAIN VMS WINDOW
# ══════════════════════════════════════════════════════════════════════════

# Patch QLabel with .also() for inline-chaining
QLabel.also = lambda self, fn: fn(self) or self


class VMSMainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Pizza & Ice Cream Club — AI VMS Terminal")
        self.setMinimumSize(1200, 700)
        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint |
            Qt.WindowType.WindowStaysOnTopHint
        )

        root   = QWidget()
        root_l = QHBoxLayout(root)
        root_l.setContentsMargins(0, 0, 0, 0)
        root_l.setSpacing(0)
        self.setCentralWidget(root)

        # ── SIDEBAR ───────────────────────────────────────────────────────
        self.sidebar = QFrame()
        self.sidebar.setFixedWidth(225)
        self.sidebar.setStyleSheet(
            f"QFrame{{background:{SIDEBAR_BG};"
            f"border-right:1px solid rgba(255,255,255,0.06);}}"
        )
        self.sidebar.hide()
        sb_l = QVBoxLayout(self.sidebar)
        sb_l.setContentsMargins(0, 0, 0, 0)
        sb_l.setSpacing(0)

        # Logo
        logo_w = QWidget()
        logo_w.setFixedHeight(84)
        logo_w.setStyleSheet(f"background:{SIDEBAR_BG};")
        logo_inner = QVBoxLayout(logo_w)
        logo_inner.setContentsMargins(16, 8, 16, 8)
        logo_inner.setAlignment(Qt.AlignmentFlag.AlignCenter)
        logo_img = QLabel()
        logo_img.setAlignment(Qt.AlignmentFlag.AlignCenter)
        logo_path = _asset("pizza_club_logo.png")
        if os.path.exists(logo_path):
            lpix = QPixmap(logo_path).scaledToHeight(
                42, Qt.TransformationMode.SmoothTransformation
            )
            logo_img.setPixmap(lpix)
        else:
            logo_img.setText("🍕 Pizza & Ice Cream")
            logo_img.setStyleSheet(f"font-size:14px; font-weight:900; color:{PURE};")
        l2 = QLabel("AI VMS TERMINAL")
        l2.setStyleSheet(f"font-size:8px; letter-spacing:3px; color:{ACCENT};")
        l2.setAlignment(Qt.AlignmentFlag.AlignCenter)
        logo_inner.addWidget(logo_img); logo_inner.addWidget(l2)
        sb_l.addWidget(logo_w)

        sep = QFrame()
        sep.setFrameShape(QFrame.Shape.HLine)
        sep.setStyleSheet("background:rgba(255,255,255,0.06); max-height:1px;")
        sb_l.addWidget(sep)

        self._nav_btns = []
        for label, idx in [("▶  Live Dashboard", 0),
                             ("📊  Analytics",      1),
                             ("⚙   Configuration", 2)]:
            btn = QPushButton(label)
            btn.setFixedHeight(52)
            btn.setStyleSheet(self._nav_style(False))
            btn.clicked.connect(lambda _, i=idx: self._switch(i))
            sb_l.addWidget(btn)
            self._nav_btns.append(btn)

        sb_l.addStretch()

        self.session_lbl = QLabel("")
        self.session_lbl.setStyleSheet(f"color:{TEXT}; font-size:10px; padding:10px 16px;")
        self.session_lbl.setWordWrap(True)
        sb_l.addWidget(self.session_lbl)

        # Vexel Innovations branding footer
        vexel_w = QWidget()
        vexel_w.setStyleSheet(f"background:{SIDEBAR_BG}; border-top:1px solid rgba(255,255,255,0.05);")
        vexel_l = QHBoxLayout(vexel_w)
        vexel_l.setContentsMargins(12, 8, 12, 8)
        vexel_l.setSpacing(6)
        vx_logo = QLabel()
        vxl_path = _asset("logo_white.png")
        if os.path.exists(vxl_path):
            vpix = QPixmap(vxl_path).scaledToHeight(
                16, Qt.TransformationMode.SmoothTransformation
            )
            vx_logo.setPixmap(vpix)
        vx_txt = QLabel("Developed by Vexel Innovations")
        vx_txt.setStyleSheet("font-size:9px; color:rgba(197,198,199,0.4);")
        vexel_l.addWidget(vx_logo)
        vexel_l.addWidget(vx_txt)
        vexel_l.addStretch()
        sb_l.addWidget(vexel_w)

        btn_logout = QPushButton("🔒 Logout")
        btn_logout.setFixedHeight(44)
        btn_logout.setStyleSheet(f"""
            QPushButton{{background:rgba(255,75,43,0.1); color:{RED}; border:none;
                font-size:13px; font-weight:bold;
                border-top:1px solid rgba(255,75,43,0.2);}}
            QPushButton:hover{{background:rgba(255,75,43,0.2);}}
        """)
        btn_logout.clicked.connect(self.logout)
        sb_l.addWidget(btn_logout)

        # ── STACK ─────────────────────────────────────────────────────────
        self.stack = QStackedWidget()
        self.login_pg   = LoginPage()
        self.dash_pg    = DashboardPage()
        self.analytics_pg = AnalyticsPage()
        self.settings_pg  = SettingsPage()

        self.stack.addWidget(self.login_pg)      # 0
        self.stack.addWidget(self.dash_pg)       # 1
        self.stack.addWidget(self.analytics_pg)  # 2
        self.stack.addWidget(self.settings_pg)   # 3
        self.stack.setCurrentIndex(0)

        self.login_pg.login_success.connect(self._on_login)

        root_l.addWidget(self.sidebar)
        root_l.addWidget(self.stack, 1)

    def _nav_style(self, active: bool) -> str:
        bg     = "rgba(102,252,241,0.08)" if active else "transparent"
        border = ACCENT if active else "transparent"
        color  = PURE   if active else TEXT
        return (
            f"QPushButton{{background:{bg}; color:{color}; text-align:left;"
            f"padding-left:22px; font-size:14px; border:none;"
            f"border-left:3px solid {border}; font-family:'Segoe UI';}}"
            f"QPushButton:hover{{background:rgba(255,255,255,0.05); color:{PURE};}}"
        )

    def _switch(self, idx: int):
        pages = [1, 2, 3]
        self.stack.setCurrentIndex(pages[idx])
        for i, btn in enumerate(self._nav_btns):
            btn.setStyleSheet(self._nav_style(i == idx))
        if idx == 1:
            self.analytics_pg.load()
        elif idx == 2:
            self.settings_pg.load()
            self.settings_pg.start_video()

    def _on_login(self):
        self.sidebar.show()
        self.session_lbl.setText(
            f"Logged in as:\n{SESSION_USER['user']} ({SESSION_ROLE['role']})"
        )
        is_mgr = SESSION_ROLE["role"] == "manager"
        self._nav_btns[2].setVisible(is_mgr)
        self.dash_pg.btn_reset.setVisible(is_mgr)
        self._switch(0)
        self.dash_pg.start_video()

    def logout(self):
        api_get("/logout")
        SESSION_COOKIE["session_token"] = ""
        SESSION_ROLE["role"] = "viewer"
        SESSION_USER["user"] = ""
        self.sidebar.hide()
        self.stack.setCurrentIndex(0)
        self.login_pg.inp_user.clear()
        self.login_pg.inp_pass.clear()
        self.dash_pg.timer.stop()

    def closeEvent(self, event):
        event.ignore()
        self.hide()


def launch_vms():
    app = QApplication.instance() or QApplication(sys.argv)
    app.setQuitOnLastWindowClosed(False)
    app.setStyleSheet(GLOBAL_STYLE)
    app.setFont(QFont("Segoe UI", 10))

    win = VMSMainWindow()
    win.showFullScreen()

    tray = QSystemTrayIcon(app)
    tray.setIcon(app.style().standardIcon(app.style().StandardPixmap.SP_ComputerIcon))
    tray_menu = QMenu()
    a_show = QAction("Open VMS Terminal", app)
    a_show.triggered.connect(win.showFullScreen)
    a_hide = QAction("Hide to Tray", app)
    a_hide.triggered.connect(win.hide)
    a_quit = QAction("Shutdown AI Engine", app)
    a_quit.triggered.connect(app.quit)
    tray_menu.addAction(a_show)
    tray_menu.addAction(a_hide)
    tray_menu.addSeparator()
    tray_menu.addAction(a_quit)
    tray.setContextMenu(tray_menu)
    tray.show()

    sys.exit(app.exec())


if __name__ == "__main__":
    launch_vms()

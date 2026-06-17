"""
Pizza & Ice Cream Club — VMS Launcher
Starts the FastAPI server in a background thread, opens the browser,
and sits in the system tray for easy control.
No complex PyQt6 widgets — just a tray icon.
"""
import sys
import os
import time
import threading
import webbrowser
import json

# ── Path helpers (works frozen + dev) ──────────────────────────────────────
BASE_DIR = (
    os.path.dirname(sys.executable)
    if getattr(sys, "frozen", False)
    else os.path.dirname(os.path.abspath(__file__))
)

def asset(name: str) -> str:
    if getattr(sys, "frozen", False):
        return os.path.join(sys._MEIPASS, "static", name)
    return os.path.join(BASE_DIR, "static", name)

def get_app_port():
    try:
        cfg_path = os.path.join(BASE_DIR, "config.json")
        with open(cfg_path, "r") as f:
            return int(json.load(f).get("app_port", 8040))
    except:
        return 8040

PORT = get_app_port()
URL  = f"http://127.0.0.1:{PORT}"

# ── Server ──────────────────────────────────────────────────────────────────
_server_thread = None

def _run_uvicorn():
    try:
        import uvicorn
        from main import app
        uvicorn.run(app, host="0.0.0.0", port=PORT,
                    reload=False, log_level="error")
    except Exception:
        import traceback
        log = os.path.join(BASE_DIR, "launcher_crash.txt")
        with open(log, "a") as f:
            f.write(traceback.format_exc())

def start_server():
    global _server_thread
    _server_thread = threading.Thread(target=_run_uvicorn, daemon=True)
    _server_thread.start()

def open_browser():
    time.sleep(2.0)          # wait for uvicorn to be ready
    webbrowser.open(URL)

# ── Tray App ─────────────────────────────────────────────────────────────────
def main():
    from PyQt6.QtWidgets import QApplication, QSystemTrayIcon, QMenu
    from PyQt6.QtGui     import QIcon, QPixmap, QColor
    from PyQt6.QtCore    import Qt

    app = QApplication(sys.argv)
    app.setQuitOnLastWindowClosed(False)

    # Build icon
    logo_path = asset("pizza_club_logo.png")
    if os.path.exists(logo_path):
        icon = QIcon(logo_path)
    else:
        pix = QPixmap(32, 32)
        pix.fill(QColor("#66fcf1"))
        icon = QIcon(pix)

    tray = QSystemTrayIcon(icon, app)
    tray.setToolTip("Pizza & Ice Cream Club — AI VMS")

    menu = QMenu()
    act_open    = menu.addAction("🌐  Open Dashboard")
    act_restart = menu.addAction("🔄  Restart Server")
    menu.addSeparator()
    act_quit    = menu.addAction("❌  Shutdown VMS")

    act_open.triggered.connect(lambda: webbrowser.open(URL))

    def restart():
        tray.showMessage("VMS", "Restarting server…",
                         QSystemTrayIcon.MessageIcon.Information, 2000)
        # Give the old server a moment then spin up a new thread
        threading.Thread(target=start_server, daemon=True).start()
        threading.Thread(target=open_browser, daemon=True).start()

    act_restart.triggered.connect(restart)
    act_quit.triggered.connect(app.quit)

    tray.setContextMenu(menu)

    # Double-click tray icon → open browser
    tray.activated.connect(
        lambda reason: webbrowser.open(URL)
        if reason == QSystemTrayIcon.ActivationReason.Trigger
        else None
    )

    tray.show()

    # Launch server + browser
    start_server()
    threading.Thread(target=open_browser, daemon=True).start()

    tray.showMessage(
        "Pizza & Ice Cream Club VMS",
        "AI engine started — dashboard opening in browser…",
        QSystemTrayIcon.MessageIcon.Information,
        3000,
    )

    sys.exit(app.exec())


if __name__ == "__main__":
    main()

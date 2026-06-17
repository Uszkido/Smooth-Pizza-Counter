# -*- mode: python ; coding: utf-8 -*-
# ─── Smooth Pizza Counter VMS — Native PyQt6 Build (No Chromium) ───────────
import sys
sys.setrecursionlimit(5000)
from PyInstaller.utils.hooks import collect_all

datas = [
    ('templates', 'templates'),
    ('static', 'static'),
    ('yolov8n.pt', '.'),
    ('ngrok.exe', '.'),
    ('START_REMOTE_ACCESS.bat', '.'),
    # vms_ui.py is auto-bundled as a Python module — no need in datas
]
binaries = []
hiddenimports = [
    'encodings',
    'requests',
    'vms_ui',             # Native VMS GUI module
    # PyQt6 native widgets needed for VMS UI
    'PyQt6.QtWidgets',
    'PyQt6.QtGui',
    'PyQt6.QtCore',
    'PyQt6.sip',
]

tmp_ret = collect_all('ultralytics')
datas += tmp_ret[0]; binaries += tmp_ret[1]; hiddenimports += tmp_ret[2]
tmp_ret = collect_all('uvicorn')
datas += tmp_ret[0]; binaries += tmp_ret[1]; hiddenimports += tmp_ret[2]
tmp_ret = collect_all('cv2')
datas += tmp_ret[0]; binaries += tmp_ret[1]; hiddenimports += tmp_ret[2]

a = Analysis(
    ['main.py'],
    pathex=[],
    binaries=binaries,
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[
        # NO Chromium / WebEngine in this build
        'PyQt6.QtWebEngineWidgets',
        'PyQt6.QtWebEngineCore',
        'PyQt6.QtWebChannel',
        'tkinter', 'matplotlib', 'PyQt5', 'PySide2', 'PySide6',
        'IPython', 'notebook', 'scipy', 'polars'
    ],
    noarchive=False,
    optimize=2,
)
pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='PizzaVMS',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,  # Hide console window for a clean VMS look
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)
coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='PizzaVMS',
)

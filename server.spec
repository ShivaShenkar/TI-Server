# -*- mode: python ; coding: utf-8 -*-
from PyInstaller.utils.hooks import collect_all
from pathlib import Path
import gevent
import greenlet

# Explicitly collect everything (datas, binaries, hiddenimports) 
# for the three troublesome packages identified in your log
gevent_datas, gevent_binaries, gevent_hiddenimports = collect_all('gevent')
greenlet_datas, greenlet_binaries, greenlet_hiddenimports = collect_all('greenlet')
cffi_datas, cffi_binaries, cffi_hiddenimports = collect_all('cffi')

# Manually include ALL C extensions (.pyd) from the entire gevent package tree
# because collect_all does not detect .pyd files
gevent_root = Path(gevent.__file__).parent
gevent_pyd = []
for pyd_file in gevent_root.rglob("*.pyd"):
    rel_dir = pyd_file.parent.relative_to(gevent_root.parent)
    gevent_pyd.append((str(pyd_file), str(rel_dir)))

greenlet_pyd = [(str(p), 'greenlet') for p in Path(greenlet.__file__).parent.glob("*.pyd")]

# Bundle ui/ files (Angular build output), preserving relative subdirectory structure
# so Angular asset paths like /TI-Logos-RGB/One-Line/Reversed/ti_hz_1c_rev_rgb.svg resolve correctly
ui_root = Path('ui')
ui_datas = [(str(f), 'ui/' + str(f.parent.relative_to(ui_root))) for f in ui_root.rglob('*') if f.is_file()]

a = Analysis(
    ['server.py'],
    pathex=[],
    binaries=gevent_pyd + greenlet_pyd + gevent_binaries + greenlet_binaries + cffi_binaries,
    datas=[('db/*.json', 'db')] + ui_datas + gevent_datas + greenlet_datas + cffi_datas,
    hiddenimports=[
        'cffi',
        'engineio.async_drivers.gevent',
        'engineio.async_drivers.threading',
        'gevent.monkey', 
        'gevent.pywsgi', 
        'geventwebsocket',
        'socketio',
    ] + gevent_hiddenimports + greenlet_hiddenimports + cffi_hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
)

pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    name='server',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
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
    name='server',
)

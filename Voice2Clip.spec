# -*- mode: python ; coding: utf-8 -*-


a = Analysis(
    ['src/main.py'],
    pathex=['src'],
    binaries=[],
    datas=[('icon.png', '.'), ('src/icons', 'src/icons')],
    hiddenimports=['history', 'recorder', 'sounds', 'transcriber', 'rumps', 'pynput', 'pynput.keyboard', 'pynput.keyboard._darwin', 'pyperclip', 'pyperclip', 'google.genai', 'hotkey_handler', 'Quartz'],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
    optimize=0,
)
pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='Voice2Clip',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,
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
    name='Voice2Clip',
)
app = BUNDLE(
    coll,
    name='Voice2Clip.app',
    icon=None,
    bundle_identifier='com.enrique.voice2clip.pro',
)

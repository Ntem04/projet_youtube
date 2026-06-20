# -*- mode: python ; coding: utf-8 -*-


a = Analysis(
    ['..\\src\\app_gui.py'],
    pathex=[],
    binaries=[('C:\\Users\\SOLUTIONS TECH\\AppData\\Local\\Programs\\Python\\Python314\\DLLs\\_tkinter.pyd', '.'), ('C:\\Users\\SOLUTIONS TECH\\AppData\\Local\\Programs\\Python\\Python314\\DLLs\\tcl86t.dll', '.'), ('C:\\Users\\SOLUTIONS TECH\\AppData\\Local\\Programs\\Python\\Python314\\DLLs\\tk86t.dll', '.')],
    datas=[('C:\\Users\\SOLUTIONS TECH\\AppData\\Local\\Programs\\Python\\Python314\\Lib\\tkinter', 'tkinter'), ('C:\\Users\\SOLUTIONS TECH\\AppData\\Local\\Programs\\Python\\Python314\\tcl\\tcl8.6', 'tcl\\tcl8.6'), ('C:\\Users\\SOLUTIONS TECH\\AppData\\Local\\Programs\\Python\\Python314\\tcl\\tk8.6', 'tcl\\tk8.6')],
    hiddenimports=[],
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
    name='YouTubeDownloader',
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
    name='YouTubeDownloader',
)

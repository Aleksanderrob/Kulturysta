# -*- mode: python ; coding: utf-8 -*-

from PyInstaller.utils.hooks import collect_submodules

hiddenimports = collect_submodules("PySide6") + ["wbb"]

a = Analysis(
    ["main.py"],
    pathex=[],
    binaries=[],
    datas=[("config/default_config.json", "config"), ("assets/logo_placeholder.png", "assets")],
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=["pytest", "jupyter", "matplotlib.tests"],
    noarchive=False,
)
pyz = PYZ(a.pure)
exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name="Kulturysta",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,
    icon=None,
)
coll = COLLECT(exe, a.binaries, a.datas, strip=False, upx=True, name="Kulturysta")

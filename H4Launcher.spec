# -*- mode: python ; coding: utf-8 -*-
#
# PyInstaller spec for H4Launcher.
#
# This file is OS-agnostic - the same spec is used on Windows, macOS,
# and Linux. PyInstaller reads sys.platform at build time and only
# produces the artifact type for whatever OS it's actually running on
# (a .exe folder on Windows, a .app bundle on macOS, a plain binary
# folder on Linux). Run it via `python build.py`, not directly, unless
# you know what you're doing.

import sys
from pathlib import Path

from PyInstaller.utils.hooks import collect_data_files

PROJECT_ROOT = Path(SPECPATH)  # noqa: F821 - SPECPATH is injected by PyInstaller

APP_NAME = "H4Launcher"
BUNDLE_IDENTIFIER = "com.h4launcher.app"

block_cipher = None

# ---------------------------------------------------------------------
# Data files
# ---------------------------------------------------------------------

datas = []

# customtkinter ships its own theme JSON files and font assets outside
# of regular .py files - PyInstaller doesn't pick those up unless we
# ask for them explicitly.
datas += collect_data_files("customtkinter")

# Our own assets folder (logo.svg, future icons, etc).
assets_dir = PROJECT_ROOT / "assets"
if assets_dir.exists():
    datas.append((str(assets_dir), "assets"))

# ---------------------------------------------------------------------
# Icon
# ---------------------------------------------------------------------
#
# Optional - only picked up if the file actually exists, so this spec
# works fine before you've made platform icons.
#   Windows -> assets/icon.ico
#   macOS   -> assets/icon.icns
#   Linux   -> PyInstaller/ELF binaries have no embedded icon; the
#              .desktop file (see packaging/linux) references a .png
#              instead.

icon_file = None

if sys.platform == "win32":
    candidate = assets_dir / "icon.ico"
    if candidate.exists():
        icon_file = str(candidate)

elif sys.platform == "darwin":
    candidate = assets_dir / "icon.icns"
    if candidate.exists():
        icon_file = str(candidate)

# ---------------------------------------------------------------------
# Analysis
# ---------------------------------------------------------------------

a = Analysis(
    ["main.py"],
    pathex=[str(PROJECT_ROOT)],
    binaries=[],
    datas=datas,
    hiddenimports=[
        "PIL._tkinter_finder",
        "minecraft_launcher_lib",
        "requests",
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(
    a.pure,
    a.zipped_data,
    cipher=block_cipher,
)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name=APP_NAME,
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=(sys.platform == "darwin"),
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=icon_file,
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name=APP_NAME,
)

# macOS gets an extra step: wrap the COLLECT output into a proper
# .app bundle with an Info.plist. Windows/Linux just ship the
# COLLECT folder as-is.

if sys.platform == "darwin":

    app = BUNDLE(
        coll,
        name=f"{APP_NAME}.app",
        icon=icon_file,
        bundle_identifier=BUNDLE_IDENTIFIER,
        info_plist={
            "NSHighResolutionCapable": "True",
            "CFBundleShortVersionString": "0.1.0",
            "CFBundleVersion": "0.1.0",
            "NSHumanReadableCopyright": "H4Launcher",
        },
    )

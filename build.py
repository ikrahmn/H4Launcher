#!/usr/bin/env python3
"""
Build script for H4Launcher.

PyInstaller cannot cross-compile: running this script on macOS
produces a macOS build, on Windows a Windows build, on Linux a Linux
build. To get all three, run this same script on all three
operating systems - either by hand, or automatically via the
included GitHub Actions workflow at
.github/workflows/build.yml, which runs it on a
windows-latest / macos-latest / ubuntu-latest matrix.

Usage:
    python build.py                 # build + package for this OS
    python build.py --no-package    # just run PyInstaller, skip zip/dmg/tar
    python build.py --skip-clean    # don't wipe dist/ and build/ first

Output lands in dist/:
    Windows -> dist/H4Launcher/H4Launcher.exe
               dist/H4Launcher-<ver>-windows-x64.zip
    macOS   -> dist/H4Launcher.app
               dist/H4Launcher-<ver>-macos.zip
               dist/H4Launcher-<ver>-macos.dmg   (if hdiutil is available)
    Linux   -> dist/H4Launcher/H4Launcher
               dist/H4Launcher-<ver>-linux-x64.tar.gz
"""

from __future__ import annotations

import argparse
import platform
import shutil
import subprocess
import sys
import tarfile
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent

DIST_DIR = PROJECT_ROOT / "dist"
BUILD_DIR = PROJECT_ROOT / "build"
SPEC_FILE = PROJECT_ROOT / "H4Launcher.spec"

APP_NAME = "H4Launcher"
VERSION = "0.1.0"


def run(cmd: list[str]) -> None:

    print(f"$ {' '.join(cmd)}")

    subprocess.run(
        cmd,
        check=True,
        cwd=PROJECT_ROOT,
    )


def ensure_pyinstaller() -> None:

    try:

        import PyInstaller  # noqa: F401

    except ImportError:

        print("PyInstaller not found - installing it now...")

        run(
            [
                sys.executable,
                "-m",
                "pip",
                "install",
                "--upgrade",
                "pyinstaller",
            ]
        )


def clean() -> None:

    for path in (DIST_DIR, BUILD_DIR):

        if path.exists():

            print(f"Removing {path}")

            shutil.rmtree(path)


def run_pyinstaller() -> None:

    if not SPEC_FILE.exists():

        raise FileNotFoundError(
            f"Could not find {SPEC_FILE}. Run this script from the "
            "project root, next to H4Launcher.spec."
        )

    run(
        [
            sys.executable,
            "-m",
            "PyInstaller",
            str(SPEC_FILE),
            "--noconfirm",
            "--clean",
        ]
    )


def package_windows() -> None:

    exe_dir = DIST_DIR / APP_NAME

    if not exe_dir.exists():

        print(
            f"Expected build output at {exe_dir} was not found - "
            "skipping packaging step."
        )

        return

    archive_base = DIST_DIR / f"{APP_NAME}-{VERSION}-windows-x64"

    shutil.make_archive(
        str(archive_base),
        "zip",
        root_dir=exe_dir,
    )

    print(f"Packaged: {archive_base}.zip")


def package_linux() -> None:

    exe_dir = DIST_DIR / APP_NAME

    if not exe_dir.exists():

        print(
            f"Expected build output at {exe_dir} was not found - "
            "skipping packaging step."
        )

        return

    archive_path = (
        DIST_DIR / f"{APP_NAME}-{VERSION}-linux-x64.tar.gz"
    )

    with tarfile.open(archive_path, "w:gz") as tar:

        tar.add(
            exe_dir,
            arcname=APP_NAME,
        )

    print(f"Packaged: {archive_path}")


def package_macos() -> None:

    app_bundle = DIST_DIR / f"{APP_NAME}.app"

    if not app_bundle.exists():

        print(
            f"Expected build output at {app_bundle} was not found - "
            "skipping packaging step."
        )

        return

    zip_base = DIST_DIR / f"{APP_NAME}-{VERSION}-macos"

    shutil.make_archive(
        str(zip_base),
        "zip",
        root_dir=DIST_DIR,
        base_dir=f"{APP_NAME}.app",
    )

    print(f"Packaged: {zip_base}.zip")

    if shutil.which("hdiutil") is None:

        print(
            "hdiutil not available on this machine - skipped .dmg "
            "creation (the .app / .zip above is still usable)."
        )

        return

    dmg_path = DIST_DIR / f"{APP_NAME}-{VERSION}-macos.dmg"

    if dmg_path.exists():

        dmg_path.unlink()

    run(
        [
            "hdiutil",
            "create",
            "-volname",
            APP_NAME,
            "-srcfolder",
            str(app_bundle),
            "-ov",
            "-format",
            "UDZO",
            str(dmg_path),
        ]
    )

    print(f"Packaged: {dmg_path}")


def main() -> None:

    parser = argparse.ArgumentParser(
        description="Build H4Launcher for the current OS.",
    )

    parser.add_argument(
        "--skip-clean",
        action="store_true",
        help="Don't clear dist/ and build/ before building.",
    )

    parser.add_argument(
        "--no-package",
        action="store_true",
        help=(
            "Only run PyInstaller - skip creating the "
            "zip/tar.gz/dmg archive."
        ),
    )

    args = parser.parse_args()

    system = platform.system()

    print(
        f"Building {APP_NAME} {VERSION} on "
        f"{system} ({platform.machine()})"
    )

    ensure_pyinstaller()

    if not args.skip_clean:

        clean()

    run_pyinstaller()

    if args.no_package:

        print("\n--no-package set, skipping archive step.")

        return

    if system == "Windows":

        package_windows()

    elif system == "Darwin":

        package_macos()

    elif system == "Linux":

        package_linux()

    else:

        print(
            f"Unrecognized platform '{system}' - build finished, "
            "but no archive was created for it."
        )

    print(f"\nDone. See {DIST_DIR}")


if __name__ == "__main__":

    main()
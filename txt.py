# core/launcher.py

from __future__ import annotations

import os
import subprocess
import threading
import traceback
from pathlib import Path
from typing import Callable, Optional

import minecraft_launcher_lib


LogCallback = Callable[[str, str], None]
FinishedCallback = Callable[[bool, Optional[str]], None]


class MinecraftLauncher:
    """
    Minecraft launch backend.

    IMPORTANT:
    This class must never directly touch Tkinter or CustomTkinter.
    It is safe to execute from a worker thread.
    """

    def __init__(
        self,
        game_directory: str | Path,
        log_callback: Optional[LogCallback] = None,
    ):
        self.game_directory = Path(game_directory).resolve()
        self.log_callback = log_callback

        self.game_directory.mkdir(parents=True, exist_ok=True)

    # ------------------------------------------------------------------
    # Logging
    # ------------------------------------------------------------------

    def log(self, message: str, level: str = "INFO") -> None:
        """
        Send a log message to the UI.

        This callback must NOT manipulate Tk directly.
        The UI is responsible for scheduling it on the Tk main thread.
        """

        if self.log_callback:
            try:
                self.log_callback(level, message)
            except Exception:
                # Logging must never break the launcher.
                pass

    # ------------------------------------------------------------------
    # Version installation
    # ------------------------------------------------------------------

    def ensure_version(self, version: str) -> None:
        self.log(f"Checking Minecraft {version} installation...")

        minecraft_launcher_lib.install.install_minecraft_version(
            version,
            str(self.game_directory),
        )

        self.log(f"Minecraft {version} is ready.")

    # ------------------------------------------------------------------
    # Forge
    # ------------------------------------------------------------------

    

    # ------------------------------------------------------------------
    # Launch command
    # ------------------------------------------------------------------

    
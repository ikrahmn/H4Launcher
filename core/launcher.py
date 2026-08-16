# project_root/core/launcher.py

from __future__ import annotations

import os
import shlex
import subprocess
import threading
from pathlib import Path
from typing import Callable, Optional

import minecraft_launcher_lib

from utils.config_manager import (
    MINECRAFT_DIRECTORY,
    get_setting,
)


# ============================================================
# Supported versions
# ============================================================

SUPPORTED_VERSIONS = [
    "1.8.9",
    "1.12.2",
    "1.16.5",
]


LOADER_VANILLA = "Vanilla"
LOADER_FORGE = "Forge"


# ============================================================
# Launcher
# ============================================================

class MinecraftLauncher:

    def __init__(self):

        self.minecraft_directory = (
            MINECRAFT_DIRECTORY
        )

        self.minecraft_directory.mkdir(
            parents=True,
            exist_ok=True,
        )

        self._process: Optional[
            subprocess.Popen
        ] = None

    # ========================================================
    # Paths
    # ========================================================

    def get_game_directory(self) -> Path:

        self.minecraft_directory.mkdir(
            parents=True,
            exist_ok=True,
        )

        return self.minecraft_directory

    def get_mods_directory(self) -> Path:

        directory = (
            self.minecraft_directory / "mods"
        )

        directory.mkdir(
            parents=True,
            exist_ok=True,
        )

        return directory

    # ========================================================
    # Installation
    # ========================================================

    def is_version_installed(
        self,
        version: str,
    ) -> bool:

        version_directory = (
            self.minecraft_directory
            / "versions"
            / version
        )

        return version_directory.exists()

    def install_version(
        self,
        version: str,
        callback: Optional[
            Callable[[str], None]
        ] = None,
        progress_callback: Optional[
            Callable[[float], None]
        ] = None,
    ) -> None:

        def on_status(status):

            if callback:
                callback(
                    f"[DOWNLOAD] {status}\n"
                )

        def on_progress(
            progress,
        ):

            if progress_callback:
                progress_callback(
                    float(progress) / 100.0
                )

        minecraft_launcher_lib.install.install_minecraft_version(
            version,
            str(self.minecraft_directory),
            callback={
                "setStatus": on_status,
                "setProgress": on_progress,
                "setMax": lambda value: None,
            },
        )

    # ========================================================
    # Forge
    # ========================================================

    def get_forge_version(
        self,
        minecraft_version: str,
    ) -> Optional[str]:

        try:

            forge_versions = (
                minecraft_launcher_lib.forge.list_forge_versions()
            )

        except Exception:

            return None

        for forge_version in forge_versions:

            if forge_version.startswith(
                minecraft_version + "-"
            ):

                return forge_version

        return None

    def install_forge(
        self,
        minecraft_version: str,
        callback: Optional[
            Callable[[str], None]
        ] = None,
    ) -> bool:

        forge_version = (
            self.get_forge_version(
                minecraft_version
            )
        )

        if not forge_version:

            if callback:
                callback(
                    "[ERROR] No Forge version found "
                    f"for Minecraft {minecraft_version}\n"
                )

            return False

        if callback:

            callback(
                "[FORGE] Installing "
                f"{forge_version}\n"
            )

        try:

            minecraft_launcher_lib.forge.install_forge_version(
                forge_version,
                str(self.minecraft_directory),
            )

            if callback:

                callback(
                    "[FORGE] Installation complete.\n"
                )

            return True

        except Exception as exc:

            if callback:

                callback(
                    "[ERROR] Forge installation failed: "
                    f"{exc}\n"
                )

            return False

    # ========================================================
    # Launch command
    # ========================================================

    def build_launch_command(
        self,
        version: str,
        username: str,
        uuid: str,
        access_token: str,
        offline: bool = False,
    ) -> list[str]:

        min_ram = int(
            get_setting(
                "min_ram",
                1024,
            )
        )

        max_ram = int(
            get_setting(
                "max_ram",
                4096,
            )
        )

        java_path = get_setting(
            "java_path",
            "",
        )

        java_arguments = get_setting(
            "java_arguments",
            "",
        )

        if not java_path:

            java_path = (
                minecraft_launcher_lib.utils.get_java_executable()
            )

        options = {
            "username": username,
            "uuid": uuid,
            "token": access_token,
            "jvmArguments": [
                f"-Xms{min_ram}M",
                f"-Xmx{max_ram}M",
            ],
        }

        # Custom JVM arguments
        if java_arguments.strip():

            options["jvmArguments"].extend(
                shlex.split(
                    java_arguments
                )
            )

        # Offline mode
        if offline:

            options["token"] = ""
            options["uuid"] = uuid

        command = (
            minecraft_launcher_lib.command.get_minecraft_command(
                version,
                str(self.minecraft_directory),
                options,
            )
        )

        # Custom Java executable
        if java_path:

            command[0] = java_path

        return command

    # ========================================================
    # Launch
    # ========================================================

    def launch(
        self,
        version: str,
        username: str,
        uuid: str,
        access_token: str = "",
        offline: bool = False,
        callback: Optional[
            Callable[[str], None]
        ] = None,
        finished_callback: Optional[
            Callable[[int], None]
        ] = None,
    ) -> None:

        def worker():

            try:

                if callback:

                    callback(
                        "[LAUNCH] Preparing Minecraft...\n"
                    )

                command = (
                    self.build_launch_command(
                        version=version,
                        username=username,
                        uuid=uuid,
                        access_token=access_token,
                        offline=offline,
                    )
                )

                if callback:

                    callback(
                        "[COMMAND]\n"
                        + " ".join(
                            shlex.quote(
                                str(part)
                            )
                            for part in command
                        )
                        + "\n\n"
                    )

                if callback:

                    callback(
                        "[LAUNCH] Starting Minecraft...\n"
                    )

                environment = os.environ.copy()

                self._process = (
                    subprocess.Popen(
                        command,

                        cwd=str(
                            self.minecraft_directory
                        ),

                        stdout=subprocess.PIPE,

                        stderr=subprocess.STDOUT,

                        text=True,

                        bufsize=1,
                    )
                )

                if self._process.stdout:

                    for line in self._process.stdout:

                        if callback:

                            callback(
                                line
                            )

                return_code = (
                    self._process.wait()
                )

                if callback:

                    callback(
                        "\n"
                        "[PROCESS] Minecraft exited "
                        f"with code {return_code}\n"
                    )

                if finished_callback:

                    finished_callback(
                        return_code
                    )

            except Exception as exc:

                if callback:

                    callback(
                        "[ERROR] Launch failed: "
                        f"{exc}\n"
                    )

                if finished_callback:

                    finished_callback(
                        -1
                    )

        threading.Thread(
            target=worker,
            daemon=True,
        ).start()

    def stop(self) -> None:

        if self._process:

            try:

                self._process.terminate()

            except Exception:

                pass
from __future__ import annotations

import os
import shlex
import subprocess
import threading
from pathlib import Path
from typing import Callable, Optional

import minecraft_launcher_lib

from core.forge_legacy import install_legacy_forge

from utils.config_manager import (
    MINECRAFT_DIRECTORY,
    get_setting,
)


SUPPORTED_VERSIONS = [
    "1.8.9",
    "1.12.2",
    "1.16.5",
]

LOADER_VANILLA = "Vanilla"
LOADER_FORGE = "Forge"


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

    # Directories

    def get_game_directory(
        self,
    ) -> Path:

        self.minecraft_directory.mkdir(
            parents=True,
            exist_ok=True,
        )

        return self.minecraft_directory

    def get_mods_directory(
        self,
    ) -> Path:

        directory = (
            self.minecraft_directory
            / "mods"
        )

        directory.mkdir(
            parents=True,
            exist_ok=True,
        )

        return directory

    # Vanilla installation

    def is_version_installed(
        self,
        version: str,
    ) -> bool:

        version_directory = (
            self.minecraft_directory
            / "versions"
            / version
        )

        version_json = (
            version_directory
            / f"{version}.json"
        )

        return (
            version_directory.exists()
            and version_json.exists()
        )

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
            str(
                self.minecraft_directory
            ),
            callback={
                "setStatus": on_status,
                "setProgress": on_progress,
                "setMax": lambda value: None,
            },
        )

    # Forge

    def find_forge_version(
        self,
        minecraft_version: str,
    ) -> Optional[str]:

        """
        Find the newest Forge version compatible with
        the selected Minecraft version.
        """

        try:

            return (
                minecraft_launcher_lib.forge.find_forge_version(
                    minecraft_version
                )
            )

        except Exception:

            # Compatibility fallback for older
            # minecraft-launcher-lib releases.
            try:

                versions = (
                    minecraft_launcher_lib.forge.list_forge_versions()
                )

                matches = [
                    version
                    for version in versions
                    if version.startswith(
                        minecraft_version + "-"
                    )
                ]

                if matches:

                    return matches[0]

            except Exception:

                pass

        return None

    def get_forge_version(
        self,
        minecraft_version: str,
    ) -> Optional[str]:

        return self.find_forge_version(
            minecraft_version
        )

    def is_forge_installed(
        self,
        minecraft_version: str,
    ) -> bool:

        forge_version = (
            self.find_forge_version(
                minecraft_version
            )
        )

        if not forge_version:

            return False

        try:

            installed_version = (
                minecraft_launcher_lib.forge.forge_to_installed_version(
                    forge_version
                )
            )

        except Exception:

            # Fallback used by older versions.
            installed_version = forge_version

        version_directory = (
            self.minecraft_directory
            / "versions"
            / installed_version
        )

        json_file = (
            version_directory
            / f"{installed_version}.json"
        )

        return (
            version_directory.exists()
            and json_file.exists()
        )

    def install_forge(
        self,
        minecraft_version: str,
        callback: Optional[
            Callable[[str], None]
        ] = None,
        progress_callback: Optional[
            Callable[[float], None]
        ] = None,
    ) -> str:

        """
        Automatically installs the newest compatible Forge.

        Returns the actual Minecraft launcher version ID
        created by Forge.
        """

        forge_version = (
            self.find_forge_version(
                minecraft_version
            )
        )

        if not forge_version:

            raise RuntimeError(
                "No Forge version was found for "
                f"Minecraft {minecraft_version}."
            )

        if callback:

            callback(
                "[FORGE] Selected Forge: "
                f"{forge_version}\n"
            )

        # Check whether minecraft-launcher-lib's built-in installer
        # supports this Forge version. It only supports Minecraft
        # 1.13+, because older Forge installers use a different,
        # simpler format that the library never implemented. For
        # those, we fall back to our own legacy installer below.

        try:

            supported = (
                minecraft_launcher_lib.forge.supports_automatic_install(
                    forge_version
                )
            )

        except AttributeError:

            supported = True

        if not supported:

            return self._install_forge_legacy(
                minecraft_version=minecraft_version,
                forge_version=forge_version,
                callback=callback,
                progress_callback=progress_callback,
            )

        # Java executable

        java_path = get_setting(
            "java_path",
            "",
        )

        if not java_path:

            try:

                java_path = (
                    minecraft_launcher_lib.utils.get_java_executable()
                )

            except Exception:

                java_path = None

        # Callbacks

        def on_status(status):

            if callback:

                callback(
                    f"[FORGE] {status}\n"
                )

        def on_progress(
            progress,
        ):

            if progress_callback:

                progress_callback(
                    float(progress) / 100.0
                )

        forge_callback = {
            "setStatus": on_status,
            "setProgress": on_progress,
            "setMax": lambda value: None,
        }

        if callback:

            callback(
                "[FORGE] Installing automatically...\n"
            )

        minecraft_launcher_lib.forge.install_forge_version(
            forge_version,
            str(
                self.minecraft_directory
            ),
            callback=forge_callback,
            java=java_path,
        )

        try:

            installed_version = (
                minecraft_launcher_lib.forge.forge_to_installed_version(
                    forge_version
                )
            )

        except Exception:

            installed_version = forge_version

        if callback:

            callback(
                "[FORGE] Installation complete.\n"
            )

            callback(
                "[FORGE] Launcher version: "
                f"{installed_version}\n"
            )

        return installed_version

    def _install_forge_legacy(
        self,
        minecraft_version: str,
        forge_version: str,
        callback: Optional[
            Callable[[str], None]
        ] = None,
        progress_callback: Optional[
            Callable[[float], None]
        ] = None,
    ) -> str:

        """
        Fully-automatic install path for Forge builds that
        minecraft-launcher-lib doesn't support (Minecraft < 1.13,
        e.g. 1.8.9 and 1.12.2). See core/forge_legacy.py.
        """

        if callback:

            callback(
                "[FORGE] This Forge build predates 1.13 and uses "
                "a legacy installer format - installing it "
                "directly...\n"
            )

        try:

            installed_version = install_legacy_forge(
                minecraft_version=minecraft_version,
                forge_version=forge_version,
                minecraft_directory=self.minecraft_directory,
                callback=callback,
                progress_callback=progress_callback,
            )

        except Exception as exc:

            raise RuntimeError(
                "Automatic legacy Forge installation failed: "
                f"{exc}"
            ) from exc

        if callback:

            callback(
                "[FORGE] Installation complete.\n"
            )

            callback(
                "[FORGE] Launcher version: "
                f"{installed_version}\n"
            )

        return installed_version

    def ensure_forge(
        self,
        minecraft_version: str,
        callback: Optional[
            Callable[[str], None]
        ] = None,
        progress_callback: Optional[
            Callable[[float], None]
        ] = None,
    ) -> str:

        """
        Ensures Forge is installed.

        If already installed:
            returns the existing version.

        Otherwise:
            downloads and installs it automatically.
        """

        forge_version = (
            self.find_forge_version(
                minecraft_version
            )
        )

        if not forge_version:

            raise RuntimeError(
                "Forge is unavailable for "
                f"Minecraft {minecraft_version}."
            )

        try:

            installed_version = (
                minecraft_launcher_lib.forge.forge_to_installed_version(
                    forge_version
                )
            )

        except Exception:

            installed_version = forge_version

        version_json = (
            self.minecraft_directory
            / "versions"
            / installed_version
            / f"{installed_version}.json"
        )

        if version_json.exists():

            if callback:

                callback(
                    "[FORGE] Already installed: "
                    f"{installed_version}\n"
                )

            return installed_version

        return self.install_forge(
            minecraft_version,
            callback=callback,
            progress_callback=progress_callback,
        )

    # Launch command

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

            "launcherName": "H4Launcher",
            "launcherVersion": "0.1.0",

            "jvmArguments": [
                f"-Xms{min_ram}M",
                f"-Xmx{max_ram}M",
            ],
        }

        # Custom JVM arguments

        if java_arguments.strip():

            options[
                "jvmArguments"
            ].extend(
                shlex.split(
                    java_arguments
                )
            )

        # Offline mode

        if offline:

            options["token"] = ""

        # Generate command

        command = (
            minecraft_launcher_lib.command.get_minecraft_command(
                version,
                str(
                    self.minecraft_directory
                ),
                options,
            )
        )

        if java_path:

            command[0] = java_path

        return command

    # Launch

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

                    for line in (
                        self._process.stdout
                    ):

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
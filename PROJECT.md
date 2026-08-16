# Project Structure
```
H4Launcher
├─assets
│   └─logo.svg
├─core
│   ├─auth.py
│   ├─launcher.py
│   └─profile.py
├─LICENSE
├─main.py
├─README.md
├─requirements.txt
├─txt.py
├─ui
│   ├─app.py
│   └─components.py
└─utils
│   └─config_manager.py
```

---

# Source Code

## File: `/Users/ikram/Desktop/Project Important/H4Launcher/core/auth.py`

```py
from __future__ import annotations

import hashlib
import threading
import webbrowser
import uuid

from http.server import (
    BaseHTTPRequestHandler,
    HTTPServer,
)

from typing import Optional
from urllib.parse import urlparse

import minecraft_launcher_lib
from minecraft_launcher_lib import microsoft_account

from utils.config_manager import (
    clear_auth_data,
    get_auth_data,
    get_setting,
    save_auth_data,
)


CLIENT_ID = "YOUR_AZURE_CLIENT_ID"

REDIRECT_HOST = "localhost"
REDIRECT_PORT = 8765
REDIRECT_PATH = "/callback"

REDIRECT_URI = (
    f"http://{REDIRECT_HOST}:{REDIRECT_PORT}"
    f"{REDIRECT_PATH}"
)


class AuthenticationError(Exception):
    pass


class _OAuthCallbackHandler(
    BaseHTTPRequestHandler
):

    received_url: Optional[str] = None

    def do_GET(self) -> None:

        parsed = urlparse(
            self.path
        )

        if parsed.path != REDIRECT_PATH:

            self.send_response(404)
            self.end_headers()

            return

        _OAuthCallbackHandler.received_url = (
            f"http://{REDIRECT_HOST}:{REDIRECT_PORT}"
            f"{self.path}"
        )

        html = """
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="utf-8">
            <title>H4Launcher</title>
        </head>

        <body style="
            background:#f4f8fc;
            color:#142033;
            font-family:Arial,sans-serif;
            text-align:center;
            padding-top:80px;
        ">

            <h2>Authentication complete</h2>

            <p>
                You can close this window and return to H4Launcher.
            </p>

        </body>
        </html>
        """

        body = html.encode(
            "utf-8"
        )

        self.send_response(200)

        self.send_header(
            "Content-Type",
            "text/html; charset=utf-8",
        )

        self.send_header(
            "Content-Length",
            str(len(body)),
        )

        self.end_headers()

        self.wfile.write(
            body
        )

    def log_message(
        self,
        format,
        *args,
    ):
        pass


class MicrosoftAuth:

    def __init__(self):

        self._lock = threading.Lock()

    @staticmethod
    def is_configured() -> bool:

        return (
            CLIENT_ID
            and CLIENT_ID
            != "YOUR_AZURE_CLIENT_ID"
        )

    def login(self) -> dict:

        if not self.is_configured():

            raise AuthenticationError(
                "Microsoft authentication is not configured."
            )

        (
            login_url,
            state,
            code_verifier,
        ) = (
            microsoft_account.get_secure_login_data(
                CLIENT_ID,
                REDIRECT_URI,
            )
        )

        _OAuthCallbackHandler.received_url = None

        server = HTTPServer(
            (
                REDIRECT_HOST,
                REDIRECT_PORT,
            ),
            _OAuthCallbackHandler,
        )

        try:

            webbrowser.open(
                login_url
            )

            while (
                _OAuthCallbackHandler.received_url
                is None
            ):

                server.handle_request()

            callback_url = (
                _OAuthCallbackHandler
                .received_url
            )

        finally:

            server.server_close()

        try:

            auth_code = (
                microsoft_account
                .parse_auth_code_url(
                    callback_url,
                    state,
                )
            )

        except Exception as exc:

            raise AuthenticationError(
                "Microsoft OAuth validation failed."
            ) from exc

        try:

            login_data = (
                microsoft_account.complete_login(
                    CLIENT_ID,
                    None,
                    REDIRECT_URI,
                    auth_code,
                    code_verifier,
                )
            )

        except Exception as exc:

            raise AuthenticationError(
                f"Microsoft authentication failed: {exc}"
            ) from exc

        self._store_login_data(
            login_data
        )

        return login_data

    def refresh(self) -> Optional[dict]:

        with self._lock:

            auth = get_auth_data()

            refresh_token = (
                auth.get(
                    "refresh_token"
                )
            )

            if not refresh_token:
                return None

            try:

                login_data = (
                    microsoft_account.complete_refresh(
                        CLIENT_ID,
                        None,
                        None,
                        refresh_token,
                    )
                )

            except Exception:

                clear_auth_data()

                return None

            self._store_login_data(
                login_data
            )

            return login_data

    def get_valid_login(
        self,
    ) -> Optional[dict]:

        if not self.is_configured():
            return None

        return self.refresh()

    @staticmethod
    def _store_login_data(
        login_data: dict,
    ) -> None:

        save_auth_data(
            {
                "username": login_data["name"],
                "uuid": login_data["id"],
                "access_token": login_data[
                    "access_token"
                ],
                "refresh_token": login_data[
                    "refresh_token"
                ],
            }
        )

    @staticmethod
    def logout() -> None:

        clear_auth_data()


def generate_offline_uuid(
    username: str,
) -> str:
    """
    Generate the UUID conventionally used by
    Minecraft's OfflinePlayer profile.

    This is useful for local/offline single-player
    profiles and testing.
    """

    username = username.strip()

    if not username:
        raise AuthenticationError(
            "Offline username cannot be empty."
        )

    raw = (
        "OfflinePlayer:"
        + username
    ).encode("utf-8")

    digest = hashlib.md5(
        raw
    ).digest()

    value = uuid.UUID(
        bytes=digest
    )

    value = uuid.UUID(
        int=(
            value.int
            & ~(
                0xF000
                << 64
            )
            | (
                3
                << 76
            )
        )
        & ~(
            0xC000
            << 48
        )
        | (
            0x8000
            << 48
        )
    )

    return str(value)


def get_offline_profile() -> dict:

    username = get_setting(
        "offline_username",
        "Player",
    )

    username = (
        str(username)
        .strip()
    )

    if not username:
        username = "Player"

    return {
        "name": username,
        "id": generate_offline_uuid(
            username
        ),

        # Offline mode intentionally does not have a real Microsoft authentication token.
        "access_token": "0",
        "refresh_token": "",
    }


auth_manager = MicrosoftAuth()
```

---

## File: `/Users/ikram/Desktop/Project Important/H4Launcher/core/launcher.py`

```py
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

        # Check whether automatic installation is supported.

        try:

            supported = (
                minecraft_launcher_lib.forge.supports_automatic_install(
                    forge_version
                )
            )

        except AttributeError:

            supported = True

        if not supported:

            raise RuntimeError(
                "This Forge version does not support "
                "automatic installation through "
                "minecraft-launcher-lib."
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
```

---

## File: `/Users/ikram/Desktop/Project Important/H4Launcher/core/profile.py`

```py
# project_root/core/profile.py

from __future__ import annotations

import hashlib
import threading
import urllib.request
import uuid
from io import BytesIO
from typing import Callable, Optional

from PIL import Image

try:
    import namemcpy
except ImportError:
    namemcpy = None


# Profile information

class PlayerProfile:

    def __init__(
        self,
        username: str,
        player_uuid: str,
        online: bool,
        avatar: Optional[Image.Image] = None,
    ):
        self.username = username
        self.uuid = player_uuid
        self.online = online
        self.avatar = avatar


# Profile service

class ProfileService:
    CRAFATAR_URL = (
        "https://crafatar.com/avatars/"
        "{uuid}?size=128&overlay"
    )

    def __init__(self):

        self._cache: dict[
            str,
            PlayerProfile
        ] = {}

    # UUID

    @staticmethod
    def offline_uuid(
        username: str,
    ) -> str:
        
        return str(
            uuid.uuid3(
                uuid.NAMESPACE_DNS,
                f"OfflinePlayer:{username}",
            )
        )

    def username_to_uuid(
        self,
        username: str,
    ) -> Optional[str]:

        if not username:
            return None

        if namemcpy is None:
            return None

        try:

            # Older namemcpy API.
            converter = getattr(
                namemcpy,
                "usernameToUuid",
                None,
            )

            if callable(converter):

                result = converter(
                    username
                )

                if result:

                    return self._normalize_uuid(
                        result
                    )

        except Exception:

            pass

        try:

            # Some versions expose a class/API object.
            api_class = getattr(
                namemcpy,
                "NameMC",
                None,
            )

            if api_class:

                api = api_class()

                converter = getattr(
                    api,
                    "usernameToUuid",
                    None,
                )

                if callable(converter):

                    result = converter(
                        username
                    )

                    if result:

                        return self._normalize_uuid(
                            result
                        )

        except Exception:

            pass

        return None

    # Profile

    def get_profile(
        self,
        username: str,
        online: bool,
    ) -> PlayerProfile:

        username = (
            username.strip()
            or "Player"
        )

        cache_key = (
            f"{online}:{username.lower()}"
        )

        if cache_key in self._cache:

            return self._cache[
                cache_key
            ]

        # Offline

        if not online:

            player_uuid = (
                self.offline_uuid(
                    username
                )
            )

            profile = PlayerProfile(
                username=username,
                player_uuid=player_uuid,
                online=False,
                avatar=None,
            )

            self._cache[
                cache_key
            ] = profile

            return profile

        # Online

        player_uuid = (
            self.username_to_uuid(
                username
            )
        )

        if not player_uuid:

            # Fall back to deterministic UUID.
            player_uuid = (
                self.offline_uuid(
                    username
                )
            )

            profile = PlayerProfile(
                username=username,
                player_uuid=player_uuid,
                online=False,
                avatar=None,
            )

            self._cache[
                cache_key
            ] = profile

            return profile

        avatar = self._download_avatar(
            player_uuid
        )

        profile = PlayerProfile(
            username=username,
            player_uuid=player_uuid,
            online=True,
            avatar=avatar,
        )

        self._cache[
            cache_key
        ] = profile

        return profile

    # Async profile loading

    def get_profile_async(
        self,
        username: str,
        online: bool,
        callback: Callable[
            [PlayerProfile],
            None,
        ],
        error_callback: Optional[
            Callable[[Exception], None]
        ] = None,
    ) -> None:

        def worker():

            try:

                profile = self.get_profile(
                    username,
                    online,
                )

                callback(
                    profile
                )

            except Exception as exc:

                if error_callback:

                    error_callback(
                        exc
                    )

        threading.Thread(
            target=worker,
            daemon=True,
        ).start()

    # Avatar

    def _download_avatar(
        self,
        player_uuid: str,
    ) -> Optional[Image.Image]:

        try:

            url = self.CRAFATAR_URL.format(
                uuid=player_uuid
            )

            request = urllib.request.Request(
                url,

                headers={
                    "User-Agent":
                        "H4Launcher/1.0"
                },
            )

            with urllib.request.urlopen(
                request,
                timeout=8,
            ) as response:

                data = response.read()

            image = Image.open(
                BytesIO(data)
            )

            image.load()

            return image.convert(
                "RGBA"
            )

        except Exception:

            return None

    # Helpers

    @staticmethod
    def _normalize_uuid(
        value,
    ) -> Optional[str]:

        if value is None:
            return None

        value = str(
            value
        ).strip()

        value = value.replace(
            "-",
            "",
        )

        if len(value) != 32:
            return None

        try:

            parsed = uuid.UUID(
                value
            )

            return str(
                parsed
            )

        except ValueError:

            return None
```

---

## File: `/Users/ikram/Desktop/Project Important/H4Launcher/main.py`

```py
from ui.app import LauncherApp

def main():

    app = LauncherApp()

    app.mainloop()


if __name__ == "__main__":
    main()
```

---

## File: `/Users/ikram/Desktop/Project Important/H4Launcher/README.md`

```md
# H4Launcher

A lightweight custom Minecraft Java Edition launcher written in Python.

H4Launcher is designed to provide a simple desktop launcher for Minecraft Java
Edition with support for vanilla installations, Forge, offline profiles,
custom Java configurations, and a verbose launch console.

## Features

- Minecraft Java Edition launcher
- Vanilla support
- Forge support
- Offline profiles
- Microsoft account authentication
- Minecraft versions:
  - 1.8.9
  - 1.12.2
  - 1.16.5
- Automatic Minecraft directory management
- Custom Java executable
- Custom JVM arguments
- Configurable RAM allocation
- Forge mods folder access
- Multiple UI color themes
- Verbose Minecraft launch console
- Background downloading and launching
- Cross-platform design for:
  - Windows
  - Linux
  - macOS

## Requirements

- Python 3.10.6
- Java
- Internet connection for downloading Minecraft/Forge files

## Installation

Clone the repository:

```bash
git clone https://github.com/YOUR_USERNAME/H4Launcher.git
cd H4Launcher
````

Create a virtual environment:

```bash
python3 -m venv .venv
```

Activate it.

### Linux / macOS

```bash
source .venv/bin/activate
```

### Windows

```powershell
.venv\Scripts\activate
```

Install the dependencies:

```bash
pip install -r requirements.txt
```

Run H4Launcher:

```bash
python main.py
```

## Minecraft Directory

H4Launcher currently stores Minecraft data inside the project directory:

```text
H4Launcher/
└── .minecraft/
```

The directory is created automatically when the launcher starts.

The launcher stores:

* Minecraft versions
* Libraries
* Assets
* Mods
* Logs
* Other Minecraft runtime files

The `.minecraft` directory is ignored by Git and will not be uploaded to
GitHub.

## Configuration

Launcher settings are stored locally in:

```text
.h4launcher/config.json
```

Settings include:

* RAM allocation
* Java executable
* JVM arguments
* Offline username
* Selected Minecraft version
* Selected loader
* UI theme

Local configuration files are ignored by Git.

## Forge

When Forge is selected, H4Launcher provides access to the local mods folder.

```text
.minecraft/
└── mods/
```

Place compatible `.jar` mods inside the directory.

Always make sure a mod matches the Minecraft and Forge version you are using.

## Offline Mode

H4Launcher supports local offline profiles.

Offline mode does not authenticate with Microsoft and should only be used with
Minecraft installations you are legally entitled to use.

## Development

The project is intentionally separated into several modules:

```text
core/
    Authentication and launcher logic

ui/
    CustomTkinter interface

utils/
    Configuration and local data management
```

The application is designed to keep UI code separate from Minecraft launcher
logic.

## Roadmap

Planned improvements include:

* Per-instance Minecraft installations
* Better Forge version management
* Installed mod management
* Mod enable/disable controls
* Minecraft profile management
* Java version detection
* Download progress improvements
* Launcher update system
* Crash log viewer
* Better Microsoft authentication handling
* More Minecraft versions
* Launcher packaging for Windows, Linux, and macOS

## Disclaimer

H4Launcher is an independent third-party project and is not affiliated with,
endorsed by, or sponsored by Mojang Studios or Microsoft.

Minecraft is a property of Mojang Studios.

Users are responsible for complying with the applicable Minecraft and Microsoft
terms and licenses.

## License

H4Launcher is released under the MIT License.

See [LICENSE](LICENSE) for details.

```

---

## File: `/Users/ikram/Desktop/Project Important/H4Launcher/requirements.txt`

```txt
customtkinter>=5.2.0
minecraft-launcher-lib>=8.0
namemcpy==1.5.1
Pillow>=9.0
requests>=2.28
```

---

## File: `/Users/ikram/Desktop/Project Important/H4Launcher/txt.py`

```py
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

    
```

---

## File: `/Users/ikram/Desktop/Project Important/H4Launcher/ui/app.py`

```py
# project_root/ui/app.py

from __future__ import annotations

import base64
import os
import subprocess
import sys
import tkinter as tk
from pathlib import Path
from tkinter import filedialog, messagebox

import customtkinter as ctk

from core.launcher import (
    MinecraftLauncher,
    SUPPORTED_VERSIONS,
    LOADER_VANILLA,
    LOADER_FORGE,
)

from core.profile import (
    ProfileService,
)

from utils.config_manager import (
    get_setting,
    set_setting,
    get_auth_data,
)

from ui.components import (
    THEMES,
    get_theme,
    FONT,
    PrimaryButton,
    SecondaryButton,
    SectionLabel,
    FlatProgressBar,
    Console,
    ProfileCard,
)


# H4Launcher
class LauncherApp(
    ctk.CTk
):

    def __init__(self):

        super().__init__()

        self.title(
            "H4Launcher"
        )

        self.geometry(
            "1080x760"
        )

        self.minsize(
            900,
            680,
        )

        self.theme_name = get_setting(
            "theme",
            "Blue",
        )

        self.theme = get_theme(
            self.theme_name
        )

        self.launcher = (
            MinecraftLauncher()
        )

        self.profile_service = (
            ProfileService()
        )

        self.is_launching = False

        self._logo_image = None

        self._configure_window_icon()

        self._build_ui()

        self._load_saved_values()

        self._load_profile()

    # Window icon

    def _configure_window_icon(
        self,
    ):

        """
        Tkinter does not natively load SVG files as window
        icons. Therefore we embed a small PNG representation
        generated from the same H4Launcher logo concept.

        The SVG remains in assets/logo.svg as the editable
        source artwork.
        """

        # Tiny 1x1 transparent fallback.
        # The actual logo can be replaced with a generated
        # PNG asset later without changing the UI.
        fallback_png = (
            "iVBORw0KGgoAAAANSUhEUgAAAAEAAAAB"
            "CAQAAAC1HAwCAAAAC0lEQVR42mNk"
            "+A8AAQUBAScY42YAAAAASUVORK5CYII="
        )

        try:

            self._logo_image = tk.PhotoImage(
                data=fallback_png
            )

            self.iconphoto(
                True,
                self._logo_image,
            )

        except Exception:

            pass

    # UI

    def _build_ui(
        self,
    ):

        self.configure(
            fg_color=self.theme["bg"]
        )

        self.grid_columnconfigure(
            1,
            weight=1,
        )

        self.grid_rowconfigure(
            0,
            weight=1,
        )

        # Sidebar

        sidebar = ctk.CTkFrame(
            self,

            width=220,

            fg_color=self.theme["surface"],

            corner_radius=0,

            border_width=1,

            border_color=self.theme["border"],
        )

        sidebar.grid(
            row=0,
            column=0,

            sticky="nsew",
        )

        sidebar.grid_propagate(
            False
        )

        # Logo

        logo_row = ctk.CTkFrame(
            sidebar,

            fg_color="transparent",
        )

        logo_row.pack(
            fill="x",

            padx=20,

            pady=(24, 4),
        )

        logo_mark = ctk.CTkLabel(
            logo_row,

            text="H4",

            width=42,

            height=42,

            fg_color="#17304D",

            corner_radius=8,

            text_color="#FFFFFF",

            font=ctk.CTkFont(
                family=FONT,
                size=15,
                weight="bold",
            ),
        )

        logo_mark.pack(
            side="left"
        )

        logo_text = ctk.CTkLabel(
            logo_row,

            text="H4Launcher",

            font=ctk.CTkFont(
                family=FONT,
                size=18,
                weight="bold",
            ),

            text_color=self.theme["text"],

            anchor="w",
        )

        logo_text.pack(
            side="left",

            padx=10,
        )

        subtitle = ctk.CTkLabel(
            sidebar,

            text="Minecraft Java Edition",

            font=ctk.CTkFont(
                family=FONT,
                size=11,
            ),

            text_color=self.theme["text_muted"],

            anchor="w",
        )

        subtitle.pack(
            fill="x",

            padx=24,

            pady=(0, 25),
        )

        separator = ctk.CTkFrame(
            sidebar,

            height=1,

            fg_color=self.theme["border"],
        )

        separator.pack(
            fill="x",

            padx=20,

            pady=(0, 20),
        )

        # Version

        SectionLabel(
            sidebar,

            "VERSION",

            theme=self.theme,

        ).pack(
            fill="x",

            padx=24,

            pady=(0, 6),
        )

        self.version_var = tk.StringVar(
            value="1.16.5"
        )

        self.version_menu = ctk.CTkOptionMenu(
            sidebar,

            variable=self.version_var,

            values=SUPPORTED_VERSIONS,

            height=38,

            corner_radius=4,

            fg_color=self.theme["surface_alt"],

            button_color=self.theme["border"],

            button_hover_color=self.theme["border"],

            dropdown_fg_color=self.theme["surface"],

            dropdown_hover_color=self.theme["surface_alt"],

            text_color=self.theme["text"],

            command=self._version_changed,
        )

        self.version_menu.pack(
            fill="x",

            padx=24,

            pady=(0, 18),
        )

        # Loader

        SectionLabel(
            sidebar,

            "LOADER",

            theme=self.theme,

        ).pack(
            fill="x",

            padx=24,

            pady=(0, 6),
        )

        self.loader_var = tk.StringVar(
            value=LOADER_VANILLA
        )

        self.loader_menu = ctk.CTkOptionMenu(
            sidebar,

            variable=self.loader_var,

            values=[
                LOADER_VANILLA,
                LOADER_FORGE,
            ],

            height=38,

            corner_radius=4,

            fg_color=self.theme["surface_alt"],

            button_color=self.theme["border"],

            button_hover_color=self.theme["border"],

            dropdown_fg_color=self.theme["surface"],

            dropdown_hover_color=self.theme["surface_alt"],

            text_color=self.theme["text"],

            command=self._loader_changed,
        )

        self.loader_menu.pack(
            fill="x",

            padx=24,

            pady=(0, 18),
        )

        self.mods_button = SecondaryButton(
            sidebar,

            text="Open Mods Folder",

            theme=self.theme,

            height=34,

            command=self._open_mods_folder,
        )

        # Sidebar bottom

        sidebar_bottom = ctk.CTkFrame(
            sidebar,

            fg_color="transparent",
        )

        sidebar_bottom.pack(
            side="bottom",

            fill="x",

            padx=24,

            pady=24,
        )

        SecondaryButton(
            sidebar_bottom,

            text="Settings",

            theme=self.theme,

            command=self._open_settings,
        ).pack(
            fill="x"
        )

        # Main

        main = ctk.CTkFrame(
            self,

            fg_color=self.theme["bg"],

            corner_radius=0,
        )

        main.grid(
            row=0,
            column=1,

            sticky="nsew",
        )

        main.grid_columnconfigure(
            0,
            weight=1,
        )

        main.grid_rowconfigure(
            4,
            weight=1,
        )

        # Header

        header = ctk.CTkFrame(
            main,

            fg_color="transparent",
        )

        header.grid(
            row=0,
            column=0,

            sticky="ew",

            padx=34,

            pady=(26, 15),
        )

        title = ctk.CTkLabel(
            header,

            text="Play Minecraft",

            font=ctk.CTkFont(
                family=FONT,
                size=28,
                weight="bold",
            ),

            text_color=self.theme["text"],

            anchor="w",
        )

        title.pack(
            anchor="w"
        )

        self.account_label = ctk.CTkLabel(
            header,

            text="Offline profile",

            font=ctk.CTkFont(
                family=FONT,
                size=12,
            ),

            text_color=self.theme["text_muted"],

            anchor="w",
        )

        self.account_label.pack(
            anchor="w",

            pady=(3, 0),
        )

        # Profile

        self.profile_card = ProfileCard(
            main,

            theme=self.theme,
        )

        self.profile_card.grid(
            row=1,
            column=0,

            sticky="ew",

            padx=34,

            pady=(0, 18),
        )

        # Play panel

        play_panel = ctk.CTkFrame(
            main,

            fg_color=self.theme["surface"],

            corner_radius=5,

            border_width=1,

            border_color=self.theme["border"],
        )

        play_panel.grid(
            row=2,
            column=0,

            sticky="ew",

            padx=34,

            pady=(0, 18),
        )

        play_panel.grid_columnconfigure(
            0,
            weight=1,
        )

        SectionLabel(
            play_panel,

            "SELECTED INSTALLATION",

            theme=self.theme,
        ).grid(
            row=0,
            column=0,

            sticky="w",

            padx=22,

            pady=(17, 3),
        )

        self.selected_installation_label = ctk.CTkLabel(
            play_panel,

            text="Minecraft 1.16.5 | Vanilla",

            font=ctk.CTkFont(
                family=FONT,
                size=18,
                weight="bold",
            ),

            text_color=self.theme["text"],

            anchor="w",
        )

        self.selected_installation_label.grid(
            row=1,
            column=0,

            sticky="w",

            padx=22,

            pady=(0, 17),
        )

        self.play_button = PrimaryButton(
            play_panel,

            text="PLAY",

            theme=self.theme,

            width=180,

            height=48,

            command=self._play,
        )

        self.play_button.grid(
            row=0,
            column=1,

            rowspan=2,

            padx=22,

            pady=17,
        )

        # Console header

        console_header = ctk.CTkFrame(
            main,

            fg_color="transparent",
        )

        console_header.grid(
            row=3,
            column=0,

            sticky="ew",

            padx=34,

            pady=(0, 5),
        )

        console_header.grid_columnconfigure(
            0,
            weight=1,
        )

        SectionLabel(
            console_header,

            "LAUNCH CONSOLE",

            theme=self.theme,
        ).grid(
            row=0,
            column=0,

            sticky="w",
        )

        SecondaryButton(
            console_header,

            text="Clear",

            theme=self.theme,

            width=65,

            height=30,

            command=self._clear_console,
        ).grid(
            row=0,
            column=1,
        )

        # Console

        self.console = Console(
            main,

            theme=self.theme,
        )

        self.console.grid(
            row=4,
            column=0,

            sticky="nsew",

            padx=34,

            pady=(0, 15),
        )

        # Status

        self.status_label = ctk.CTkLabel(
            main,

            text="Ready",

            font=ctk.CTkFont(
                family=FONT,
                size=11,
            ),

            text_color=self.theme["text_muted"],

            anchor="w",
        )

        self.status_label.grid(
            row=5,
            column=0,

            sticky="ew",

            padx=34,

            pady=(0, 7),
        )

        self.progress = FlatProgressBar(
            main,

            theme=self.theme,
        )

        self.progress.grid(
            row=6,
            column=0,

            sticky="ew",

            padx=34,

            pady=(0, 22),
        )

        self.progress.set(0)

        self._loader_changed(
            self.loader_var.get()
        )

    # Saved settings

    def _load_saved_values(
        self,
    ):

        version = get_setting(
            "selected_version",
            "1.16.5",
        )

        loader = get_setting(
            "selected_loader",
            LOADER_VANILLA,
        )

        if version in SUPPORTED_VERSIONS:

            self.version_var.set(
                version
            )

        if loader in (
            LOADER_VANILLA,
            LOADER_FORGE,
        ):

            self.loader_var.set(
                loader
            )

        self._update_installation_label()

    # Profile

    def _load_profile(
        self,
    ):

        auth = get_auth_data()

        username = (
            auth.get(
                "username",
                "",
            )
            or get_setting(
                "offline_username",
                "Player",
            )
            or "Player"
        )

        access_token = auth.get(
            "access_token",
            "",
        )

        online = bool(
            access_token
        )

        if online:

            self.account_label.configure(
                text=(
                    f"Microsoft account: "
                    f"{username}"
                )
            )

        else:

            self.account_label.configure(
                text=(
                    f"Offline profile: "
                    f"{username}"
                )
            )

        # Show loading state

        self.profile_card.name_label.configure(
            text=username
        )

        self.profile_card.status_label.configure(
            text=(
                "Loading profile..."
                if online
                else "Offline profile"
            )
        )

        self.profile_service.get_profile_async(

            username=username,

            online=online,

            callback=self._profile_loaded,

            error_callback=self._profile_error,
        )

    def _profile_loaded(
        self,
        profile,
    ):

        self.after(
            0,
            lambda: self.profile_card.set_profile(
                profile
            ),
        )

    def _profile_error(
        self,
        error,
    ):

        self.after(
            0,
            lambda: self.profile_card.status_label.configure(
                text="Profile unavailable"
            ),
        )

        self._write_console(
            "[PROFILE] Could not load profile: "
            f"{error}\n"
        )

    # Version / loader

    def _version_changed(
        self,
        version,
    ):

        set_setting(
            "selected_version",
            version,
        )

        self._update_installation_label()

    def _loader_changed(
        self,
        loader,
    ):

        set_setting(
            "selected_loader",
            loader,
        )

        self._update_installation_label()

        if loader == LOADER_FORGE:

            self.mods_button.pack(
                fill="x",

                padx=24,

                pady=(0, 18),

                after=self.loader_menu,
            )

        else:

            self.mods_button.pack_forget()

    def _update_installation_label(
        self,
    ):

        version = (
            self.version_var.get()
        )

        loader = (
            self.loader_var.get()
        )

        self.selected_installation_label.configure(
            text=(
                f"Minecraft {version}"
                f"  |  "
                f"{loader}"
            )
        )

    # Mods

    def _open_mods_folder(
        self,
    ):

        mods_directory = (
            self.launcher.get_mods_directory()
        )

        self._open_path(
            mods_directory
        )

    def _open_path(
        self,
        path: Path,
    ):

        path = Path(
            path
        )

        path.mkdir(
            parents=True,
            exist_ok=True,
        )

        try:

            if sys.platform.startswith(
                "win"
            ):

                os.startfile(
                    str(path)
                )

            elif sys.platform == "darwin":

                subprocess.Popen(
                    [
                        "open",
                        str(path),
                    ]
                )

            else:

                subprocess.Popen(
                    [
                        "xdg-open",
                        str(path),
                    ]
                )

        except Exception as exc:

            messagebox.showerror(
                "H4Launcher",
                f"Could not open folder:\n\n{exc}",
            )

    # Console

    def _write_console(
        self,
        text: str,
    ):

        self.after(
            0,
            lambda: self.console.write(
                text
            ),
        )

    def _clear_console(
        self,
    ):

        self.console.clear()

    def _set_status(
        self,
        text: str,
    ):

        self.after(
            0,
            lambda: self.status_label.configure(
                text=text
            ),
        )

    def _set_progress(
        self,
        value: float,
    ):

        value = max(
            0.0,
            min(
                1.0,
                value,
            ),
        )

        self.after(
            0,
            lambda: self.progress.set(
                value
            ),
        )

    # Play

    def _play(
        self,
    ):

        if self.is_launching:

            return

        self.is_launching = True

        self.play_button.configure(
            state="disabled",

            text="LAUNCHING...",
        )

        self._set_status(
            "Preparing Minecraft..."
        )

        self._set_progress(
            0
        )

        self._write_console(
            "\n"
            "==================================================\n"
            "H4Launcher\n"
            "==================================================\n"
        )

        version = (
            self.version_var.get()
        )

        loader = (
            self.loader_var.get()
        )

        self._write_console(
            f"[CONFIG] Minecraft: {version}\n"
        )

        self._write_console(
            f"[CONFIG] Loader: {loader}\n"
        )

        # Authentication / offline profile

        auth = get_auth_data()

        username = (
            auth.get(
                "username",
                "",
            )
            or get_setting(
                "offline_username",
                "Player",
            )
            or "Player"
        )

        access_token = auth.get(
            "access_token",
            "",
        )

        player_uuid = auth.get(
            "uuid",
            "",
        )

        offline = not bool(
            access_token
        )

        if not player_uuid:

            player_uuid = (
                self.profile_service.offline_uuid(
                    username
                )
            )

        if offline:

            self._write_console(
                "[AUTH] Offline profile\n"
            )

        else:

            self._write_console(
                "[AUTH] Microsoft account: "
                f"{username}\n"
            )

        # Background installation / launch

        def worker():

            try:

                # Vanilla

                if not self.launcher.is_version_installed(
                    version
                ):

                    self._write_console(
                        "[DOWNLOAD] Minecraft "
                        f"{version} is not installed.\n"
                    )

                    self._set_status(
                        f"Downloading Minecraft {version}..."
                    )

                    self.launcher.install_version(

                        version,

                        callback=self._write_console,

                        progress_callback=self._set_progress,
                    )

                # Forge

                if loader == LOADER_FORGE:

                    self._set_status(
                        "Checking Forge..."
                    )

                    self._write_console(
                        "[FORGE] Checking installation...\n"
                    )

                    forge_version = (
                        self.launcher.find_forge_version(
                            version
                        )
                    )

                    if not forge_version:

                        raise RuntimeError(
                            "No compatible Forge version "
                            f"was found for Minecraft {version}."
                        )

                    self._write_console(
                        "[FORGE] Compatible version: "
                        f"{forge_version}\n"
                    )

                    forge_installed_version = (
                        self.launcher.ensure_forge(

                            version,

                            callback=self._write_console,

                            progress_callback=self._set_progress,
                        )
                    )

                    launch_version = (
                        forge_installed_version
                    )

                else:

                    launch_version = version

                # Launch

                self._set_progress(
                    1.0
                )

                self._set_status(
                    "Launching Minecraft..."
                )

                self._write_console(
                    "[LAUNCH] Version: "
                    f"{launch_version}\n"
                )

                self.launcher.launch(

                    version=launch_version,

                    username=username,

                    uuid=player_uuid,

                    access_token=access_token,

                    offline=offline,

                    callback=self._write_console,

                    finished_callback=self._launch_finished,
                )

            except Exception as exc:

                self._write_console(
                    "[ERROR] "
                    f"{exc}\n"
                )

                self.after(
                    0,
                    lambda: messagebox.showerror(
                        "H4Launcher",
                        str(exc),
                    ),
                )

                self._launch_finished(
                    -1
                )

        import threading

        threading.Thread(
            target=worker,
            daemon=True,
        ).start()

    def _launch_finished(
        self,
        return_code: int,
    ):

        def update():

            self.is_launching = False

            self.play_button.configure(
                state="normal",

                text="PLAY",
            )

            if return_code == 0:

                self.status_label.configure(
                    text="Minecraft closed normally."
                )

            elif return_code == -1:

                self.status_label.configure(
                    text="Launch failed."
                )

            else:

                self.status_label.configure(
                    text=(
                        "Minecraft exited "
                        f"with code {return_code}."
                    )
                )

        self.after(
            0,
            update,
        )

    # Settings

    def _open_settings(
        self,
    ):

        window = ctk.CTkToplevel(
            self
        )

        window.title(
            "H4Launcher Settings"
        )

        window.geometry(
            "560x650"
        )

        window.minsize(
            500,
            600,
        )

        window.configure(
            fg_color=self.theme["bg"]
        )

        window.transient(
            self
        )

        container = ctk.CTkScrollableFrame(
            window,

            fg_color=self.theme["bg"],
        )

        container.pack(
            fill="both",

            expand=True,

            padx=24,

            pady=24,
        )

        # Theme

        SectionLabel(
            container,

            "COLOR THEME",

            theme=self.theme,
        ).pack(
            fill="x"
        )

        theme_var = tk.StringVar(
            value=self.theme_name
        )

        ctk.CTkOptionMenu(
            container,

            variable=theme_var,

            values=list(
                THEMES.keys()
            ),

            height=40,

            corner_radius=4,

            fg_color=self.theme["surface_alt"],

            button_color=self.theme["border"],

            button_hover_color=self.theme["border"],

            dropdown_fg_color=self.theme["surface"],

            dropdown_hover_color=self.theme["surface_alt"],

            text_color=self.theme["text"],
        ).pack(
            fill="x",

            pady=(6, 20)
        )

        # RAM

        SectionLabel(
            container,

            "MINIMUM RAM (MB)",

            theme=self.theme,
        ).pack(
            fill="x"
        )

        min_ram_var = tk.StringVar(
            value=str(
                get_setting(
                    "min_ram",
                    1024,
                )
            )
        )

        ctk.CTkEntry(
            container,

            textvariable=min_ram_var,

            height=40,

            corner_radius=4,

            fg_color=self.theme["surface"],

            border_color=self.theme["border"],

            text_color=self.theme["text"],
        ).pack(
            fill="x",

            pady=(6, 16)
        )

        SectionLabel(
            container,

            "MAXIMUM RAM (MB)",

            theme=self.theme,
        ).pack(
            fill="x"
        )

        max_ram_var = tk.StringVar(
            value=str(
                get_setting(
                    "max_ram",
                    4096,
                )
            )
        )

        ctk.CTkEntry(
            container,

            textvariable=max_ram_var,

            height=40,

            corner_radius=4,

            fg_color=self.theme["surface"],

            border_color=self.theme["border"],

            text_color=self.theme["text"],
        ).pack(
            fill="x",

            pady=(6, 16)
        )

        # Java

        SectionLabel(
            container,

            "JAVA EXECUTABLE",

            theme=self.theme,
        ).pack(
            fill="x"
        )

        java_var = tk.StringVar(
            value=get_setting(
                "java_path",
                "",
            )
        )

        java_row = ctk.CTkFrame(
            container,

            fg_color="transparent",
        )

        java_row.pack(
            fill="x",

            pady=(6, 16)
        )

        java_row.grid_columnconfigure(
            0,
            weight=1,
        )

        ctk.CTkEntry(
            java_row,

            textvariable=java_var,

            height=40,

            corner_radius=4,

            fg_color=self.theme["surface"],

            border_color=self.theme["border"],

            text_color=self.theme["text"],
        ).grid(
            row=0,
            column=0,

            sticky="ew",

            padx=(0, 8),
        )

        def browse_java():

            selected = (
                filedialog.askopenfilename(
                    title="Select Java executable"
                )
            )

            if selected:

                java_var.set(
                    selected
                )

        SecondaryButton(
            java_row,

            text="Browse",

            theme=self.theme,

            width=90,

            height=40,

            command=browse_java,
        ).grid(
            row=0,
            column=1,
        )

        # JVM args

        SectionLabel(
            container,

            "JAVA / JVM ARGUMENTS",

            theme=self.theme,
        ).pack(
            fill="x"
        )

        java_args_var = tk.StringVar(
            value=get_setting(
                "java_arguments",
                "",
            )
        )

        ctk.CTkEntry(
            container,

            textvariable=java_args_var,

            height=40,

            corner_radius=4,

            fg_color=self.theme["surface"],

            border_color=self.theme["border"],

            text_color=self.theme["text"],
        ).pack(
            fill="x",

            pady=(6, 16)
        )

        # Offline name

        SectionLabel(
            container,

            "OFFLINE USERNAME",

            theme=self.theme,
        ).pack(
            fill="x"
        )

        offline_name_var = tk.StringVar(
            value=get_setting(
                "offline_username",
                "Player",
            )
        )

        ctk.CTkEntry(
            container,

            textvariable=offline_name_var,

            height=40,

            corner_radius=4,

            fg_color=self.theme["surface"],

            border_color=self.theme["border"],

            text_color=self.theme["text"],
        ).pack(
            fill="x",

            pady=(6, 20)
        )

        # Save

        def apply_settings():

            try:

                min_ram = int(
                    min_ram_var.get()
                )

                max_ram = int(
                    max_ram_var.get()
                )

                if min_ram <= 0:

                    raise ValueError(
                        "Minimum RAM must be greater than 0."
                    )

                if max_ram <= 0:

                    raise ValueError(
                        "Maximum RAM must be greater than 0."
                    )

                if min_ram > max_ram:

                    raise ValueError(
                        "Minimum RAM cannot be greater "
                        "than maximum RAM."
                    )

            except ValueError as exc:

                messagebox.showerror(
                    "Invalid settings",

                    str(exc),

                    parent=window,
                )

                return

            set_setting(
                "min_ram",
                min_ram,
            )

            set_setting(
                "max_ram",
                max_ram,
            )

            set_setting(
                "java_path",
                java_var.get().strip(),
            )

            set_setting(
                "java_arguments",
                java_args_var.get().strip(),
            )

            set_setting(
                "offline_username",
                offline_name_var.get().strip()
                or "Player",
            )

            selected_theme = (
                theme_var.get()
            )

            set_setting(
                "theme",
                selected_theme,
            )

            window.destroy()

            # Refresh profile because offline name may
            # have changed.
            if selected_theme != self.theme_name:

                self._apply_theme(
                    selected_theme
                )

            else:

                self._load_profile()

        PrimaryButton(
            container,

            text="Apply settings",

            theme=self.theme,

            height=44,

            command=apply_settings,
        ).pack(
            fill="x",

            pady=(10, 20)
        )

    # Theme

    def _apply_theme(
        self,
        theme_name: str,
    ):

        self.theme_name = (
            theme_name
        )

        self.theme = get_theme(
            theme_name
        )

        set_setting(
            "theme",
            theme_name,
        )

        for widget in (
            self.winfo_children()
        ):

            widget.destroy()

        self._build_ui()

        self._load_saved_values()

        self._load_profile()


# Entry point compatibility

if __name__ == "__main__":

    app = LauncherApp()

    app.mainloop()
```

---

## File: `/Users/ikram/Desktop/Project Important/H4Launcher/ui/components.py`

```py
# project_root/ui/components.py

from __future__ import annotations

import customtkinter as ctk


FONT = "Arial"

# Themes

THEMES = {

    "Blue": {
        "bg": "#F4F7FB",
        "surface": "#FFFFFF",
        "surface_alt": "#EEF4FA",

        "border": "#D8E1EC",

        "text": "#152238",
        "text_muted": "#6E7D90",

        "accent": "#2F6FED",
        "accent_hover": "#255DCE",

        "console_bg": "#111827",
        "console_text": "#D8E2F0",
        "console_border": "#243247",
    },

    "Slate": {
        "bg": "#F2F4F7",
        "surface": "#FFFFFF",
        "surface_alt": "#E9EDF2",

        "border": "#D0D6DE",

        "text": "#20252C",
        "text_muted": "#6B7280",

        "accent": "#53657A",
        "accent_hover": "#435366",

        "console_bg": "#171A1F",
        "console_text": "#D7DCE3",
        "console_border": "#303741",
    },

    "Midnight": {
        "bg": "#111827",
        "surface": "#172033",
        "surface_alt": "#202B40",

        "border": "#2D3A50",

        "text": "#F2F5F9",
        "text_muted": "#9BA8BA",

        "accent": "#4C8DFF",
        "accent_hover": "#3B78E7",

        "console_bg": "#0A0F18",
        "console_text": "#DCE7F5",
        "console_border": "#26344A",
    },

    "Forest": {
        "bg": "#F2F7F3",
        "surface": "#FFFFFF",
        "surface_alt": "#E8F1EA",

        "border": "#CFDED2",

        "text": "#17251B",
        "text_muted": "#6A7A6E",

        "accent": "#347A4A",
        "accent_hover": "#28633B",

        "console_bg": "#101A13",
        "console_text": "#D9E8DC",
        "console_border": "#294331",
    },

    "Warm": {
        "bg": "#F8F5F1",
        "surface": "#FFFFFF",
        "surface_alt": "#F1ECE6",

        "border": "#DED5CA",

        "text": "#29231E",
        "text_muted": "#786F66",

        "accent": "#A0643B",
        "accent_hover": "#87502F",

        "console_bg": "#1B1714",
        "console_text": "#E9DED5",
        "console_border": "#3D3028",
    },
}


def get_theme(
    name: str,
) -> dict:

    return THEMES.get(
        name,
        THEMES["Blue"],
    )

# Buttons

class PrimaryButton(
    ctk.CTkButton
):

    def __init__(
        self,
        master,
        text: str,
        theme: dict,
        **kwargs,
    ):

        kwargs.setdefault(
            "height",
            44,
        )

        kwargs.setdefault(
            "corner_radius",
            5,
        )

        kwargs.setdefault(
            "fg_color",
            theme["accent"],
        )

        kwargs.setdefault(
            "hover_color",
            theme["accent_hover"],
        )

        kwargs.setdefault(
            "text_color",
            "#FFFFFF",
        )

        kwargs.setdefault(
            "font",
            ctk.CTkFont(
                family=FONT,
                size=13,
                weight="bold",
            ),
        )

        super().__init__(
            master,
            text=text,
            **kwargs,
        )


class SecondaryButton(
    ctk.CTkButton
):

    def __init__(
        self,
        master,
        text: str,
        theme: dict,
        **kwargs,
    ):

        kwargs.setdefault(
            "height",
            40,
        )

        kwargs.setdefault(
            "corner_radius",
            5,
        )

        kwargs.setdefault(
            "fg_color",
            theme["surface"],
        )

        kwargs.setdefault(
            "hover_color",
            theme["surface_alt"],
        )

        kwargs.setdefault(
            "border_width",
            1,
        )

        kwargs.setdefault(
            "border_color",
            theme["border"],
        )

        kwargs.setdefault(
            "text_color",
            theme["text"],
        )

        kwargs.setdefault(
            "font",
            ctk.CTkFont(
                family=FONT,
                size=12,
            ),
        )

        super().__init__(
            master,
            text=text,
            **kwargs,
        )

# Labels

class SectionLabel(
    ctk.CTkLabel
):

    def __init__(
        self,
        master,
        text: str,
        theme: dict,
        **kwargs,
    ):

        kwargs.setdefault(
            "font",
            ctk.CTkFont(
                family=FONT,
                size=11,
                weight="bold",
            ),
        )

        kwargs.setdefault(
            "text_color",
            theme["text_muted"],
        )

        super().__init__(
            master,
            text=text,
            **kwargs,
        )

# Progress

class FlatProgressBar(
    ctk.CTkProgressBar
):

    def __init__(
        self,
        master,
        theme: dict,
        **kwargs,
    ):

        kwargs.setdefault(
            "height",
            5,
        )

        kwargs.setdefault(
            "corner_radius",
            2,
        )

        kwargs.setdefault(
            "fg_color",
            theme["surface_alt"],
        )

        kwargs.setdefault(
            "progress_color",
            theme["accent"],
        )

        super().__init__(
            master,
            **kwargs,
        )

        self.set(0)

# Console

class Console(
    ctk.CTkTextbox
):

    def __init__(
        self,
        master,
        theme: dict,
        **kwargs,
    ):

        kwargs.setdefault(
            "fg_color",
            theme["console_bg"],
        )

        kwargs.setdefault(
            "text_color",
            theme["console_text"],
        )

        kwargs.setdefault(
            "border_width",
            1,
        )

        kwargs.setdefault(
            "border_color",
            theme["console_border"],
        )

        kwargs.setdefault(
            "corner_radius",
            4,
        )

        kwargs.setdefault(
            "font",
            ctk.CTkFont(
                family="Courier New",
                size=11,
            ),
        )

        kwargs.setdefault(
            "wrap",
            "none",
        )

        super().__init__(
            master,
            **kwargs,
        )

        self.configure(
            state="disabled"
        )

    def write(
        self,
        text: str,
    ) -> None:

        self.configure(
            state="normal"
        )

        self.insert(
            "end",
            text,
        )

        self.see(
            "end"
        )

        self.configure(
            state="disabled"
        )

    def clear(self) -> None:

        self.configure(
            state="normal"
        )

        self.delete(
            "1.0",
            "end",
        )

        self.configure(
            state="disabled"
        )

# Profile card

class ProfileCard(
    ctk.CTkFrame
):

    def __init__(
        self,
        master,
        theme: dict,
        **kwargs,
    ):

        super().__init__(
            master,

            fg_color=theme["surface"],

            corner_radius=5,

            border_width=1,

            border_color=theme["border"],

            **kwargs,
        )

        self.theme = theme

        self.grid_columnconfigure(
            1,
            weight=1,
        )

        # Avatar

        self.avatar_label = ctk.CTkLabel(
            self,

            text="H4",

            width=64,

            height=64,

            fg_color=theme["surface_alt"],

            corner_radius=8,

            font=ctk.CTkFont(
                family=FONT,
                size=16,
                weight="bold",
            ),

            text_color=theme["accent"],
        )

        self.avatar_label.grid(
            row=0,
            column=0,

            padx=18,
            pady=16,
        )

        # Text

        text_frame = ctk.CTkFrame(
            self,

            fg_color="transparent",
        )

        text_frame.grid(
            row=0,
            column=1,

            sticky="ew",

            padx=(0, 18),

            pady=16,
        )

        self.name_label = ctk.CTkLabel(
            text_frame,

            text="Player",

            font=ctk.CTkFont(
                family=FONT,
                size=17,
                weight="bold",
            ),

            text_color=theme["text"],

            anchor="w",
        )

        self.name_label.pack(
            fill="x"
        )

        self.status_label = ctk.CTkLabel(
            text_frame,

            text="Offline profile",

            font=ctk.CTkFont(
                family=FONT,
                size=11,
            ),

            text_color=theme["text_muted"],

            anchor="w",
        )

        self.status_label.pack(
            fill="x",

            pady=(3, 0),
        )

        self.uuid_label = ctk.CTkLabel(
            text_frame,

            text="",

            font=ctk.CTkFont(
                family="Courier New",
                size=9,
            ),

            text_color=theme["text_muted"],

            anchor="w",
        )

        self.uuid_label.pack(
            fill="x",

            pady=(5, 0),
        )

    # Profile update

    def set_profile(
        self,
        profile,
    ):

        self.name_label.configure(
            text=profile.username
        )

        if profile.online:

            self.status_label.configure(
                text="Microsoft account"
            )

        else:

            self.status_label.configure(
                text="Offline profile"
            )

        self.uuid_label.configure(
            text=profile.uuid
        )

        # Avatar

        if profile.avatar:

            image = ctk.CTkImage(
                light_image=profile.avatar,

                dark_image=profile.avatar,

                size=(64, 64),
            )

            self.avatar_label.configure(
                image=image,
                text="",
            )

            # Keep reference alive.
            self._avatar_image = image

        else:

            self.avatar_label.configure(
                image=None,

                text="H4",
            )

            self._avatar_image = None
```

---

## File: `/Users/ikram/Desktop/Project Important/H4Launcher/utils/config_manager.py`

```py
# project_root/utils/config_manager.py

from __future__ import annotations

import json
from pathlib import Path
from typing import Any


APP_NAME = "H4Launcher"

# Project paths
PROJECT_ROOT = Path(__file__).resolve().parent.parent

# H4Launcher/.minecraft
MINECRAFT_DIRECTORY = PROJECT_ROOT / ".minecraft"

# Automatically create the Minecraft directory.
MINECRAFT_DIRECTORY.mkdir(
    parents=True,
    exist_ok=True,
)

# H4Launcher/.h4launcher/config.json
CONFIG_DIRECTORY = PROJECT_ROOT / ".h4launcher"

CONFIG_DIRECTORY.mkdir(
    parents=True,
    exist_ok=True,
)

CONFIG_FILE = CONFIG_DIRECTORY / "config.json"


# Default configuration
DEFAULT_CONFIG: dict[str, Any] = {
    "settings": {
        # Minecraft
        "selected_version": "1.16.5",
        "selected_loader": "Vanilla",

        # RAM
        "min_ram": 1024,
        "max_ram": 4096,

        # Java
        "java_path": "",
        "java_arguments": "",

        # Game window
        "resolution_width": 1280,
        "resolution_height": 720,

        # Offline mode
        "offline_username": "Player",

        # Appearance
        "theme": "Blue",

        # Launcher
        "close_launcher_after_launch": False,
    },

    "auth": {
        "username": "",
        "uuid": "",
        "access_token": "",
        "refresh_token": "",
    },
}


# Internal helpers
def _deep_merge(
    defaults: dict[str, Any],
    values: dict[str, Any],
) -> dict[str, Any]:

    result = defaults.copy()

    for key, value in values.items():

        if (
            key in result
            and isinstance(result[key], dict)
            and isinstance(value, dict)
        ):
            result[key] = _deep_merge(
                result[key],
                value,
            )
        else:
            result[key] = value

    return result


# Config API
def load_config() -> dict[str, Any]:

    if not CONFIG_FILE.exists():

        return _deep_merge(
            DEFAULT_CONFIG,
            {},
        )

    try:

        with CONFIG_FILE.open(
            "r",
            encoding="utf-8",
        ) as file:

            data = json.load(file)

        if not isinstance(data, dict):

            return _deep_merge(
                DEFAULT_CONFIG,
                {},
            )

        return _deep_merge(
            DEFAULT_CONFIG,
            data,
        )

    except (
        OSError,
        json.JSONDecodeError,
    ):

        return _deep_merge(
            DEFAULT_CONFIG,
            {},
        )


def save_config(
    config: dict[str, Any],
) -> None:

    CONFIG_DIRECTORY.mkdir(
        parents=True,
        exist_ok=True,
    )

    temporary_file = (
        CONFIG_FILE.with_suffix(".tmp")
    )

    with temporary_file.open(
        "w",
        encoding="utf-8",
    ) as file:

        json.dump(
            config,
            file,
            indent=4,
            ensure_ascii=False,
        )

    temporary_file.replace(
        CONFIG_FILE
    )


def get_setting(
    key: str,
    default: Any = None,
) -> Any:

    config = load_config()

    return config.get(
        "settings",
        {},
    ).get(
        key,
        default,
    )


def set_setting(
    key: str,
    value: Any,
) -> None:

    config = load_config()

    config.setdefault(
        "settings",
        {}
    )

    config["settings"][key] = value

    save_config(
        config
    )


# Authentication
def get_auth_data() -> dict[str, Any]:

    config = load_config()

    return config.get(
        "auth",
        {},
    ).copy()


def save_auth_data(
    auth_data: dict[str, Any],
) -> None:

    config = load_config()

    config["auth"] = auth_data

    save_config(
        config
    )


def clear_auth_data() -> None:

    config = load_config()

    config["auth"] = (
        DEFAULT_CONFIG["auth"].copy()
    )

    save_config(
        config
    )
```

---


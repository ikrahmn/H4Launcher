# project_root/core/auth.py

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

        # Offline mode intentionally
        # does not have a real Microsoft
        # authentication token.
        "access_token": "0",
        "refresh_token": "",
    }


auth_manager = MicrosoftAuth()
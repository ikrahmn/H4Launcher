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
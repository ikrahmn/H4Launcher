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
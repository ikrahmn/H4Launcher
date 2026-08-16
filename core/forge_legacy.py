# project_root/core/forge_legacy.py
"""
Why this exists
----------------
minecraft_launcher_lib.forge.install_forge_version() only supports
Minecraft 1.13 and newer, because those Forge installers require
running Java "processors" (bytecode patchers) to produce the final
Forge jar. supports_automatic_install() correctly returns False for
older versions and there is no silent equivalent in the library for
them - the only fallback it offers is run_forge_installer(), which
pops up Forge's own Swing GUI and does not target a custom Minecraft
directory.

Legacy Forge (<=1.12.2) installers do NOT use processors. Their
"install_profile.json" is a much simpler manifest:
"""

from __future__ import annotations

import json
import os
import shutil
import tempfile
import zipfile
from pathlib import Path
from typing import Callable, Optional

import requests

try:
    import minecraft_launcher_lib
except ImportError:  # pragma: no cover
    minecraft_launcher_lib = None


class LegacyForgeInstallError(Exception):
    pass


# Mirrors tried in order for any library/jar download. Old
# install_profile.json files often point at Forge's legacy
# "files.minecraftforge.net/maven" host, which has been unreliable
# for years, so we always fall back to the modern hosts.
FALLBACK_MAVEN_MIRRORS = [
    "https://maven.minecraftforge.net/",
    "https://libraries.minecraft.net/",
    "https://repo1.maven.org/maven2/",
]

FORGE_MAVEN_BASE = "https://maven.minecraftforge.net/"

REQUEST_TIMEOUT = 30


# ---------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------

def _maven_name_to_path(name: str) -> str:
    """
    Converts a maven coordinate string such as

        net.minecraftforge:forge:1.12.2-14.23.5.2860
        net.minecraftforge:forge:1.12.2-14.23.5.2860:universal

    into the standard maven repository relative path:

        net/minecraftforge/forge/1.12.2-14.23.5.2860/forge-1.12.2-14.23.5.2860.jar
        net/minecraftforge/forge/1.12.2-14.23.5.2860/forge-1.12.2-14.23.5.2860-universal.jar
    """

    parts = name.split(":")

    if len(parts) < 3:
        raise LegacyForgeInstallError(
            f"Malformed maven coordinate: {name!r}"
        )

    group, artifact, version = parts[0], parts[1], parts[2]

    classifier = parts[3] if len(parts) > 3 else None

    extension = "jar"

    if "@" in version:
        version, extension = version.split("@", 1)

    filename = f"{artifact}-{version}"

    if classifier:
        filename += f"-{classifier}"

    filename += f".{extension}"

    group_path = group.replace(".", "/")

    return f"{group_path}/{artifact}/{version}/{filename}"


def _download_with_fallback(
    urls: list[str],
    destination: Path,
) -> None:

    destination.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    last_error: Optional[Exception] = None

    for url in urls:

        try:

            response = requests.get(
                url,
                timeout=REQUEST_TIMEOUT,
                stream=True,
            )

            if response.status_code != 200:

                last_error = LegacyForgeInstallError(
                    f"HTTP {response.status_code} for {url}"
                )

                continue

            with open(destination, "wb") as file:

                for chunk in response.iter_content(
                    chunk_size=65536,
                ):

                    if chunk:

                        file.write(chunk)

            return

        except requests.RequestException as exc:

            last_error = exc

            continue

    raise LegacyForgeInstallError(
        f"Could not download {destination.name} from any mirror: "
        f"{last_error}"
    )


# ---------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------

def install_legacy_forge(
    minecraft_version: str,
    forge_version: str,
    minecraft_directory: Path,
    callback: Optional[Callable[[str], None]] = None,
    progress_callback: Optional[Callable[[float], None]] = None,
) -> str:
    """
    Fully-automatic installer for Forge builds older than 1.13.

    Returns the launcher version id that was installed (the id you
    pass into minecraft_launcher_lib.command.get_minecraft_command).
    """

    def status(text: str) -> None:

        if callback:

            callback(f"[FORGE] {text}\n")

    def progress(value: float) -> None:

        if progress_callback:

            progress_callback(
                max(0.0, min(1.0, value))
            )

    minecraft_directory = Path(minecraft_directory)

    libraries_directory = minecraft_directory / "libraries"

    versions_directory = minecraft_directory / "versions"

    # 1. Download the installer jar.

    installer_url = (
        f"{FORGE_MAVEN_BASE}net/minecraftforge/forge/"
        f"{forge_version}/forge-{forge_version}-installer.jar"
    )

    status(f"Downloading installer ({forge_version})...")

    progress(0.05)

    with tempfile.TemporaryDirectory(
        prefix="h4launcher_forge_",
    ) as tmp_dir_name:

        tmp_dir = Path(tmp_dir_name)

        installer_path = tmp_dir / "installer.jar"

        _download_with_fallback(
            [installer_url],
            installer_path,
        )

        # 2. Read install_profile.json out of the installer jar.

        status("Reading install profile...")

        progress(0.2)

        try:

            with zipfile.ZipFile(installer_path) as archive:

                with archive.open(
                    "install_profile.json"
                ) as profile_file:

                    profile = json.load(profile_file)

                install_section = profile.get(
                    "install",
                    profile,
                )

                version_info = profile.get("versionInfo")

                if version_info is None:

                    raise LegacyForgeInstallError(
                        "install_profile.json has no 'versionInfo' "
                        "section - this installer does not use the "
                        "legacy format this installer expects."
                    )

                maven_path = install_section.get("path")

                bundled_filename = install_section.get(
                    "filePath"
                )

                if not maven_path:

                    raise LegacyForgeInstallError(
                        "install_profile.json is missing 'path' "
                        "in its 'install' section."
                    )

                # 3. Get the Forge jar itself into the libraries
                #    folder.
                #
                # Older installers (e.g. 1.11-era) bundle nothing
                # and leave 'filePath' empty - in that case the
                # Forge jar is just another entry in
                # versionInfo.libraries with its own maven URL, and
                # the download loop below picks it up normally.
                # Later installers (later 1.12.2 builds) embed the
                # universal jar in the installer and set 'filePath'
                # to its name inside the jar - extract it directly.

                extracted_forge_jar = False

                if bundled_filename:

                    status("Installing Forge library...")

                    progress(0.35)

                    relative_lib_path = _maven_name_to_path(
                        maven_path
                    )

                    target_lib_path = (
                        libraries_directory / relative_lib_path
                    )

                    target_lib_path.parent.mkdir(
                        parents=True,
                        exist_ok=True,
                    )

                    try:

                        with archive.open(
                            bundled_filename
                        ) as source, open(
                            target_lib_path,
                            "wb",
                        ) as dest:

                            shutil.copyfileobj(
                                source,
                                dest,
                            )

                        extracted_forge_jar = True

                    except KeyError:

                        # Listed but not actually present in this
                        # jar - fall back to downloading it like a
                        # normal library below.

                        extracted_forge_jar = False

        except KeyError as exc:

            raise LegacyForgeInstallError(
                f"Installer jar is missing an expected file: {exc}"
            ) from exc

        except zipfile.BadZipFile as exc:

            raise LegacyForgeInstallError(
                "Downloaded Forge installer is not a valid jar "
                "file (the download may be corrupted)."
            ) from exc

        # 4. Work out the installed version id and write the
        #    version JSON.

        try:

            installed_version = (
                minecraft_launcher_lib.forge.forge_to_installed_version(
                    forge_version
                )
            )

        except Exception:

            installed_version = version_info.get(
                "id",
                forge_version,
            )

        version_info["id"] = installed_version

        version_info.setdefault(
            "inheritsFrom",
            minecraft_version,
        )

        status(f"Writing version metadata ({installed_version})...")

        progress(0.45)

        version_dir = versions_directory / installed_version

        version_dir.mkdir(
            parents=True,
            exist_ok=True,
        )

        version_json_path = (
            version_dir / f"{installed_version}.json"
        )

        with open(
            version_json_path,
            "w",
            encoding="utf-8",
        ) as file:

            json.dump(
                version_info,
                file,
                indent=2,
            )

        # 5. Download whatever extra libraries this Forge build
        #    needs (asm, launchwrapper forks, etc).

        libraries = version_info.get("libraries", [])

        # If we already extracted the universal jar straight from
        # the installer, don't re-download that same entry.

        skip_names = {maven_path} if extracted_forge_jar else set()

        total = len(libraries) or 1

        for index, library in enumerate(libraries):

            name = library.get("name")

            if not name or name in skip_names:

                progress(
                    0.45 + 0.5 * ((index + 1) / total)
                )

                continue

            # Some legacy entries mark themselves as server-only.

            if library.get("clientreq") is False:

                continue

            relative_path = _maven_name_to_path(name)

            lib_target = libraries_directory / relative_path

            if lib_target.exists() and lib_target.stat().st_size > 0:

                progress(
                    0.45 + 0.5 * ((index + 1) / total)
                )

                continue

            candidate_urls = []

            explicit_url = library.get("url")

            if explicit_url:

                candidate_urls.append(
                    explicit_url.rstrip("/") + "/" + relative_path
                )

            for mirror in FALLBACK_MAVEN_MIRRORS:

                candidate_urls.append(mirror + relative_path)

            status(f"Downloading library: {name}")

            try:

                _download_with_fallback(
                    candidate_urls,
                    lib_target,
                )

            except LegacyForgeInstallError as exc:

                status(
                    f"WARNING: could not download {name} "
                    f"({exc}) - the game may still run if this "
                    "library is optional."
                )

            progress(
                0.45 + 0.5 * ((index + 1) / total)
            )

    status("Legacy Forge installation complete.")

    progress(1.0)

    return installed_version
# project_root/ui/app.py

from __future__ import annotations

import os
import subprocess
import sys
import uuid
from pathlib import Path
import tkinter as tk
from tkinter import filedialog, messagebox

import customtkinter as ctk

from core.launcher import (
    MinecraftLauncher,
    SUPPORTED_VERSIONS,
    LOADER_VANILLA,
    LOADER_FORGE,
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
)


# ============================================================
# H4Launcher
# ============================================================

class LauncherApp(ctk.CTk):

    def __init__(self):

        super().__init__()

        self.title(
            "H4Launcher"
        )

        self.geometry(
            "1080x700"
        )

        self.minsize(
            900,
            620,
        )

        self.theme_name = get_setting(
            "theme",
            "Blue",
        )

        self.theme = get_theme(
            self.theme_name
        )

        ctk.set_appearance_mode(
            "light"
        )

        self.launcher = (
            MinecraftLauncher()
        )

        self.is_launching = False

        self._build_ui()

        self._load_saved_values()

    # ========================================================
    # UI
    # ========================================================

    def _build_ui(self):

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

        # ----------------------------------------------------
        # Sidebar
        # ----------------------------------------------------

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
        logo = ctk.CTkLabel(
            sidebar,

            text="H4Launcher",

            font=ctk.CTkFont(
                family=FONT,
                size=22,
                weight="bold",
            ),

            text_color=self.theme["text"],

            anchor="w",
        )

        logo.pack(
            fill="x",

            padx=24,

            pady=(28, 5),
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

            pady=(0, 30),
        )

        # Navigation separator
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

        # Forge mods button
        self.mods_button = SecondaryButton(
            sidebar,

            text="Open Mods Folder",

            theme=self.theme,

            height=34,

            command=self._open_mods_folder,
        )

        # hidden initially
        self.mods_button.pack(
            fill="x",

            padx=24,

            pady=(0, 18),
        )

        # Hide until Forge
        self.mods_button.pack_forget()

        # Bottom navigation
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

        # ----------------------------------------------------
        # Main area
        # ----------------------------------------------------

        main = ctk.CTkFrame(
            self,

            fg_color=self.theme["bg"],

            corner_radius=0,
        )

        main.grid(
            row=0,
            column=1,

            sticky="nsew",

            padx=0,
            pady=0,
        )

        main.grid_columnconfigure(
            0,
            weight=1,
        )

        main.grid_rowconfigure(
            2,
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
            pady=(28, 20),
        )

        title = ctk.CTkLabel(
            header,

            text="Play",

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

            text="Not signed in",

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

        # ----------------------------------------------------
        # Play section
        # ----------------------------------------------------

        play_panel = ctk.CTkFrame(
            main,

            fg_color=self.theme["surface"],

            corner_radius=5,

            border_width=1,

            border_color=self.theme["border"],
        )

        play_panel.grid(
            row=1,
            column=0,

            sticky="ew",

            padx=34,
            pady=(0, 18),
        )

        play_panel.grid_columnconfigure(
            0,
            weight=1,
        )

        selected_label = ctk.CTkLabel(
            play_panel,

            text="Selected installation",

            font=ctk.CTkFont(
                family=FONT,
                size=10,
                weight="bold",
            ),

            text_color=self.theme["text_muted"],

            anchor="w",
        )

        selected_label.grid(
            row=0,
            column=0,

            padx=22,
            pady=(18, 3),

            sticky="w",
        )

        self.selected_installation_label = ctk.CTkLabel(
            play_panel,

            text="Minecraft 1.16.5",

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

            padx=22,

            pady=(0, 18),

            sticky="w",
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
            pady=18,
        )

        # ----------------------------------------------------
        # Console
        # ----------------------------------------------------

        console_header = ctk.CTkFrame(
            main,

            fg_color="transparent",
        )

        console_header.grid(
            row=2,
            column=0,

            sticky="new",

            padx=34,
            pady=(0, 5),
        )

        console_header.grid_columnconfigure(
            0,
            weight=1,
        )

        console_title = ctk.CTkLabel(
            console_header,

            text="LAUNCH CONSOLE",

            font=ctk.CTkFont(
                family=FONT,
                size=10,
                weight="bold",
            ),

            text_color=self.theme["text_muted"],

            anchor="w",
        )

        console_title.grid(
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

            padx=(10, 0),
        )

        self.console = Console(
            main,

            theme=self.theme,
        )

        self.console.grid(
            row=3,
            column=0,

            sticky="nsew",

            padx=34,
            pady=(0, 18),
        )

        main.grid_rowconfigure(
            3,
            weight=1,
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
            row=4,
            column=0,

            sticky="ew",

            padx=34,

            pady=(0, 8),
        )

        self.progress = FlatProgressBar(
            main,

            theme=self.theme,
        )

        self.progress.grid(
            row=5,
            column=0,

            sticky="ew",

            padx=34,

            pady=(0, 24),
        )

        self.progress.set(0)

        # Initial loader state
        self._loader_changed(
            self.loader_var.get()
        )

    # ========================================================
    # Saved settings
    # ========================================================

    def _load_saved_values(self):

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

        auth = get_auth_data()

        username = auth.get(
            "username",
            "",
        )

        if username:

            self.account_label.configure(
                text=f"Signed in as {username}"
            )

    # ========================================================
    # Version / loader
    # ========================================================

    def _version_changed(
        self,
        version,
    ):

        set_setting(
            "selected_version",
            version,
        )

        self._update_installation_label()

        if self.loader_var.get() == LOADER_FORGE:

            self._refresh_forge_state()

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

            self._refresh_forge_state()

        else:

            self.mods_button.pack_forget()

    def _update_installation_label(self):

        version = (
            self.version_var.get()
        )

        loader = (
            self.loader_var.get()
        )

        self.selected_installation_label.configure(
            text=f"Minecraft {version}  |  {loader}"
        )

    def _refresh_forge_state(self):

        version = (
            self.version_var.get()
        )

        forge_version = (
            self.launcher.get_forge_version(
                version
            )
        )

        if forge_version:

            self._write_console(
                f"[FORGE] Available: "
                f"{forge_version}\n"
            )

        else:

            self._write_console(
                f"[FORGE] No Forge installation "
                f"detected for Minecraft {version}.\n"
            )

    # ========================================================
    # Mods
    # ========================================================

    def _get_mods_directory(self) -> Path:

        return (
            self.launcher.get_mods_directory()
        )

    def _get_installed_mods(self) -> list[Path]:

        mods_directory = (
            self._get_mods_directory()
        )

        return sorted(
            [
                path
                for path in mods_directory.iterdir()
                if path.is_file()
                and path.suffix.lower() == ".jar"
            ],
            key=lambda path: path.name.lower(),
        )

    def _open_mods_folder(self):

        mods_directory = (
            self._get_mods_directory()
        )

        mods_directory.mkdir(
            parents=True,
            exist_ok=True,
        )

        self._open_path(
            mods_directory
        )

    def _open_path(
        self,
        path: Path,
    ):

        path = Path(path)

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

    # ========================================================
    # Console
    # ========================================================

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

    def _clear_console(self):

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

    # ========================================================
    # Play
    # ========================================================

    def _play(self):

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

        # ----------------------------------------------------
        # Offline account
        # ----------------------------------------------------

        auth = get_auth_data()

        username = auth.get(
            "username",
            "",
        )

        access_token = auth.get(
            "access_token",
            "",
        )

        player_uuid = auth.get(
            "uuid",
            "",
        )

        if not username:

            username = get_setting(
                "offline_username",
                "Player",
            )

        if not player_uuid:

            player_uuid = str(
                uuid.uuid3(
                    uuid.NAMESPACE_DNS,
                    f"H4Launcher:{username}",
                )
            )

        offline = not bool(
            access_token
        )

        if offline:

            self._write_console(
                "[AUTH] Offline mode\n"
            )

        else:

            self._write_console(
                f"[AUTH] Microsoft account: "
                f"{username}\n"
            )

        # ----------------------------------------------------
        # Background launch
        # ----------------------------------------------------

        def worker():

            try:

                # Vanilla installation
                if not self.launcher.is_version_installed(
                    version
                ):

                    self._write_console(
                        "[DOWNLOAD] Minecraft version "
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

                    self._write_console(
                        "[FORGE] Checking installation...\n"
                    )

                    forge_version = (
                        self.launcher.get_forge_version(
                            version
                        )
                    )

                    if not forge_version:

                        raise RuntimeError(
                            f"No Forge version available "
                            f"for Minecraft {version}."
                        )

                    forge_dir = (
                        self.launcher.minecraft_directory
                        / "versions"
                        / forge_version
                    )

                    if not forge_dir.exists():

                        self._set_status(
                            "Installing Forge..."
                        )

                        if not self.launcher.install_forge(
                            version,
                            callback=self._write_console,
                        ):

                            raise RuntimeError(
                                "Forge installation failed."
                            )

                    launch_version = (
                        forge_version
                    )

                else:

                    launch_version = version

                self._set_progress(
                    1.0
                )

                self._set_status(
                    "Launching Minecraft..."
                )

                self._write_console(
                    f"[LAUNCH] Version: "
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
                        "Launch Error",
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

    # ========================================================
    # Settings
    # ========================================================

    def _open_settings(self):

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

        # ----------------------------------------------------
        # Appearance
        # ----------------------------------------------------

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

        theme_menu = ctk.CTkOptionMenu(
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

        )

        theme_menu.pack(
            fill="x",

            pady=(6, 20)
        )

        # ----------------------------------------------------
        # RAM
        # ----------------------------------------------------

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

        min_ram_entry = ctk.CTkEntry(
            container,

            textvariable=min_ram_var,

            height=40,

            corner_radius=4,

            fg_color=self.theme["surface"],

            border_color=self.theme["border"],

            text_color=self.theme["text"],
        )

        min_ram_entry.pack(
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

        max_ram_entry = ctk.CTkEntry(
            container,

            textvariable=max_ram_var,

            height=40,

            corner_radius=4,

            fg_color=self.theme["surface"],

            border_color=self.theme["border"],

            text_color=self.theme["text"],
        )

        max_ram_entry.pack(
            fill="x",

            pady=(6, 16)
        )

        # ----------------------------------------------------
        # Java executable
        # ----------------------------------------------------

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

            selected = filedialog.askopenfilename(
                title="Select Java executable"
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

        # ----------------------------------------------------
        # JVM arguments
        # ----------------------------------------------------

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

        # ----------------------------------------------------
        # Offline username
        # ----------------------------------------------------

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

        # ----------------------------------------------------
        # Apply
        # ----------------------------------------------------

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

            if selected_theme != self.theme_name:

                self._apply_theme(
                    selected_theme
                )

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

    # ========================================================
    # Theme
    # ========================================================

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

        # Rebuild application UI.
        for widget in self.winfo_children():

            widget.destroy()

        self._build_ui()

        self._load_saved_values()


# ============================================================
# Entry point compatibility
# ============================================================

if __name__ == "__main__":

    app = LauncherApp()

    app.mainloop()
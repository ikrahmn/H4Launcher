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
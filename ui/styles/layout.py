"""Lightweight layout constants, fonts, and emoji helpers."""

from __future__ import annotations

import tkinter as tk
import tkinter.font as tkfont

# Consistent page margins
PAD_X = 16
PAD_Y = 12
GAP = 8
GAP_SM = 4

# Shared control sizing
CTRL_H = 32
BTN_H = 36
NAV_H = 40

_EMOJI_OK: bool | None = None


def supports_emoji() -> bool:
    """Return True when the system likely renders emoji in Tk labels."""
    global _EMOJI_OK
    if _EMOJI_OK is not None:
        return _EMOJI_OK
    try:
        root = tk.Tk()
        root.withdraw()
        families = {f.lower() for f in tkfont.families()}
        root.destroy()
        _EMOJI_OK = any(
            name in families
            for name in (
                "segoe ui emoji", "noto color emoji", "apple color emoji",
                "twitter color emoji", "emojione color", "symbola",
            )
        )
    except Exception:
        _EMOJI_OK = False
    return _EMOJI_OK


def emoji_label(emoji_text: str, plain_text: str) -> str:
    """Return plain text (emoji disabled app-wide)."""
    return plain_text


def font_title(size: int = 18):
    import customtkinter as ctk
    return ctk.CTkFont(size=size, weight="bold")


def font_heading(size: int = 14):
    import customtkinter as ctk
    return ctk.CTkFont(size=size, weight="bold")


def font_body(size: int = 13):
    import customtkinter as ctk
    return ctk.CTkFont(size=size)


def font_small(size: int = 11):
    import customtkinter as ctk
    return ctk.CTkFont(size=size)


def font_caption(size: int = 10):
    import customtkinter as ctk
    return ctk.CTkFont(size=size)


def muted_color(cfg: dict) -> str:
    return "#8b949e"


def border_color(cfg: dict) -> str:
    return "#3d3d3d"


def card_bg(cfg: dict) -> str:
    return cfg.get("theme", {}).get("card_bg", "#2b2b2b")


def subtle_card(parent, cfg: dict, **kwargs):
    """Muted panel used to group related controls or content."""
    import customtkinter as ctk

    opts = dict(
        corner_radius=10,
        fg_color=card_bg(cfg),
        border_width=1,
        border_color=border_color(cfg),
    )
    opts.update(kwargs)
    return ctk.CTkFrame(parent, **opts)


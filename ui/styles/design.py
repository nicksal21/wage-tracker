"""Shared design tokens and UI primitives for a consistent dark-theme layout."""

from __future__ import annotations

import tkinter as tk
from typing import Any

import customtkinter as ctk

# ── spacing ──────────────────────────────────────────────────────────
PAGE_PAD_X = 20
PAGE_PAD_Y = 16
SECTION_GAP = 12
ITEM_GAP = 8
CARD_PAD = 16
INNER_PAD = 12

# ── radii ────────────────────────────────────────────────────────────
RADIUS_CARD = 12
RADIUS_PANEL = 10
RADIUS_BTN = 8

# ── sidebar ──────────────────────────────────────────────────────────
SIDEBAR_WIDTH = 220
NAV_BTN_HEIGHT = 44


def theme_colors(cfg: dict) -> dict[str, str]:
    """Resolved palette from config (defaults match dark theme)."""
    t = cfg.get("theme", {})
    return {
        "card_bg": t.get("card_bg", "#2b2b2b"),
        "sidebar_bg": t.get("sidebar_bg", "#1f1f1f"),
        "surface": t.get("bg_color", "#1a1a1a"),
        "secondary": t.get("secondary_color", "#2d2d2d"),
        "accent": t.get("accent_color", "#3b8ed0"),
        "primary": t.get("primary_color", "#1f6aa5"),
        "text": t.get("text_color", "#DCE4EE"),
        "muted": "#8b949e",
        "border": "#3a3a3a",
        "success": t.get("success_color", "#28a745"),
        "danger": t.get("danger_color", "#dc3545"),
        "warning": t.get("warning_color", "#ffc107"),
    }


def font_title(size: int = 22) -> ctk.CTkFont:
    return ctk.CTkFont(size=size, weight="bold")


def font_section(size: int = 15) -> ctk.CTkFont:
    return ctk.CTkFont(size=size, weight="bold")


def font_body(size: int = 13) -> ctk.CTkFont:
    return ctk.CTkFont(size=size)


def font_caption(size: int = 11) -> ctk.CTkFont:
    return ctk.CTkFont(size=size)


def font_metric(size: int = 20) -> ctk.CTkFont:
    return ctk.CTkFont(size=size, weight="bold")


def font_label() -> ctk.CTkFont:
    return ctk.CTkFont(size=12)


def make_card(parent, cfg: dict, **kwargs: Any) -> ctk.CTkFrame:
    """Raised panel with subtle border."""
    colors = theme_colors(cfg)
    opts: dict[str, Any] = dict(
        corner_radius=RADIUS_CARD,
        fg_color=colors["card_bg"],
        border_width=1,
        border_color=colors["border"],
    )
    opts.update(kwargs)
    return ctk.CTkFrame(parent, **opts)


def make_panel(parent, cfg: dict, **kwargs: Any) -> ctk.CTkFrame:
    """Compact panel for toolbars and filter bars."""
    colors = theme_colors(cfg)
    opts: dict[str, Any] = dict(
        corner_radius=RADIUS_PANEL,
        fg_color=colors["card_bg"],
        border_width=1,
        border_color=colors["border"],
    )
    opts.update(kwargs)
    return ctk.CTkFrame(parent, **opts)


def make_tree_holder(parent, cfg: dict) -> tuple[ctk.CTkFrame, tk.Frame]:
    """Card wrapper + inner tk.Frame for ttk.Treeview."""
    colors = theme_colors(cfg)
    outer = make_panel(parent, cfg)
    inner = tk.Frame(outer, bd=0, highlightthickness=0, bg=colors["card_bg"])
    inner.pack(fill="both", expand=True, padx=2, pady=2)
    return outer, inner


def section_label(parent, text: str, **kwargs: Any) -> ctk.CTkLabel:
    colors = kwargs.pop("text_color", None)
    kw: dict[str, Any] = dict(text=text, font=font_label(), anchor="w")
    if colors:
        kw["text_color"] = colors
    kw.update(kwargs)
    return ctk.CTkLabel(parent, **kw)


def muted_label(parent, text: str, **kwargs: Any) -> ctk.CTkLabel:
    return ctk.CTkLabel(
        parent, text=text, font=font_caption(),
        text_color=kwargs.pop("text_color", "#8b949e"), **kwargs)


def refresh_button(parent, command, width: int = 40) -> ctk.CTkButton:
    return ctk.CTkButton(
        parent, text="↻", width=width, height=32,
        corner_radius=RADIUS_BTN, font=font_body(14),
        command=command,
    )


def danger_button(parent, text: str, command, width: int = 120) -> ctk.CTkButton:
    return ctk.CTkButton(
        parent, text=text, width=width, height=32,
        corner_radius=RADIUS_BTN, command=command,
        fg_color="#dc3545", hover_color="#a71d2a",
    )


def primary_button(parent, text: str, command, width: int = 140) -> ctk.CTkButton:
    return ctk.CTkButton(
        parent, text=text, width=width, height=34,
        corner_radius=RADIUS_BTN, command=command,
    )


class PageHeader(ctk.CTkFrame):
    """Top-of-page title row with optional trailing controls."""

    def __init__(
        self, parent, title: str, cfg: dict,
        subtitle: str = "", **kw,
    ):
        super().__init__(parent, fg_color="transparent", **kw)
        colors = theme_colors(cfg)
        left = ctk.CTkFrame(self, fg_color="transparent")
        left.pack(side="left", fill="y")
        ctk.CTkLabel(
            left, text=title, font=font_title(20),
            text_color=colors["text"],
        ).pack(anchor="w")
        if subtitle:
            ctk.CTkLabel(
                left, text=subtitle, font=font_caption(),
                text_color=colors["muted"],
            ).pack(anchor="w", pady=(2, 0))
        self.trailing = ctk.CTkFrame(self, fg_color="transparent")
        self.trailing.pack(side="right", fill="y")


class SectionCard(ctk.CTkFrame):
    """Settings-style section: titled card with inner content area."""

    def __init__(self, parent, title: str, cfg: dict, **kw):
        super().__init__(parent, fg_color="transparent", **kw)
        self.card = make_card(self, cfg)
        self.card.pack(fill="x")
        colors = theme_colors(cfg)
        ctk.CTkLabel(
            self.card, text=title, font=font_section(),
            text_color=colors["text"],
        ).pack(anchor="w", padx=CARD_PAD, pady=(CARD_PAD, INNER_PAD))
        ctk.CTkFrame(
            self.card, height=1, fg_color=colors["border"],
        ).pack(fill="x", padx=CARD_PAD)
        self.body = ctk.CTkFrame(self.card, fg_color="transparent")
        self.body.pack(fill="x", padx=CARD_PAD, pady=(INNER_PAD, CARD_PAD))

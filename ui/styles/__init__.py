"""Styles module."""

from ui.styles.ttk_styles import configure_ttk_styles
from ui.styles.layout import (
    PAD_X, PAD_Y, GAP, GAP_SM, CTRL_H, BTN_H, NAV_H,
    supports_emoji, emoji_label,
    font_title, font_heading, font_body, font_small, font_caption,
    muted_color, border_color, card_bg, subtle_card,
)

__all__ = [
    "configure_ttk_styles",
    "PAD_X", "PAD_Y", "GAP", "GAP_SM", "CTRL_H", "BTN_H", "NAV_H",
    "supports_emoji", "emoji_label",
    "font_title", "font_heading", "font_body", "font_small", "font_caption",
    "muted_color", "border_color", "card_bg", "subtle_card",
]
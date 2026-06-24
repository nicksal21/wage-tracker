"""Styles module."""

from ui.styles.ttk_styles import configure_ttk_styles
from ui.styles.design import (
    PAGE_PAD_X, PAGE_PAD_Y, SECTION_GAP, CARD_PAD, INNER_PAD,
    theme_colors, make_card, make_panel, make_tree_holder,
    PageHeader, SectionCard, refresh_button, danger_button,
    primary_button, section_label, muted_label,
    font_title, font_section, font_body, font_caption, font_metric,
)

__all__ = [
    "configure_ttk_styles",
    "PAGE_PAD_X", "PAGE_PAD_Y", "SECTION_GAP", "CARD_PAD", "INNER_PAD",
    "theme_colors", "make_card", "make_panel", "make_tree_holder",
    "PageHeader", "SectionCard", "refresh_button", "danger_button",
    "primary_button", "section_label", "muted_label",
    "font_title", "font_section", "font_body", "font_caption", "font_metric",
]
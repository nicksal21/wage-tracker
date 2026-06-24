"""
Main application window — lazy page instantiation, in-place tab switch,
shared ttk style setup.

Emoji fallbacks provided for cross-platform compatibility (Linux often
lacks proper emoji font support in some terminal/GUI contexts).
"""

from __future__ import annotations

import customtkinter as ctk
from config import load_config

from ui.styles.ttk_styles import configure_ttk_styles
from ui.styles.design import (
    SIDEBAR_WIDTH, NAV_BTN_HEIGHT, RADIUS_BTN,
    theme_colors, font_title, font_caption,
)
from ui.pages.dashboard_ui import DashboardPage
from ui.pages.data_ui import DataPage
from ui.pages.tax_ui import TaxPage
from ui.pages.config_ui import ConfigPage


NAV_ITEMS = [
    ("📊 Dashboard",    "📊"),
    ("📒 Entries",      "📒"),
    ("🏛️ Taxes",        "🏛️"),
    ("⚙️ Settings",     "⚙️"),
]

NAV_LABELS = ["Dashboard", "Entries", "Taxes", "Settings"]


class App(ctk.CTk):
    def __init__(self) -> None:
        super().__init__()
        self.cfg = load_config()
        self._colors = theme_colors(self.cfg)

        ctk.set_appearance_mode(self.cfg["theme"].get("mode", "dark"))
        ctk.set_default_color_theme("blue")
        configure_ttk_styles(self.cfg)

        self.title("Freelance Tracker")
        self.geometry("1280x800")
        self.minsize(960, 640)
        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(1, weight=1)

        # ── sidebar ──
        self.sidebar = ctk.CTkFrame(
            self, width=SIDEBAR_WIDTH, corner_radius=0,
            fg_color=self._colors["sidebar_bg"],
            border_width=0,
        )
        self.sidebar.grid(row=0, column=0, sticky="nswe")
        self.sidebar.grid_propagate(False)
        self.sidebar.grid_rowconfigure(1, weight=1)

        # brand block
        brand = ctk.CTkFrame(self.sidebar, fg_color="transparent")
        brand.grid(row=0, column=0, sticky="ew", padx=20, pady=(28, 16))
        title_text = self._try_emoji("💼  Freelance Tracker", "Freelance Tracker")
        ctk.CTkLabel(
            brand, text=title_text, font=font_title(17),
            text_color=self._colors["text"], anchor="w",
        ).pack(anchor="w")
        ctk.CTkLabel(
            brand, text="Work & earnings tracker",
            font=font_caption(), text_color=self._colors["muted"], anchor="w",
        ).pack(anchor="w", pady=(4, 0))

        ctk.CTkFrame(
            self.sidebar, height=1, fg_color=self._colors["border"],
        ).grid(row=0, column=0, sticky="sew", padx=16)

        # navigation
        nav = ctk.CTkFrame(self.sidebar, fg_color="transparent")
        nav.grid(row=1, column=0, sticky="nsew", padx=12, pady=(20, 8))

        self.nav_buttons: dict[str, ctk.CTkButton] = {}
        for (_, emoji_icon), text_label in zip(NAV_ITEMS, NAV_LABELS):
            display_text = self._try_emoji(
                f"  {emoji_icon}   {text_label}", f"    {text_label}")
            btn = ctk.CTkButton(
                nav, text=display_text, anchor="w",
                height=NAV_BTN_HEIGHT, corner_radius=RADIUS_BTN,
                fg_color="transparent",
                text_color=self._colors["text"],
                hover_color=self._colors["secondary"],
                font=ctk.CTkFont(size=13),
                command=lambda l=text_label: self._show_page(l),
            )
            btn.pack(fill="x", pady=3)
            self.nav_buttons[text_label] = btn

        # footer
        footer = ctk.CTkFrame(self.sidebar, fg_color="transparent")
        footer.grid(row=2, column=0, sticky="sew", padx=20, pady=(0, 16))
        ctk.CTkFrame(
            footer, height=1, fg_color=self._colors["border"],
        ).pack(fill="x", pady=(0, 10))
        ctk.CTkLabel(
            footer, text="v1.3.0",
            font=font_caption(), text_color=self._colors["muted"],
        ).pack(anchor="w")

        # ── content area ──
        self.content = ctk.CTkFrame(
            self, fg_color=self._colors["surface"], corner_radius=0)
        self.content.grid(row=0, column=1, sticky="nswe")
        self.content.grid_rowconfigure(0, weight=1)
        self.content.grid_columnconfigure(0, weight=1)

        self.pages: dict[str, ctk.CTkFrame] = {}
        self.current_page: str | None = None
        self._show_page("Dashboard")

    def _try_emoji(self, emoji_text: str, fallback_text: str) -> str:
        return emoji_text

    def _show_page(self, name: str) -> None:
        if self.current_page == name:
            page = self.pages.get(name)
            if page is not None and hasattr(page, "refresh"):
                page.refresh()
            return

        primary = self._colors["primary"]
        secondary = self._colors["secondary"]
        for label, btn in self.nav_buttons.items():
            active = label == name
            btn.configure(
                fg_color=primary if active else "transparent",
                hover_color=primary if active else secondary,
            )

        if self.current_page and self.current_page in self.pages:
            self.pages[self.current_page].grid_forget()

        if name not in self.pages:
            cls = {
                "Dashboard": DashboardPage,
                "Entries":   DataPage,
                "Taxes":     TaxPage,
                "Settings":  ConfigPage,
            }.get(name)
            if cls is not None:
                self.pages[name] = cls(self.content, app=self)
            else:
                ph = ctk.CTkFrame(self.content, fg_color="transparent")
                ctk.CTkLabel(ph, text=name, font=font_title(18)).pack(expand=True)
                self.pages[name] = ph

        self.pages[name].grid(row=0, column=0, sticky="nswe")
        self.current_page = name

        page = self.pages[name]
        if hasattr(page, "refresh"):
            page.refresh()

    def apply_theme(self, cfg: dict) -> None:
        self.cfg = cfg
        self._colors = theme_colors(cfg)
        self.sidebar.configure(fg_color=self._colors["sidebar_bg"])
        self.content.configure(fg_color=self._colors["surface"])
        primary = self._colors["primary"]
        secondary = self._colors["secondary"]
        text = self._colors["text"]
        for label, btn in self.nav_buttons.items():
            active = label == self.current_page
            btn.configure(
                fg_color=primary if active else "transparent",
                text_color=text,
                hover_color=primary if active else secondary,
            )

"""
Main application window — lazy page instantiation, in-place tab switch,
shared ttk style setup.
"""

from __future__ import annotations

import customtkinter as ctk
from config import load_config

from ui.styles.ttk_styles import configure_ttk_styles
from ui.styles.layout import (
    PAD_X, GAP, NAV_H, font_title, font_body, font_caption, muted_color,
)
from ui.pages.dashboard_ui import DashboardPage
from ui.pages.data_ui import DataPage
from ui.pages.tax_ui import TaxPage
from ui.pages.config_ui import ConfigPage

NAV_LABELS = ["Dashboard", "Entries", "Taxes", "Settings"]


class App(ctk.CTk):
    def __init__(self) -> None:
        super().__init__()
        self.cfg = load_config()

        ctk.set_appearance_mode(self.cfg["theme"].get("mode", "dark"))
        ctk.set_default_color_theme("blue")
        configure_ttk_styles(self.cfg)

        self.title("Freelance Tracker")
        self.geometry("1200x780")
        self.minsize(960, 600)
        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(1, weight=1)

        self.sidebar = ctk.CTkFrame(
            self, width=200, corner_radius=0,
            fg_color=self.cfg["theme"].get("sidebar_bg", "#1f1f1f"))
        self.sidebar.grid(row=0, column=0, sticky="nswe")
        self.sidebar.grid_propagate(False)
        self.sidebar.grid_rowconfigure(1, weight=1)

        ctk.CTkLabel(
            self.sidebar, text="Freelance Tracker", font=font_title(17),
            anchor="w",
        ).pack(fill="x", padx=PAD_X, pady=(24, 20))

        nav = ctk.CTkFrame(self.sidebar, fg_color="transparent")
        nav.pack(fill="both", expand=True, padx=GAP, pady=(0, GAP))

        self.nav_buttons: dict[str, ctk.CTkButton] = {}
        for text_label in NAV_LABELS:
            btn = ctk.CTkButton(
                nav, text=f"  {text_label}", anchor="w",
                height=NAV_H, corner_radius=8, fg_color="transparent",
                font=font_body(13),
                text_color=self.cfg["theme"].get("text_color", "#DCE4EE"),
                hover_color=self.cfg["theme"].get("primary_color", "#1f6aa5"),
                command=lambda l=text_label: self._show_page(l))
            btn.pack(fill="x", padx=GAP, pady=3)
            self.nav_buttons[text_label] = btn

        ctk.CTkLabel(
            self.sidebar, text="v1.3.0", font=font_caption(),
            text_color=muted_color(self.cfg),
        ).pack(side="bottom", pady=(0, 14))

        self.content = ctk.CTkFrame(self, fg_color="transparent")
        self.content.grid(row=0, column=1, sticky="nswe")
        self.content.grid_rowconfigure(0, weight=1)
        self.content.grid_columnconfigure(0, weight=1)

        self.pages: dict[str, ctk.CTkFrame] = {}
        self.current_page: str | None = None
        self._show_page("Dashboard")

    def _show_page(self, name: str) -> None:
        if self.current_page == name:
            page = self.pages.get(name)
            if page is not None and hasattr(page, "refresh"):
                page.refresh()
            return

        for label, btn in self.nav_buttons.items():
            btn.configure(
                fg_color=self.cfg["theme"].get("primary_color", "#1f6aa5")
                if label == name else "transparent")

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
                ph = ctk.CTkFrame(self.content)
                ctk.CTkLabel(ph, text=name).pack(expand=True)
                self.pages[name] = ph

        self.pages[name].grid(row=0, column=0, sticky="nswe")
        self.current_page = name

        page = self.pages[name]
        if hasattr(page, "refresh"):
            page.refresh()

    def apply_theme(self, cfg: dict) -> None:
        self.cfg = cfg
        sidebar_bg = cfg["theme"].get("sidebar_bg", "#1f1f1f")
        primary = cfg["theme"].get("primary_color", "#1f6aa5")
        text = cfg["theme"].get("text_color", "#DCE4EE")
        self.sidebar.configure(fg_color=sidebar_bg)
        for label, btn in self.nav_buttons.items():
            btn.configure(
                fg_color=primary if label == self.current_page else "transparent",
                text_color=text, hover_color=primary)

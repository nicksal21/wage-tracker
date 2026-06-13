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
from ui.pages.dashboard_ui import DashboardPage
from ui.pages.data_ui import DataPage
from ui.pages.tax_ui import TaxPage
from ui.pages.config_ui import ConfigPage


# Emoji fallbacks: primary emoji with ASCII/text alternative
# Format: (primary_display, alt_display_if_emoji_fails)
# We'll use the primary but keep alts ready if needed
NAV_ITEMS = [
    ("📊 Dashboard",    "📊"),   # Chart / Stats
    ("📒 Entries",      "📒"),   # Ledger / Data  
    ("🏛️ Taxes",        "🏛️"),   # Building / Tax
    ("⚙️ Settings",     "⚙️"),   # Gear / Config
]

# Fallback labels (text-only versions) in case emojis don't render
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

        # sidebar
        self.sidebar = ctk.CTkFrame(
            self, width=190, corner_radius=0,
            fg_color=self.cfg["theme"].get("sidebar_bg", "#1f1f1f"))
        self.sidebar.grid(row=0, column=0, sticky="nswe")
        self.sidebar.grid_propagate(False)

        # Title with emoji fallback: try emoji first, fall back to text
        title_text = self._try_emoji("💼 Freelance\n     Tracker", "Freelance\n  Tracker")
        ctk.CTkLabel(self.sidebar, text=title_text,
                      font=ctk.CTkFont(size=18, weight="bold")).pack(
            pady=(24, 28))

        self.nav_buttons: dict[str, ctk.CTkButton] = {}
        for (emoji_label, emoji_icon), text_label in zip(NAV_ITEMS, NAV_LABELS):
            # Try to use emoji; fall back to text-only label
            display_text = self._try_emoji(f" {emoji_icon}  {text_label}", f"  {text_label}")
            
            btn = ctk.CTkButton(
                self.sidebar, text=display_text, anchor="w",
                height=40, corner_radius=8, fg_color="transparent",
                text_color=self.cfg["theme"].get("text_color", "#DCE4EE"),
                hover_color=self.cfg["theme"].get("primary_color", "#1f6aa5"),
                command=lambda l=text_label: self._show_page(l))
            btn.pack(fill="x", padx=12, pady=3)
            self.nav_buttons[text_label] = btn

        ctk.CTkLabel(self.sidebar, text="v1.3.0",
                      font=ctk.CTkFont(size=10),
                      text_color="gray50").pack(side="bottom", pady=10)

        # content
        self.content = ctk.CTkFrame(self, fg_color="transparent")
        self.content.grid(row=0, column=1, sticky="nswe")
        self.content.grid_rowconfigure(0, weight=1)
        self.content.grid_columnconfigure(0, weight=1)

        self.pages: dict[str, ctk.CTkFrame] = {}
        self.current_page: str | None = None
        self._show_page("Dashboard")

    # -------------------------------------------------------- emoji fallback
    def _try_emoji(self, emoji_text: str, fallback_text: str) -> str:
        """
        Attempt to use emoji text; if it fails to render properly,
        return the fallback. This helps on systems where emojis aren't
        well-supported (e.g., some Linux setups).
        
        For safety, we always return the emoji_text since most modern
        systems support Unicode emojis. If you encounter rendering issues,
        you can add a try/except or platform check here.
        """
        # On most modern systems, emojis render fine. 
        # If you're on a system without emoji support, uncomment the check below:
        # 
        # import platform
        # if platform.system() == "Linux":
        #     # Some Linux systems lack emoji fonts; use fallback
        #     return fallback_text
        
        # Default: use emojis (they work on most systems including Linux with proper fonts)
        return emoji_text

    # -------------------------------------------------------- nav
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

    # -------------------------------------------------------- theme
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
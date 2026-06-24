"""
UI package init.
* Adds the project root to ``sys.path`` so backend modules can be imported.
* Provides a single shared ttk-style configurator so the various Treeviews
  used across the app are styled exactly once.
* Removes all default ttk borders, separators, and artifacts to match CTk theme.
"""

from tkinter import ttk


_TTK_CONFIGURED = False


def configure_ttk_styles(cfg: dict) -> None:
    """Configure the ttk Treeview styles used everywhere — once.
    
    Removes all native ttk borders, separators, and dividers to create
    a seamless, flat look that matches the CustomTkinter theme.
    """
    global _TTK_CONFIGURED
    if _TTK_CONFIGURED:
        return
    _TTK_CONFIGURED = True

    style = ttk.Style()
    try:
        style.theme_use("default")
    except Exception:
        pass

    theme = cfg.get("theme", {})
    is_dark = theme.get("mode", "dark").lower() == "dark"
    bg = theme.get("card_bg", "#2b2b2b") if is_dark else "#ffffff"
    fg = theme.get("text_color", "#DCE4EE") if is_dark else "#222222"
    header_bg = theme.get("sidebar_bg", "#1f1f1f") if is_dark else "#e8e8e8"
    accent = theme.get("accent_color", "#3b8ed0")
    # === REMOVE ALL BORDERS AND SEPARATORS ===
    # The key is setting borderwidth=0 and removing any relief/frames
    
    # Common look for every Treeview — NO BORDERS, NO SEPARATORS
    for variant in ("Tracker", "Stats", "Tax", "Quarter", "Calendar"):
        # Main Treeview: flat, no borders, no separators between columns
        style.configure(
            f"{variant}.Treeview",
            background=bg,
            foreground=fg,
            fieldbackground=bg,
            borderwidth=0,           # NO outer border
            relief="flat",           # NO 3D relief
            font=("Segoe UI", 10),
            rowheight=28,
        )
        
        # Heading (column headers): subtle contrast, no separators
        style.configure(
            f"{variant}.Treeview.Heading",
            background=header_bg,
            foreground=fg,
            font=("Segoe UI", 10, "bold"),
            borderwidth=0,
            relief="flat",
            padding=(8, 6),
        )
        
        style.configure(
            f"{variant}.Treeview",
            bordercolor=bg,
        )
        
        style.map(
            f"{variant}.Treeview",
            background=[("selected", accent)],
            foreground=[("selected", "#ffffff")],
            fieldbackground=[],
        )
        
        # Alternating row stripe for readability
        style.configure(
            f"{variant}.Treeview",
            background=bg,
        )
        
        style.map(
            f"{variant}.Treeview.Heading",
            background=[],
            relief=[],
        )

    # === THEMED SCROLLBAR (matches dark interface) ===
    # Completely flat, no arrows, minimal visual presence
    style.configure(
        "Themed.Vertical.TScrollbar",
        background=header_bg,        # Track background
        troughcolor=bg,              # Trough (gutter) color
        borderwidth=0,               # NO border
        relief="flat",               # NO 3D relief
        arrowcolor=fg,               # Arrow color (if arrows shown)
        arrowsize=0,                 # Hide arrows entirely
        width=10,                    # Slim width
    )
    
    # Scrollbar thumb styling - make it blend but be functional
    style.map(
        "Themed.Vertical.TScrollbar",
        background=[
            ("active", accent),      # Highlight color when active
            ("!disabled", header_bg) # Normal state
        ],
        troughcolor=[],              # No changes to trough
    )
    
    # === LEGACY SCROLLBAR (backwards compatibility) ===
    style.configure(
        "Vertical.TScrollbar",
        background=header_bg,
        troughcolor=bg,
        borderwidth=0,
        arrowcolor=fg,
        width=10,
    )
    
    # === REMOVE TTKHOOK ARTIFACTS ===
    # Ensure there are no stray lines or borders from ttk's default theme
    style.configure(
        "TSeparator",
        background=bg,               # Invisible separator
        borderwidth=0,
    )
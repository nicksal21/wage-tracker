"""Dashboard build helper classes."""

from __future__ import annotations

import tkinter as tk
from tkinter import ttk
from typing import TYPE_CHECKING

import customtkinter as ctk

from ui.styles.layout import (
    PAD_X, GAP, GAP_SM, CTRL_H, emoji_label, font_body, font_small, font_heading,
)

if TYPE_CHECKING:
    from ui.pages.dashboard_ui import DashboardPage


class DashboardToolbar:
    """Dashboard toolbar widget."""
    
    def __init__(self, parent: "DashboardPage"):
        self.parent = parent
        self.frame = ctk.CTkFrame(parent, fg_color="transparent")
        self._build()
    
    def _build(self):
        from ui.components.dashboard_specs import PERIODS

        lbl_kw = dict(font=font_body(12))

        ctk.CTkLabel(self.frame, text="Period:", **lbl_kw).pack(
            side="left", padx=(0, GAP_SM))
        self.period_var = ctk.StringVar(value="Monthly")
        self.period_btn = ctk.CTkSegmentedButton(
            self.frame, values=PERIODS, variable=self.period_var,
            command=self.parent._on_period_change, height=CTRL_H,
        )
        self.period_btn.pack(side="left", padx=(0, GAP))

        self.subperiod_frame = ctk.CTkFrame(self.frame, fg_color="transparent")
        self.subperiod_frame.pack(side="left", padx=(0, GAP))

        self.month_label = ctk.CTkLabel(self.subperiod_frame, text="Month:", **lbl_kw)
        self.month_var = ctk.StringVar(value="")
        self.month_menu = ctk.CTkOptionMenu(
            self.subperiod_frame, variable=self.month_var,
            values=[], command=lambda _: self.parent.refresh(),
            width=120, height=CTRL_H)

        self.quarter_label = ctk.CTkLabel(self.subperiod_frame, text="Quarter:", **lbl_kw)
        self.quarter_var = ctk.StringVar(value="")
        self.quarter_menu = ctk.CTkOptionMenu(
            self.subperiod_frame, variable=self.quarter_var,
            values=[], command=lambda _: self.parent.refresh(),
            width=100, height=CTRL_H)

        self.day_label = ctk.CTkLabel(self.subperiod_frame, text="Day:", **lbl_kw)
        self.day_var = ctk.StringVar(value="")
        self.day_menu = ctk.CTkOptionMenu(
            self.subperiod_frame, variable=self.day_var,
            values=[], command=lambda _: self.parent.refresh(),
            width=120, height=CTRL_H)

        ctk.CTkLabel(self.frame, text="Year:", **lbl_kw).pack(
            side="left", padx=(0, GAP_SM))
        self.year_var = ctk.StringVar(value="All")
        self.year_menu = ctk.CTkOptionMenu(
            self.frame, variable=self.year_var, values=["All"],
            command=self.parent._on_year_change, width=90, height=CTRL_H)
        self.year_menu.pack(side="left", padx=(0, GAP))

        ctk.CTkLabel(self.frame, text="Search:", **lbl_kw).pack(
            side="left", padx=(0, GAP_SM))
        self.search_var = ctk.StringVar()
        self.search_var.trace_add("write", self.parent._on_search_change)
        ctk.CTkEntry(
            self.frame, textvariable=self.search_var, width=180, height=CTRL_H,
            placeholder_text="Task / notes…",
        ).pack(side="left", padx=(0, GAP))

        ctk.CTkLabel(self.frame, text="Mode:", **lbl_kw).pack(
            side="left", padx=(0, GAP_SM))
        self.mode_filt_var = ctk.StringVar(value="All")
        ctk.CTkOptionMenu(
            self.frame, variable=self.mode_filt_var,
            values=["All", "Hourly", "Per Task"],
            command=lambda _: self.parent.refresh(), width=100, height=CTRL_H,
        ).pack(side="left")

        ctk.CTkButton(
            self.frame, text=emoji_label("⟳", "Refresh"), width=42, height=CTRL_H,
            command=lambda: self.parent.refresh(force=True),
        ).pack(side="right")


class DashboardCards:
    """Dashboard cards display widget."""
    
    def __init__(self, parent: "DashboardPage", cfg: dict):
        self.parent = parent
        self.cfg = cfg
        self.frame = ctk.CTkFrame(parent, fg_color="transparent")
        self.value_labels: list[ctk.CTkLabel] = []
        self._build()
    
    def _build(self):
        from ui.components.dashboard_specs import CARDS
        
        for i, (title, _, _) in enumerate(CARDS):
            card = ctk.CTkFrame(
                self.frame, corner_radius=10,
                fg_color=self.cfg["theme"].get("card_bg", "#2b2b2b"))
            card.grid(row=0, column=i, padx=GAP_SM, pady=GAP_SM, sticky="nsew")
            self.frame.grid_columnconfigure(i, weight=1)
            ctk.CTkLabel(
                card, text=title, font=font_small(),
            ).pack(pady=(8, 0), padx=8)
            v = ctk.CTkLabel(
                card, text="—",
                font=font_heading(18),
                text_color=self.cfg["theme"].get("accent_color", "#3b8ed0"))
            v.pack(pady=(0, 8), padx=8)
            self.value_labels.append(v)


class DashboardViewSwitch:
    """Dashboard view switch widget."""
    
    def __init__(self, parent: "DashboardPage"):
        self.parent = parent
        self.frame = ctk.CTkFrame(parent, fg_color="transparent")
        self._build()
    
    def _build(self):
        from ui.components.dashboard_specs import CHARTS
        
        self._view_var = ctk.StringVar(value="Statistics")
        ctk.CTkSegmentedButton(
            self.frame, values=["Statistics", "Graphs"],
            variable=self._view_var, command=self.parent._switch_view,
            height=CTRL_H,
        ).pack(side="left")
        self.chart_var = ctk.StringVar(value=CHARTS[0])
        self.chart_menu = ctk.CTkOptionMenu(
            self.frame, variable=self.chart_var, values=CHARTS,
            command=lambda _: self.parent._draw_chart(force=True),
            width=220, height=CTRL_H)


class DashboardStats:
    """Dashboard statistics treeview widget."""
    
    def __init__(self, parent: "DashboardPage", cfg: dict):
        self.parent = parent
        self.cfg = cfg
        self.holder = tk.Frame(parent, bd=0, highlightthickness=0)
        self.tree = None
        self.stat_iids: dict[str, str] = {}
        self._build()
    
    def _build(self):
        from ui.components.dashboard_specs import STAT_ROWS
        
        self.tree = ttk.Treeview(
            self.holder, columns=("metric", "value"),
            show="headings", style="Stats.Treeview", selectmode="none")
        self.tree.heading("metric", text="Metric", anchor="w")
        self.tree.heading("value",  text="Value",  anchor="e")
        self.tree.column("metric", width=320, anchor="w", stretch=True)
        self.tree.column("value",  width=200, anchor="e", stretch=False)
        accent = self.cfg["theme"].get("accent_color", "#3b8ed0")
        self.tree.tag_configure(
            "header", background="#1a1a1a", foreground=accent,
            font=("Segoe UI", 11, "bold"))
        sb = ttk.Scrollbar(self.holder, orient="vertical",
                            command=self.tree.yview,
                            style="Themed.Vertical.TScrollbar")
        self.tree.configure(yscrollcommand=sb.set)
        sb.pack(side="right", fill="y")
        self.tree.pack(side="left", fill="both", expand=True)
        
        for label, key, _kind in STAT_ROWS:
            if key is None:
                self.tree.insert(
                    "", "end", values=(label, ""), tags=("header",))
            else:
                iid = self.tree.insert(
                    "", "end", values=(f"   {label}", "—"))
                self.stat_iids[key] = iid
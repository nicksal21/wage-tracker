"""Dashboard build helper classes."""

from __future__ import annotations

import tkinter as tk
from tkinter import ttk
from typing import TYPE_CHECKING, Optional

import customtkinter as ctk

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
        
        ctk.CTkLabel(self.frame, text="Period:").pack(side="left", padx=(0, 6))
        self.period_var = ctk.StringVar(value="Monthly")
        self.period_btn = ctk.CTkSegmentedButton(
            self.frame, values=PERIODS, variable=self.period_var,
            command=self.parent._on_period_change,
        )
        self.period_btn.pack(side="left", padx=(0, 12))

        self.subperiod_frame = ctk.CTkFrame(self.frame, fg_color="transparent")
        self.subperiod_frame.pack(side="left", padx=(0, 12))
        
        self.month_label = ctk.CTkLabel(self.subperiod_frame, text="Month:")
        self.month_var = ctk.StringVar(value="")
        self.month_menu = ctk.CTkOptionMenu(
            self.subperiod_frame, variable=self.month_var,
            values=[], command=lambda _: self.parent.refresh(), width=120)
        
        self.quarter_label = ctk.CTkLabel(self.subperiod_frame, text="Quarter:")
        self.quarter_var = ctk.StringVar(value="")
        self.quarter_menu = ctk.CTkOptionMenu(
            self.subperiod_frame, variable=self.quarter_var,
            values=[], command=lambda _: self.parent.refresh(), width=100)
        
        self.day_label = ctk.CTkLabel(self.subperiod_frame, text="Day:")
        self.day_var = ctk.StringVar(value="")
        self.day_menu = ctk.CTkOptionMenu(
            self.subperiod_frame, variable=self.day_var,
            values=[], command=lambda _: self.parent.refresh(), width=120)

        ctk.CTkLabel(self.frame, text="Year:").pack(side="left", padx=(0, 4))
        self.year_var = ctk.StringVar(value="All")
        self.year_menu = ctk.CTkOptionMenu(
            self.frame, variable=self.year_var, values=["All"],
            command=self.parent._on_year_change, width=90)
        self.year_menu.pack(side="left", padx=(0, 12))

        ctk.CTkLabel(self.frame, text="Search:").pack(side="left", padx=(0, 4))
        self.search_var = ctk.StringVar()
        self.search_var.trace_add("write", self.parent._on_search_change)
        ctk.CTkEntry(self.frame, textvariable=self.search_var, width=180,
                      placeholder_text="Task / notes…").pack(
            side="left", padx=(0, 12))

        ctk.CTkLabel(self.frame, text="Mode:").pack(side="left", padx=(0, 4))
        self.mode_filt_var = ctk.StringVar(value="All")
        ctk.CTkOptionMenu(
            self.frame, variable=self.mode_filt_var,
            values=["All", "Hourly", "Per Task"],
            command=lambda _: self.parent.refresh(), width=100,
        ).pack(side="left")

        ctk.CTkButton(self.frame, text="⟳", width=42,
                       command=lambda: self.parent.refresh(force=True)).pack(side="right")


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
            card.grid(row=0, column=i, padx=4, pady=2, sticky="nsew")
            self.frame.grid_columnconfigure(i, weight=1)
            ctk.CTkLabel(card, text=title,
                          font=ctk.CTkFont(size=11)).pack(pady=(6, 0))
            v = ctk.CTkLabel(
                card, text="—",
                font=ctk.CTkFont(size=18, weight="bold"),
                text_color=self.cfg["theme"].get("accent_color", "#3b8ed0"))
            v.pack(pady=(0, 6))
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
        ).pack(side="left")
        self.chart_var = ctk.StringVar(value=CHARTS[0])
        self.chart_menu = ctk.CTkOptionMenu(
            self.frame, variable=self.chart_var, values=CHARTS,
            command=lambda _: self.parent._draw_chart(force=True), width=220)


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
        self.tree.column("metric", width=320, anchor="w")
        self.tree.column("value",  width=200, anchor="e")
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
"""Dashboard build helper classes."""

from __future__ import annotations

import tkinter as tk
from tkinter import ttk
from typing import TYPE_CHECKING

import customtkinter as ctk

from ui.styles.design import (
    CARD_PAD, INNER_PAD, ITEM_GAP, RADIUS_BTN,
    make_panel, make_tree_holder,
    section_label, refresh_button,
    font_caption, font_metric, theme_colors,
)

if TYPE_CHECKING:
    from ui.pages.dashboard_ui import DashboardPage


class DashboardToolbar:
    """Dashboard toolbar widget."""

    def __init__(self, parent: "DashboardPage"):
        self.parent = parent
        self.cfg = parent.cfg
        self.frame = make_panel(parent, self.cfg)
        self._inner = ctk.CTkFrame(self.frame, fg_color="transparent")
        self._inner.pack(fill="x", padx=CARD_PAD, pady=INNER_PAD)
        self._build()

    def _build(self):
        from ui.components.dashboard_specs import PERIODS

        row1 = ctk.CTkFrame(self._inner, fg_color="transparent")
        row1.pack(fill="x", pady=(0, ITEM_GAP))

        section_label(row1, "Period").pack(side="left", padx=(0, 8))
        self.period_var = ctk.StringVar(value="Monthly")
        self.period_btn = ctk.CTkSegmentedButton(
            row1, values=PERIODS, variable=self.period_var,
            command=self.parent._on_period_change, height=32,
        )
        self.period_btn.pack(side="left", padx=(0, 16))

        self.subperiod_frame = ctk.CTkFrame(row1, fg_color="transparent")
        self.subperiod_frame.pack(side="left", padx=(0, 16))

        self.month_label = section_label(self.subperiod_frame, "Month")
        self.month_var = ctk.StringVar(value="")
        self.month_menu = ctk.CTkOptionMenu(
            self.subperiod_frame, variable=self.month_var,
            values=[], command=lambda _: self.parent.refresh(), width=130, height=32)

        self.quarter_label = section_label(self.subperiod_frame, "Quarter")
        self.quarter_var = ctk.StringVar(value="")
        self.quarter_menu = ctk.CTkOptionMenu(
            self.subperiod_frame, variable=self.quarter_var,
            values=[], command=lambda _: self.parent.refresh(), width=100, height=32)

        self.day_label = section_label(self.subperiod_frame, "Day")
        self.day_var = ctk.StringVar(value="")
        self.day_menu = ctk.CTkOptionMenu(
            self.subperiod_frame, variable=self.day_var,
            values=[], command=lambda _: self.parent.refresh(), width=130, height=32)

        section_label(row1, "Year").pack(side="left", padx=(0, 8))
        self.year_var = ctk.StringVar(value="All")
        self.year_menu = ctk.CTkOptionMenu(
            row1, variable=self.year_var, values=["All"],
            command=self.parent._on_year_change, width=90, height=32)
        self.year_menu.pack(side="left")

        row2 = ctk.CTkFrame(self._inner, fg_color="transparent")
        row2.pack(fill="x")

        section_label(row2, "Search").pack(side="left", padx=(0, 8))
        self.search_var = ctk.StringVar()
        self.search_var.trace_add("write", self.parent._on_search_change)
        ctk.CTkEntry(
            row2, textvariable=self.search_var, width=200, height=32,
            placeholder_text="Task / notes…",
        ).pack(side="left", padx=(0, 16))

        section_label(row2, "Mode").pack(side="left", padx=(0, 8))
        self.mode_filt_var = ctk.StringVar(value="All")
        ctk.CTkOptionMenu(
            row2, variable=self.mode_filt_var,
            values=["All", "Hourly", "Per Task"],
            command=lambda _: self.parent.refresh(), width=110, height=32,
        ).pack(side="left")

        refresh_button(
            row2, command=lambda: self.parent.refresh(force=True),
        ).pack(side="right")


class DashboardCards:
    """Dashboard summary metric cards."""

    def __init__(self, parent: "DashboardPage", cfg: dict):
        self.parent = parent
        self.cfg = cfg
        self.colors = theme_colors(cfg)
        self.frame = ctk.CTkFrame(parent, fg_color="transparent")
        self.value_labels: list[ctk.CTkLabel] = []
        self._build()

    def _build(self):
        from ui.components.dashboard_specs import CARDS

        for i, (title, _, _) in enumerate(CARDS):
            card = ctk.CTkFrame(
                self.frame, corner_radius=12,
                fg_color=self.colors["card_bg"],
                border_width=1, border_color=self.colors["border"],
            )
            card.grid(row=0, column=i, padx=4, pady=2, sticky="nsew")
            self.frame.grid_columnconfigure(i, weight=1)

            accent_bar = ctk.CTkFrame(
                card, height=3, corner_radius=0,
                fg_color=self.colors["accent"],
            )
            accent_bar.pack(fill="x")

            inner = ctk.CTkFrame(card, fg_color="transparent")
            inner.pack(fill="both", expand=True, padx=14, pady=(10, 12))

            ctk.CTkLabel(
                inner, text=title.upper(),
                font=font_caption(), text_color=self.colors["muted"],
            ).pack(anchor="w")
            v = ctk.CTkLabel(
                inner, text="—", font=font_metric(),
                text_color=self.colors["accent"],
            )
            v.pack(anchor="w", pady=(4, 0))
            self.value_labels.append(v)


class DashboardViewSwitch:
    """Dashboard view switch widget."""

    def __init__(self, parent: "DashboardPage"):
        self.parent = parent
        self.cfg = parent.cfg
        self.frame = ctk.CTkFrame(parent, fg_color="transparent")
        self._build()

    def _build(self):
        from ui.components.dashboard_specs import CHARTS

        self._view_var = ctk.StringVar(value="Statistics")
        ctk.CTkSegmentedButton(
            self.frame, values=["Statistics", "Graphs"],
            variable=self._view_var, command=self.parent._switch_view,
            height=32,
        ).pack(side="left")
        self.chart_var = ctk.StringVar(value=CHARTS[0])
        self.chart_menu = ctk.CTkOptionMenu(
            self.frame, variable=self.chart_var, values=CHARTS,
            command=lambda _: self.parent._draw_chart(force=True),
            width=220, height=32)


class DashboardStats:
    """Dashboard statistics treeview widget."""

    def __init__(self, parent: "DashboardPage", cfg: dict):
        self.parent = parent
        self.cfg = cfg
        self.holder, inner = make_tree_holder(parent, cfg)
        self.tree = None
        self.stat_iids: dict[str, str] = {}
        self._build(inner)

    def _build(self, inner: tk.Frame):
        from ui.components.dashboard_specs import STAT_ROWS

        colors = theme_colors(self.cfg)
        self.tree = ttk.Treeview(
            inner, columns=("metric", "value"),
            show="headings", style="Stats.Treeview", selectmode="none")
        self.tree.heading("metric", text="Metric", anchor="w")
        self.tree.heading("value",  text="Value",  anchor="e")
        self.tree.column("metric", width=320, anchor="w", stretch=True)
        self.tree.column("value",  width=200, anchor="e", stretch=False)
        accent = colors["accent"]
        self.tree.tag_configure(
            "header", background=colors["surface"], foreground=accent,
            font=("Segoe UI", 11, "bold"))
        sb = ttk.Scrollbar(inner, orient="vertical",
                           command=self.tree.yview,
                           style="Themed.Vertical.TScrollbar")
        self.tree.configure(yscrollcommand=sb.set)
        sb.pack(side="right", fill="y", padx=(0, 4), pady=4)
        self.tree.pack(side="left", fill="both", expand=True, padx=(4, 0), pady=4)

        for label, key, _kind in STAT_ROWS:
            if key is None:
                self.tree.insert("", "end", values=(label, ""), tags=("header",))
            else:
                iid = self.tree.insert("", "end", values=(f"   {label}", "—"))
                self.stat_iids[key] = iid

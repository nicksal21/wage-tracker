"""Dashboard build helper classes."""

from __future__ import annotations

import tkinter as tk
from tkinter import ttk
from typing import TYPE_CHECKING

import customtkinter as ctk

from ui.styles.layout import (
    PAD_X, GAP, GAP_SM, CTRL_H,
    font_body, font_small, font_heading, font_caption,
    muted_color, card_bg, subtle_card,
)

if TYPE_CHECKING:
    from ui.pages.dashboard_ui import DashboardPage

# Inner padding for grouped panels
CARD_INNER = 8


class DashboardToolbar:
    """Dashboard toolbar widget."""

    def __init__(self, parent: "DashboardPage"):
        self.parent = parent
        self.cfg = parent.cfg
        self.frame = ctk.CTkFrame(
            parent, fg_color=card_bg(self.cfg),
            corner_radius=10, border_width=1,
            border_color="#3d3d3d",
        )
        self.frame.grid_propagate(True)
        self._build()

    def _build(self):
        from ui.components.dashboard_specs import PERIODS

        lbl_kw = dict(font=font_body(12))
        bar = ctk.CTkFrame(self.frame, fg_color="transparent")
        bar.grid(row=0, column=0, sticky="ew", padx=CARD_INNER, pady=CARD_INNER)
        self.frame.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(bar, text="Period:", **lbl_kw).pack(
            side="left", padx=(0, GAP_SM))
        self.period_var = ctk.StringVar(value="Monthly")
        self.period_btn = ctk.CTkSegmentedButton(
            bar, values=PERIODS, variable=self.period_var,
            command=self.parent._on_period_change, height=CTRL_H,
        )
        self.period_btn.pack(side="left", padx=(0, GAP))

        self.subperiod_frame = ctk.CTkFrame(bar, fg_color="transparent")
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

        ctk.CTkLabel(bar, text="Year:", **lbl_kw).pack(
            side="left", padx=(0, GAP_SM))
        self.year_var = ctk.StringVar(value="All")
        self.year_menu = ctk.CTkOptionMenu(
            bar, variable=self.year_var, values=["All"],
            command=self.parent._on_year_change, width=90, height=CTRL_H)
        self.year_menu.pack(side="left", padx=(0, GAP))

        ctk.CTkLabel(bar, text="Search:", **lbl_kw).pack(
            side="left", padx=(0, GAP_SM))
        self.search_var = ctk.StringVar()
        self.search_var.trace_add("write", self.parent._on_search_change)
        ctk.CTkEntry(
            bar, textvariable=self.search_var, width=160, height=CTRL_H,
            placeholder_text="Task / notes…",
        ).pack(side="left", padx=(0, GAP))

        ctk.CTkLabel(bar, text="Mode:", **lbl_kw).pack(
            side="left", padx=(0, GAP_SM))
        self.mode_filt_var = ctk.StringVar(value="All")
        ctk.CTkOptionMenu(
            bar, variable=self.mode_filt_var,
            values=["All", "Hourly", "Per Task"],
            command=lambda _: self.parent.refresh(), width=100, height=CTRL_H,
        ).pack(side="left")

        ctk.CTkButton(
            bar, text="Refresh", width=80, height=CTRL_H,
            command=lambda: self.parent.refresh(force=True),
        ).pack(side="right", padx=(GAP, 0))


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

        accent = self.cfg["theme"].get("accent_color", "#3b8ed0")
        muted = muted_color(self.cfg)

        for i, (title, _, _) in enumerate(CARDS):
            card = subtle_card(self.frame, self.cfg)
            card.grid(row=0, column=i, padx=GAP_SM, pady=GAP_SM, sticky="nsew")
            self.frame.grid_columnconfigure(i, weight=1, uniform="metric")

            inner = ctk.CTkFrame(card, fg_color="transparent")
            inner.pack(fill="both", expand=True, padx=12, pady=10)

            ctk.CTkLabel(
                inner, text=title.upper(), font=font_caption(),
                text_color=muted, anchor="center",
            ).pack(fill="x")
            v = ctk.CTkLabel(
                inner, text="—", font=font_heading(20),
                text_color=accent, anchor="center",
            )
            v.pack(fill="x", pady=(4, 0))
            self.value_labels.append(v)


class DashboardViewSwitch:
    """Dashboard view switch widget."""

    def __init__(self, parent: "DashboardPage"):
        self.parent = parent
        self.frame = ctk.CTkFrame(parent, fg_color="transparent")
        self._build()

    def _build(self):
        from ui.components.dashboard_specs import CHARTS

        ctk.CTkLabel(
            self.frame, text="View", font=font_small(),
            text_color=muted_color(self.parent.cfg),
        ).pack(side="left", padx=(0, GAP_SM))

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
        bg = card_bg(cfg)
        self.frame = subtle_card(parent, cfg)
        self.holder = tk.Frame(self.frame, bd=0, highlightthickness=0, bg=bg)
        self.holder.pack(fill="both", expand=True, padx=6, pady=6)
        self.tree = None
        self.stat_iids: dict[str, str] = {}
        self._build()

    def _build(self):
        from ui.components.dashboard_specs import STAT_ROWS

        theme = self.cfg.get("theme", {})
        accent = theme.get("accent_color", "#3b8ed0")
        header_bg = theme.get("sidebar_bg", "#1f1f1f")
        text = theme.get("text_color", "#DCE4EE")

        self.tree = ttk.Treeview(
            self.holder, columns=("metric", "value"),
            show="headings", style="Stats.Treeview", selectmode="none")
        self.tree.heading("metric", text="Metric", anchor="w")
        self.tree.heading("value",  text="Value",  anchor="e")
        self.tree.column("metric", width=320, anchor="w", stretch=True)
        self.tree.column("value",  width=200, anchor="e", stretch=False)
        self.tree.tag_configure(
            "header", background=header_bg, foreground=text,
            font=("Segoe UI", 10, "bold"))
        self.tree.tag_configure(
            "section", background=header_bg, foreground=accent,
            font=("Segoe UI", 10, "bold"))

        sb = ttk.Scrollbar(self.holder, orient="vertical",
                           command=self.tree.yview,
                           style="Themed.Vertical.TScrollbar")
        self.tree.configure(yscrollcommand=sb.set)
        sb.pack(side="right", fill="y", padx=(0, 2), pady=2)
        self.tree.pack(side="left", fill="both", expand=True, padx=(2, 0), pady=2)

        for label, key, _kind in STAT_ROWS:
            if key is None:
                self.tree.insert(
                    "", "end", values=(f"  {label.upper()}", ""), tags=("section",))
            else:
                iid = self.tree.insert(
                    "", "end", values=(f"    {label}", "—"))
                self.stat_iids[key] = iid

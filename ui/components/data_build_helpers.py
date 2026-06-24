"""Data page build helper classes."""

from __future__ import annotations

import tkinter
from datetime import datetime, date
from tkinter import ttk
from typing import TYPE_CHECKING, Optional, Callable

import customtkinter as ctk

from ui.widgets.calendar_popup import CalendarPopup
from ui.styles.design import (
    CARD_PAD, INNER_PAD, ITEM_GAP, RADIUS_BTN,
    make_panel, make_tree_holder,
    section_label, refresh_button, danger_button, primary_button,
    font_section, font_caption, theme_colors,
)

if TYPE_CHECKING:
    from ui.pages.data_ui import DataPage


class DataToolbar:
    """Data page toolbar widget."""

    def __init__(self, parent, import_cmd, export_cmd, recalc_cmd, clear_cmd, refresh_cmd):
        self.cfg = parent.cfg if hasattr(parent, "cfg") else {}
        self.frame = make_panel(parent, self.cfg)
        inner = ctk.CTkFrame(self.frame, fg_color="transparent")
        inner.pack(fill="x", padx=CARD_PAD, pady=INNER_PAD)

        for txt, cmd, kw in (
            ("Import",   import_cmd,      {}),
            ("Export",   export_cmd,       {}),
            ("Recalc",   recalc_cmd,       {}),
            ("Clear All", clear_cmd,
             {"fg_color": "#dc3545", "hover_color": "#a71d2a"}),
        ):
            ctk.CTkButton(
                inner, text=txt, width=110, height=32,
                corner_radius=RADIUS_BTN, command=cmd, **kw,
            ).pack(side="left", padx=(0, ITEM_GAP))
        refresh_button(inner, command=refresh_cmd).pack(side="right")


class DataForm:
    """Data entry form widget."""

    def __init__(self, parent: "DataPage", cfg: dict, mode_var: ctk.StringVar,
                 on_mode_toggle: Callable[[str], None]):
        self.parent = parent
        self.cfg = cfg
        self.colors = theme_colors(cfg)
        self.mode_var = mode_var
        self.frame = make_panel(parent, cfg)

        self.task_entry: Optional[ctk.CTkEntry] = None
        self.date_entry: Optional[ctk.CTkEntry] = None
        self.start_entry: Optional[ctk.CTkEntry] = None
        self.end_entry: Optional[ctk.CTkEntry] = None
        self.qty_entry: Optional[ctk.CTkEntry] = None
        self.rate_entry: Optional[ctk.CTkEntry] = None
        self.notes_entry: Optional[ctk.CTkEntry] = None
        self.adjust_entry: Optional[ctk.CTkEntry] = None
        self.adjust_reason: Optional[ctk.CTkEntry] = None
        self.hourly_row: Optional[ctk.CTkFrame] = None
        self.task_row: Optional[ctk.CTkFrame] = None
        self.adjust_row: Optional[ctk.CTkFrame] = None
        self.rate_label: Optional[ctk.CTkLabel] = None
        self.save_btn: Optional[ctk.CTkButton] = None
        self.cancel_btn: Optional[ctk.CTkButton] = None
        self.form_status: Optional[ctk.CTkLabel] = None

        self._on_mode_toggle = on_mode_toggle
        self._body = ctk.CTkFrame(self.frame, fg_color="transparent")
        self._body.pack(fill="x", padx=CARD_PAD, pady=(CARD_PAD, CARD_PAD))
        self._build()

    def _build(self):
        ctk.CTkLabel(
            self._body, text="Entry Form", font=font_section(),
            text_color=self.colors["text"],
        ).grid(row=0, column=0, columnspan=6, sticky="w", pady=(0, INNER_PAD))

        for c in (1, 4):
            self._body.grid_columnconfigure(c, weight=1)

        section_label(self._body, "Mode").grid(
            row=1, column=0, padx=(0, 8), pady=(0, ITEM_GAP), sticky="w")
        ctk.CTkSegmentedButton(
            self._body, values=["hourly", "per_task"], variable=self.mode_var,
            command=self._on_mode_toggle, height=32,
        ).grid(row=1, column=1, columnspan=5, pady=(0, ITEM_GAP), sticky="w")

        section_label(self._body, "Task").grid(
            row=2, column=0, padx=(0, 8), pady=4, sticky="w")
        self.task_entry = ctk.CTkEntry(
            self._body, placeholder_text="e.g. Article writing", height=32)
        self.task_entry.grid(row=2, column=1, columnspan=2,
                             padx=(0, 12), pady=4, sticky="ew")

        section_label(self._body, "Date").grid(
            row=2, column=3, padx=(0, 8), pady=4, sticky="w")
        date_box = ctk.CTkFrame(self._body, fg_color="transparent")
        date_box.grid(row=2, column=4, columnspan=2, pady=4, sticky="w")
        self.date_entry = ctk.CTkEntry(
            date_box, width=110, height=32, placeholder_text="MM/DD/YY")
        self.date_entry.pack(side="left", padx=(0, 4))

        def open_calendar():
            CalendarPopup(self.parent, self.date_entry)

        def fill_today():
            self.date_entry.delete(0, "end")
            self.date_entry.insert(0, date.today().strftime("%m/%d/%y"))

        ctk.CTkButton(
            date_box, text="📅", width=34, height=32,
            corner_radius=RADIUS_BTN, command=open_calendar,
        ).pack(side="left", padx=(0, 4))
        ctk.CTkButton(
            date_box, text="Today", width=58, height=32,
            corner_radius=RADIUS_BTN, command=fill_today,
        ).pack(side="left")

        self.hourly_row = ctk.CTkFrame(self._body, fg_color="transparent")
        self.hourly_row.grid(row=3, column=0, columnspan=6, sticky="ew", pady=4)
        section_label(self.hourly_row, "Start").pack(side="left", padx=(0, 8))
        self.start_entry = ctk.CTkEntry(
            self.hourly_row, width=120, height=32, placeholder_text="HH:MM AM/PM")
        self.start_entry.pack(side="left", padx=(0, 4))

        def fill_now(entry):
            entry.delete(0, "end")
            entry.insert(0, datetime.now().strftime("%I:%M %p").lstrip("0"))

        ctk.CTkButton(
            self.hourly_row, text="Now", width=48, height=32,
            corner_radius=RADIUS_BTN,
            command=lambda: fill_now(self.start_entry),
        ).pack(side="left", padx=(0, 18))
        section_label(self.hourly_row, "End").pack(side="left", padx=(0, 8))
        self.end_entry = ctk.CTkEntry(
            self.hourly_row, width=120, height=32, placeholder_text="HH:MM AM/PM")
        self.end_entry.pack(side="left", padx=(0, 4))
        ctk.CTkButton(
            self.hourly_row, text="Now", width=48, height=32,
            corner_radius=RADIUS_BTN,
            command=lambda: fill_now(self.end_entry),
        ).pack(side="left")

        self.task_row = ctk.CTkFrame(self._body, fg_color="transparent")
        section_label(self.task_row, "# Tasks").pack(side="left", padx=(0, 8))
        self.qty_entry = ctk.CTkEntry(
            self.task_row, width=100, height=32, placeholder_text="e.g. 5")
        self.qty_entry.pack(side="left")

        self.rate_label = section_label(self._body, "Rate ($/hr)")
        self.rate_label.grid(row=4, column=0, padx=(0, 8), pady=4, sticky="w")
        self.rate_entry = ctk.CTkEntry(
            self._body, width=120, height=32, placeholder_text="0.00")
        dr = self.cfg["general"].get("default_rate", 0)
        if dr:
            self.rate_entry.insert(0, str(dr))
        self.rate_entry.grid(row=4, column=1, pady=4, sticky="w")

        section_label(self._body, "Notes").grid(
            row=4, column=3, padx=(0, 8), pady=4, sticky="w")
        self.notes_entry = ctk.CTkEntry(
            self._body, placeholder_text="Optional notes", height=32)
        self.notes_entry.grid(row=4, column=4, columnspan=2, pady=4, sticky="ew")

        self.adjust_row = ctk.CTkFrame(self._body, fg_color="transparent")
        self.adjust_row.grid(row=5, column=0, columnspan=6, sticky="ew", pady=4)
        section_label(self.adjust_row, "Time Adjust (min)").pack(side="left", padx=(0, 8))
        self.adjust_entry = ctk.CTkEntry(
            self.adjust_row, width=80, height=32, placeholder_text="e.g. -20")
        self.adjust_entry.pack(side="left", padx=(0, 12))
        section_label(self.adjust_row, "Reason").pack(side="left", padx=(0, 8))
        self.adjust_reason = ctk.CTkEntry(
            self.adjust_row, height=32, placeholder_text="e.g. lunch break")
        self.adjust_reason.pack(side="left", fill="x", expand=True)

        btn_row = ctk.CTkFrame(self._body, fg_color="transparent")
        btn_row.grid(row=6, column=0, columnspan=6, pady=(INNER_PAD, 0), sticky="w")
        self.save_btn = primary_button(btn_row, text="Add Entry", width=130)
        self.save_btn.pack(side="left", padx=(0, ITEM_GAP))
        self.cancel_btn = ctk.CTkButton(
            btn_row, text="Cancel Edit", width=120, height=34,
            corner_radius=RADIUS_BTN, fg_color="gray40")
        self.cancel_btn.pack(side="left")
        self.form_status = ctk.CTkLabel(
            btn_row, text="", text_color=self.colors["success"],
            font=font_caption())
        self.form_status.pack(side="left", padx=(16, 0))


class DataSearchBar:
    """Data page search and filter bar."""

    def __init__(self, parent, search_var: ctk.StringVar, mode_var: ctk.StringVar,
                 year_var: ctk.StringVar, year_menu, on_search_change, on_refresh):
        cfg = parent.cfg if hasattr(parent, "cfg") else {}
        self.frame = make_panel(parent, cfg)
        inner = ctk.CTkFrame(self.frame, fg_color="transparent")
        inner.pack(fill="x", padx=CARD_PAD, pady=INNER_PAD)

        ctk.CTkEntry(
            inner, textvariable=search_var, width=240, height=32,
            placeholder_text="Search task, notes, date…",
        ).pack(side="left", padx=(0, 16))

        section_label(inner, "Mode").pack(side="left", padx=(0, 8))
        ctk.CTkOptionMenu(
            inner, variable=mode_var,
            values=["All", "Hourly", "Per Task"],
            command=lambda _: on_refresh(), width=110, height=32,
        ).pack(side="left", padx=(0, 16))

        section_label(inner, "Year").pack(side="left", padx=(0, 8))
        year_menu.configure(height=32)
        year_menu.pack(in_=inner, side="left")


class DataTable:
    """Data table treeview widget."""

    def __init__(self, parent, on_click: Callable, cfg: dict | None = None):
        cfg = cfg or {}
        self.holder, inner = make_tree_holder(parent, cfg)
        self.tree = None
        self._build(inner, on_click)

    def _build(self, inner: tkinter.Frame, on_click: Callable):
        cols = ("id", "task", "date", "start", "end", "minutes",
                "rate", "total", "time_fmt", "mode", "notes")
        self.tree = ttk.Treeview(inner, columns=cols, show="headings",
                                 style="Tracker.Treeview",
                                 selectmode="browse")
        headings = {
            "id": ("ID", 40), "task": ("Task Name", 160),
            "date": ("Date", 80), "start": ("Start", 100),
            "end": ("End", 100), "minutes": ("Min/Qty", 65),
            "rate": ("Rate", 70), "total": ("Total", 80),
            "time_fmt": ("Time (H+M)", 140), "mode": ("Mode", 65),
            "notes": ("Notes", 120),
        }
        for col, (heading, width) in headings.items():
            self.tree.heading(col, text=heading)
            self.tree.column(col, width=width, minwidth=40, stretch=(col == "task"))
        scroll = ttk.Scrollbar(inner, orient="vertical",
                               command=self.tree.yview,
                               style="Themed.Vertical.TScrollbar")
        self.tree.configure(yscrollcommand=scroll.set)
        scroll.pack(side="right", fill="y", padx=(0, 4), pady=4)
        self.tree.pack(side="left", fill="both", expand=True, padx=(4, 0), pady=4)
        self.tree.bind("<Button-1>", on_click)


class DataPagination:
    """Data page pagination widget."""

    def __init__(self, parent, prev_cmd, next_cmd, page_size_var,
                 on_page_size_change, delete_cmd, edit_cmd):
        from ui.components.dashboard_specs import PAGE_SIZES

        cfg = parent.cfg if hasattr(parent, "cfg") else {}
        self.frame = ctk.CTkFrame(parent, fg_color="transparent")
        nav = ctk.CTkFrame(self.frame, fg_color="transparent")
        nav.pack(side="left")

        ctk.CTkButton(
            nav, text="◀", width=40, height=32,
            corner_radius=RADIUS_BTN, command=prev_cmd,
        ).pack(side="left", padx=(0, 4))
        self.pag_label = ctk.CTkLabel(nav, text="—", font=font_caption())
        self.pag_label.pack(side="left", padx=8)
        ctk.CTkButton(
            nav, text="▶", width=40, height=32,
            corner_radius=RADIUS_BTN, command=next_cmd,
        ).pack(side="left")

        section_label(self.frame, "Rows").pack(side="left", padx=(20, 8))
        ctk.CTkOptionMenu(
            self.frame, variable=page_size_var,
            values=PAGE_SIZES, command=on_page_size_change,
            width=80, height=32,
        ).pack(side="left")

        actions = ctk.CTkFrame(self.frame, fg_color="transparent")
        actions.pack(side="right")
        ctk.CTkButton(
            actions, text="Edit Selected", width=120, height=32,
            corner_radius=RADIUS_BTN, command=edit_cmd,
        ).pack(side="right", padx=(ITEM_GAP, 0))
        danger_button(actions, text="Delete Selected", width=130,
                      command=delete_cmd).pack(side="right")

"""Data page build helper classes."""

from __future__ import annotations

import tkinter
from datetime import datetime, date
from tkinter import ttk
from typing import TYPE_CHECKING, Optional, Callable

import customtkinter as ctk

from ui.widgets.calendar_popup import CalendarPopup
from ui.styles.layout import (
    PAD_X, GAP, GAP_SM, CTRL_H, BTN_H, emoji_label,
    font_body, font_heading, font_small,
)

if TYPE_CHECKING:
    from ui.pages.data_ui import DataPage


class DataToolbar:
    """Data page toolbar widget."""
    
    def __init__(self, parent, import_cmd, export_cmd, recalc_cmd, clear_cmd, refresh_cmd):
        self.frame = ctk.CTkFrame(parent, fg_color="transparent")
        for txt, cmd, kw in (
            (emoji_label("📥 Import", "Import"),   import_cmd,      {}),
            (emoji_label("📤 Export", "Export"),   export_cmd,       {}),
            (emoji_label("🔄 Recalc", "Recalc"),   recalc_cmd,  {}),
            (emoji_label("🗑 Clear All", "Clear All"), clear_cmd,
             {"fg_color": "#dc3545", "hover_color": "#a71d2a"}),
        ):
            ctk.CTkButton(
                self.frame, text=txt, width=120, height=BTN_H, command=cmd, **kw,
            ).pack(side="left", padx=(0, GAP))
        ctk.CTkButton(
            self.frame, text=emoji_label("⟳", "Refresh"), width=42, height=CTRL_H,
            command=refresh_cmd,
        ).pack(side="right")


class DataForm:
    """Data entry form widget."""
    
    def __init__(self, parent: "DataPage", cfg: dict, mode_var: ctk.StringVar, 
                 on_mode_toggle: Callable[[str], None]):
        self.parent = parent
        self.cfg = cfg
        self.mode_var = mode_var
        self.frame = ctk.CTkFrame(parent, corner_radius=10)
        
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
        self._build()
    
    def _build(self):
        for c in (1, 4):
            self.frame.grid_columnconfigure(c, weight=1)

        lbl = dict(font=font_body(12))
        px, py = PAD_X, GAP_SM

        ctk.CTkLabel(self.frame, text="Mode:", font=font_heading(12)).grid(
            row=0, column=0, padx=px, pady=(px, py), sticky="w")
        ctk.CTkSegmentedButton(
            self.frame, values=["hourly", "per_task"], variable=self.mode_var,
            command=self._on_mode_toggle, height=CTRL_H,
        ).grid(row=0, column=1, columnspan=5, padx=(0, px),
               pady=(px, py), sticky="w")

        ctk.CTkLabel(self.frame, text="Task:", **lbl).grid(
            row=1, column=0, padx=px, pady=py, sticky="w")
        self.task_entry = ctk.CTkEntry(
            self.frame, placeholder_text="e.g. Article writing", height=CTRL_H)
        self.task_entry.grid(row=1, column=1, columnspan=2,
                             padx=(0, GAP), pady=py, sticky="ew")

        ctk.CTkLabel(self.frame, text="Date:", **lbl).grid(
            row=1, column=3, padx=(0, GAP_SM), pady=py, sticky="w")
        date_box = ctk.CTkFrame(self.frame, fg_color="transparent")
        date_box.grid(row=1, column=4, columnspan=2,
                       padx=(0, px), pady=py, sticky="w")
        self.date_entry = ctk.CTkEntry(
            date_box, width=110, height=CTRL_H, placeholder_text="MM/DD/YY")
        self.date_entry.pack(side="left", padx=(0, GAP_SM))

        def open_calendar():
            CalendarPopup(self.parent, self.date_entry)

        def fill_today():
            self.date_entry.delete(0, "end")
            self.date_entry.insert(0, date.today().strftime("%m/%d/%y"))

        ctk.CTkButton(
            date_box, text=emoji_label("📅", "Cal"), width=34, height=CTRL_H,
            command=open_calendar,
        ).pack(side="left", padx=(0, GAP_SM))
        ctk.CTkButton(
            date_box, text="Today", width=58, height=CTRL_H,
            command=fill_today,
        ).pack(side="left")

        self.hourly_row = ctk.CTkFrame(self.frame, fg_color="transparent")
        self.hourly_row.grid(row=2, column=0, columnspan=6,
                              sticky="ew", padx=px, pady=py)
        ctk.CTkLabel(self.hourly_row, text="Start:", width=60, **lbl).pack(side="left")
        self.start_entry = ctk.CTkEntry(
            self.hourly_row, width=120, height=CTRL_H,
            placeholder_text="HH:MM AM/PM")
        self.start_entry.pack(side="left", padx=(0, GAP_SM))

        def fill_now(entry):
            entry.delete(0, "end")
            entry.insert(0, datetime.now().strftime("%I:%M %p").lstrip("0"))

        ctk.CTkButton(
            self.hourly_row, text="Now", width=42, height=CTRL_H,
            command=lambda: fill_now(self.start_entry),
        ).pack(side="left", padx=(0, 18))
        ctk.CTkLabel(self.hourly_row, text="End:", width=50, **lbl).pack(side="left")
        self.end_entry = ctk.CTkEntry(
            self.hourly_row, width=120, height=CTRL_H,
            placeholder_text="HH:MM AM/PM")
        self.end_entry.pack(side="left", padx=(0, GAP_SM))
        ctk.CTkButton(
            self.hourly_row, text="Now", width=42, height=CTRL_H,
            command=lambda: fill_now(self.end_entry),
        ).pack(side="left")

        self.task_row = ctk.CTkFrame(self.frame, fg_color="transparent")
        ctk.CTkLabel(self.task_row, text="# Tasks:", width=80, **lbl).pack(side="left")
        self.qty_entry = ctk.CTkEntry(
            self.task_row, width=100, height=CTRL_H, placeholder_text="e.g. 5")
        self.qty_entry.pack(side="left")

        self.rate_label = ctk.CTkLabel(self.frame, text="Rate ($/hr):", **lbl)
        self.rate_label.grid(row=3, column=0, padx=px, pady=py, sticky="w")
        self.rate_entry = ctk.CTkEntry(
            self.frame, width=120, height=CTRL_H, placeholder_text="0.00")
        dr = self.cfg["general"].get("default_rate", 0)
        if dr:
            self.rate_entry.insert(0, str(dr))
        self.rate_entry.grid(row=3, column=1, pady=py, sticky="w")

        ctk.CTkLabel(self.frame, text="Notes:", **lbl).grid(
            row=3, column=3, padx=(0, GAP_SM), pady=py, sticky="w")
        self.notes_entry = ctk.CTkEntry(
            self.frame, placeholder_text="Optional notes", height=CTRL_H)
        self.notes_entry.grid(row=3, column=4, columnspan=2,
                               padx=(0, px), pady=py, sticky="ew")

        self.adjust_row = ctk.CTkFrame(self.frame, fg_color="transparent")
        self.adjust_row.grid(row=4, column=0, columnspan=6,
                              sticky="ew", padx=px, pady=py)
        ctk.CTkLabel(self.adjust_row, text="Time Adjust (min):", **lbl).pack(side="left")
        self.adjust_entry = ctk.CTkEntry(
            self.adjust_row, width=80, height=CTRL_H, placeholder_text="e.g. -20")
        self.adjust_entry.pack(side="left", padx=(GAP_SM, GAP))
        ctk.CTkLabel(self.adjust_row, text="Reason:", **lbl).pack(side="left")
        self.adjust_reason = ctk.CTkEntry(
            self.adjust_row, height=CTRL_H, placeholder_text="e.g. lunch break")
        self.adjust_reason.pack(side="left", fill="x", expand=True, padx=(GAP_SM, 0))

        btn_row = ctk.CTkFrame(self.frame, fg_color="transparent")
        btn_row.grid(row=5, column=0, columnspan=6,
                       padx=px, pady=(GAP, px), sticky="w")
        self.save_btn = ctk.CTkButton(
            btn_row, text=emoji_label("➕ Add Entry", "Add Entry"),
            width=140, height=BTN_H)
        self.save_btn.pack(side="left", padx=(0, GAP))
        self.cancel_btn = ctk.CTkButton(
            btn_row, text=emoji_label("✖ Cancel Edit", "Cancel Edit"),
            width=120, height=BTN_H, fg_color="gray40")
        self.cancel_btn.pack(side="left")
        self.form_status = ctk.CTkLabel(
            btn_row, text="", text_color="#28a745", font=font_small())
        self.form_status.pack(side="left", padx=(GAP, 0))


class DataSearchBar:
    """Data page search and filter bar."""
    
    def __init__(self, parent, search_var: ctk.StringVar, mode_var: ctk.StringVar,
                 year_var: ctk.StringVar, year_menu, on_search_change, on_refresh):
        self.frame = ctk.CTkFrame(parent, fg_color="transparent")
        ctk.CTkLabel(
            self.frame, text=emoji_label("🔍", "Search:"),
            font=font_body(12),
        ).pack(side="left", padx=(0, GAP_SM))
        ctk.CTkEntry(
            self.frame, textvariable=search_var, width=240, height=CTRL_H,
            placeholder_text="Search task, notes, date…",
        ).pack(side="left", padx=(0, GAP))

        ctk.CTkLabel(self.frame, text="Mode:", font=font_body(12)).pack(
            side="left", padx=(0, GAP_SM))
        ctk.CTkOptionMenu(
            self.frame, variable=mode_var,
            values=["All", "Hourly", "Per Task"],
            command=lambda _: on_refresh(), width=110, height=CTRL_H,
        ).pack(side="left", padx=(0, GAP))

        ctk.CTkLabel(self.frame, text="Year:", font=font_body(12)).pack(
            side="left", padx=(0, GAP_SM))
        year_menu.configure(height=CTRL_H)
        year_menu.pack(side="left")


class DataTable:
    """Data table treeview widget."""
    
    def __init__(self, parent, on_click: Callable):
        self.holder = tkinter.Frame(parent, bd=0, highlightthickness=0)
        self.tree = None
        self._build(on_click)
    
    def _build(self, on_click: Callable):
        cols = ("id", "task", "date", "start", "end", "minutes",
                "rate", "total", "time_fmt", "mode", "notes")
        self.tree = ttk.Treeview(self.holder, columns=cols, show="headings",
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
            stretch = col in ("task", "notes")
            self.tree.column(col, width=width, minwidth=40, stretch=stretch)
        scroll = ttk.Scrollbar(self.holder, orient="vertical",
                                command=self.tree.yview,
                                style="Themed.Vertical.TScrollbar")
        self.tree.configure(yscrollcommand=scroll.set)
        scroll.pack(side="right", fill="y")
        self.tree.pack(side="left", fill="both", expand=True)
        self.tree.bind("<Button-1>", on_click)


class DataPagination:
    """Data page pagination widget."""
    
    def __init__(self, parent, prev_cmd, next_cmd, page_size_var, 
                 on_page_size_change, delete_cmd, edit_cmd):
        from ui.components.dashboard_specs import PAGE_SIZES
        
        self.frame = ctk.CTkFrame(parent, fg_color="transparent")
        ctk.CTkButton(
            self.frame, text="◀", width=42, height=CTRL_H, command=prev_cmd,
        ).pack(side="left", padx=(0, GAP_SM))
        self.pag_label = ctk.CTkLabel(self.frame, text="—", font=font_small())
        self.pag_label.pack(side="left", padx=GAP)
        ctk.CTkButton(
            self.frame, text="▶", width=42, height=CTRL_H, command=next_cmd,
        ).pack(side="left")
        ctk.CTkLabel(self.frame, text="Page:", font=font_body(12)).pack(
            side="left", padx=(20, GAP_SM))
        ctk.CTkOptionMenu(
            self.frame, variable=page_size_var,
            values=PAGE_SIZES, command=on_page_size_change,
            width=80, height=CTRL_H,
        ).pack(side="left")

        ctk.CTkButton(
            self.frame,
            text=emoji_label("🗑 Delete Sel.", "Delete Sel."),
            width=120, height=CTRL_H,
            fg_color="#dc3545", hover_color="#a71d2a",
            command=delete_cmd,
        ).pack(side="right")
        ctk.CTkButton(
            self.frame,
            text=emoji_label("✏ Edit Sel.", "Edit Sel."),
            width=120, height=CTRL_H, command=edit_cmd,
        ).pack(side="right", padx=(0, GAP))
"""Calendar popup widget."""

from __future__ import annotations

import calendar as cal_mod
import tkinter
from datetime import date, datetime
from tkinter import ttk

import customtkinter as ctk

from config import load_config
from ui.styles.design import (
    RADIUS_BTN, CARD_PAD, INNER_PAD,
    make_panel, theme_colors, font_section, font_caption,
)


class CalendarPopup(ctk.CTkToplevel):
    def __init__(self, parent, target_entry):
        super().__init__(parent)
        self.target = target_entry
        self.title("Select Date")
        self.geometry("340x360")
        self.resizable(False, False)

        self._cfg = load_config()
        self._colors = theme_colors(self._cfg)

        today = date.today()
        cur = today
        val = target_entry.get().strip()
        if val:
            for fmt in ("%m/%d/%y", "%m/%d/%Y"):
                try:
                    cur = datetime.strptime(val, fmt).date()
                    break
                except ValueError:
                    continue
        self._year, self._month = cur.year, cur.month
        self._today = today
        self._build()
        self.update_idletasks()
        self._position_near_target()
        self.after(80, self._modalize)

    def _modalize(self):
        try:
            self.transient(self.master.winfo_toplevel())
            self.grab_set()
            self.lift()
            self.focus_force()
        except Exception:
            pass

    def _position_near_target(self):
        try:
            self.target.update_idletasks()
            x = self.target.winfo_rootx()
            y = self.target.winfo_rooty() + self.target.winfo_height() + 4
            self.geometry(f"+{x}+{y}")
        except Exception:
            pass

    def _build(self):
        bg_color = self._colors["surface"]
        accent = self._colors["accent"]
        text_color = self._colors["text"]
        cal_bg = self._colors["card_bg"]

        self.configure(fg_color=bg_color)

        panel = make_panel(self, self._cfg)
        panel.pack(fill="both", expand=True, padx=12, pady=12)

        hdr = ctk.CTkFrame(panel, fg_color="transparent")
        hdr.pack(fill="x", padx=CARD_PAD, pady=(CARD_PAD, INNER_PAD))
        ctk.CTkButton(
            hdr, text="◀", width=36, height=32,
            corner_radius=RADIUS_BTN, command=self._prev,
        ).pack(side="left")
        self.lbl = ctk.CTkLabel(
            hdr, text="", font=font_section(14),
            text_color=text_color,
        )
        self.lbl.pack(side="left", expand=True)
        ctk.CTkButton(
            hdr, text="▶", width=36, height=32,
            corner_radius=RADIUS_BTN, command=self._next,
        ).pack(side="right")

        names = ctk.CTkFrame(panel, fg_color="transparent")
        names.pack(fill="x", padx=CARD_PAD)
        for d in ("Mo", "Tu", "We", "Th", "Fr", "Sa", "Su"):
            ctk.CTkLabel(
                names, text=d, width=42, font=font_caption(),
                text_color=self._colors["muted"],
            ).pack(side="left", padx=1)

        self.grid_frame = tkinter.Frame(panel, bd=0, highlightthickness=0,
                                        bg=cal_bg)
        self.grid_frame.pack(fill="both", expand=True,
                             padx=CARD_PAD, pady=(INNER_PAD, CARD_PAD))

        style = ttk.Style()
        style.theme_use("default")

        style.configure("Calendar.Treeview",
                        background=cal_bg,
                        foreground=text_color,
                        fieldbackground=cal_bg,
                        borderwidth=0,
                        font=("Segoe UI", 11),
                        rowheight=28)
        style.configure("Calendar.Treeview.Heading",
                        background=cal_bg,
                        foreground=text_color,
                        borderwidth=0)
        style.map("Calendar.Treeview",
                  background=[("selected", accent)],
                  foreground=[("selected", "#ffffff")])

        self.cal_tree = ttk.Treeview(
            self.grid_frame, columns=tuple(range(7)), show="",
            style="Calendar.Treeview", height=6, selectmode="browse")

        for i in range(7):
            self.cal_tree.column(i, width=42, anchor="center", stretch=False)

        self.cal_tree.pack(fill="both", expand=True)
        self.cal_tree.bind("<<TreeviewSelect>>", self._on_tree_select)

        self._render()

    def _render(self):
        for item in self.cal_tree.get_children():
            self.cal_tree.delete(item)

        self.lbl.configure(
            text=f"{cal_mod.month_name[self._month]} {self._year}")

        weeks = cal_mod.monthcalendar(self._year, self._month)

        self._date_map = {}

        accent = self._colors["accent"]

        for row_idx, week in enumerate(weeks):
            row_vals = []
            for col_idx, day in enumerate(week):
                if day == 0:
                    row_vals.append("")
                else:
                    d = date(self._year, self._month, day)
                    if d == self._today:
                        row_vals.append(f"●{day}●")
                        today_tag = f"today_{row_idx}_{col_idx}"
                        self.cal_tree.tag_configure(
                            today_tag, background=accent, foreground="#ffffff")
                    else:
                        row_vals.append(str(day))
                    self._date_map[(row_idx, col_idx)] = d

            self.cal_tree.insert("", "end", values=tuple(row_vals))

    def _on_tree_select(self, event):
        sel = self.cal_tree.selection()
        if not sel:
            return

        item = sel[0]
        children = self.cal_tree.get_children()
        row_idx = list(children).index(item)

        try:
            col_id = self.cal_tree.identify_column(event.x)
            if col_id:
                col_num = int(col_id[1:]) - 1
                key = (row_idx, col_num)
                if key in self._date_map:
                    self._pick(self._date_map[key])
        except (ValueError, TypeError):
            pass

    def _pick(self, d):
        self.target.delete(0, "end")
        self.target.insert(0, d.strftime("%m/%d/%y"))
        self.destroy()

    def _prev(self):
        self._month, self._year = ((12, self._year - 1)
                                    if self._month == 1
                                    else (self._month - 1, self._year))
        self._render()

    def _next(self):
        self._month, self._year = ((1, self._year + 1)
                                    if self._month == 12
                                    else (self._month + 1, self._year))
        self._render()

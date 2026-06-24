"""Tax estimation with annual breakdown and quarterly payment schedule."""

from __future__ import annotations

import tkinter as tk
from tkinter import ttk
from datetime import date
from typing import TYPE_CHECKING

import customtkinter as ctk
import matplotlib
matplotlib.use("Agg")
from matplotlib.figure import Figure
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg

from config import load_config, US_STATES, get_config_version
from db import Database
from taxes import compute_full_tax
from ui.styles.ttk_styles import configure_ttk_styles
from ui.styles.layout import (
    PAD_X, PAD_Y, GAP, GAP_SM, CTRL_H,
    font_title, font_body, font_caption, muted_color, card_bg, subtle_card,
)

if TYPE_CHECKING:
    from ui.ui_main import App


# (display label, dict key, tag)
BREAKDOWN_ROWS = [
    ("Income Summary",            None,         "header"),
    ("Gross Income",              "gross",      "value"),
    ("Above-Line Deductions",     "above",      "value"),
    ("Adjusted Gross Income",     "agi",        "value"),
    ("Standard / Itemized Ded.",  "standard",   "value"),
    ("Taxable Income",            "taxable",    "bold"),
    ("Tax Breakdown",             None,         "header"),
    ("Federal Income Tax",        "federal",    "value"),
    ("State Tax",                 "state",      "value"),
    ("Self-Employment Tax",       "se",         "value"),
    ("    Social Security",       "ss",         "value"),
    ("    Medicare",              "medicare",   "value"),
    ("    Addl. Medicare",        "addl_med",   "value"),
    ("Total Estimated Tax",       "total_tax",  "total"),
    ("Effective Tax Rate",        "eff_rate",   "accent"),
]


class TaxPage(ctk.CTkFrame):
    def __init__(self, master, app: "App", **kw):
        super().__init__(master, **kw)
        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(0, weight=1)
        self.app = app
        self.db = Database()
        self.cfg = load_config()
        configure_ttk_styles(self.cfg)

        # ── cache ──
        self._last_data_version = -1
        self._last_config_version = -1
        self._last_year: str | None = None
        self._last_pie_sig: tuple | None = None

        # ── mpl state ──
        self._mpl_figure: Figure | None = None
        self._mpl_axes = None
        self._mpl_canvas: FigureCanvasTkAgg | None = None
        self._chart_resize_id: str | None = None

        self._build()
        self.refresh()

    # ============================================================ build
    def _build(self) -> None:
        top = ctk.CTkFrame(self, fg_color="transparent")
        top.pack(fill="x", padx=PAD_X, pady=(PAD_Y, GAP))
        ctk.CTkLabel(top, text="Tax Estimator", font=font_title(20)).pack(side="left")

        ctk.CTkLabel(top, text="Year:", font=font_body(12)).pack(
            side="left", padx=(20, GAP_SM))
        self.year_var = ctk.StringVar(
            value=str(self.cfg["tax"].get("tax_year", date.today().year)))
        self.year_menu = ctk.CTkOptionMenu(
            top, variable=self.year_var,
            values=[str(date.today().year)],
            command=lambda _: self.refresh(), width=90, height=CTRL_H)
        self.year_menu.pack(side="left", padx=(0, GAP))
        ctk.CTkButton(
            top, text="Recalculate", width=110, height=CTRL_H,
            command=lambda: self.refresh(force=True),
        ).pack(side="right")

        info_strip = subtle_card(self, self.cfg)
        info_strip.pack(fill="x", padx=PAD_X, pady=(0, GAP))
        self._info_label = ctk.CTkLabel(
            info_strip, text="", font=font_caption(),
            text_color=muted_color(self.cfg),
        )
        self._info_label.pack(padx=PAD_X, pady=GAP)

        main = ctk.CTkFrame(self, fg_color="transparent")
        main.pack(fill="both", expand=True, padx=PAD_X, pady=(0, GAP))
        main.grid_rowconfigure(0, weight=3)
        main.grid_rowconfigure(1, weight=2)
        main.grid_columnconfigure(0, weight=3)
        main.grid_columnconfigure(1, weight=2)

        bd_panel = subtle_card(main, self.cfg)
        bd_panel.grid(row=0, column=0, sticky="nsew", padx=(0, GAP_SM))
        bg = card_bg(self.cfg)
        bd_holder = tk.Frame(bd_panel, bd=0, highlightthickness=0, bg=bg)
        bd_holder.pack(fill="both", expand=True, padx=6, pady=6)

        self.breakdown_tree = ttk.Treeview(
            bd_holder, columns=("label", "value"), show="headings",
            style="Tax.Treeview", selectmode="none")
        self.breakdown_tree.heading("label", text="Item",   anchor="w")
        self.breakdown_tree.heading("value", text="Amount", anchor="e")
        self.breakdown_tree.column("label", width=300, anchor="w", stretch=True)
        self.breakdown_tree.column("value", width=150, anchor="e", stretch=False)

        accent = self.cfg["theme"].get("accent_color", "#3b8ed0")
        self.breakdown_tree.tag_configure(
            "header", background="#1a1a1a", foreground=accent,
            font=("Segoe UI", 11, "bold"))
        self.breakdown_tree.tag_configure(
            "total", foreground="#dc3545",
            font=("Segoe UI", 11, "bold"))
        self.breakdown_tree.tag_configure(
            "bold", font=("Segoe UI", 10, "bold"))
        self.breakdown_tree.tag_configure(
            "accent", foreground=accent,
            font=("Segoe UI", 10, "bold"))
        self.breakdown_tree.tag_configure("value")

        sb = ttk.Scrollbar(bd_holder, orient="vertical",
                           command=self.breakdown_tree.yview,
                           style="Themed.Vertical.TScrollbar")
        self.breakdown_tree.configure(yscrollcommand=sb.set)
        sb.pack(side="right", fill="y", padx=(0, 2), pady=2)
        self.breakdown_tree.pack(side="left", fill="both", expand=True, padx=(2, 0), pady=2)

        self._bd_iids: dict[str, str] = {}
        for label, key, tag in BREAKDOWN_ROWS:
            if key is None:
                self.breakdown_tree.insert(
                    "", "end", values=(label, ""), tags=(tag,))
            else:
                iid = self.breakdown_tree.insert(
                    "", "end", values=(f"   {label}", "—"), tags=(tag,))
                self._bd_iids[key] = iid

        chart_panel = subtle_card(main, self.cfg)
        chart_panel.grid(row=0, column=1, sticky="nsew", padx=(GAP_SM, 0))
        self._chart_holder = tk.Frame(chart_panel, bd=0, highlightthickness=0, bg=bg)
        self._chart_holder.pack(fill="both", expand=True, padx=6, pady=6)
        self._chart_holder.bind("<Configure>", self._on_chart_configure)

        q_panel = subtle_card(main, self.cfg)
        q_panel.grid(row=1, column=0, columnspan=2, sticky="nsew", pady=(GAP, 0))
        q_holder = tk.Frame(q_panel, bd=0, highlightthickness=0, bg=bg)
        q_holder.pack(fill="both", expand=True, padx=6, pady=6)
        self.quarter_tree = ttk.Treeview(
            q_holder,
            columns=("q", "period", "due", "amount", "status"),
            show="headings", style="Quarter.Treeview",
            selectmode="none", height=4)
        self.quarter_tree.heading("q",      text="Quarter",       anchor="w")
        self.quarter_tree.heading("period", text="Income Period", anchor="w")
        self.quarter_tree.heading("due",    text="Due Date",      anchor="w")
        self.quarter_tree.heading("amount", text="Amount",        anchor="e")
        self.quarter_tree.heading("status", text="Status",        anchor="w")
        self.quarter_tree.column("q",      width=80,  anchor="w")
        self.quarter_tree.column("period", width=180, anchor="w", stretch=True)
        self.quarter_tree.column("due",    width=180, anchor="w")
        self.quarter_tree.column("amount", width=140, anchor="e")
        self.quarter_tree.column("status", width=140, anchor="w")
        self.quarter_tree.tag_configure("past",     foreground="#6c757d")
        self.quarter_tree.tag_configure("due",      foreground="#ffc107")
        self.quarter_tree.tag_configure("upcoming", foreground="#28a745")
        self.quarter_tree.pack(fill="both", expand=True, padx=2, pady=2)

        self._quarter_iids: list[str] = []
        for _ in range(4):
            iid = self.quarter_tree.insert(
                "", "end", values=("", "", "", "", ""))
            self._quarter_iids.append(iid)

        ctk.CTkLabel(
            self,
            text=("Estimates only. Brackets are approximate (2024); "
                  "consult a tax professional before filing."),
            font=font_caption(), text_color=muted_color(self.cfg),
            wraplength=900,
        ).pack(anchor="w", padx=PAD_X, pady=(0, PAD_Y))

    # ============================================================ refresh
    def refresh(self, force: bool = False) -> None:
        self.cfg = load_config()
        self._refresh_year_list()

        ver, cfg_ver = self.db.version, get_config_version()
        year_sel = self.year_var.get()
        if (not force
                and ver == self._last_data_version
                and cfg_ver == self._last_config_version
                and year_sel == self._last_year):
            return
        self._last_data_version = ver
        self._last_config_version = cfg_ver
        self._last_year = year_sel

        year_int = int(year_sel) if year_sel.isdigit() else date.today().year
        gross = self.db.sum_total(year=year_int)

        tax_cfg = self.cfg.get("tax", {})
        result = compute_full_tax(
            gross_income=gross,
            filing_status=tax_cfg.get("filing_status", "single"),
            state=tax_cfg.get("state", "CA"),
            deductions_cfg=tax_cfg.get("deductions", {}),
            tax_year=year_int,
        )
        self._update_values(result, year_int)
        self._draw_pie(result)

    def _refresh_year_list(self) -> None:
        years = self.db.get_distinct_years()
        opts = [str(y) for y in years] if years else [str(date.today().year)]
        if list(self.year_menu.cget("values")) != opts:
            self.year_menu.configure(values=opts)
        if self.year_var.get() not in opts:
            self.year_var.set(opts[0])

    # ============================================================ update
    def _update_values(self, result: dict, year_int: int) -> None:
        sym = self.cfg["general"].get("currency_symbol", "$")
        se = result["se_tax"]

        self._info_label.configure(text=(
            f"Filing: {result['filing_status']}   •   "
            f"State: {US_STATES.get(result['state'], result['state'])}   •   "
            f"Year: {year_int}"))

        vals = {
            "gross":     f"{sym}{result['gross_income']:,.2f}",
            "above":     f"−{sym}{result['total_deductions_above']:,.2f}",
            "agi":       f"{sym}{result['agi']:,.2f}",
            "standard":  f"−{sym}{result['standard_or_itemized']:,.2f}",
            "taxable":   f"{sym}{result['taxable_income']:,.2f}",
            "federal":   f"{sym}{result['federal_tax']:,.2f}",
            "state":     f"{sym}{result['state_tax']:,.2f}",
            "se":        f"{sym}{se['total_se_tax']:,.2f}",
            "ss":        f"{sym}{se['ss_tax']:,.2f}",
            "medicare":  f"{sym}{se['medicare_tax']:,.2f}",
            "addl_med":  (f"{sym}{se['additional_medicare']:,.2f}"
                          if se["additional_medicare"] > 0 else "—"),
            "total_tax": f"{sym}{result['total_tax']:,.2f}",
            "eff_rate":  f"{result['effective_rate']:.1f}%",
        }
        for key, txt in vals.items():
            iid = self._bd_iids.get(key)
            if iid is None:
                continue
            if self.breakdown_tree.set(iid, "value") != txt:
                self.breakdown_tree.set(iid, "value", txt)

        # ── quarterly rows ──
        for iid, q in zip(self._quarter_iids, result["quarterly_schedule"]):
            tag = ("past" if q["status"] == "Paid / Past"
                   else "due" if q["status"] == "Due Soon"
                   else "upcoming")
            new_vals = (q["quarter"], q["period"], q["due_date"],
                        f"{sym}{q['amount']:,.2f}", q["status"])
            current = self.quarter_tree.item(iid, "values")
            if tuple(current) != new_vals:
                self.quarter_tree.item(iid, values=new_vals, tags=(tag,))

    # ============================================================ chart
    def _on_chart_configure(self, event) -> None:
        if self._mpl_figure is None or event.widget is not self._chart_holder:
            return
        w, h = event.width, event.height
        if w < 80 or h < 80:
            return
        if self._chart_resize_id:
            self.after_cancel(self._chart_resize_id)
        self._chart_resize_id = self.after(50, lambda: self._resize_chart(w, h))

    def _resize_chart(self, width: int, height: int) -> None:
        self._chart_resize_id = None
        if self._mpl_figure is None or self._mpl_canvas is None:
            return
        dpi = self._mpl_figure.get_dpi()
        self._mpl_figure.set_size_inches(width / dpi, height / dpi, forward=True)
        try:
            self._mpl_canvas.draw_idle()
        except Exception:
            pass

    def _draw_pie(self, result: dict) -> None:
        fed = result["federal_tax"]
        state = result["state_tax"]
        se = result["se_tax"]["total_se_tax"]
        is_dark = self.cfg["theme"].get("mode", "dark").lower() == "dark"

        sym = self.cfg["general"].get("currency_symbol", "$")
        bg = card_bg(self.cfg) if is_dark else "#ffffff"
        fg = "#dcdcdc" if is_dark else "#222222"
        palette = self.cfg["theme"].get(
            "chart_colors", ["#3b8ed0", "#28a745", "#ffc107"])

        slices: list[tuple[str, float]] = []
        if fed > 0:
            slices.append(("Federal", fed))
        if state > 0:
            slices.append(("State", state))
        if se > 0:
            slices.append(("Self-Employment", se))

        sig = (round(fed, 2), round(state, 2), round(se, 2), is_dark)
        if sig == self._last_pie_sig and self._mpl_canvas is not None:
            return
        self._last_pie_sig = sig

        if not slices:
            return

        if self._mpl_figure is None:
            self._chart_holder.configure(bg=bg)
            self._mpl_figure = Figure(figsize=(3.5, 3.0), dpi=100, facecolor=bg)
            self._mpl_axes = self._mpl_figure.add_subplot(111)
            self._mpl_canvas = FigureCanvasTkAgg(self._mpl_figure,
                                                  master=self._chart_holder)
            w = self._mpl_canvas.get_tk_widget()
            w.configure(bg=bg, borderwidth=0, highlightthickness=0)
            w.pack(fill="both", expand=True)
            self._chart_holder.update_idletasks()
            cw = max(self._chart_holder.winfo_width(), 280)
            ch = max(self._chart_holder.winfo_height(), 220)
            self._resize_chart(cw, ch)
        else:
            self._mpl_figure.set_facecolor(bg)
            self._chart_holder.configure(bg=bg)

        ax = self._mpl_axes
        ax.clear()
        ax.set_facecolor(bg)

        values = [v for _, v in slices]
        legend_labels = [f"{name}  {sym}{v:,.0f}" for name, v in slices]
        colors = palette[:len(slices)]

        wedges, _, autotexts = ax.pie(
            values,
            autopct="%1.0f%%",
            pctdistance=0.78,
            startangle=90,
            colors=colors,
            wedgeprops=dict(width=0.42, edgecolor=bg, linewidth=1.5),
            textprops={"color": fg, "fontsize": 9, "weight": "bold"},
        )
        for t in autotexts:
            try:
                t.set_visible(float(t.get_text().rstrip("%")) >= 4)
            except ValueError:
                t.set_visible(False)

        ax.legend(
            wedges, legend_labels,
            loc="center left", bbox_to_anchor=(1.02, 0.5),
            fontsize=8, frameon=False, labelcolor=fg,
        )
        ax.set_title("Tax Breakdown", color=fg, fontsize=11, pad=8)
        ax.set_aspect("equal")
        self._mpl_figure.subplots_adjust(left=0.02, right=0.58, top=0.92, bottom=0.08)
        try:
            self._mpl_canvas.draw_idle()
        except AttributeError:
            pass
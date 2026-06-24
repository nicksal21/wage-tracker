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
    ("    ↳ Social Security",     "ss",         "value"),
    ("    ↳ Medicare",            "medicare",   "value"),
    ("    ↳ Addl. Medicare",      "addl_med",   "value"),
    ("Total Estimated Tax",       "total_tax",  "total"),
    ("Effective Tax Rate",        "eff_rate",   "accent"),
]


class TaxPage(ctk.CTkFrame):
    def __init__(self, master, app: "App", **kw):
        super().__init__(master, **kw)
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

        self._build()
        self.refresh()

    # ============================================================ build
    def _build(self) -> None:
        # ── Top bar ──
        top = ctk.CTkFrame(self, fg_color="transparent")
        top.pack(fill="x", padx=10, pady=(10, 4))
        ctk.CTkLabel(top, text="Tax Estimator",
                      font=ctk.CTkFont(size=20, weight="bold")).pack(side="left")

        ctk.CTkLabel(top, text="Year:").pack(side="left", padx=(20, 4))
        self.year_var = ctk.StringVar(
            value=str(self.cfg["tax"].get("tax_year", date.today().year)))
        self.year_menu = ctk.CTkOptionMenu(
            top, variable=self.year_var,
            values=[str(date.today().year)],
            command=lambda _: self.refresh(), width=90)
        self.year_menu.pack(side="left", padx=(0, 12))

        ctk.CTkButton(top, text="⟳ Recalculate", width=130,
                       command=lambda: self.refresh(force=True)).pack(side="right")

        # ── Info strip ──
        info_strip = ctk.CTkFrame(
            self, corner_radius=6,
            fg_color=self.cfg["theme"].get("card_bg", "#2b2b2b"))
        info_strip.pack(fill="x", padx=10, pady=(0, 6))
        self._info_label = ctk.CTkLabel(info_strip, text="",
                                          font=ctk.CTkFont(size=12))
        self._info_label.pack(padx=10, pady=6)

        # ── Main grid: [breakdown tree] | [pie chart] ──
        main = tk.Frame(self, bd=0, highlightthickness=0)
        main.pack(fill="both", expand=True, padx=10, pady=(0, 4))
        main.grid_rowconfigure(0, weight=3)
        main.grid_rowconfigure(1, weight=2)
        main.grid_columnconfigure(0, weight=3)
        main.grid_columnconfigure(1, weight=2)

        # — breakdown tree (top-left) —
        bd_holder = tk.Frame(main, bd=0, highlightthickness=0)
        bd_holder.grid(row=0, column=0, sticky="nsew", padx=(0, 6))
        self.breakdown_tree = ttk.Treeview(
            bd_holder, columns=("label", "value"), show="headings",
            style="Tax.Treeview", selectmode="none")
        self.breakdown_tree.heading("label", text="Item",   anchor="w")
        self.breakdown_tree.heading("value", text="Amount", anchor="e")
        self.breakdown_tree.column("label", width=300, anchor="w")
        self.breakdown_tree.column("value", width=150, anchor="e")

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
        
        # ── scrollbar ──
        sb = ttk.Scrollbar(bd_holder, orient="vertical",
                            command=self.breakdown_tree.yview,
                            style="Themed.Vertical.TScrollbar")
        self.breakdown_tree.configure(yscrollcommand=sb.set)
        sb.pack(side="right", fill="y")
        self.breakdown_tree.pack(side="left", fill="both", expand=True)

        self._bd_iids: dict[str, str] = {}
        for label, key, tag in BREAKDOWN_ROWS:
            if key is None:
                self.breakdown_tree.insert(
                    "", "end", values=(label, ""), tags=(tag,))
            else:
                iid = self.breakdown_tree.insert(
                    "", "end", values=(f"   {label}", "—"), tags=(tag,))
                self._bd_iids[key] = iid

        # — chart (top-right): plain tk.Frame ——
        self._chart_holder = tk.Frame(main, bd=0, highlightthickness=0)
        self._chart_holder.grid(row=0, column=1, sticky="nsew", padx=(6, 0))

        # — quarterly tree (bottom, spans both columns) ——
        q_holder = tk.Frame(main, bd=0, highlightthickness=0)
        q_holder.grid(row=1, column=0, columnspan=2, sticky="nsew",
                       pady=(8, 0))
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
        self.quarter_tree.column("period", width=180, anchor="w")
        self.quarter_tree.column("due",    width=180, anchor="w")
        self.quarter_tree.column("amount", width=140, anchor="e")
        self.quarter_tree.column("status", width=140, anchor="w")
        self.quarter_tree.tag_configure("past",     foreground="#6c757d")
        self.quarter_tree.tag_configure("due",      foreground="#ffc107")
        self.quarter_tree.tag_configure("upcoming", foreground="#28a745")
        self.quarter_tree.pack(fill="both", expand=True)

        self._quarter_iids: list[str] = []
        for _ in range(4):
            iid = self.quarter_tree.insert(
                "", "end", values=("", "", "", "", ""))
            self._quarter_iids.append(iid)

        # ── Disclaimer ──
        ctk.CTkLabel(
            self,
            text=("⚠ Estimates only. Brackets are approximate (2024); "
                  "consult a tax professional before filing."),
            font=ctk.CTkFont(size=10), text_color="gray60",
            wraplength=900,
        ).pack(anchor="w", padx=10, pady=(0, 8))

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
    def _draw_pie(self, result: dict) -> None:
        fed = result["federal_tax"]
        state = result["state_tax"]
        se = result["se_tax"]["total_se_tax"]
        is_dark = self.cfg["theme"].get("mode", "dark").lower() == "dark"

        sig = (round(fed, 2), round(state, 2), round(se, 2), is_dark)
        if sig == self._last_pie_sig and self._mpl_canvas is not None:
            return
        self._last_pie_sig = sig

        if fed + state + se <= 0:
            return

        sym = self.cfg["general"].get("currency_symbol", "$")
        bg = "#1a1a1a" if is_dark else "#ffffff"
        fg = "#dcdcdc" if is_dark else "#222222"
        colors = self.cfg["theme"].get(
            "chart_colors", ["#3b8ed0", "#28a745", "#ffc107"])

        if self._mpl_figure is None:
            self._chart_holder.configure(bg=bg)
            self._mpl_figure = Figure(figsize=(4.5, 3.0), dpi=100, facecolor=bg)
            self._mpl_axes = self._mpl_figure.add_subplot(111)
            self._mpl_canvas = FigureCanvasTkAgg(self._mpl_figure,
                                                  master=self._chart_holder)
            w = self._mpl_canvas.get_tk_widget()
            w.configure(bg=bg, borderwidth=0, highlightthickness=0)
            w.pack(fill="both", expand=True)
        else:
            self._mpl_figure.set_facecolor(bg)
            self._chart_holder.configure(bg=bg)

        ax = self._mpl_axes
        ax.clear()
        ax.set_facecolor(bg)
        ax.pie(
            [fed, state, se],
            labels=[f"Federal\n{sym}{fed:,.0f}",
                    f"State\n{sym}{state:,.0f}",
                    f"SE Tax\n{sym}{se:,.0f}"],
            autopct="%1.1f%%", colors=colors[:3],
            textprops={"color": fg, "fontsize": 8})
        ax.set_title("Tax Breakdown", color=fg, fontsize=10)
        self._mpl_figure.tight_layout()
        try:
            self._mpl_canvas.draw_idle()
        except AttributeError:
            pass
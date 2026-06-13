"""Analytics dashboard with period filtering, statistics, and charts."""

from __future__ import annotations

import tkinter as tk
from typing import TYPE_CHECKING
from datetime import date

import customtkinter as ctk

from config import load_config
from db import Database
from dashboard import iso_range
from ui.styles import configure_ttk_styles
from ui.components import (
    format_value, month_name,
    PERIODS, CHARTS, CHART_KEYS, CARDS, STAT_ROWS,
    DashboardToolbar, DashboardCards, DashboardViewSwitch, DashboardStats
)
from ui.charts import (
    setup_figure, configure_axes, create_chart_canvas,
    draw_line_chart, draw_bar_chart, draw_pie_chart, draw_rate_distribution
)

if TYPE_CHECKING:
    from ui.ui_main import App


def _fmt(kind: str, value, sym: str) -> str:
    return format_value(kind, value, sym)


class DashboardPage(ctk.CTkFrame):
    def __init__(self, master, app: "App", **kw):
        super().__init__(master, **kw)
        self.app = app
        self.db = Database()
        self.cfg = load_config()
        configure_ttk_styles(self.cfg)

        # ── cache / debounce ──
        self._last_data_version = -1
        self._last_filter_key: tuple | None = None
        self._last_chart_sig: tuple | None = None
        self._theme_token = self._theme_token_now()
        self._search_debounce_id: str | None = None
        self._current_view = "Statistics"

        # ── mpl state ──
        self._mpl_figure = None
        self._mpl_axes = None
        self._mpl_canvas = None

        self._summary: dict = {}
        self._filters: dict = {}

        self._toolbar: DashboardToolbar | None = None
        self._cards: DashboardCards | None = None
        self._view_switch: DashboardViewSwitch | None = None
        self._stats: DashboardStats | None = None
        self._chart_holder = None

        self._build()
        self.refresh()

    # ============================================================ build
    def _build(self) -> None:
        self._toolbar = DashboardToolbar(self)
        self._toolbar.frame.pack(fill="x", padx=10, pady=(10, 2))

        self._cards = DashboardCards(self, self.cfg)
        self._cards.frame.pack(fill="x", padx=10, pady=4)

        self._view_switch = DashboardViewSwitch(self)
        self._view_switch.frame.pack(fill="x", padx=10, pady=(2, 0))

        self._stats = DashboardStats(self, self.cfg)
        self._stats.holder.pack(fill="both", expand=True, padx=10, pady=(4, 10))

        self._chart_holder = tk.Frame(self, bd=0, highlightthickness=0)

        self._update_subperiod_menus()

    # ============================================================ sub-period handling
    def _on_period_change(self, _):
        self._update_subperiod_menus()
        self.refresh()
    
    def _on_year_change(self, _):
        self._update_subperiod_menus()
        self.refresh()
    
    def _update_subperiod_menus(self) -> None:
        if not self._toolbar:
            return
            
        period = self._toolbar.period_var.get()
        year_sel = self._toolbar.year_var.get()
        year_int = int(year_sel) if year_sel.isdigit() else None
        
        self._toolbar.month_label.pack_forget()
        self._toolbar.month_menu.pack_forget()
        self._toolbar.quarter_label.pack_forget()
        self._toolbar.quarter_menu.pack_forget()
        self._toolbar.day_label.pack_forget()
        self._toolbar.day_menu.pack_forget()
        
        if period == "Monthly" and year_int is not None:
            months = [f"{i:02d} - {month_name(i)}" for i in range(1, 13)]
            current = self._toolbar.month_var.get()
            if current not in months:
                self._toolbar.month_var.set(months[0] if months else "")
            self._toolbar.month_menu.configure(values=months)
            self._toolbar.month_label.pack(side="left", padx=(0, 4))
            self._toolbar.month_menu.pack(side="left", padx=(0, 8))
            
        elif period == "Quarterly" and year_int is not None:
            quarters = ["Q1", "Q2", "Q3", "Q4"]
            current = self._toolbar.quarter_var.get()
            if current not in quarters:
                self._toolbar.quarter_var.set(quarters[0] if quarters else "")
            self._toolbar.quarter_menu.configure(values=quarters)
            self._toolbar.quarter_label.pack(side="left", padx=(0, 4))
            self._toolbar.quarter_menu.pack(side="left", padx=(0, 8))
            
        elif period == "Daily" and year_int is not None:
            days = self._get_available_days(year_int)
            current = self._toolbar.day_var.get()
            if current not in days:
                self._toolbar.day_var.set(days[0] if days else "")
            self._toolbar.day_menu.configure(values=days)
            self._toolbar.day_label.pack(side="left", padx=(0, 4))
            self._toolbar.day_menu.pack(side="left", padx=(0, 8))
    
    def _get_available_days(self, year: int) -> list[str]:
        dates = self.db.get_distinct_dates(year=year)
        if not dates:
            return []
        return [d.strftime("%Y-%m-%d") if hasattr(d, 'strftime') else str(d) for d in dates]

    # ============================================================ view swap
    def _switch_view(self, choice: str) -> None:
        if choice == self._current_view:
            return
        self._current_view = choice
        if choice == "Statistics":
            if self._chart_holder:
                self._chart_holder.pack_forget()
            if self._view_switch and self._view_switch.chart_menu:
                self._view_switch.chart_menu.pack_forget()
            if self._stats:
                self._stats.holder.pack(fill="both", expand=True,
                                          padx=10, pady=(4, 10))
        else:
            if self._stats:
                self._stats.holder.pack_forget()
            if self._view_switch and self._view_switch.chart_menu:
                self._view_switch.chart_menu.pack(side="left", padx=(20, 0))
            if self._chart_holder:
                self._chart_holder.pack(fill="both", expand=True,
                                          padx=10, pady=(4, 10))
            self._ensure_canvas()
            self._draw_chart(force=True)

    # ============================================================ helpers
    def _theme_token_now(self) -> str:
        t = self.cfg["theme"]
        return (f"{t.get('mode','dark')}|{t.get('accent_color','')}"
                f"|{','.join(t.get('chart_colors', []))}")

    def _on_search_change(self, *_):
        if self._search_debounce_id:
            self.after_cancel(self._search_debounce_id)
        delay = self.cfg["general"].get("search_debounce_ms", 300)
        self._search_debounce_id = self.after(delay, self.refresh)

    def _filter_key(self) -> tuple:
        if not self._toolbar:
            return ("", "", "", "", "", "", "")
        return (self._toolbar.period_var.get(), self._toolbar.year_var.get(),
                self._toolbar.search_var.get().strip().lower(),
                self._toolbar.mode_filt_var.get(),
                self._toolbar.month_var.get(), self._toolbar.quarter_var.get(), 
                self._toolbar.day_var.get())

    def _refresh_year_list(self) -> None:
        if not self._toolbar:
            return
        opts = ["All"] + [str(y) for y in self.db.get_distinct_years()]
        if list(self._toolbar.year_menu.cget("values")) != opts:
            self._toolbar.year_menu.configure(values=opts)
        if self._toolbar.year_var.get() not in opts:
            self._toolbar.year_var.set("All")

    # ============================================================ refresh
    def refresh(self, force: bool = False) -> None:
        self.cfg = load_config()
        new_theme = self._theme_token_now()
        if new_theme != self._theme_token:
            self._theme_token = new_theme
            self._last_chart_sig = None

        self._refresh_year_list()

        filt_key = self._filter_key()
        ver = self.db.version
        if (not force and ver == self._last_data_version
                and filt_key == self._last_filter_key):
            return
        self._last_data_version = ver
        self._last_filter_key = filt_key

        if not self._toolbar:
            return

        period = self._toolbar.period_var.get().lower().replace("-", "")
        year_sel = self._toolbar.year_var.get()
        year_int = int(year_sel) if year_sel.isdigit() else None
        
        start_iso, end_iso = self._compute_date_range(period, year_int)

        mode_filt = self._toolbar.mode_filt_var.get()
        mode_arg = ("hourly" if mode_filt == "Hourly"
                    else "per_task" if mode_filt == "Per Task" else None)

        self._filters = {
            "mode": mode_arg,
            "search": self._toolbar.search_var.get().strip() or None,
            "start_iso": start_iso, "end_iso": end_iso,
        }
        self._summary = self.db.aggregate_summary(**self._filters)
        self._update_cards()
        self._update_stats()
        if self._current_view == "Graphs":
            self._draw_chart()
    
    def _compute_date_range(self, period: str, year_int: int | None) -> tuple[str, str]:
        if period == "alltime":
            return iso_range("all-time", year=year_int)
        
        if year_int is None:
            return iso_range(period, year=year_int)
        
        if not self._toolbar:
            return iso_range(period, year=year_int)
        
        if period == "monthly":
            month_sel = self._toolbar.month_var.get()
            if month_sel:
                try:
                    month_num = int(month_sel.split(" - ")[0])
                    start = date(year_int, month_num, 1)
                    if month_num == 12:
                        end = date(year_int, 12, 31)
                    else:
                        end = date(year_int, month_num + 1, 1) - __import__('datetime').timedelta(days=1)
                    return start.strftime("%Y-%m-%d"), end.strftime("%Y-%m-%d")
                except (ValueError, AttributeError):
                    pass
            return iso_range("monthly", year=year_int)
        
        elif period == "quarterly":
            quarter_sel = self._toolbar.quarter_var.get()
            if quarter_sel and quarter_sel.startswith("Q"):
                try:
                    q_num = int(quarter_sel[1])
                    start_month = (q_num - 1) * 3 + 1
                    end_month = start_month + 2
                    start = date(year_int, start_month, 1)
                    if end_month == 12:
                        end = date(year_int, 12, 31)
                    else:
                        end = date(year_int, end_month + 1, 1) - __import__('datetime').timedelta(days=1)
                    return start.strftime("%Y-%m-%d"), end.strftime("%Y-%m-%d")
                except (ValueError, AttributeError):
                    pass
            return iso_range("quarterly", year=year_int)
        
        elif period == "daily":
            day_sel = self._toolbar.day_var.get()
            if day_sel:
                try:
                    return day_sel, day_sel
                except Exception:
                    pass
            return iso_range("daily", year=year_int)
        
        elif period == "yearly":
            return iso_range("yearly", year=year_int)
        
        elif period == "weekly":
            return iso_range("weekly", year=year_int)
        
        else:
            return iso_range(period, year=year_int)

    # ============================================================ updates
    def _update_cards(self) -> None:
        if not self._cards:
            return
        sym = self.cfg["general"].get("currency_symbol", "$")
        for lbl, (_, key, kind) in zip(self._cards.value_labels, CARDS):
            txt = _fmt(kind, self._summary.get(key), sym)
            if lbl.cget("text") != txt:
                lbl.configure(text=txt)

    def _update_stats(self) -> None:
        if not self._stats or not self._stats.tree:
            return
        sym = self.cfg["general"].get("currency_symbol", "$")
        s = self._summary
        for _label, key, kind in STAT_ROWS:
            if key is None:
                continue
            iid = self._stats.stat_iids.get(key)
            if iid is None:
                continue
            if kind == "busiest":
                txt = (f"{s.get('busiest_day', 'N/A')}  "
                       f"({sym}{s.get('busiest_day_earning', 0):,.2f})")
            else:
                txt = _fmt(kind, s.get(key), sym)
            if self._stats.tree.set(iid, "value") != txt:
                self._stats.tree.set(iid, "value", txt)

    # ============================================================ chart
    def _ensure_canvas(self) -> None:
        if self._mpl_canvas is not None:
            return
        is_dark = self.cfg["theme"].get("mode", "dark").lower() == "dark"
        bg = "#1a1a1a" if is_dark else "#ffffff"
        if self._chart_holder:
            self._chart_holder.configure(bg=bg)

        self._mpl_figure = setup_figure(bg, figsize=(8, 4), dpi=100)
        self._mpl_axes = self._mpl_figure.add_subplot(111)
        if self._chart_holder:
            self._mpl_canvas = create_chart_canvas(self._chart_holder, self._mpl_figure)
            widget = self._mpl_canvas.get_tk_widget()
            widget.configure(bg=bg)

    def _draw_chart(self, force: bool = False) -> None:
        if self._current_view != "Graphs":
            return
        self._ensure_canvas()

        if not self._view_switch:
            return

        chart_key = CHART_KEYS[
            CHARTS.index(self._view_switch.chart_var.get())
            if self._view_switch.chart_var.get() in CHARTS else 0]

        if chart_key in ("earnings_over_time", "cumulative_earnings",
                         "hours_over_time"):
            rows = self.db.aggregate_by_day(**self._filters)
            data = {
                "dates":  [r["date"] or r["date_iso"] for r in rows],
                "totals": [r["total"] for r in rows],
                "hours":  [r["hours"] for r in rows],
            }
        elif chart_key == "task_distribution":
            rows = self.db.aggregate_by_task(limit=10, **self._filters)
            data = {"labels": [r["task_name"] for r in rows],
                    "values": [r["total"]     for r in rows]}
        elif chart_key == "rate_distribution":
            data = {"buckets": self.db.aggregate_rate_buckets(**self._filters)}
        else:
            data = {}

        sig = (chart_key, self._theme_token, repr(data))
        if not force and sig == self._last_chart_sig:
            return
        self._last_chart_sig = sig

        is_dark = self.cfg["theme"].get("mode", "dark").lower() == "dark"
        bg = "#1a1a1a" if is_dark else "#ffffff"
        fg = "#dcdcdc" if is_dark else "#222222"
        accent = self.cfg["theme"].get("accent_color", "#3b8ed0")
        chart_colors = self.cfg["theme"].get(
            "chart_colors",
            ["#3b8ed0", "#28a745", "#ffc107", "#dc3545", "#9b59b6"])

        ax = self._mpl_axes
        ax.clear()
        if self._mpl_figure:
            self._mpl_figure.set_facecolor(bg)
        if self._chart_holder:
            self._chart_holder.configure(bg=bg)
        configure_axes(ax, fg, bg)

        if chart_key == "earnings_over_time":
            draw_line_chart(ax, data["dates"], data["totals"], accent,
                           "Earnings ($)", "Earnings Over Time")
        elif chart_key == "cumulative_earnings":
            run, cum = 0.0, []
            for v in data["totals"]:
                run += v
                cum.append(run)
            draw_line_chart(ax, data["dates"], cum, accent,
                           "Cumulative Earnings ($)", "Cumulative Earnings")
        elif chart_key == "hours_over_time":
            draw_bar_chart(ax, data["dates"], data["hours"], accent,
                          "Hours", "Hours Over Time")
        elif chart_key == "task_distribution":
            if data["labels"]:
                colors = (chart_colors *
                          ((len(data["labels"]) // len(chart_colors)) + 1)
                          )[:len(data["labels"])]
                draw_pie_chart(ax, data["labels"], data["values"], colors, fg)
            else:
                ax.set_title("Earnings by Task")
        elif chart_key == "rate_distribution":
            draw_rate_distribution(ax, data["buckets"], fg, bg, accent)

        if self._mpl_figure:
            self._mpl_figure.tight_layout()
        try:
            if self._mpl_canvas:
                self._mpl_canvas.draw_idle()
        except AttributeError:
            pass
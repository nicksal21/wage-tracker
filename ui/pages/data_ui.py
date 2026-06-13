"""Entry management page with form, table, and bulk operations."""

from __future__ import annotations

import importlib.util
import os
import threading
from typing import TYPE_CHECKING, Optional

import customtkinter as ctk
from tkinter import messagebox, filedialog

from config import load_config
from db import Database
from ui.styles import configure_ttk_styles
from ui.widgets import CalendarPopup, ProgressDialog
from ui.components import (
    PAGE_SIZES,
    DataToolbar, DataForm, DataSearchBar, DataTable, DataPagination
)

_io_path = os.path.join(
    os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), "io.py")
_spec = importlib.util.spec_from_file_location("tracker_io", _io_path)
tracker_io = importlib.util.module_from_spec(_spec)  # type: ignore[arg-type]
_spec.loader.exec_module(tracker_io)                 # type: ignore[union-attr]

if TYPE_CHECKING:
    from ui.ui_main import App


class DataPage(ctk.CTkFrame):
    def __init__(self, master, app: "App", **kw):
        super().__init__(master, **kw)
        self.app = app
        self.db = Database()
        self.cfg = load_config()
        configure_ttk_styles(self.cfg)

        self.editing_id: Optional[int] = None
        self._orig_start = ""
        self._orig_end = ""
        self._orig_total_min = 0.0

        self._sort_col = "date"
        self._sort_desc = True
        self._page = 0
        try:
            self._page_size = int(self.cfg["general"].get("page_size", 100))
        except (TypeError, ValueError):
            self._page_size = 100
        self._total_count = 0

        # ── caching / debouncing ──
        self._last_data_version = -1
        self._last_filter_key: tuple | None = None
        self._search_debounce_id: str | None = None
        self._status_clear_id: str | None = None

        self._toolbar: Optional[DataToolbar] = None
        self._form: Optional[DataForm] = None
        self._search_bar: Optional[DataSearchBar] = None
        self._table: Optional[DataTable] = None
        self._pagination: Optional[DataPagination] = None
        
        self.tbl_search_var = ctk.StringVar()
        self.tbl_mode_var = ctk.StringVar(value="All")
        self.tbl_year_var = ctk.StringVar(value="All")
        self.page_size_var = ctk.StringVar(value=str(self._page_size))
        self.mode_var = ctk.StringVar(
            value=self.cfg["general"].get("default_mode", "hourly"))
        self.tbl_search_var.trace_add("write", self._on_search_change)

        self._build()
        self.refresh_table(force=True)

    # ============================================================ build
    def _build(self) -> None:
        self._toolbar = DataToolbar(self, self._import_file, self._export_csv, 
                                    self._recalculate_all, self._clear_all,
                                    lambda: self.refresh_table(force=True))
        self._toolbar.frame.pack(fill="x", padx=10, pady=(10, 4))
        
        self._form = DataForm(self, self.cfg, self.mode_var, self._on_mode_toggle)
        self._form.frame.pack(fill="x", padx=10, pady=6)
        if self._form.save_btn:
            self._form.save_btn.configure(command=self._save_entry)
        if self._form.cancel_btn:
            self._form.cancel_btn.configure(command=self._cancel_edit)
        
        self.tbl_year_menu = ctk.CTkOptionMenu(
            self, variable=self.tbl_year_var, values=["All"],
            command=lambda _: self.refresh_table(), width=90)

        self._search_bar = DataSearchBar(self, self.tbl_search_var, self.tbl_mode_var,
                                         self.tbl_year_var, self.tbl_year_menu,
                                         self._on_search_change, self.refresh_table)
        self._search_bar.frame.pack(fill="x", padx=10, pady=(4, 2))

        self._table = DataTable(self, self._on_tree_click)
        self._table.holder.pack(fill="both", expand=True, padx=10, pady=(0, 4))

        self._pagination = DataPagination(self, self._prev_page, self._next_page,
                                          self.page_size_var, self._on_page_size_change,
                                          self._delete_selected, self._edit_selected)
        self._pagination.frame.pack(fill="x", padx=10, pady=(2, 10))

    def _on_tree_click(self, event):
        if not self._table or not self._table.tree:
            return
        col = self._table.tree.identify_column(event.x)
        if col and col != "#0":
            col_name = col.lstrip("#")
            if col_name.isdigit():
                cols = ("id", "task", "date", "start", "end", "minutes",
                        "rate", "total", "time_fmt", "mode", "notes")
                idx = int(col_name) - 1
                if 0 <= idx < len(cols):
                    self._sort_by_column(cols[idx])

    # ============================================================ mode
    def _on_mode_toggle(self, mode: str) -> None:
        if not self._form:
            return
        if mode == "hourly":
            if self._form.task_row:
                self._form.task_row.grid_remove()
            if self._form.hourly_row:
                self._form.hourly_row.grid()
            if self._form.adjust_row:
                self._form.adjust_row.grid()
            if self._form.rate_label:
                self._form.rate_label.configure(text="Rate ($/hr):")
        else:
            if self._form.hourly_row:
                self._form.hourly_row.grid_remove()
            if self._form.adjust_row:
                self._form.adjust_row.grid_remove()
            if self._form.task_row:
                self._form.task_row.grid(row=2, column=0, columnspan=6,
                                          sticky="ew", padx=10, pady=2)
            if self._form.rate_label:
                self._form.rate_label.configure(text="Price/Task ($):")

    # ============================================================ helpers
    def _clear_form(self):
        if not self._form:
            return
        for e in (self._form.task_entry, self._form.date_entry, self._form.start_entry,
                  self._form.end_entry, self._form.qty_entry, self._form.rate_entry,
                  self._form.notes_entry, self._form.adjust_entry, self._form.adjust_reason):
            if e:
                e.delete(0, "end")
        dr = self.cfg["general"].get("default_rate", 0)
        if dr and self._form.rate_entry:
            self._form.rate_entry.insert(0, str(dr))
        self.editing_id = None
        self._orig_start = ""
        self._orig_end = ""
        self._orig_total_min = 0.0
        if self._form.save_btn:
            self._form.save_btn.configure(text="➕ Add Entry")
        if self._form.cancel_btn:
            self._form.cancel_btn.pack_forget()
        if self._form.form_status:
            self._form.form_status.configure(text="")

    @staticmethod
    def _safe_float(entry):
        try:
            return float(entry.get().replace(",", "").replace("$", ""))
        except ValueError:
            return 0.0

    def _flash_status(self, text, color):
        if not self._form or not self._form.form_status:
            return
        self._form.form_status.configure(text=text, text_color=color)
        if self._status_clear_id:
            self.after_cancel(self._status_clear_id)
        self._status_clear_id = self.after(
            3000, lambda: self._form.form_status.configure(text="") if self._form and self._form.form_status else None)

    # ============================================================ CRUD
    def _save_entry(self) -> None:
        if not self._form:
            return
        mode = self.mode_var.get()
        task = self._form.task_entry.get().strip() if self._form.task_entry else ""
        date_str = self._form.date_entry.get().strip() if self._form.date_entry else ""
        rate = self._safe_float(self._form.rate_entry) if self._form.rate_entry else 0.0
        notes = self._form.notes_entry.get().strip() if self._form.notes_entry else ""

        if not task:
            self._flash_status("⚠ Task name required.", "#ffc107"); return
        if not date_str:
            self._flash_status("⚠ Date required.", "#ffc107"); return

        if mode == "hourly":
            start = self._form.start_entry.get().strip() if self._form.start_entry else ""
            end = self._form.end_entry.get().strip() if self._form.end_entry else ""
            if not start or not end:
                self._flash_status(
                    "⚠ Start and end times required.", "#ffc107"); return

            if (self.editing_id is not None
                    and start == self._orig_start
                    and end == self._orig_end):
                base_min = self._orig_total_min
            else:
                base_min = self.db.calc_total_minutes(start, end)

            adj = self._safe_float(self._form.adjust_entry) if self._form.adjust_entry else 0.0
            if adj != 0:
                reason = self._form.adjust_reason.get().strip() if self._form.adjust_reason else ""
                tag = f"Adjusted {adj:+.0f} min"
                if reason:
                    tag += f": {reason}"
                notes = (notes + " | " + tag) if notes else tag
            total_min = max(base_min + adj, 0)
            total = self.db.calc_total(total_min, rate, "hourly")
            start_val, end_val = start, end
        else:
            qty = self._safe_float(self._form.qty_entry) if self._form.qty_entry else 0.0
            if qty <= 0:
                self._flash_status(
                    "⚠ Task quantity must be > 0.", "#ffc107"); return
            total_min = qty
            total = self.db.calc_total(qty, rate, "per_task")
            start_val, end_val = "", ""

        if self.editing_id is not None:
            self.db.update_entry(
                self.editing_id, task_name=task, date=date_str,
                start_time=start_val, end_time=end_val,
                total_minutes=total_min, rate=rate,
                total=total, mode=mode, notes=notes)
            self._flash_status("✓ Entry updated.", "#28a745")
        else:
            self.db.add_entry(task, date_str, start_val, end_val,
                              total_min, rate, total, mode, notes)
            self._flash_status("✓ Entry added.", "#28a745")

        self._clear_form()
        self.refresh_table(force=True)

    def _edit_selected(self):
        if not self._table or not self._table.tree:
            return
        sel = self._table.tree.selection()
        if not sel:
            messagebox.showinfo("Edit", "Select a row first."); return
        entry_id = int(self._table.tree.item(sel[0], "values")[0])
        entry = self.db.get_entry(entry_id)
        if not entry:
            return
        self._clear_form()
        self.editing_id = entry_id
        self.mode_var.set(entry["mode"])
        self._on_mode_toggle(entry["mode"])

        self._orig_start = entry.get("start_time", "") or ""
        self._orig_end = entry.get("end_time", "") or ""
        self._orig_total_min = float(entry.get("total_minutes", 0) or 0)

        if self._form:
            if self._form.task_entry:
                self._form.task_entry.insert(0, entry["task_name"])
            if self._form.date_entry:
                self._form.date_entry.insert(0, entry["date"])
            if entry["mode"] == "hourly":
                if self._form.start_entry:
                    self._form.start_entry.insert(0, self._orig_start)
                if self._form.end_entry:
                    self._form.end_entry.insert(0, self._orig_end)
            else:
                if self._form.qty_entry:
                    self._form.qty_entry.insert(0, str(entry["total_minutes"]))
            if self._form.rate_entry:
                self._form.rate_entry.delete(0, "end")
                self._form.rate_entry.insert(0, str(entry["rate"]))
            if self._form.notes_entry:
                self._form.notes_entry.insert(0, entry.get("notes", ""))
            if self._form.save_btn:
                self._form.save_btn.configure(text="💾 Update Entry")
            if self._form.cancel_btn and self._form.form_status:
                self._form.cancel_btn.pack(side="left", padx=(0, 8),
                                            before=self._form.form_status)

    def _cancel_edit(self):
        self._clear_form()

    def _delete_selected(self):
        if not self._table or not self._table.tree:
            return
        sel = self._table.tree.selection()
        if not sel:
            messagebox.showinfo("Delete", "Select a row first."); return
        if not messagebox.askyesno("Confirm", "Delete this entry?"):
            return
        entry_id = int(self._table.tree.item(sel[0], "values")[0])
        self.db.delete_entry(entry_id)
        self.refresh_table(force=True)

    # ============================================================ bulk
    def _run_threaded(self, op, on_done, dialog_title, dialog_message):
        dlg = ProgressDialog(self, dialog_title, dialog_message)
        result_box: dict = {"result": None, "error": None}

        def worker():
            try:
                result_box["result"] = op(dlg)
            except Exception as e:
                result_box["error"] = e
            self.after(0, finish)

        def finish():
            dlg.close()
            if result_box["error"] is not None:
                messagebox.showerror("Error", str(result_box["error"]))
            else:
                on_done(result_box["result"])

        threading.Thread(target=worker, daemon=True).start()

    def _recalculate_all(self):
        def op(dlg):
            dlg.set_message("Recalculating totals…")
            return self.db.recalculate_all()

        def done(n):
            self.refresh_table(force=True)
            messagebox.showinfo(
                "Recalculate",
                f"Recalculated totals for {n} entr{'y' if n == 1 else 'ies'}.")

        self._run_threaded(op, done, "Recalculate", "Working…")

    def _clear_all(self):
        if not messagebox.askyesno(
                "Clear All Entries",
                "This will permanently delete ALL entries.\n\nAre you sure?",
                icon="warning"):
            return
        if not messagebox.askyesno(
                "Final Confirmation",
                "This action CANNOT be undone.\nProceed?", icon="warning"):
            return

        def op(dlg):
            dlg.set_message("Clearing database…")
            return self.db.clear_all_entries()

        def done(n):
            self.refresh_table(force=True)
            messagebox.showinfo("Cleared", f"Deleted {n} entries.")

        self._run_threaded(op, done, "Clear All", "Deleting…")

    # ============================================================ table
    def _on_search_change(self, *_):
        if self._search_debounce_id:
            self.after_cancel(self._search_debounce_id)
        delay = self.cfg["general"].get("search_debounce_ms", 300)
        self._search_debounce_id = self.after(delay, self.refresh_table)

    def _filter_key(self) -> tuple:
        return (self.tbl_search_var.get().strip().lower(),
                self.tbl_mode_var.get(), self.tbl_year_var.get(),
                self._sort_col, self._sort_desc,
                self._page, self._page_size)

    def _refresh_year_list(self) -> None:
        opts = ["All"] + [str(y) for y in self.db.get_distinct_years()]
        if list(self.tbl_year_menu.cget("values")) != opts:
            self.tbl_year_menu.configure(values=opts)
        if self.tbl_year_var.get() not in opts:
            self.tbl_year_var.set("All")

    def refresh_table(self, force: bool = False) -> None:
        self._refresh_year_list()
        key = self._filter_key()
        ver = self.db.version
        if (not force and ver == self._last_data_version
                and key == self._last_filter_key):
            return
        self._last_data_version = ver
        self._last_filter_key = key

        mode_filt = self.tbl_mode_var.get()
        mode_arg = ("hourly" if mode_filt == "Hourly"
                    else "per_task" if mode_filt == "Per Task" else None)
        year_sel = self.tbl_year_var.get()
        year_arg = int(year_sel) if year_sel.isdigit() else None
        search_arg = self.tbl_search_var.get().strip() or None

        self._total_count = self.db.count_entries(
            mode=mode_arg, search=search_arg, year=year_arg)

        max_page = (max(self._total_count - 1, 0) // self._page_size
                    if self._page_size else 0)
        if self._page > max_page:
            self._page = max_page

        page = self.db.query_entries(
            mode=mode_arg, search=search_arg, year=year_arg,
            sort_col=self._sort_col, sort_desc=self._sort_desc,
            limit=self._page_size, offset=self._page * self._page_size)
        self._populate_tree(page)
        self._update_pagination_label()

    def _populate_tree(self, entries: list[dict]) -> None:
        if not self._table or not self._table.tree:
            return
        self._table.tree.delete(*self._table.tree.get_children())
        sym = self.cfg["general"].get("currency_symbol", "$")
        fmt_hm = self.db.format_hours_minutes
        rows = [
            (e["id"], e["task_name"], e["date"],
             e.get("start_time", ""), e.get("end_time", ""),
             f"{e['total_minutes']:.1f}", f"{sym}{e['rate']:.2f}",
             f"{sym}{e['total']:.2f}",
             fmt_hm(e["total_minutes"]) if e["mode"] == "hourly" else "",
             e["mode"], e.get("notes", ""))
            for e in entries
        ]
        for row in rows:
            self._table.tree.insert("", "end", iid=str(row[0]), values=row)

    def _update_pagination_label(self):
        if not self._pagination:
            return
        if not self._total_count:
            self._pagination.pag_label.configure(text="No entries"); return
        start = self._page * self._page_size + 1
        end = min(start + self._page_size - 1, self._total_count)
        pages = (self._total_count + self._page_size - 1) // self._page_size
        self._pagination.pag_label.configure(
            text=f"{start:,}–{end:,} of {self._total_count:,}  "
                 f"(page {self._page + 1}/{pages})")

    def _prev_page(self):
        if self._page > 0:
            self._page -= 1
            self.refresh_table()

    def _next_page(self):
        max_page = (max(self._total_count - 1, 0)) // self._page_size
        if self._page < max_page:
            self._page += 1
            self.refresh_table()

    def _on_page_size_change(self, choice):
        try:
            self._page_size = int(choice)
        except ValueError:
            self._page_size = 100
        self._page = 0
        self.refresh_table(force=True)

    def _sort_by_column(self, col):
        self._sort_desc = (not self._sort_desc
                            if col == self._sort_col else False)
        self._sort_col = col
        self._page = 0
        self.refresh_table(force=True)

    # ============================================================ IO
    def _import_file(self):
        path = filedialog.askopenfilename(
            title="Import Spreadsheet",
            filetypes=[
                ("All Supported", "*.csv *.xlsx *.xls *.ods"),
                ("CSV files",      "*.csv"),
                ("Excel files",    "*.xlsx *.xls"),
                ("ODS files",      "*.ods"),
                ("All files",      "*.*"),
            ])
        if not path:
            return

        def op(dlg):
            def cb(done, total):
                self.after(0, lambda: dlg.set_progress(done, total))
            dlg.set_message(f"Importing {os.path.basename(path)}…")
            return tracker_io.import_file(path, self.db, progress_callback=cb)

        def done(result):
            count, warnings = result
            self.refresh_table(force=True)
            msg = f"Imported {count} entries."
            if warnings:
                msg += "\n\nWarnings:\n" + "\n".join(warnings[:20])
            messagebox.showinfo("Import Complete", msg)

        self._run_threaded(op, done, "Importing", "Reading file…")

    def _export_csv(self):
        path = filedialog.asksaveasfilename(
            title="Export CSV", defaultextension=".csv",
            filetypes=[("CSV files", "*.csv")])
        if not path:
            return

        def op(dlg):
            def cb(done, total):
                self.after(0, lambda: dlg.set_progress(done, total))
            dlg.set_message(f"Streaming to {os.path.basename(path)}…")
            return tracker_io.export_csv(path, self.db, progress_callback=cb)

        def done(count):
            messagebox.showinfo("Export Complete",
                                f"Exported {count} entries to:\n{path}")

        self._run_threaded(op, done, "Exporting", "Writing CSV…")
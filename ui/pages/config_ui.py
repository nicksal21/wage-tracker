"""Settings page: theme, filing status, state, deductions, and general prefs."""

from __future__ import annotations

import customtkinter as ctk
from tkinter import colorchooser
from typing import TYPE_CHECKING

from config import (
    load_config, save_config, US_STATES, FILING_STATUSES, DEFAULT_CONFIG,
)

if TYPE_CHECKING:
    from ui.ui_main import App


class ConfigPage(ctk.CTkScrollableFrame):
    def __init__(self, master: ctk.CTkFrame, app: "App", **kw):
        super().__init__(master, **kw)
        self.app = app
        # Work on an own copy so live edits do not poison the shared cache
        # before the user clicks "Save".
        import copy
        self.cfg = copy.deepcopy(load_config())
        self._status_clear_id: str | None = None
        self._build()

    # ============================================================ build
    def _build(self) -> None:
        self._section("Theme Settings")

        row = ctk.CTkFrame(self, fg_color="transparent")
        row.pack(fill="x", padx=10, pady=4)
        ctk.CTkLabel(row, text="Appearance Mode:").pack(side="left", padx=(0, 10))
        self.mode_var = ctk.StringVar(value=self.cfg["theme"]["mode"].capitalize())
        ctk.CTkOptionMenu(
            row, variable=self.mode_var, values=["Dark", "Light", "System"],
            command=self._on_mode_change,
        ).pack(side="left")

        for key, label in (
            ("primary_color", "Primary Colour"),
            ("accent_color", "Accent Colour"),
            ("sidebar_bg", "Sidebar BG"),
            ("card_bg", "Card BG"),
        ):
            self._color_row(label, key)

        self._section("Tax / Filing Settings")

        row2 = ctk.CTkFrame(self, fg_color="transparent")
        row2.pack(fill="x", padx=10, pady=4)
        ctk.CTkLabel(row2, text="Filing Status:").pack(side="left", padx=(0, 10))
        self.filing_var = ctk.StringVar(
            value=FILING_STATUSES.get(self.cfg["tax"]["filing_status"], "Single")
        )
        ctk.CTkOptionMenu(
            row2, variable=self.filing_var,
            values=list(FILING_STATUSES.values()),
        ).pack(side="left")

        row3 = ctk.CTkFrame(self, fg_color="transparent")
        row3.pack(fill="x", padx=10, pady=4)
        ctk.CTkLabel(row3, text="State:").pack(side="left", padx=(0, 10))
        state_labels = [f"{c} – {n}" for c, n in US_STATES.items()]
        cur_state = self.cfg["tax"]["state"]
        self.state_var = ctk.StringVar(
            value=f"{cur_state} – {US_STATES.get(cur_state, '')}"
        )
        ctk.CTkOptionMenu(
            row3, variable=self.state_var, values=state_labels, width=280,
        ).pack(side="left")

        row_year = ctk.CTkFrame(self, fg_color="transparent")
        row_year.pack(fill="x", padx=10, pady=4)
        ctk.CTkLabel(row_year, text="Tax Year:").pack(side="left", padx=(0, 10))
        self.year_entry = ctk.CTkEntry(row_year, width=80)
        self.year_entry.insert(0, str(self.cfg["tax"].get("tax_year", 2024)))
        self.year_entry.pack(side="left")

        self._section("Deductions")

        ded = self.cfg["tax"]["deductions"]
        self.std_var = ctk.BooleanVar(value=ded.get("use_standard", True))
        ctk.CTkCheckBox(
            self, text="Use Standard Deduction", variable=self.std_var,
            command=self._toggle_custom,
        ).pack(anchor="w", padx=10, pady=4)

        self.custom_ded_entry = self._ded_row(
            "Custom Deduction ($):", ded.get("custom_deduction", 0))
        self.biz_entry = self._ded_row(
            "Business Expenses ($):", ded.get("business_expenses", 0))
        self.health_entry = self._ded_row(
            "Health Insurance ($):", ded.get("health_insurance", 0))
        self.retire_entry = self._ded_row(
            "Retirement Contributions ($):",
            ded.get("retirement_contributions", 0))
        self.home_entry = self._ded_row(
            "Home Office ($):", ded.get("home_office", 0))
        self.other_entry = self._ded_row(
            "Other Deductions ($):", ded.get("other_deductions", 0))
        self._toggle_custom()

        self._section("General")

        row_rate = ctk.CTkFrame(self, fg_color="transparent")
        row_rate.pack(fill="x", padx=10, pady=4)
        ctk.CTkLabel(row_rate, text="Default Rate ($):").pack(
            side="left", padx=(0, 10))
        self.default_rate_entry = ctk.CTkEntry(row_rate, width=100)
        self.default_rate_entry.insert(
            0, str(self.cfg["general"].get("default_rate", 0)))
        self.default_rate_entry.pack(side="left")

        row_mode = ctk.CTkFrame(self, fg_color="transparent")
        row_mode.pack(fill="x", padx=10, pady=4)
        ctk.CTkLabel(row_mode, text="Default Entry Mode:").pack(
            side="left", padx=(0, 10))
        self.default_mode_var = ctk.StringVar(
            value=self.cfg["general"].get("default_mode", "hourly").capitalize())
        ctk.CTkOptionMenu(
            row_mode, variable=self.default_mode_var,
            values=["Hourly", "Per_task"],
        ).pack(side="left")

        row_ps = ctk.CTkFrame(self, fg_color="transparent")
        row_ps.pack(fill="x", padx=10, pady=4)
        ctk.CTkLabel(row_ps, text="Table Page Size:").pack(side="left", padx=(0, 10))
        self.page_size_entry = ctk.CTkEntry(row_ps, width=80)
        self.page_size_entry.insert(
            0, str(self.cfg["general"].get("page_size", 100)))
        self.page_size_entry.pack(side="left")

        # ── buttons ──
        btn_row = ctk.CTkFrame(self, fg_color="transparent")
        btn_row.pack(fill="x", padx=10, pady=20)
        ctk.CTkButton(btn_row, text="💾  Save Settings",
                       command=self._save, width=180).pack(side="left",
                                                            padx=(0, 10))
        ctk.CTkButton(btn_row, text="↺  Reset Defaults",
                       command=self._reset,
                       fg_color="#dc3545", hover_color="#a71d2a",
                       width=160).pack(side="left")

        self.status_label = ctk.CTkLabel(self, text="", text_color="#28a745")
        self.status_label.pack(pady=(0, 10))

    # ============================================================ helpers
    def _section(self, title: str) -> None:
        ctk.CTkLabel(self, text=title,
                      font=ctk.CTkFont(size=16, weight="bold")).pack(
            anchor="w", padx=10, pady=(18, 4))
        ctk.CTkFrame(self, height=2, fg_color="gray40").pack(
            fill="x", padx=10, pady=(0, 6))

    def _color_row(self, label: str, key: str) -> None:
        row = ctk.CTkFrame(self, fg_color="transparent")
        row.pack(fill="x", padx=10, pady=3)
        ctk.CTkLabel(row, text=f"{label}:").pack(side="left", padx=(0, 10))
        color = self.cfg["theme"].get(key, "#3b8ed0")
        swatch = ctk.CTkButton(
            row, text=color, width=120, fg_color=color, text_color="white",
            hover_color=color, command=lambda k=key: self._pick_color(k))
        swatch.pack(side="left")
        setattr(self, f"_swatch_{key}", swatch)

    def _pick_color(self, key: str) -> None:
        r = colorchooser.askcolor(
            color=self.cfg["theme"].get(key, "#3b8ed0"),
            title=f"Choose {key}")
        if r and r[1]:
            self.cfg["theme"][key] = r[1]
            getattr(self, f"_swatch_{key}").configure(
                fg_color=r[1], hover_color=r[1], text=r[1])

    def _ded_row(self, label: str, value: float) -> ctk.CTkEntry:
        row = ctk.CTkFrame(self, fg_color="transparent")
        row.pack(fill="x", padx=20, pady=2)
        ctk.CTkLabel(row, text=label, width=240, anchor="w").pack(side="left")
        entry = ctk.CTkEntry(row, width=120)
        entry.insert(0, f"{value:.2f}")
        entry.pack(side="left")
        return entry

    def _toggle_custom(self) -> None:
        self.custom_ded_entry.configure(
            state="disabled" if self.std_var.get() else "normal")

    @staticmethod
    def _safe_float(entry: ctk.CTkEntry) -> float:
        try:
            return float(entry.get().replace(",", "").replace("$", ""))
        except ValueError:
            return 0.0

    # ============================================================ callbacks
    def _on_mode_change(self, choice: str) -> None:
        ctk.set_appearance_mode(choice.lower())
        self.cfg["theme"]["mode"] = choice.lower()

    def _flash_status(self, text: str, color: str) -> None:
        self.status_label.configure(text=text, text_color=color)
        if self._status_clear_id:
            self.after_cancel(self._status_clear_id)
        self._status_clear_id = self.after(
            3000, lambda: self.status_label.configure(text=""))

    # ============================================================ save / reset
    def _save(self) -> None:
        self.cfg["theme"]["mode"] = self.mode_var.get().lower()
        rev = {v: k for k, v in FILING_STATUSES.items()}
        self.cfg["tax"]["filing_status"] = rev.get(
            self.filing_var.get(), "single")
        self.cfg["tax"]["state"] = self.state_var.get().split("–")[0].strip()
        try:
            self.cfg["tax"]["tax_year"] = int(self.year_entry.get())
        except ValueError:
            pass
        self.cfg["tax"]["deductions"] = {
            "use_standard": self.std_var.get(),
            "custom_deduction": self._safe_float(self.custom_ded_entry),
            "business_expenses": self._safe_float(self.biz_entry),
            "health_insurance": self._safe_float(self.health_entry),
            "retirement_contributions": self._safe_float(self.retire_entry),
            "home_office": self._safe_float(self.home_entry),
            "other_deductions": self._safe_float(self.other_entry),
        }
        self.cfg["general"]["default_rate"] = self._safe_float(
            self.default_rate_entry)
        self.cfg["general"]["default_mode"] = self.default_mode_var.get().lower()
        try:
            self.cfg["general"]["page_size"] = max(
                10, int(self.page_size_entry.get()))
        except ValueError:
            pass

        save_config(self.cfg)
        ctk.set_appearance_mode(self.cfg["theme"]["mode"])
        self.app.apply_theme(self.cfg)
        self._flash_status("✓  Settings saved successfully.", "#28a745")

    def _reset(self) -> None:
        save_config(DEFAULT_CONFIG)
        self._flash_status(
            "↺  Defaults restored — please restart the app.", "#ffc107")
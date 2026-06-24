"""Settings page: theme, filing status, state, deductions, and general prefs."""

from __future__ import annotations

import copy

import customtkinter as ctk
from tkinter import colorchooser
from typing import TYPE_CHECKING

from config import (
    load_config, save_config, US_STATES, FILING_STATUSES, DEFAULT_CONFIG,
)
from ui.styles.design import (
    PAGE_PAD_X, PAGE_PAD_Y, SECTION_GAP, CARD_PAD, INNER_PAD, ITEM_GAP,
    RADIUS_BTN, SectionCard, PageHeader,
    section_label, danger_button, primary_button,
    font_caption, theme_colors,
)

if TYPE_CHECKING:
    from ui.ui_main import App


class ConfigPage(ctk.CTkScrollableFrame):
    def __init__(self, master: ctk.CTkFrame, app: "App", **kw):
        super().__init__(master, fg_color="transparent", **kw)
        self.app = app
        self.cfg = copy.deepcopy(load_config())
        self._colors = theme_colors(self.cfg)
        self._status_clear_id: str | None = None
        self._build()

    def _build(self) -> None:
        header = PageHeader(
            self, "Settings", self.cfg,
            subtitle="Appearance, tax profile, and application preferences",
        )
        header.pack(fill="x", padx=PAGE_PAD_X, pady=(PAGE_PAD_Y, SECTION_GAP))

        self._build_theme_section()
        self._build_tax_section()
        self._build_deductions_section()
        self._build_general_section()

        btn_row = ctk.CTkFrame(self, fg_color="transparent")
        btn_row.pack(fill="x", padx=PAGE_PAD_X, pady=(SECTION_GAP, ITEM_GAP))
        primary_button(btn_row, text="Save Settings", command=self._save,
                       width=160).pack(side="left", padx=(0, ITEM_GAP))
        danger_button(btn_row, text="Reset Defaults", command=self._reset,
                      width=150).pack(side="left")

        self.status_label = ctk.CTkLabel(
            self, text="", text_color=self._colors["success"], font=font_caption())
        self.status_label.pack(anchor="w", padx=PAGE_PAD_X, pady=(0, PAGE_PAD_Y))

    def _build_theme_section(self) -> None:
        sec = SectionCard(self, "Theme", self.cfg)
        sec.pack(fill="x", padx=PAGE_PAD_X, pady=(0, SECTION_GAP))
        body = sec.body

        row = ctk.CTkFrame(body, fg_color="transparent")
        row.pack(fill="x", pady=4)
        section_label(row, "Appearance").pack(side="left", padx=(0, 12))
        self.mode_var = ctk.StringVar(value=self.cfg["theme"]["mode"].capitalize())
        ctk.CTkOptionMenu(
            row, variable=self.mode_var, values=["Dark", "Light", "System"],
            command=self._on_mode_change, height=32,
        ).pack(side="left")

        for key, label in (
            ("primary_color", "Primary"),
            ("accent_color", "Accent"),
            ("sidebar_bg", "Sidebar"),
            ("card_bg", "Cards"),
        ):
            self._color_row(body, label, key)

    def _build_tax_section(self) -> None:
        sec = SectionCard(self, "Tax & Filing", self.cfg)
        sec.pack(fill="x", padx=PAGE_PAD_X, pady=(0, SECTION_GAP))
        body = sec.body

        row2 = ctk.CTkFrame(body, fg_color="transparent")
        row2.pack(fill="x", pady=4)
        section_label(row2, "Filing Status").pack(side="left", padx=(0, 12))
        self.filing_var = ctk.StringVar(
            value=FILING_STATUSES.get(self.cfg["tax"]["filing_status"], "Single")
        )
        ctk.CTkOptionMenu(
            row2, variable=self.filing_var,
            values=list(FILING_STATUSES.values()), height=32,
        ).pack(side="left")

        row3 = ctk.CTkFrame(body, fg_color="transparent")
        row3.pack(fill="x", pady=4)
        section_label(row3, "State").pack(side="left", padx=(0, 12))
        state_labels = [f"{c} – {n}" for c, n in US_STATES.items()]
        cur_state = self.cfg["tax"]["state"]
        self.state_var = ctk.StringVar(
            value=f"{cur_state} – {US_STATES.get(cur_state, '')}"
        )
        ctk.CTkOptionMenu(
            row3, variable=self.state_var, values=state_labels, width=280, height=32,
        ).pack(side="left")

        row_year = ctk.CTkFrame(body, fg_color="transparent")
        row_year.pack(fill="x", pady=4)
        section_label(row_year, "Tax Year").pack(side="left", padx=(0, 12))
        self.year_entry = ctk.CTkEntry(row_year, width=90, height=32)
        self.year_entry.insert(0, str(self.cfg["tax"].get("tax_year", 2024)))
        self.year_entry.pack(side="left")

    def _build_deductions_section(self) -> None:
        sec = SectionCard(self, "Deductions", self.cfg)
        sec.pack(fill="x", padx=PAGE_PAD_X, pady=(0, SECTION_GAP))
        body = sec.body

        ded = self.cfg["tax"]["deductions"]
        self.std_var = ctk.BooleanVar(value=ded.get("use_standard", True))
        ctk.CTkCheckBox(
            body, text="Use Standard Deduction", variable=self.std_var,
            command=self._toggle_custom, font=font_caption(),
        ).pack(anchor="w", pady=(0, INNER_PAD))

        self.custom_ded_entry = self._ded_row(
            body, "Custom Deduction ($):", ded.get("custom_deduction", 0))
        self.biz_entry = self._ded_row(
            body, "Business Expenses ($):", ded.get("business_expenses", 0))
        self.health_entry = self._ded_row(
            body, "Health Insurance ($):", ded.get("health_insurance", 0))
        self.retire_entry = self._ded_row(
            body, "Retirement Contributions ($):",
            ded.get("retirement_contributions", 0))
        self.home_entry = self._ded_row(
            body, "Home Office ($):", ded.get("home_office", 0))
        self.other_entry = self._ded_row(
            body, "Other Deductions ($):", ded.get("other_deductions", 0))
        self._toggle_custom()

    def _build_general_section(self) -> None:
        sec = SectionCard(self, "General", self.cfg)
        sec.pack(fill="x", padx=PAGE_PAD_X, pady=(0, SECTION_GAP))
        body = sec.body

        row_rate = ctk.CTkFrame(body, fg_color="transparent")
        row_rate.pack(fill="x", pady=4)
        section_label(row_rate, "Default Rate ($)").pack(side="left", padx=(0, 12))
        self.default_rate_entry = ctk.CTkEntry(row_rate, width=100, height=32)
        self.default_rate_entry.insert(
            0, str(self.cfg["general"].get("default_rate", 0)))
        self.default_rate_entry.pack(side="left")

        row_mode = ctk.CTkFrame(body, fg_color="transparent")
        row_mode.pack(fill="x", pady=4)
        section_label(row_mode, "Default Entry Mode").pack(side="left", padx=(0, 12))
        self.default_mode_var = ctk.StringVar(
            value=self.cfg["general"].get("default_mode", "hourly").capitalize())
        ctk.CTkOptionMenu(
            row_mode, variable=self.default_mode_var,
            values=["Hourly", "Per_task"], height=32,
        ).pack(side="left")

        row_ps = ctk.CTkFrame(body, fg_color="transparent")
        row_ps.pack(fill="x", pady=4)
        section_label(row_ps, "Table Page Size").pack(side="left", padx=(0, 12))
        self.page_size_entry = ctk.CTkEntry(row_ps, width=80, height=32)
        self.page_size_entry.insert(
            0, str(self.cfg["general"].get("page_size", 100)))
        self.page_size_entry.pack(side="left")

    def _color_row(self, parent, label: str, key: str) -> None:
        row = ctk.CTkFrame(parent, fg_color="transparent")
        row.pack(fill="x", pady=4)
        section_label(row, label, width=100).pack(side="left", padx=(0, 12))
        color = self.cfg["theme"].get(key, "#3b8ed0")
        swatch = ctk.CTkButton(
            row, text=color, width=120, height=32,
            corner_radius=RADIUS_BTN,
            fg_color=color, text_color="white",
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

    def _ded_row(self, parent, label: str, value: float) -> ctk.CTkEntry:
        row = ctk.CTkFrame(parent, fg_color="transparent")
        row.pack(fill="x", pady=3)
        section_label(row, label, width=240, anchor="w").pack(side="left")
        entry = ctk.CTkEntry(row, width=120, height=32)
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

    def _on_mode_change(self, choice: str) -> None:
        ctk.set_appearance_mode(choice.lower())
        self.cfg["theme"]["mode"] = choice.lower()

    def _flash_status(self, text: str, color: str) -> None:
        self.status_label.configure(text=text, text_color=color)
        if self._status_clear_id:
            self.after_cancel(self._status_clear_id)
        self._status_clear_id = self.after(
            3000, lambda: self.status_label.configure(text=""))

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
        self._flash_status("Settings saved successfully.", self._colors["success"])

    def _reset(self) -> None:
        save_config(DEFAULT_CONFIG)
        self._flash_status(
            "Defaults restored — please restart the app.", self._colors["warning"])

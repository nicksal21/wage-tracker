"""Progress dialog widget."""

from __future__ import annotations

import customtkinter as ctk

from config import load_config
from ui.styles.design import (
    CARD_PAD, INNER_PAD, make_panel,
    font_body, font_caption, theme_colors,
)


class ProgressDialog(ctk.CTkToplevel):
    def __init__(self, parent, title="Working…", message="Please wait…"):
        super().__init__(parent)
        self.title(title)
        self.geometry("400x150")
        self.resizable(False, False)
        self.protocol("WM_DELETE_WINDOW", lambda: None)

        cfg = load_config()
        colors = theme_colors(cfg)
        self.configure(fg_color=colors["surface"])

        panel = make_panel(self, cfg)
        panel.pack(fill="both", expand=True, padx=16, pady=16)

        self._msg = ctk.CTkLabel(
            panel, text=message, font=font_body(),
            text_color=colors["text"],
        )
        self._msg.pack(pady=(CARD_PAD, INNER_PAD), padx=CARD_PAD)
        self._bar = ctk.CTkProgressBar(panel, mode="indeterminate", width=320, height=8)
        self._bar.pack(pady=INNER_PAD, padx=CARD_PAD)
        self._bar.start()
        self._detail = ctk.CTkLabel(
            panel, text="", font=font_caption(),
            text_color=colors["muted"],
        )
        self._detail.pack(pady=(0, CARD_PAD))
        self.after(50, self._modalize)

    def _modalize(self):
        try:
            self.transient(self.master.winfo_toplevel())
            self.grab_set()
            self.lift()
        except Exception:
            pass

    def set_progress(self, done: int, total: int):
        if total and total > 0:
            if self._bar.cget("mode") != "determinate":
                self._bar.stop()
                self._bar.configure(mode="determinate")
            self._bar.set(min(done / total, 1.0))
            self._detail.configure(text=f"{done:,} / {total:,}")

    def set_message(self, msg: str):
        self._msg.configure(text=msg)

    def close(self):
        try:
            self._bar.stop()
        except Exception:
            pass
        try:
            self.grab_release()
        except Exception:
            pass
        self.destroy()

"""Progress dialog widget."""

from __future__ import annotations

import customtkinter as ctk


class ProgressDialog(ctk.CTkToplevel):
    def __init__(self, parent, title="Working…", message="Please wait…"):
        super().__init__(parent)
        self.title(title)
        self.geometry("360x130")
        self.resizable(False, False)
        self.protocol("WM_DELETE_WINDOW", lambda: None)

        self._msg = ctk.CTkLabel(self, text=message,
                                  font=ctk.CTkFont(size=13))
        self._msg.pack(pady=(20, 6))
        self._bar = ctk.CTkProgressBar(self, mode="indeterminate", width=300)
        self._bar.pack(pady=8)
        self._bar.start()
        self._detail = ctk.CTkLabel(self, text="",
                                     font=ctk.CTkFont(size=11),
                                     text_color="gray60")
        self._detail.pack()
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
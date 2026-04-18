from __future__ import annotations

import tkinter as tk
from queue import Empty, Queue
from typing import Callable, Optional


class OverlayWindow:
    def __init__(
        self,
        master: Optional[tk.Misc] = None,
        *,
        on_close: Optional[Callable[[], None]] = None,
    ) -> None:
        self._queue: Queue[str] = Queue()
        self._owns_root = master is None
        self._on_close = on_close
        self._closed = False
        self._after_id: Optional[str] = None
        self._root = tk.Tk() if self._owns_root else tk.Toplevel(master)
        self._root.title("AI Subtitle Overlay")
        self._root.attributes("-topmost", True)
        self._root.geometry("960x180+420+840")
        self._root.configure(bg="black")
        self._root.protocol("WM_DELETE_WINDOW", self.close)

        self._label = tk.Label(
            self._root,
            text="Waiting for OCR...",
            fg="white",
            bg="black",
            font=("Microsoft YaHei UI", 20, "bold"),
            justify="center",
            wraplength=920,
        )
        self._label.pack(fill="both", expand=True, padx=20, pady=20)
        self._after_id = self._root.after(100, self._poll_queue)

    def set_text(self, text: str) -> None:
        if self._closed:
            return
        self._queue.put(text)

    def clear_text(self) -> None:
        self.set_text("")

    def _poll_queue(self) -> None:
        if self._closed:
            return

        try:
            while True:
                text = self._queue.get_nowait()
                self._label.config(text=text or " ")
        except Empty:
            pass
        finally:
            if self._closed:
                return
            try:
                self._after_id = self._root.after(100, self._poll_queue)
            except tk.TclError:
                self._after_id = None

    def close(self) -> None:
        if self._closed:
            return

        self._closed = True
        if self._after_id is not None:
            try:
                self._root.after_cancel(self._after_id)
            except tk.TclError:
                pass
            self._after_id = None

        try:
            self._root.destroy()
        except tk.TclError:
            pass

        if self._on_close is not None:
            self._on_close()

    def run(self) -> None:
        if self._owns_root:
            self._root.mainloop()

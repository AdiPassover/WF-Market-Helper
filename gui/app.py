import os
import queue
import threading
import tkinter as tk
from pathlib import Path
from tkinter import messagebox, ttk
from typing import Any, Callable, Optional

from gui import theme
from gui.theme import px

PROJECT_ROOT = Path(__file__).resolve().parent.parent


class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Warframe Market Tool")
        theme.setup(self)
        self.geometry(f"{px(1320)}x{px(820)}")
        self.minsize(px(1000), px(640))
        try:
            self.state("zoomed")  # start maximized: the tables benefit from the room
        except tk.TclError:
            pass
        self.busy = False

        # Imported here so the theme's DPI scale is known before pages are built.
        from gui.arcanes_page import ArcanesPage
        from gui.home_page import HomePage
        from gui.set_page import SetAnalysisPage
        from gui.syndicates_page import SyndicatesPage

        container = ttk.Frame(self)
        container.pack(fill="both", expand=True)
        container.rowconfigure(0, weight=1)
        container.columnconfigure(0, weight=1)

        self.pages = {}
        for key, page_class in (("home", HomePage), ("arcanes", ArcanesPage),
                                ("syndicates", SyndicatesPage), ("set", SetAnalysisPage)):
            page = page_class(container, self)
            page.grid(row=0, column=0, sticky="nsew")
            self.pages[key] = page

        self.current_page = None
        self.bind_all("<Control-f>", self._on_find)
        self.bind_all("<Control-F>", self._on_find)
        self.show_home()

    def show(self, key: str) -> None:
        page = self.pages[key]
        page.tkraise()
        self.current_page = page
        if hasattr(page, "on_show"):
            page.on_show()

    def show_home(self) -> None:
        self.show("home")

    def _on_find(self, _event) -> str:
        if hasattr(self.current_page, "open_find"):
            self.current_page.open_find()
        return "break"

    def run_task(self, work: Callable[[Callable[..., None]], Any], *,
                 on_done: Callable[[Any], None],
                 on_progress: Optional[Callable[..., None]] = None,
                 on_error: Optional[Callable[[Exception], None]] = None,
                 on_finish: Optional[Callable[[], None]] = None) -> bool:
        """Run work(report) on a background thread so the window stays responsive.

        Whatever the worker passes to report(...) is forwarded to on_progress on the UI thread.
        Returns False (and runs nothing) if another task is still running.
        """
        if self.busy:
            messagebox.showinfo("Please wait", "Another analysis is still running.", parent=self)
            return False
        self.busy = True
        events = queue.Queue()

        def target():
            try:
                events.put(("done", work(lambda *args: events.put(("progress", args)))))
            except Exception as error:  # reported to the page, not swallowed
                events.put(("error", error))

        def poll():
            try:
                while True:
                    kind, payload = events.get_nowait()
                    if kind == "progress":
                        if on_progress:
                            on_progress(*payload)
                        continue
                    self.busy = False
                    if on_finish:
                        on_finish()
                    if kind == "done":
                        on_done(payload)
                    elif on_error:
                        on_error(payload)
                    else:
                        messagebox.showerror("Error", str(payload), parent=self)
                    return
            except queue.Empty:
                self.after(50, poll)

        threading.Thread(target=target, daemon=True).start()
        poll()
        return True


def main() -> None:
    # The analysis code reads some data files with paths relative to the project root.
    os.chdir(PROJECT_ROOT)
    try:  # crisp rendering on high-DPI Windows displays
        import ctypes
        ctypes.windll.shcore.SetProcessDpiAwareness(1)
    except (AttributeError, OSError):
        pass
    App().mainloop()

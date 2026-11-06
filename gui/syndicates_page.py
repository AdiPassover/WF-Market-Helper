import tkinter as tk
from pathlib import Path
from tkinter import ttk
from typing import Optional

from analysis.syndicate_profit import profit_from_syndicate
from gui import theme
from gui.theme import px
from gui.widgets import ClickCard, Column, DataTable, ProgressPanel, format_number, page_header, prettify_slug
from syndicates.wf_metadata import SYNDICATE_NAMES

try:
    from PIL import Image, ImageTk
except ImportError:  # icons are optional; cards fall back to text only
    Image = ImageTk = None

ICONS_DIR = Path(__file__).resolve().parent.parent / "syndicates" / "data" / "icons"

SYNDICATES = {  # name -> (display name, flag icon)
    "steel_meridian": ("Steel Meridian", "SteelMeridianFlag.webp"),
    "red_veil": ("Red Veil", "RedVeilFlag.webp"),
    "arbiters_of_hexis": ("Arbiters of Hexis", "ArbitersofHexisFlag.webp"),
    "cephalon_suda": ("Cephalon Suda", "CephalonSudaFlag.webp"),
    "perrin_sequence": ("The Perrin Sequence", "ThePerrinSequenceFlag.webp"),
    "new_loka": ("New Loka", "NewLokaFlag.webp"),
}


def _load_icon(filename: str, height: int) -> Optional[tk.PhotoImage]:
    if Image is None:
        return None
    try:
        image = Image.open(ICONS_DIR / filename)
    except OSError:
        return None
    width = max(1, round(image.width * height / image.height))
    return ImageTk.PhotoImage(image.resize((width, height), Image.LANCZOS))


class SyndicatesPage(ttk.Frame):
    def __init__(self, parent, app):
        super().__init__(parent, padding=px(20))
        self.app = app
        self.selected: list[str] = []
        self.cards: dict[str, ClickCard] = {}
        self.name_labels: dict[str, tk.Label] = {}
        self.tab_icons: dict[str, Optional[tk.PhotoImage]] = {}
        self._card_icons = []
        self.columnconfigure(0, weight=1)
        self.rowconfigure(4, weight=1)

        page_header(self, "Syndicates Profit", app.show_home,
                    "Select the syndicates to analyse").grid(row=0, column=0, sticky="ew")

        picker = ttk.Frame(self)
        picker.grid(row=1, column=0, pady=(px(18), px(12)))
        for column, name in enumerate(SYNDICATE_NAMES):
            display_name, icon_file = SYNDICATES.get(name, (prettify_slug(name), ""))
            card = ClickCard(picker, command=lambda n=name: self._toggle(n), padx=px(14), pady=px(12))
            card.grid(row=0, column=column, padx=px(6))
            icon = _load_icon(icon_file, px(96))
            if icon:
                self._card_icons.append(icon)
                card.add(tk.Label(card, image=icon)).pack()
            self.name_labels[name] = card.add(tk.Label(card, text=display_name, font=theme.BOLD,
                                                       fg=theme.TEXT, width=17))
            self.name_labels[name].pack(pady=(px(8), 0))
            self.cards[name] = card
            self.tab_icons[name] = _load_icon(icon_file, px(20))

        actions = ttk.Frame(self)
        actions.grid(row=2, column=0, sticky="ew")
        actions.columnconfigure(2, weight=1)
        ttk.Button(actions, text="Select all", command=lambda: self._set_selection(list(SYNDICATE_NAMES))).grid(
            row=0, column=0)
        ttk.Button(actions, text="Clear", command=lambda: self._set_selection([])).grid(
            row=0, column=1, padx=px(8))
        self.selection_label = ttk.Label(actions, style="Muted.TLabel")
        self.selection_label.grid(row=0, column=2, sticky="w", padx=px(8))
        self.analyse_button = ttk.Button(actions, text="Analyse", style="Accent.TButton", command=self.analyse)
        self.analyse_button.grid(row=0, column=3, sticky="e")

        self.progress = ProgressPanel(self)
        self.progress.grid(row=3, column=0, sticky="ew", pady=(px(12), 0))
        self.progress.grid_remove()

        results = ttk.Frame(self)
        results.grid(row=4, column=0, sticky="nsew", pady=(px(12), 0))
        results.rowconfigure(0, weight=1)
        results.columnconfigure(0, weight=1)
        self.placeholder = ttk.Label(results, style="Muted.TLabel",
                                     text="Results will appear here, one tab per syndicate.")
        self.placeholder.grid(row=0, column=0)
        self.notebook = ttk.Notebook(results)
        self.notebook.grid(row=0, column=0, sticky="nsew")
        self.notebook.grid_remove()

        self._set_selection([])

    def _toggle(self, name: str) -> None:
        if name in self.selected:
            self._set_selection([n for n in self.selected if n != name])
        else:
            self._set_selection(self.selected + [name])

    def _set_selection(self, names: list[str]) -> None:
        self.selected = [n for n in SYNDICATE_NAMES if n in names]
        for name, card in self.cards.items():
            card.set_selected(name in self.selected)
            self.name_labels[name].configure(fg=theme.ACCENT if name in self.selected else theme.TEXT)
        count = len(self.selected)
        self.selection_label.configure(text=f"{count} selected" if count else "No syndicate selected")
        if count:
            self.analyse_button.grid()
        else:
            self.analyse_button.grid_remove()

    def analyse(self) -> None:
        names = list(self.selected)
        if not names:
            return

        def work(report):
            results = []
            for index, name in enumerate(names):
                report(index, 0, 0)
                profits = profit_from_syndicate(
                    name, progress_callback=lambda current, total, i=index: report(i, current, total))
                results.append((name, profits))
            return results

        def on_progress(index, current, total):
            display_name = SYNDICATES.get(names[index], (prettify_slug(names[index]),))[0]
            fraction = (index + (current / total if total else 0)) / len(names)
            text = f"Analysing {display_name} ({index + 1}/{len(names)})"
            if total:
                text += f"  ·  offer {current}/{total}"
            self.progress.set_progress(fraction, text)

        def on_error(error):
            self.placeholder.configure(text=f"Analysis failed: {error}", foreground=theme.DANGER)
            self.notebook.grid_remove()
            self.placeholder.grid()

        def on_finish():
            self.progress.finish()
            self.analyse_button.state(["!disabled"])

        if self.app.run_task(work, on_progress=on_progress, on_done=self._show_results,
                             on_error=on_error, on_finish=on_finish):
            self.analyse_button.state(["disabled"])
            self.progress.start("Analysing syndicates…")

    def _show_results(self, results: list[tuple[str, list[tuple[str, int, int]]]]) -> None:
        for tab in self.notebook.tabs():
            widget = self.nametowidget(tab)
            self.notebook.forget(tab)
            widget.destroy()

        for name, profits in results:
            display_name = SYNDICATES.get(name, (prettify_slug(name),))[0]
            table = DataTable(
                self.notebook, title=display_name,
                subtitle="Best online buy order for each tradeable offer",
                columns=[Column("item", "Item", 280, stretch=True),
                         Column("standing", "Standing cost", 120, anchor="e", fmt=format_number(0)),
                         Column("platinum", "Platinum", 100, anchor="e", fmt=format_number(0)),
                         Column("ratio", "Plat per 1K standing", 160, anchor="e", fmt=format_number(2))],
                sort_key="ratio",
            )
            table.set_rows([
                {"item": prettify_slug(slug), "standing": standing, "platinum": platinum,
                 "ratio": platinum / (float(standing) / 1000)}
                for slug, standing, platinum in profits
            ])
            icon = self.tab_icons.get(name)
            if icon:
                self.notebook.add(table, text=f" {display_name}", image=icon, compound="left")
            else:
                self.notebook.add(table, text=display_name)

        self.placeholder.grid_remove()
        self.notebook.grid()

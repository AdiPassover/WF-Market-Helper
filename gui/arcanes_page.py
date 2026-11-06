import time
from pathlib import Path
from tkinter import ttk

from analysis.arcanes_analysis import ArcanesAnalyzer
from gui import theme
from gui.theme import px
from gui.widgets import Column, DataTable, FindBar, ProgressPanel, format_number, page_header

RESULTS_DIR = Path(__file__).resolve().parent.parent / "saved_analysis_results"
PRICES_CSV = RESULTS_DIR / "arcane_prices.csv"
RATIO_CSV = RESULTS_DIR / "arcane_plat_vosfor_ratio.csv"
PLAT_EXPECTANCY_CSV = RESULTS_DIR / "arcane_collections_plat_expectancy.csv"
DISSOLUTION_EXPECTANCY_CSV = RESULTS_DIR / "arcane_collections_dissolution_expectancy.csv"

COLLECTION_SUFFIX = " Collection"


class _ProgressReportingAnalyzer(ArcanesAnalyzer):
    """ArcanesAnalyzer whose console loading bar is redirected to a callback."""

    def __init__(self, progress_callback, **kwargs):
        self._progress_callback = progress_callback
        super().__init__(**kwargs)

    def _print_progress(self, current, total, width=30):
        self._progress_callback(current, total)


def _rows(values: dict) -> list[dict]:
    return [{"name": name, "value": value} for name, value in values.items()]


class ArcanesPage(ttk.Frame):
    def __init__(self, parent, app):
        super().__init__(parent, padding=px(20))
        self.app = app
        self._loaded = False
        self.columnconfigure(0, weight=1)
        self.rowconfigure(4, weight=1)

        header = page_header(self, "Arcanes Analysis", app.show_home)
        header.grid(row=0, column=0, sticky="ew")
        self.fetch_button = ttk.Button(header, text="Fetch live prices", style="Accent.TButton",
                                       command=lambda: self.load(live=True))
        self.fetch_button.pack(side="right")
        self.saved_button = ttk.Button(header, text="Load saved prices", command=lambda: self.load(live=False))
        self.saved_button.pack(side="right", padx=px(8))
        ttk.Label(header, text="Ctrl+F to find", style="Muted.TLabel").pack(side="right", padx=px(12))

        self.status = ttk.Label(self, style="Muted.TLabel")
        self.status.grid(row=1, column=0, sticky="w", pady=(px(10), 0))

        self.find_bar = FindBar(self, lambda: self.tables)
        self.find_bar.grid(row=2, column=0, sticky="ew", pady=(px(10), 0))
        self.find_bar.grid_remove()

        self.progress = ProgressPanel(self)
        self.progress.grid(row=3, column=0, sticky="ew", pady=(px(10), 0))
        self.progress.grid_remove()

        body = ttk.Frame(self)
        body.grid(row=4, column=0, sticky="nsew", pady=(px(12), 0))
        body.rowconfigure(1, weight=1)
        body.columnconfigure(0, weight=5, uniform="tables")
        body.columnconfigure(1, weight=4, uniform="tables")

        self.ratio_table = DataTable(
            body, title="Arcanes Plat / Vosfor Ratio",
            subtitle="Larger ratio means more platinum per Vosfor (collections included)",
            columns=[Column("name", "Arcane / Collection", 200, stretch=True),
                     Column("value", "Plat / Vosfor", 120, anchor="e", fmt=format_number(4))],
            sort_key="value",
            is_highlighted=lambda row: row["name"].endswith(COLLECTION_SUFFIX),
            legend=[("Arcane", theme.SURFACE_HIGH, theme.TEXT),
                    ("Collection", theme.HIGHLIGHT_BG, theme.HIGHLIGHT_FG)],
        )
        self.price_table = DataTable(
            body, title="Arcane Prices",
            subtitle="Lowest online sell price per single arcane (plat)",
            columns=[Column("name", "Arcane", 180, stretch=True),
                     Column("value", "Price (plat)", 110, anchor="e", fmt=format_number(2))],
            sort_key="value",
        )
        self.collections_table = DataTable(
            body, title="Collections Platinum Expectancy",
            subtitle="Expected platinum from one collection",
            columns=[Column("name", "Collection", 180, stretch=True),
                     Column("value", "Expected plat", 110, anchor="e", fmt=format_number(2))],
            sort_key="value", height=9,
        )
        self.tables = [self.ratio_table, self.price_table, self.collections_table]
        self.ratio_table.grid(row=0, column=0, rowspan=2, sticky="nsew")
        self.collections_table.grid(row=0, column=1, sticky="nsew", padx=(px(12), 0))
        self.price_table.grid(row=1, column=1, sticky="nsew", padx=(px(12), 0), pady=(px(12), 0))

    def on_show(self) -> None:
        if not self._loaded and not self.app.busy:
            self.load(live=True)

    def open_find(self) -> None:
        self.find_bar.show()

    def load(self, live: bool) -> None:
        if not live and not PRICES_CSV.exists():
            self.status.configure(text=f"No saved prices found at {PRICES_CSV}", foreground=theme.DANGER)
            return

        def work(report):
            if live:
                analyzer = _ProgressReportingAnalyzer(report, save_path=str(PRICES_CSV))
                ratio = analyzer.get_plat_vosfor_ratio(include_collections=True, save_path=str(RATIO_CSV))
                plat = analyzer.get_collections_plat_expectancy(save_path=str(PLAT_EXPECTANCY_CSV))
                analyzer.get_collections_dissolution_expectancy(save_path=str(DISSOLUTION_EXPECTANCY_CSV))
            else:
                analyzer = ArcanesAnalyzer(load_prices=str(PRICES_CSV))
                ratio = analyzer.get_plat_vosfor_ratio(include_collections=True)
                plat = analyzer.get_collections_plat_expectancy()
            return analyzer.arcane_prices, plat, ratio

        def on_progress(current, total):
            self.progress.set_progress(current / total, f"Fetching arcane prices…  {current}/{total}")

        def on_done(result):
            prices, plat, ratio = result
            self.price_table.set_rows(_rows(prices))
            self.collections_table.set_rows(_rows(plat))
            self.ratio_table.set_rows(_rows(ratio))
            self._loaded = True
            if live:
                text = f"Live prices fetched at {time.strftime('%H:%M')} · saved to {RESULTS_DIR.name}"
            else:
                saved_at = time.strftime("%Y-%m-%d %H:%M", time.localtime(PRICES_CSV.stat().st_mtime))
                text = f"Saved prices from {saved_at}"
            self.status.configure(text=text, foreground=theme.MUTED)
            self.find_bar.refresh()  # re-run any active search against the new rows

        def on_error(error):
            self.status.configure(text=f"Failed to load arcanes: {error}", foreground=theme.DANGER)

        def on_finish():
            self.progress.finish()
            self.fetch_button.state(["!disabled"])
            self.saved_button.state(["!disabled"])

        if self.app.run_task(work, on_progress=on_progress, on_done=on_done, on_error=on_error,
                             on_finish=on_finish):
            self.fetch_button.state(["disabled"])
            self.saved_button.state(["disabled"])
            self.progress.start("Fetching arcane prices…" if live else "Loading saved prices…")

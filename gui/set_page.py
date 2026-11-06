import tkinter as tk
from tkinter import ttk

import requests

from analysis.individual_or_set import analyse_set_vs_individual_for
from gui import theme
from gui.theme import px
from gui.widgets import ProgressPanel, page_header, prettify_slug

VERDICT_MESSAGES = {
    "set": "Set is better.",
    "individual": "Individual components are better.",
    "equal": "Both options have equal prices.",
    "unknown": "Insufficient market data.",
}
VERDICT_COLORS = {"set": theme.ACCENT, "individual": theme.SUCCESS, "equal": theme.MUTED, "unknown": theme.DANGER}


def _plat(value) -> str:
    return "—" if value is None else f"{value:,} plat"


class _VerdictCard(tk.Frame):
    def __init__(self, parent, title: str, subtitle: str):
        super().__init__(parent, bg=theme.SURFACE)
        self.bar = tk.Frame(self, bg=theme.MUTED, width=px(5))
        self.bar.pack(side="left", fill="y")
        body = tk.Frame(self, bg=theme.SURFACE, padx=px(18), pady=px(14))
        body.pack(side="left", fill="both", expand=True)
        tk.Label(body, text=title.upper(), font=theme.SMALL_BOLD, fg=theme.MUTED, bg=theme.SURFACE).pack(anchor="w")
        self.message = tk.Label(body, font=theme.BIG, fg=theme.TEXT, bg=theme.SURFACE)
        self.message.pack(anchor="w", pady=px(2))
        tk.Label(body, text=subtitle, font=theme.SMALL, fg=theme.MUTED, bg=theme.SURFACE).pack(anchor="w")

    def set_verdict(self, verdict: str) -> None:
        color = VERDICT_COLORS.get(verdict, theme.TEXT)
        self.bar.configure(bg=color)
        self.message.configure(text=VERDICT_MESSAGES.get(verdict, verdict), fg=color)


class SetAnalysisPage(ttk.Frame):
    def __init__(self, parent, app):
        super().__init__(parent, padding=px(20))
        self.app = app
        self.columnconfigure(0, weight=1)

        page_header(self, "Individual or Set", app.show_home,
                    "Compare a set's price with the total price of its parts").grid(row=0, column=0, sticky="ew")

        form = ttk.Frame(self, style="Surface.TFrame", padding=px(16))
        form.grid(row=1, column=0, sticky="ew", pady=(px(18), 0))
        ttk.Label(form, text="Item slug", style="SurfaceTitle.TLabel").grid(row=0, column=0, sticky="w",
                                                                         padx=(0, px(12)))
        self.slug_var = tk.StringVar()
        self.entry = ttk.Entry(form, textvariable=self.slug_var, width=40, font=theme.BODY)
        self.entry.grid(row=0, column=1, sticky="w")
        self.entry.bind("<Return>", lambda event: self.analyse())
        self.analyse_button = ttk.Button(form, text="Analyse", style="Accent.TButton", command=self.analyse)
        self.analyse_button.grid(row=0, column=2, padx=(px(12), 0))
        ttk.Label(form, text="e.g. mesa_prime or mesa_prime_set", style="SurfaceMuted.TLabel").grid(
            row=1, column=1, sticky="w", pady=(px(4), 0))

        self.progress = ProgressPanel(self)
        self.progress.grid(row=2, column=0, sticky="ew", pady=(px(12), 0))
        self.progress.grid_remove()

        self.error = ttk.Label(self, style="Error.TLabel")
        self.error.grid(row=3, column=0, sticky="w", pady=(px(12), 0))

        self.results = ttk.Frame(self)
        self.results.grid(row=4, column=0, sticky="ew", pady=(px(8), 0))
        self.results.columnconfigure(0, weight=1)
        self._build_results(self.results)
        self.results.grid_remove()

    def on_show(self) -> None:
        self.entry.focus_set()

    def _build_results(self, parent) -> None:
        self.set_title = ttk.Label(parent, style="H1.TLabel")
        self.set_title.grid(row=0, column=0, sticky="w")
        self.set_slug = ttk.Label(parent, style="Muted.TLabel")
        self.set_slug.grid(row=1, column=0, sticky="w")

        verdicts = ttk.Frame(parent)
        verdicts.grid(row=2, column=0, sticky="ew", pady=(px(14), 0))
        self.verdict_cards = {
            "buying": _VerdictCard(verdicts, "Buying", "Compares the lowest sell orders"),
            "selling": _VerdictCard(verdicts, "Selling", "Compares the highest buy orders"),
        }
        for column, card in enumerate(self.verdict_cards.values()):
            verdicts.columnconfigure(column, weight=1, uniform="verdicts")
            card.grid(row=0, column=column, sticky="nsew", padx=(0 if column == 0 else px(12), 0))

        prices = tk.Frame(parent, bg=theme.SURFACE, padx=px(18), pady=px(14))
        prices.grid(row=3, column=0, sticky="ew", pady=(px(12), 0))
        prices.columnconfigure(0, weight=1)
        prices.columnconfigure((1, 2), minsize=px(220))
        for column, text in ((1, "Set"), (2, "Individual parts total")):
            tk.Label(prices, text=text.upper(), font=theme.SMALL_BOLD, fg=theme.MUTED, bg=theme.SURFACE).grid(
                row=0, column=column, sticky="e")

        self.price_cells = {}
        for row, (key, title, subtitle) in enumerate((
                ("buying", "Buying price", "from the lowest online sell orders"),
                ("selling", "Selling price", "to the highest online buy orders")), 1):
            label = tk.Frame(prices, bg=theme.SURFACE)
            label.grid(row=row, column=0, sticky="w", pady=(px(10), 0))
            tk.Label(label, text=title, font=theme.BOLD, fg=theme.TEXT, bg=theme.SURFACE).pack(anchor="w")
            tk.Label(label, text=subtitle, font=theme.SMALL, fg=theme.MUTED, bg=theme.SURFACE).pack(anchor="w")
            cells = []
            for column in (1, 2):
                cell = tk.Label(prices, font=theme.H2, fg=theme.TEXT, bg=theme.SURFACE)
                cell.grid(row=row, column=column, sticky="e", pady=(px(10), 0))
                cells.append(cell)
            self.price_cells[key] = cells

        self.notes = ttk.Label(parent, style="Muted.TLabel", justify="left")
        self.notes.grid(row=4, column=0, sticky="w", pady=(px(10), 0))

    def analyse(self) -> None:
        slug = self.slug_var.get().strip().lower().replace(" ", "_")
        if not slug:
            self.error.configure(text="Enter an item slug, e.g. mesa_prime.")
            return

        def on_error(error):
            if isinstance(error, requests.HTTPError) and getattr(error.response, "status_code", None) == 404:
                self.error.configure(text=f"No set found for '{slug}'. Check the slug (e.g. mesa_prime).")
            else:
                self.error.configure(text=f"Analysis failed: {error}")

        def on_finish():
            self.progress.finish()
            self.analyse_button.state(["!disabled"])

        if self.app.run_task(lambda report: analyse_set_vs_individual_for(slug), on_done=self._show_result,
                             on_error=on_error, on_finish=on_finish):
            self.analyse_button.state(["disabled"])
            self.error.configure(text="")
            self.results.grid_remove()
            self.progress.start(f"Fetching orders for {slug} and its parts…", indeterminate=True)

    def _show_result(self, result: dict) -> None:
        self.set_title.configure(text=prettify_slug(result["set_slug"]))
        self.set_slug.configure(text=result["set_slug"])

        rows = (
            ("buying", result["set_sell_order_price"], result["individual_sell"], result["buying_verdict"]),
            ("selling", result["set_buy_order_price"], result["individual_buy"], result["selling_verdict"]),
        )
        notes = []
        for key, set_price, parts, verdict in rows:
            self.verdict_cards[key].set_verdict(verdict)
            set_cell, parts_cell = self.price_cells[key]
            set_cell.configure(text=_plat(set_price), fg=VERDICT_COLORS["set"] if verdict == "set" else theme.TEXT)
            if parts["complete"]:
                parts_text = _plat(parts["price"])
            else:
                parts_text = f"≥ {_plat(parts['known_total'])}  (incomplete)"
                notes.append(f"{key.capitalize()}: no orders for {', '.join(parts['missing'])} "
                             f"— known subtotal {_plat(parts['known_total'])}.")
            parts_cell.configure(text=parts_text,
                                 fg=VERDICT_COLORS["individual"] if verdict == "individual" else theme.TEXT)

        self.notes.configure(text="\n".join(notes))
        self.results.grid()

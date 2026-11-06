import tkinter as tk
from tkinter import ttk

from gui import theme
from gui.theme import px
from gui.widgets import ClickCard

OPTIONS = [
    ("arcanes", "Arcanes Analysis", "Arcane prices, collection expectancy and plat / Vosfor ratios"),
    ("syndicates", "Syndicates Profit", "Which syndicate offers give the most platinum per standing"),
    ("set", "Individual or Set", "Is it better to trade a set or its individual parts?"),
]


class HomePage(ttk.Frame):
    def __init__(self, parent, app):
        super().__init__(parent)
        inner = ttk.Frame(self)
        inner.place(relx=0.5, rely=0.45, anchor="center")

        ttk.Label(inner, text="Warframe Market Tool", style="Title.TLabel").pack()
        ttk.Label(inner, text="Choose an analysis", style="Muted.TLabel").pack(pady=(px(4), px(28)))

        for number, (page, title, description) in enumerate(OPTIONS, 1):
            card = ClickCard(inner, command=lambda p=page: app.show(p), padx=px(20), pady=px(14))
            card.pack(fill="x", pady=px(6))
            card.columnconfigure(1, weight=1)
            card.add(tk.Label(card, text=str(number), font=theme.NUMBER, fg=theme.ACCENT, width=2)).grid(
                row=0, column=0, rowspan=2, padx=(0, px(14)))
            card.add(tk.Label(card, text=title, font=theme.H2, fg=theme.TEXT, anchor="w")).grid(
                row=0, column=1, sticky="w")
            card.add(tk.Label(card, text=description, font=theme.BODY, fg=theme.MUTED, anchor="w")).grid(
                row=1, column=1, sticky="w")
            card.add(tk.Label(card, text="›", font=theme.NUMBER, fg=theme.MUTED)).grid(
                row=0, column=2, rowspan=2, padx=(px(24), 0))

"""Reusable widgets: sortable tables, a find bar, a progress panel and clickable cards."""
import tkinter as tk
import unicodedata
from dataclasses import dataclass
from tkinter import ttk
from typing import Any, Callable, Optional

from gui import theme
from gui.theme import px


def format_number(digits: int) -> Callable[[Any], str]:
    def fmt(value):
        return "—" if value is None else f"{value:,.{digits}f}"
    return fmt


def prettify_slug(slug: str) -> str:
    return slug.replace("_", " ").title()


def _normalize(text: str) -> str:
    """Case- and accent-insensitive form of text, so 'hollvania' finds 'Höllvania'."""
    decomposed = unicodedata.normalize("NFKD", text)
    return "".join(c for c in decomposed if not unicodedata.combining(c)).casefold()


def page_header(parent, title: str, on_back: Callable[[], None], subtitle: Optional[str] = None) -> ttk.Frame:
    """A 'Back' button followed by the page title. Pack extra controls into it with side='right'."""
    header = ttk.Frame(parent)
    ttk.Button(header, text="←  Back", command=on_back).pack(side="left", anchor="n")
    titles = ttk.Frame(header)
    titles.pack(side="left", padx=(px(16), 0))
    ttk.Label(titles, text=title, style="H1.TLabel").pack(anchor="w")
    if subtitle:
        ttk.Label(titles, text=subtitle, style="Muted.TLabel").pack(anchor="w")
    return header


@dataclass
class Column:
    key: str
    heading: str
    width: int = 120
    anchor: str = "w"
    fmt: Callable[[Any], str] = str
    stretch: bool = False


class DataTable(ttk.Frame):
    """A titled table of dict rows, sorted by `sort_key` (largest first by default).

    Rows whose sort value is None always stay at the bottom.
    """

    def __init__(self, parent, *, title: str, columns: list[Column], sort_key: str,
                 subtitle: Optional[str] = None, search_key: Optional[str] = None,
                 is_highlighted: Optional[Callable[[dict], bool]] = None,
                 legend: Optional[list[tuple[str, str, str]]] = None, descending: bool = True,
                 height: int = 8):
        super().__init__(parent, style="Surface.TFrame", padding=px(12))
        self.columns = columns
        self.sort_key = sort_key
        self.search_key = search_key or columns[0].key
        self.is_highlighted = is_highlighted
        self.descending = descending
        self._rows: list[dict] = []
        self._query = ""
        self._matches: list[str] = []
        self._match_index = 0
        self._row_tags: dict[str, str] = {}  # iid -> its normal tag (restored when deselected)
        self._current_iid: Optional[str] = None

        self.columnconfigure(0, weight=1)
        self.rowconfigure(1, weight=1)

        header = ttk.Frame(self, style="Surface.TFrame")
        header.grid(row=0, column=0, sticky="ew", pady=(0, px(8)))
        header.columnconfigure(0, weight=1)
        ttk.Label(header, text=title, style="SurfaceTitle.TLabel").grid(row=0, column=0, sticky="w")
        ttk.Button(header, text="↑↓  Reverse", style="Chip.TButton", command=self.reverse).grid(
            row=0, column=1, sticky="e", padx=(px(8), 0))
        if subtitle:
            label = ttk.Label(header, text=subtitle, style="SurfaceMuted.TLabel")
            label.grid(row=1, column=0, columnspan=2, sticky="ew")
            label.bind("<Configure>", lambda event: label.configure(wraplength=max(event.width, px(120))))
        if legend:
            chips = ttk.Frame(header, style="Surface.TFrame")
            chips.grid(row=2, column=0, columnspan=2, sticky="w", pady=(px(6), 0))
            for text, bg, fg in legend:
                tk.Label(chips, text=text, bg=bg, fg=fg, font=theme.SMALL, padx=px(8), pady=px(1)).pack(
                    side="left", padx=(0, px(6)))

        body = ttk.Frame(self, style="Surface.TFrame")
        body.grid(row=1, column=0, sticky="nsew")
        body.columnconfigure(0, weight=1)
        body.rowconfigure(0, weight=1)

        self.tree = ttk.Treeview(body, columns=["rank"] + [c.key for c in columns], show="headings",
                                 selectmode="browse", height=height)
        self.tree.grid(row=0, column=0, sticky="nsew")
        scrollbar = ttk.Scrollbar(body, orient="vertical", command=self.tree.yview)
        scrollbar.grid(row=0, column=1, sticky="ns")
        self.tree.configure(yscrollcommand=scrollbar.set)

        self.tree.heading("rank", text="#", anchor="e")
        self.tree.column("rank", width=px(44), minwidth=px(36), anchor="e", stretch=False)
        for column in columns:
            options = {"text": column.heading, "anchor": column.anchor}
            if column.key == sort_key:
                options["command"] = self.reverse
            self.tree.heading(column.key, **options)
            self.tree.column(column.key, width=px(column.width), minwidth=px(60),
                             anchor=column.anchor, stretch=column.stretch)

        self.tree.tag_configure("even", background=theme.SURFACE)
        self.tree.tag_configure("odd", background=theme.SURFACE_ALT)
        self.tree.tag_configure("highlight_even", background=theme.HIGHLIGHT_BG, foreground=theme.HIGHLIGHT_FG)
        self.tree.tag_configure("highlight_odd", background=theme.HIGHLIGHT_BG_ALT, foreground=theme.HIGHLIGHT_FG)
        # Row tag colors hide Tk's own selection color, so the selected row gets its own tag.
        self.tree.tag_configure("current", background=theme.ACCENT, foreground=theme.ACCENT_TEXT)
        self.tree.bind("<<TreeviewSelect>>", lambda event: self._mark_selection())
        self._update_sort_heading()

    def set_rows(self, rows: list[dict]) -> None:
        self._rows = list(rows)
        self._render()

    def reverse(self) -> None:
        self.descending = not self.descending
        self._render()

    def _update_sort_heading(self) -> None:
        column = next(c for c in self.columns if c.key == self.sort_key)
        arrow = "▼" if self.descending else "▲"
        self.tree.heading(column.key, text=f"{column.heading}  {arrow}")

    def _render(self) -> None:
        selected = self.tree.selection()
        key = self.sort_key
        indexed = list(enumerate(self._rows))
        present = [item for item in indexed if item[1].get(key) is not None]
        missing = [item for item in indexed if item[1].get(key) is None]
        present.sort(key=lambda item: item[1][key], reverse=self.descending)

        self.tree.delete(*self.tree.get_children())
        self._row_tags.clear()
        self._current_iid = None
        for position, (index, row) in enumerate(present + missing, 1):
            parity = "even" if position % 2 else "odd"
            tag = f"highlight_{parity}" if self.is_highlighted and self.is_highlighted(row) else parity
            rank = position if row.get(key) is not None else ""
            values = [rank] + [column.fmt(row.get(column.key)) for column in self.columns]
            self.tree.insert("", "end", iid=str(index), values=values, tags=(tag,))
            self._row_tags[str(index)] = tag
        self._update_sort_heading()

        if self._query:
            self.search(self._query, keep_current=selected[0] if selected else None)
        elif selected and self.tree.exists(selected[0]):
            self.tree.selection_set(selected[0])
            self.tree.see(selected[0])

    def _mark_selection(self) -> None:
        if self._current_iid and self.tree.exists(self._current_iid):
            self.tree.item(self._current_iid, tags=(self._row_tags[self._current_iid],))
        selection = self.tree.selection()
        self._current_iid = selection[0] if selection else None
        if self._current_iid:
            self.tree.item(self._current_iid, tags=("current",))

    # --- find support -------------------------------------------------------------------------

    def search(self, query: str, keep_current: Optional[str] = None) -> int:
        """Select the first row whose search column contains `query`; returns the match count."""
        self._query = _normalize(query.strip())
        if self._query:
            self._matches = [iid for iid in self.tree.get_children()
                             if self._query in _normalize(str(self._rows[int(iid)][self.search_key]))]
        else:
            self._matches = []
        self._match_index = self._matches.index(keep_current) if keep_current in self._matches else 0
        self._show_match()
        return len(self._matches)

    def step_match(self, step: int) -> None:
        if self._matches:
            self._match_index = (self._match_index + step) % len(self._matches)
            self._show_match()

    def _show_match(self) -> None:
        if self._matches:
            iid = self._matches[self._match_index]
            self.tree.selection_set(iid)
            self.tree.update_idletasks()  # settle the layout so the visible row range is accurate
            first, last = self.tree.yview()
            position = self.tree.index(iid) / max(1, len(self.tree.get_children()))
            if not first <= position < last:  # jump so the match sits mid-table
                self.tree.yview_moveto(max(0.0, position - (last - first) / 2))
        else:
            self.tree.selection_set(())


class FindBar(ttk.Frame):
    """Ctrl+F bar that jumps to matching rows in every table given by `get_tables`."""

    def __init__(self, parent, get_tables: Callable[[], list[DataTable]]):
        super().__init__(parent, style="Surface.TFrame", padding=(px(12), px(8)))
        self._get_tables = get_tables
        self.var = tk.StringVar()

        ttk.Label(self, text="Find", style="SurfaceTitle.TLabel").pack(side="left", padx=(0, px(10)))
        self.entry = ttk.Entry(self, textvariable=self.var, width=36, font=theme.BODY)
        self.entry.pack(side="left")
        self.count = ttk.Label(self, style="SurfaceMuted.TLabel")
        self.count.pack(side="left", padx=px(10))
        ttk.Label(self, text="Enter / Shift+Enter to cycle matches, Esc to close",
                  style="SurfaceMuted.TLabel").pack(side="left", padx=px(10))
        ttk.Button(self, text="✕", style="Chip.TButton", width=3, command=self.hide).pack(side="right")
        ttk.Button(self, text="▼", style="Chip.TButton", width=3, command=lambda: self._step(1)).pack(
            side="right", padx=(px(4), px(8)))
        ttk.Button(self, text="▲", style="Chip.TButton", width=3, command=lambda: self._step(-1)).pack(side="right")

        self.var.trace_add("write", lambda *_: self.refresh())
        for sequence, step in (("<Return>", 1), ("<Down>", 1), ("<Shift-Return>", -1), ("<Up>", -1)):
            self.entry.bind(sequence, lambda event, s=step: self._step(s) or "break")
        self.entry.bind("<Escape>", lambda event: self.hide())

    def show(self) -> None:
        self.grid()
        self.entry.focus_set()
        self.entry.select_range(0, "end")

    def hide(self) -> None:
        self.var.set("")
        self.grid_remove()

    def refresh(self) -> None:
        query = self.var.get()
        total = sum(table.search(query) for table in self._get_tables())
        if not query.strip():
            self.count.configure(text="")
        elif total:
            self.count.configure(text=f"{total} match{'es' if total != 1 else ''}", foreground=theme.MUTED)
        else:
            self.count.configure(text="No matches", foreground=theme.DANGER)

    def _step(self, step: int) -> None:
        for table in self._get_tables():
            table.step_match(step)


class ProgressPanel(ttk.Frame):
    """A label plus loading bar. Grid it once, then call grid_remove(); start() shows it."""

    def __init__(self, parent):
        super().__init__(parent, style="Surface.TFrame", padding=(px(14), px(10)))
        self.columnconfigure(0, weight=1)
        self._text = ttk.Label(self, style="Surface.TLabel")
        self._text.grid(row=0, column=0, sticky="w")
        self._percent = ttk.Label(self, style="SurfaceMuted.TLabel")
        self._percent.grid(row=0, column=1, sticky="e")
        self._bar = ttk.Progressbar(self, orient="horizontal", mode="determinate", maximum=1.0)
        self._bar.grid(row=1, column=0, columnspan=2, sticky="ew", pady=(px(6), 0))

    def start(self, text: str, indeterminate: bool = False) -> None:
        self.grid()
        self._text.configure(text=text)
        self._bar.stop()
        if indeterminate:
            self._percent.configure(text="")
            self._bar.configure(mode="indeterminate")
            self._bar.start(15)
        else:
            self._bar.configure(mode="determinate", value=0)
            self._percent.configure(text="0%")

    def set_progress(self, fraction: float, text: Optional[str] = None) -> None:
        self._bar.configure(value=fraction)
        self._percent.configure(text=f"{int(fraction * 100)}%")
        if text:
            self._text.configure(text=text)

    def finish(self) -> None:
        self._bar.stop()
        self.grid_remove()


class ClickCard(tk.Frame):
    """A clickable card with hover and (optional) selected states. Register children with add()."""

    def __init__(self, parent, command: Callable[[], None], *, padx: int = 0, pady: int = 0):
        super().__init__(parent, bg=theme.SURFACE, highlightthickness=max(1, px(2)),
                         highlightbackground=theme.BORDER, highlightcolor=theme.BORDER,
                         padx=padx, pady=pady, cursor="hand2")
        self._command = command
        self._hovered = False
        self.selected = False
        self._bind_events(self)

    def add(self, widget: tk.Widget) -> tk.Widget:
        widget.configure(bg=self["bg"], cursor="hand2")
        self._bind_events(widget)
        return widget

    def set_selected(self, selected: bool) -> None:
        self.selected = selected
        self._refresh()

    def _bind_events(self, widget: tk.Widget) -> None:
        widget.bind("<Enter>", self._on_enter, add="+")
        widget.bind("<Leave>", self._on_leave, add="+")
        widget.bind("<ButtonRelease-1>", self._on_click, add="+")

    def _pointer_inside(self) -> bool:
        try:
            widget = self.winfo_containing(*self.winfo_pointerxy())
        except (KeyError, tk.TclError):
            return False
        return widget is not None and (widget == self or str(widget).startswith(f"{self}."))

    def _on_enter(self, _event) -> None:
        self._hovered = True
        self._refresh()

    def _on_leave(self, _event) -> None:
        self._hovered = self._pointer_inside()
        self._refresh()

    def _on_click(self, _event) -> None:
        if self._pointer_inside():
            self._command()

    def _refresh(self) -> None:
        if self.selected:
            bg, border = theme.SELECTED_CARD, theme.ACCENT
        elif self._hovered:
            bg, border = theme.SURFACE_HIGH, theme.ACCENT
        else:
            bg, border = theme.SURFACE, theme.BORDER
        self.configure(bg=bg, highlightbackground=border, highlightcolor=border)
        for child in self.winfo_children():
            child.configure(bg=bg)

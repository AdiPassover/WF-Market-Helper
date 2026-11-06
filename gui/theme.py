"""Colors, fonts and ttk styling for the GUI (a dark theme with a gold accent)."""
import tkinter as tk
import tkinter.font as tkfont
from tkinter import ttk

BG = "#15171c"
SURFACE = "#1d2027"
SURFACE_ALT = "#22262e"
SURFACE_HIGH = "#2a2e38"
BORDER = "#343a46"
TEXT = "#e8eaef"
MUTED = "#98a1b0"
ACCENT = "#d6b16b"
ACCENT_HOVER = "#e4c588"
ACCENT_TEXT = "#15171c"
SELECTED_CARD = "#2d2920"
SUCCESS = "#5fc9a8"
DANGER = "#e07a7a"

# Highlighted rows (e.g. arcane collections in the plat/vosfor table).
HIGHLIGHT_BG = "#262c4d"
HIGHLIGHT_BG_ALT = "#2b3256"
HIGHLIGHT_FG = "#c3cbff"

FONT_FAMILY = "Segoe UI"
TITLE = (FONT_FAMILY, 24, "bold")
H1 = (FONT_FAMILY, 18, "bold")
H2 = (FONT_FAMILY, 13, "bold")
BIG = (FONT_FAMILY, 15, "bold")
NUMBER = (FONT_FAMILY, 22, "bold")
BODY = (FONT_FAMILY, 10)
BOLD = (FONT_FAMILY, 10, "bold")
SMALL = (FONT_FAMILY, 9)
SMALL_BOLD = (FONT_FAMILY, 9, "bold")

_scale = 1.0


def px(value: float) -> int:
    """Scale a pixel size for the screen's DPI (fonts scale on their own)."""
    return int(round(value * _scale))


def setup(root: tk.Tk) -> None:
    global _scale
    _scale = root.winfo_fpixels("1i") / 96.0
    root.configure(bg=BG)

    style = ttk.Style(root)
    style.theme_use("clam")

    style.configure(
        ".", background=BG, foreground=TEXT, font=BODY, bordercolor=BORDER,
        lightcolor=BG, darkcolor=BG, troughcolor=SURFACE, fieldbackground=SURFACE_HIGH,
        selectbackground=ACCENT, selectforeground=ACCENT_TEXT, insertcolor=TEXT, focuscolor=BG,
    )

    style.configure("TFrame", background=BG)
    style.configure("Surface.TFrame", background=SURFACE)

    style.configure("TLabel", background=BG, foreground=TEXT)
    style.configure("Muted.TLabel", foreground=MUTED)
    style.configure("Title.TLabel", font=TITLE)
    style.configure("H1.TLabel", font=H1)
    style.configure("Error.TLabel", foreground=DANGER)
    style.configure("Surface.TLabel", background=SURFACE)
    style.configure("SurfaceTitle.TLabel", background=SURFACE, font=H2)
    style.configure("SurfaceMuted.TLabel", background=SURFACE, foreground=MUTED, font=SMALL)

    button_colors = dict(background=SURFACE_HIGH, lightcolor=SURFACE_HIGH, darkcolor=SURFACE_HIGH)
    style.configure("TButton", foreground=TEXT, bordercolor=BORDER, relief="flat",
                    padding=(px(14), px(6)), **button_colors)
    hover = [("disabled", SURFACE), ("pressed", BORDER), ("active", BORDER)]
    style.map("TButton", background=hover, lightcolor=hover, darkcolor=hover,
              foreground=[("disabled", MUTED)])

    style.configure("Accent.TButton", background=ACCENT, lightcolor=ACCENT, darkcolor=ACCENT,
                    foreground=ACCENT_TEXT, bordercolor=ACCENT, font=BOLD, padding=(px(18), px(6)))
    accent_hover = [("disabled", SURFACE_HIGH), ("pressed", ACCENT), ("active", ACCENT_HOVER)]
    style.map("Accent.TButton", background=accent_hover, lightcolor=accent_hover, darkcolor=accent_hover,
              bordercolor=accent_hover, foreground=[("disabled", MUTED)])

    style.configure("Chip.TButton", font=SMALL, padding=(px(10), px(3)))

    rowheight = tkfont.Font(root=root, font=BODY).metrics("linespace") + px(10)
    style.configure("Treeview", background=SURFACE, fieldbackground=SURFACE, foreground=TEXT,
                    rowheight=rowheight, borderwidth=0, font=BODY)
    style.map("Treeview", background=[("selected", ACCENT)], foreground=[("selected", ACCENT_TEXT)])
    style.layout("Treeview", [("Treeview.treearea", {"sticky": "nswe"})])
    style.configure("Treeview.Heading", background=SURFACE_HIGH, lightcolor=SURFACE_HIGH,
                    darkcolor=SURFACE_HIGH, bordercolor=SURFACE, foreground=MUTED, font=SMALL_BOLD,
                    relief="flat", padding=(px(6), px(5)))
    style.map("Treeview.Heading", background=[("active", BORDER)], foreground=[("active", TEXT)])

    style.configure("Vertical.TScrollbar", background=SURFACE_HIGH, troughcolor=SURFACE,
                    bordercolor=SURFACE, lightcolor=SURFACE_HIGH, darkcolor=SURFACE_HIGH,
                    arrowcolor=MUTED, gripcount=0, arrowsize=px(12))
    style.map("Vertical.TScrollbar", background=[("active", BORDER)])

    style.configure("Horizontal.TProgressbar", background=ACCENT, troughcolor=SURFACE_HIGH,
                    bordercolor=SURFACE_HIGH, lightcolor=ACCENT, darkcolor=ACCENT, thickness=px(8))

    style.configure("TEntry", fieldbackground=SURFACE_HIGH, foreground=TEXT, bordercolor=BORDER,
                    lightcolor=SURFACE_HIGH, darkcolor=SURFACE_HIGH, insertcolor=TEXT,
                    padding=(px(8), px(5)))
    style.map("TEntry", bordercolor=[("focus", ACCENT)], lightcolor=[("focus", ACCENT)])

    style.configure("TNotebook", background=BG, borderwidth=0, bordercolor=BG,
                    lightcolor=BG, darkcolor=BG, tabmargins=(0, 0, 0, 0))
    style.configure("TNotebook.Tab", background=SURFACE, foreground=MUTED, bordercolor=BG,
                    lightcolor=SURFACE, darkcolor=SURFACE, padding=(px(12), px(6)))
    style.map("TNotebook.Tab", background=[("selected", SURFACE_HIGH)], foreground=[("selected", TEXT)],
              lightcolor=[("selected", ACCENT)])

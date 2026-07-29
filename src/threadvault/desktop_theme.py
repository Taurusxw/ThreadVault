from __future__ import annotations

from dataclasses import dataclass, field
from tkinter import Menu, TclError, Text, Tk, Toplevel, ttk


@dataclass(frozen=True)
class DesktopPalette:
    """Semantic colors shared by every ThreadVault desktop surface."""

    canvas: str = "#F3F6FA"
    surface: str = "#FFFFFF"
    surface_muted: str = "#EAF0F7"
    ink: str = "#172033"
    muted: str = "#64748B"
    border: str = "#D8E0EA"
    accent: str = "#1463D6"
    accent_hover: str = "#0E4FAF"
    accent_soft: str = "#E8F1FF"
    success: str = "#16794A"
    success_soft: str = "#E9F7EF"
    warning: str = "#A85D00"
    warning_soft: str = "#FFF5E6"
    danger: str = "#B42318"
    danger_soft: str = "#FDECEC"
    disabled_bg: str = "#F5F7FA"
    disabled_fg: str = "#9AA7B8"


@dataclass(frozen=True)
class DesktopAppTheme:
    font_family: str = "Segoe UI"
    font_size: int = 10
    window_width: int = 1080
    window_height: int = 700
    palette: DesktopPalette = field(default_factory=DesktopPalette)


def configure_desktop_theme(root: Tk, theme: DesktopAppTheme) -> ttk.Style:
    """Apply one restrained visual system to ttk and Tk widget surfaces."""

    palette = theme.palette
    font = (theme.font_family, theme.font_size)
    root.configure(background=palette.canvas)
    root.option_add("*Font", font)
    root.option_add("*Text.background", palette.surface)
    root.option_add("*Text.foreground", palette.ink)
    root.option_add("*Text.insertBackground", palette.ink)
    root.option_add("*Text.selectBackground", palette.accent)
    root.option_add("*Text.selectForeground", palette.surface)
    root.option_add("*Text.highlightBackground", palette.border)
    root.option_add("*Text.highlightColor", palette.accent)
    root.option_add("*Menu.background", palette.surface)
    root.option_add("*Menu.foreground", palette.ink)
    root.option_add("*Menu.activeBackground", palette.accent_soft)
    root.option_add("*Menu.activeForeground", palette.accent_hover)
    root.option_add("*Menu.disabledForeground", palette.disabled_fg)

    style = ttk.Style(root)
    try:
        style.theme_use("clam")
    except TclError:
        pass

    style.configure(".", background=palette.surface, foreground=palette.ink, font=font)
    style.configure("TFrame", background=palette.surface)
    style.configure("Header.TFrame", background=palette.surface)
    style.configure("Toolbar.TFrame", background=palette.surface_muted)
    style.configure("Status.TFrame", background=palette.surface_muted)
    style.configure("Dialog.TFrame", background=palette.surface)
    style.configure("TLabel", background=palette.surface, foreground=palette.ink)
    style.configure("AppTitle.TLabel", background=palette.surface, foreground=palette.ink, font=(theme.font_family, 17, "bold"))
    style.configure("AppSubtitle.TLabel", background=palette.surface, foreground=palette.muted)
    style.configure("Toolbar.TLabel", background=palette.surface_muted, foreground=palette.ink)
    style.configure("Status.TLabel", background=palette.surface_muted, foreground=palette.muted)
    style.configure("Heading.TLabel", background=palette.surface, foreground=palette.ink, font=(theme.font_family, 14, "bold"))
    style.configure("Hint.TLabel", background=palette.surface, foreground=palette.muted)
    style.configure("DialogTitle.TLabel", background=palette.surface, foreground=palette.ink, font=(theme.font_family, 13, "bold"))
    style.configure("DialogBody.TLabel", background=palette.surface, foreground=palette.ink)
    style.configure(
        "Badge.TLabel",
        background=palette.accent_soft,
        foreground=palette.accent_hover,
        font=(theme.font_family, theme.font_size - 1, "bold"),
        padding=(8, 3),
    )

    style.configure("TButton", background=palette.surface, foreground=palette.ink, bordercolor=palette.border, padding=(10, 6))
    style.map(
        "TButton",
        background=[("disabled", palette.disabled_bg), ("pressed", palette.accent_soft), ("active", palette.surface_muted)],
        foreground=[("disabled", palette.disabled_fg), ("pressed", palette.accent_hover), ("active", palette.accent_hover)],
        bordercolor=[("focus", palette.accent), ("active", palette.accent_hover), ("disabled", palette.border)],
    )
    style.configure("Quiet.TButton", background=palette.surface, foreground=palette.ink, bordercolor=palette.border)
    style.configure("Accent.TButton", background=palette.accent, foreground=palette.surface, bordercolor=palette.accent)
    style.map(
        "Accent.TButton",
        background=[("disabled", palette.disabled_bg), ("pressed", palette.accent_hover), ("active", palette.accent_hover)],
        foreground=[("disabled", palette.disabled_fg), ("!disabled", palette.surface)],
        bordercolor=[("focus", palette.ink), ("active", palette.accent_hover), ("disabled", palette.border)],
    )
    style.configure("Success.TButton", background=palette.success, foreground=palette.surface, bordercolor=palette.success)
    style.map(
        "Success.TButton",
        background=[("disabled", palette.disabled_bg), ("pressed", palette.success), ("active", palette.success)],
        foreground=[("disabled", palette.disabled_fg), ("!disabled", palette.surface)],
        bordercolor=[("focus", palette.ink), ("disabled", palette.border)],
    )
    style.configure("Danger.TButton", background=palette.danger_soft, foreground=palette.danger, bordercolor=palette.danger_soft)
    style.map(
        "Danger.TButton",
        background=[("disabled", palette.disabled_bg), ("pressed", palette.danger_soft), ("active", palette.danger_soft)],
        foreground=[("disabled", palette.disabled_fg), ("!disabled", palette.danger)],
        bordercolor=[("focus", palette.danger), ("active", palette.danger), ("disabled", palette.border)],
    )
    style.configure(
        "TMenubutton",
        background=palette.surface,
        foreground=palette.ink,
        bordercolor=palette.border,
        lightcolor=palette.border,
        darkcolor=palette.border,
        arrowcolor=palette.muted,
        padding=(10, 6),
    )
    style.map(
        "TMenubutton",
        background=[("disabled", palette.disabled_bg), ("pressed", palette.accent_soft), ("active", palette.surface_muted)],
        foreground=[("disabled", palette.disabled_fg), ("active", palette.accent_hover)],
        bordercolor=[("disabled", palette.border), ("focus", palette.accent), ("active", palette.accent_hover)],
        arrowcolor=[("disabled", palette.disabled_fg), ("active", palette.accent_hover)],
    )

    style.configure(
        "TEntry",
        background=palette.surface,
        fieldbackground=palette.surface,
        foreground=palette.ink,
        bordercolor=palette.border,
        lightcolor=palette.border,
        darkcolor=palette.border,
        insertcolor=palette.ink,
        padding=(7, 5),
    )
    style.map(
        "TEntry",
        background=[("disabled", palette.disabled_bg), ("readonly", palette.surface)],
        fieldbackground=[("disabled", palette.disabled_bg), ("readonly", palette.surface)],
        foreground=[("disabled", palette.disabled_fg)],
        bordercolor=[("focus", palette.accent), ("disabled", palette.border)],
    )
    style.configure(
        "TCombobox",
        fieldbackground=palette.surface,
        background=palette.surface,
        foreground=palette.ink,
        bordercolor=palette.border,
        lightcolor=palette.border,
        darkcolor=palette.border,
        arrowcolor=palette.muted,
        padding=(6, 4),
    )
    style.map(
        "TCombobox",
        background=[("disabled", palette.disabled_bg), ("active", palette.accent_soft), ("readonly", palette.surface)],
        fieldbackground=[("disabled", palette.disabled_bg), ("readonly", palette.surface)],
        foreground=[("disabled", palette.disabled_fg)],
        bordercolor=[("focus", palette.accent), ("disabled", palette.border)],
        arrowcolor=[("disabled", palette.disabled_fg), ("active", palette.accent_hover)],
    )
    style.configure(
        "TLabelframe",
        background=palette.surface,
        bordercolor=palette.border,
        lightcolor=palette.border,
        darkcolor=palette.border,
        padding=8,
    )
    style.map("TLabelframe", background=[("disabled", palette.disabled_bg)])
    style.configure(
        "TLabelframe.Label", background=palette.surface, foreground=palette.ink, font=(theme.font_family, theme.font_size, "bold")
    )
    style.configure("TNotebook", background=palette.canvas, bordercolor=palette.border, tabmargins=(0, 0, 0, 0))
    style.configure(
        "TNotebook.Tab", background=palette.surface_muted, foreground=palette.muted, bordercolor=palette.border, padding=(12, 7)
    )
    style.map(
        "TNotebook.Tab",
        background=[("selected", palette.surface), ("active", palette.accent_soft)],
        foreground=[("selected", palette.accent_hover), ("active", palette.accent_hover)],
        bordercolor=[("selected", palette.border), ("focus", palette.accent)],
    )
    style.configure(
        "Treeview",
        background=palette.surface,
        fieldbackground=palette.surface,
        foreground=palette.ink,
        bordercolor=palette.border,
        rowheight=28,
    )
    style.map(
        "Treeview",
        background=[("disabled", palette.disabled_bg), ("selected", palette.accent)],
        foreground=[("disabled", palette.disabled_fg), ("selected", palette.surface)],
        bordercolor=[("focus", palette.accent)],
    )
    style.configure(
        "Treeview.Heading",
        background=palette.surface_muted,
        foreground=palette.ink,
        bordercolor=palette.border,
        padding=(7, 5),
        font=(theme.font_family, theme.font_size, "bold"),
    )
    style.map("Treeview.Heading", background=[("active", palette.accent_soft)], foreground=[("active", palette.accent_hover)])
    style.configure(
        "Vertical.TScrollbar",
        background=palette.surface_muted,
        troughcolor=palette.canvas,
        bordercolor=palette.border,
        arrowcolor=palette.muted,
    )
    style.configure(
        "Horizontal.TScrollbar",
        background=palette.surface_muted,
        troughcolor=palette.canvas,
        bordercolor=palette.border,
        arrowcolor=palette.muted,
    )
    for scrollbar_style in ("Vertical.TScrollbar", "Horizontal.TScrollbar"):
        style.map(
            scrollbar_style,
            background=[("disabled", palette.disabled_bg), ("active", palette.accent_soft), ("pressed", palette.accent_soft)],
            arrowcolor=[("disabled", palette.disabled_fg), ("active", palette.accent_hover)],
        )
    style.configure(
        "Horizontal.TProgressbar", background=palette.accent, troughcolor=palette.surface_muted, bordercolor=palette.surface_muted
    )
    style.configure("TPanedwindow", background=palette.canvas, sashwidth=6)
    style.configure("TSeparator", background=palette.border)
    return style


def configure_text_surface(widget: Text, theme: DesktopAppTheme) -> None:
    palette = theme.palette
    widget.configure(
        background=palette.surface,
        foreground=palette.ink,
        insertbackground=palette.ink,
        selectbackground=palette.accent,
        selectforeground=palette.surface,
        relief="flat",
        borderwidth=0,
        highlightthickness=1,
        highlightbackground=palette.border,
        highlightcolor=palette.accent,
        padx=9,
        pady=7,
    )


def configure_popup_menu(menu: Menu, theme: DesktopAppTheme) -> None:
    palette = theme.palette
    menu.configure(
        background=palette.surface,
        foreground=palette.ink,
        activebackground=palette.accent_soft,
        activeforeground=palette.accent_hover,
        disabledforeground=palette.disabled_fg,
        borderwidth=1,
        relief="solid",
        activeborderwidth=0,
        selectcolor=palette.accent,
        font=(theme.font_family, theme.font_size),
    )


def ask_themed_confirmation(
    parent: Tk,
    theme: DesktopAppTheme,
    message: str,
    *,
    title: str = "ThreadVault",
    confirm_text: str = "继续",
) -> bool:
    """Show a local, keyboard-safe confirmation dialog that follows the app theme."""

    dialog = Toplevel(parent)
    dialog.title(title)
    dialog.transient(parent)
    dialog.resizable(False, False)
    dialog.configure(background=theme.palette.canvas)
    result = False

    content = ttk.Frame(dialog, style="Dialog.TFrame", padding=(20, 18))
    content.pack(fill="both", expand=True)
    ttk.Label(content, text=title, style="DialogTitle.TLabel").pack(anchor="w", pady=(0, 8))
    ttk.Label(content, text=message, style="DialogBody.TLabel", justify="left", wraplength=480).pack(anchor="w", fill="x")
    buttons = ttk.Frame(content, style="Dialog.TFrame")
    buttons.pack(anchor="e", fill="x", pady=(18, 0))

    def close(answer: bool) -> None:
        nonlocal result
        result = answer
        try:
            dialog.grab_release()
        except TclError:
            pass
        dialog.destroy()

    confirm = ttk.Button(buttons, text=confirm_text, style="Accent.TButton", command=lambda: close(True), takefocus=True)
    confirm.pack(side="right")
    cancel = ttk.Button(buttons, text="取消", style="Quiet.TButton", command=lambda: close(False), takefocus=True)
    cancel.pack(side="right", padx=(0, 8))
    dialog.protocol("WM_DELETE_WINDOW", lambda: close(False))
    dialog.bind("<Escape>", lambda _event: close(False))
    dialog.bind("<Return>", lambda _event: close(True))
    dialog.update_idletasks()
    x = parent.winfo_rootx() + max((parent.winfo_width() - dialog.winfo_width()) // 2, 0)
    y = parent.winfo_rooty() + max((parent.winfo_height() - dialog.winfo_height()) // 3, 0)
    dialog.geometry(f"+{x}+{y}")
    dialog.grab_set()
    cancel.focus_set()
    parent.wait_window(dialog)
    return result

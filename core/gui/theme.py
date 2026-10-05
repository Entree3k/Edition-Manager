"""Theming: one set of color tokens drives both the palette and the stylesheet,
so light and dark mode share a single definition."""

from __future__ import annotations

from dataclasses import dataclass

from PySide6 import QtGui, QtWidgets


def _shift(hex_color: str, factor: float) -> str:
    """Lighten (factor > 0) or darken (factor < 0) a hex color."""
    color = QtGui.QColor(hex_color)
    if factor >= 0:
        rgb = (min(255, int(c * (1 + factor))) for c in (color.red(), color.green(), color.blue()))
    else:
        rgb = (max(0, int(c * (1 + factor))) for c in (color.red(), color.green(), color.blue()))
    r, g, b = rgb
    return f"#{r:02x}{g:02x}{b:02x}"


@dataclass
class Tokens:
    window: str       # main window background
    card: str         # card / panel background
    base: str         # input & log background
    border: str
    text: str
    subtext: str
    hover: str        # subtle hover wash for outlined/text buttons
    accent: str
    accent_hover: str
    accent_disabled: str
    on_accent: str = "#FFFFFF"
    success: str = "#1E8E3E"
    danger: str = "#D93025"
    warning: str = "#E37400"


def tokens(dark: bool, accent: str) -> Tokens:
    color = QtGui.QColor(accent)
    accent = color.name() if color.isValid() else "#5687F5"
    # Choose readable text even when the user picks a very light accent.
    components = (color.redF(), color.greenF(), color.blueF())
    linear = [c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4 for c in components]
    luminance = sum(c * weight for c, weight in zip(linear, (0.2126, 0.7152, 0.0722)))
    on_accent = "#111827" if luminance > 0.3 else "#FFFFFF"
    if dark:
        return Tokens(
            window="#10141D", card="#191F2B", base="#131924", border="#2C3545",
            text="#EEF2FA", subtext="#9CAAC0", hover="#252E3F",
            accent=accent, accent_hover=_shift(accent, 0.15), accent_disabled=_shift(accent, -0.45),
            on_accent=on_accent, success="#71D8AB", danger="#FF9494", warning="#EBC078",
        )
    return Tokens(
        window="#F3F5F9", card="#FFFFFF", base="#F8FAFD", border="#DDE3ED",
        text="#19253A", subtext="#607086", hover="#EDF1F8",
        accent=accent, accent_hover=_shift(accent, -0.13), accent_disabled=_shift(accent, 0.45),
        on_accent=on_accent, success="#157950", danger="#C93648", warning="#966013",
    )


def palette(t: Tokens) -> QtGui.QPalette:
    pal = QtGui.QPalette()
    roles = {
        QtGui.QPalette.Window: t.window,
        QtGui.QPalette.WindowText: t.text,
        QtGui.QPalette.Base: t.base,
        QtGui.QPalette.AlternateBase: t.card,
        QtGui.QPalette.ToolTipBase: t.card,
        QtGui.QPalette.ToolTipText: t.text,
        QtGui.QPalette.Text: t.text,
        QtGui.QPalette.Button: t.card,
        QtGui.QPalette.ButtonText: t.text,
        QtGui.QPalette.Highlight: t.accent,
        QtGui.QPalette.HighlightedText: t.on_accent,
    }
    for role, color in roles.items():
        pal.setColor(role, QtGui.QColor(color))
    placeholder = QtGui.QColor(t.text)
    placeholder.setAlpha(140)
    pal.setColor(QtGui.QPalette.PlaceholderText, placeholder)
    return pal


def stylesheet(t: Tokens) -> str:
    return f"""
        QWidget {{ color: {t.text}; }}
        QLabel {{ background: transparent; }}
        QLabel#AppTitle {{ font-size: 22pt; font-weight: 700; color: {t.text}; }}
        QLabel#AppTagline {{ color: {t.subtext}; font-size: 10pt; }}
        QLabel#PageTitle {{ font-size: 18pt; font-weight: 700; }}
        QLabel#CardTitle {{ font-size: 12pt; font-weight: 600; }}
        QLabel#Metric {{ font-size: 17pt; font-weight: 700; }}
        QLabel#Preview {{ background: {t.base}; color: {t.text}; border: 1px solid {t.border};
                           border-radius: 8px; padding: 12px; font-size: 11pt; }}
        QLabel#SectionTitle {{ margin-top: 6px; font-size: 10.5pt; font-weight: 700;
                               letter-spacing: .8px; color: {t.subtext}; }}
        QLabel#GroupLabel {{ color: {t.subtext}; font-weight: 600; }}
        QLabel#StatusPill {{ background: {t.hover}; color: {t.subtext}; border-radius: 8px;
                             padding: 6px 12px; font-weight: 600; font-size: 9pt; }}
        QLabel#StatusPill[state="success"] {{ color: {t.success}; }}
        QLabel#StatusPill[state="error"] {{ color: {t.danger}; }}
        QLabel#StatusPill[state="busy"] {{ color: {t.warning}; }}
        QLabel#Hint {{ color: {t.subtext}; font-size: 9pt; }}

        QFrame#AppBar {{
            background: transparent; border: none;
        }}

        QFrame#Card, QGroupBox#Card {{
            background: {t.card}; border: 1px solid {t.border}; border-radius: 12px;
        }}

        QFrame#Divider {{ border: none; background: {t.border}; max-height: 1px; }}

        QPushButton {{ background: {t.card}; color: {t.text}; border: 1px solid {t.border};
                       padding: 8px 14px; border-radius: 7px; font-weight: 600; min-height: 18px; }}
        QPushButton:hover {{ background: {t.hover}; }}
        QPushButton:focus {{ border: 1px solid {t.accent}; }}
        QPushButton:disabled {{ color: {t.subtext}; background: {t.base}; border-color: {t.border}; }}
        QPushButton#Primary {{ background: {t.accent}; color: {t.on_accent}; border: none; }}
        QPushButton#Primary:hover {{ background: {t.accent_hover}; }}
        QPushButton#Primary:disabled {{ background: {t.accent_disabled}; color: {t.on_accent}; }}

        QPushButton#Outlined {{ background: transparent; color: {t.text}; border: 1px solid {t.border}; }}
        QPushButton#Outlined:hover {{ background: {t.hover}; }}
        QPushButton#Outlined:disabled {{ color: {t.subtext}; }}

        QPushButton#Danger {{ background: transparent; color: {t.danger}; border: 1px solid {t.danger}; }}
        QPushButton#Danger:hover {{ background: rgba(217,48,37,.10); }}
        QPushButton#Danger:disabled {{ color: {t.subtext}; border-color: {t.border}; }}

        QPushButton#Text {{ background: transparent; color: {t.accent}; border: none; padding: 6px 10px; }}
        QPushButton#Text:hover {{ background: {t.hover}; border-radius: 6px; }}
        QPushButton#Text:disabled {{ color: {t.subtext}; }}

        QPushButton#OnAccent {{ background: rgba(255,255,255,.16); color: {t.on_accent};
                                border: 1px solid rgba(255,255,255,.45); }}
        QPushButton#OnAccent:hover {{ background: rgba(255,255,255,.28); }}

        QProgressBar {{ border: 1px solid {t.border}; border-radius: 8px; background: {t.base};
                        height: 16px; color: {t.subtext}; text-align: center; font-weight: 600; }}
        QProgressBar::chunk {{ background-color: {t.accent}; border-radius: 7px; }}

        QTextEdit, QPlainTextEdit {{ background: {t.base}; border: 1px solid {t.border};
                                     border-radius: 8px; padding: 8px; color: {t.text}; }}
        QLineEdit, QSpinBox, QComboBox {{ background: {t.base}; border: 1px solid {t.border};
                                          border-radius: 6px; padding: 5px 8px; color: {t.text}; }}
        QLineEdit:focus, QSpinBox:focus, QComboBox:focus {{ border-color: {t.accent}; }}

        QListWidget {{ background: {t.base}; border: 1px solid {t.border}; border-radius: 8px; }}
        QListWidget::item:selected {{ background: {t.hover}; color: {t.text}; }}
        QListWidget::item:hover {{ background: {t.hover}; }}
        QListWidget#SettingsNav {{ background: transparent; border: none; outline: none; }}
        QListWidget#SettingsNav::item {{ padding: 12px 14px; margin: 2px 0; border-radius: 7px; }}
        QListWidget#SettingsNav::item:selected {{ background: {t.hover}; color: {t.accent}; font-weight: 600; }}
        QScrollArea {{ background: transparent; border: none; }}
        QScrollArea > QWidget > QWidget {{ background: {t.card}; }}
        QWidget#Dashboard {{ background: {t.window}; }}
        QGroupBox {{ border: 1px solid {t.border}; border-radius: 8px; margin-top: 16px; padding: 14px 8px 8px; }}
        QGroupBox::title {{ subcontrol-origin: margin; left: 12px; padding: 0 5px; color: {t.subtext}; }}
        QCheckBox {{ spacing: 8px; }}
        QCheckBox::indicator {{ width: 16px; height: 16px; }}
        QScrollBar:vertical {{ background: transparent; width: 10px; margin: 2px; }}
        QScrollBar::handle:vertical {{ background: {t.border}; border-radius: 4px; min-height: 28px; }}
        QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{ height: 0; }}
        QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical {{ background: transparent; }}
        QToolTip {{ background: {t.card}; color: {t.text}; border: 1px solid {t.border}; padding: 6px; }}
        QMenu {{ background: {t.card}; border: 1px solid {t.border}; padding: 5px; }}
        QMenu::item {{ padding: 8px 24px; border-radius: 4px; }}
        QMenu::item:selected {{ background: {t.hover}; }}

        QTabWidget::pane {{ border: 1px solid {t.border}; border-radius: 10px; padding: 6px;
                            background: {t.card}; }}
        QTabBar::tab {{ padding: 8px 16px; margin: 2px; border-radius: 8px; background: transparent;
                        color: {t.subtext}; border: 1px solid transparent; font-weight: 600; }}
        QTabBar::tab:selected {{ background: {t.card}; color: {t.text}; border-color: {t.border}; }}
        QTabBar::tab:hover:!selected {{ background: {t.hover}; }}
    """


# Tokens of the currently applied theme, for ad-hoc coloring (e.g. log lines).
current: Tokens = tokens(dark=True, accent="#6750A4")


def apply(app: QtWidgets.QApplication, dark: bool, accent: str) -> Tokens:
    """Apply the theme application-wide; returns the tokens for ad-hoc coloring."""
    global current
    t = tokens(dark, accent)
    app.setStyle("Fusion")
    app.setPalette(palette(t))
    app.setStyleSheet(stylesheet(t))
    current = t
    return t

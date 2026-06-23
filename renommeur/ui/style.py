"""Thèmes graphiques (sombre / clair) — QSS construit depuis une palette."""

THEMES = {
    "dark": {
        "bg": "#1f2330", "card": "#2a2f3f", "field": "#232838", "border": "#3a4154",
        "text": "#e6e8f0", "muted": "#8a90a6",
        "accent": "#6366f1", "accent_dark": "#535bdf", "accent_darker": "#4750cf",
        "danger": "#ef4458", "danger_dark": "#d62f43",
        "sec_bg": "#353b4e", "sec_text": "#c7cce0", "sec_hover": "#3f4660",
        "item_hover": "#2f3548", "dis_bg": "#3a4154", "dis_text": "#707892",
        "drop_idle_b": "#4a5168", "drop_idle_bg": "#262b3a", "drop_idle_t": "#8a90a6",
        "drop_hover_b": "#6366f1", "drop_hover_bg": "#2c3350", "drop_hover_t": "#c7ccff",
        "drop_done_b": "#22c55e", "drop_done_bg": "#1f3a2c", "drop_done_t": "#86efac",
    },
    "light": {
        "bg": "#eef1fa", "card": "#ffffff", "field": "#ffffff", "border": "#cdd3e6",
        "text": "#1f2430", "muted": "#6b7180",
        "accent": "#4f46e5", "accent_dark": "#4338ca", "accent_darker": "#3730a3",
        "danger": "#e11d48", "danger_dark": "#be123c",
        "sec_bg": "#eceefb", "sec_text": "#4f46e5", "sec_hover": "#dfe2f7",
        "item_hover": "#eef0fb", "dis_bg": "#c7cadb", "dis_text": "#f0f1f8",
        "drop_idle_b": "#b7bedd", "drop_idle_bg": "#fbfcff", "drop_idle_t": "#6b7180",
        "drop_hover_b": "#4f46e5", "drop_hover_bg": "#e8ebfd", "drop_hover_t": "#4f46e5",
        "drop_done_b": "#16a34a", "drop_done_bg": "#e9f9ef", "drop_done_t": "#15803d",
    },
}

_theme = "dark"


def set_theme(name: str) -> None:
    global _theme
    if name in THEMES:
        _theme = name


def current() -> str:
    return _theme


def app_stylesheet() -> str:
    c = THEMES[_theme]
    return f"""
QWidget {{
    background-color: {c['bg']};
    color: {c['text']};
    font-family: "Segoe UI", "Helvetica Neue", Arial, sans-serif;
    font-size: 13px;
}}
QLabel {{ background: transparent; }}
QGroupBox {{
    background-color: {c['card']};
    border: 1px solid {c['border']};
    border-radius: 14px;
    margin-top: 16px;
    padding: 12px;
    font-weight: bold;
}}
QGroupBox::title {{ subcontrol-origin: margin; left: 16px; padding: 2px 8px; color: {c['accent']}; }}
QLabel#refImage {{
    background: {c['field']};
    border: 1px solid {c['border']};
    border-radius: 10px;
    color: {c['muted']};
}}
QPushButton {{
    background-color: {c['accent']};
    color: white;
    border: none;
    border-radius: 9px;
    padding: 8px 14px;
    font-weight: 600;
}}
QPushButton:hover {{ background-color: {c['accent_dark']}; }}
QPushButton:pressed {{ background-color: {c['accent_darker']}; }}
QPushButton:disabled {{ background-color: {c['dis_bg']}; color: {c['dis_text']}; }}
QPushButton#secondary {{ background-color: {c['sec_bg']}; color: {c['sec_text']}; }}
QPushButton#secondary:hover {{ background-color: {c['sec_hover']}; }}
QPushButton#danger {{ background-color: {c['danger']}; }}
QPushButton#danger:hover {{ background-color: {c['danger_dark']}; }}
QPushButton#counter {{ padding: 2px 0; font-size: 15px; }}
QLineEdit, QSpinBox, QPlainTextEdit, QListWidget, QComboBox {{
    background-color: {c['field']};
    border: 1px solid {c['border']};
    border-radius: 9px;
    padding: 6px 9px;
    color: {c['text']};
    selection-background-color: {c['accent']};
    selection-color: white;
}}
QLineEdit:focus, QSpinBox:focus, QPlainTextEdit:focus, QListWidget:focus, QComboBox:focus {{
    border: 1px solid {c['accent']};
}}
QComboBox::drop-down {{ border: none; width: 22px; }}
QComboBox#iconCombo {{ padding: 4px 4px; }}
QComboBox#iconCombo::drop-down {{ width: 16px; }}
QToolButton#iconBtn {{
    background-color: {c['field']};
    border: 1px solid {c['border']};
    border-radius: 9px;
    padding: 6px 14px;
}}
QToolButton#iconBtn:hover {{ border-color: {c['accent']}; }}
QToolButton#iconBtn::menu-indicator {{ image: none; width: 0; }}
QMenu {{ background-color: {c['field']}; color: {c['text']}; border: 1px solid {c['border']}; }}
QMenu::item:selected {{ background-color: {c['accent']}; color: white; }}
QComboBox QAbstractItemView {{
    background-color: {c['field']};
    color: {c['text']};
    border: 1px solid {c['border']};
    selection-background-color: {c['accent']};
    selection-color: white;
    outline: none;
}}
QListWidget {{ padding: 4px; }}
QListWidget::item {{ padding: 9px 8px; border-radius: 7px; margin: 1px 0; }}
QListWidget::item:hover {{ background-color: {c['item_hover']}; }}
QListWidget::item:selected {{ background-color: {c['accent']}; color: white; }}
QCheckBox {{ spacing: 8px; }}
QCheckBox::indicator {{
    width: 18px; height: 18px;
    border: 2px solid {c['border']};
    border-radius: 5px;
    background: {c['field']};
}}
QCheckBox::indicator:hover {{ border-color: {c['accent']}; }}
QCheckBox::indicator:checked {{ background: {c['accent']}; border-color: {c['accent']}; }}
QScrollArea {{ border: none; background: transparent; }}
QScrollArea > QWidget > QWidget {{ background: transparent; }}
"""


def _drop(border: str, bg: str, text: str) -> str:
    return f"""
QFrame#dropBox {{ border: 2px dashed {border}; border-radius: 14px; background: {bg}; }}
QFrame#dropBox QLabel {{ color: {text}; background: transparent; }}
"""


def drop_idle() -> str:
    c = THEMES[_theme]
    return _drop(c["drop_idle_b"], c["drop_idle_bg"], c["drop_idle_t"])


def drop_hover() -> str:
    c = THEMES[_theme]
    return _drop(c["drop_hover_b"], c["drop_hover_bg"], c["drop_hover_t"]).replace("dashed", "solid")


def drop_done() -> str:
    c = THEMES[_theme]
    return _drop(c["drop_done_b"], c["drop_done_bg"], c["drop_done_t"]).replace("dashed", "solid")

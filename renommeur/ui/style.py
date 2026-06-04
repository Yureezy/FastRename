"""Thème graphique de l'application (feuille de style Qt / QSS)."""

# Palette : indigo comme couleur d'accent, fond bleu très clair, cartes blanches.
ACCENT = "#4f46e5"
ACCENT_DARK = "#4338ca"
ACCENT_DARKER = "#3730a3"
DANGER = "#e11d48"
DANGER_DARK = "#be123c"

STYLESHEET = f"""
QWidget {{
    background-color: #eef1fa;
    color: #1f2430;
    font-family: "Segoe UI", "Helvetica Neue", Arial, sans-serif;
    font-size: 13px;
}}

/* Bandeau de titre */
QLabel#header {{
    background-color: {ACCENT};
    color: white;
    font-size: 18px;
    font-weight: bold;
    padding: 14px 18px;
    border-radius: 12px;
}}
QLabel#subtitle {{
    color: #5b6172;
    font-size: 12px;
}}

/* Cartes (group boxes) */
QGroupBox {{
    background-color: #ffffff;
    border: 1px solid #e2e6f3;
    border-radius: 14px;
    margin-top: 16px;
    padding: 12px;
    font-weight: bold;
}}
QGroupBox::title {{
    subcontrol-origin: margin;
    left: 16px;
    padding: 2px 8px;
    color: {ACCENT};
}}

/* Boutons */
QPushButton {{
    background-color: {ACCENT};
    color: white;
    border: none;
    border-radius: 9px;
    padding: 8px 14px;
    font-weight: 600;
}}
QPushButton:hover {{ background-color: {ACCENT_DARK}; }}
QPushButton:pressed {{ background-color: {ACCENT_DARKER}; }}
QPushButton:disabled {{ background-color: #c7cadb; color: #f0f1f8; }}

QPushButton#secondary {{ background-color: #eceefb; color: {ACCENT}; }}
QPushButton#secondary:hover {{ background-color: #dfe2f7; }}
QPushButton#danger {{ background-color: {DANGER}; }}
QPushButton#danger:hover {{ background-color: {DANGER_DARK}; }}

/* Champs de saisie */
QLineEdit, QSpinBox, QPlainTextEdit, QListWidget {{
    background-color: #ffffff;
    border: 1px solid #cdd3e6;
    border-radius: 9px;
    padding: 6px 9px;
    selection-background-color: {ACCENT};
    selection-color: white;
}}
QLineEdit:focus, QSpinBox:focus, QPlainTextEdit:focus, QListWidget:focus {{
    border: 1px solid {ACCENT};
}}

/* Liste des références */
QListWidget {{ padding: 4px; }}
QListWidget::item {{
    padding: 9px 8px;
    border-radius: 7px;
    margin: 1px 0;
}}
QListWidget::item:hover {{ background-color: #eef0fb; }}
QListWidget::item:selected {{ background-color: {ACCENT}; color: white; }}

QCheckBox {{ spacing: 8px; }}
QScrollArea {{ border: none; background: transparent; }}
QScrollArea > QWidget > QWidget {{ background: transparent; }}
"""

# Styles des cases de dépôt (appliqués widget par widget pour le retour visuel).
DROP_IDLE = """
QFrame#dropBox {
    border: 2px dashed #b7bedd;
    border-radius: 14px;
    background: #fbfcff;
}
QFrame#dropBox QLabel { color: #6b7180; background: transparent; }
"""
DROP_HOVER = """
QFrame#dropBox {
    border: 2px solid #4f46e5;
    border-radius: 14px;
    background: #e8ebfd;
}
QFrame#dropBox QLabel { color: #4f46e5; background: transparent; }
"""
DROP_DONE = """
QFrame#dropBox {
    border: 2px solid #16a34a;
    border-radius: 14px;
    background: #e9f9ef;
}
QFrame#dropBox QLabel { color: #15803d; background: transparent; }
"""

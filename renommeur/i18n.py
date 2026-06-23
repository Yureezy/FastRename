"""Traductions FR / EN / ES — dico simple, pas de machinerie Qt.

``t(key, **kw)`` renvoie la chaîne dans la langue courante (repli français).
Les noms de dossiers (``dir_renamed`` / ``dir_originals``) suivent la langue.
"""

from __future__ import annotations

LANGUAGES = {"fr": "Français", "en": "English", "es": "Español"}
_DEFAULT = "fr"
_current = _DEFAULT

STRINGS: dict[str, dict[str, str]] = {
    "language": {"fr": "Langue :", "en": "Language:", "es": "Idioma:"},
    "theme": {"fr": "Thème :", "en": "Theme:", "es": "Tema:"},
    "theme_dark": {"fr": "Sombre", "en": "Dark", "es": "Oscuro"},
    "theme_light": {"fr": "Clair", "en": "Light", "es": "Claro"},
    # Sidebar / référence
    "ref_title": {"fr": "1 · Référence", "en": "1 · Reference", "es": "1 · Referencia"},
    "import_excel": {"fr": "📄 Importer un Excel…", "en": "📄 Import Excel…", "es": "📄 Importar Excel…"},
    "import_tip": {
        "fr": "Importer des références (et leurs images) depuis un fichier .xlsx",
        "en": "Import references (and their images) from an .xlsx file",
        "es": "Importar referencias (y sus imágenes) desde un archivo .xlsx",
    },
    "choose_ref": {"fr": "Choisis ta référence :", "en": "Choose your reference:", "es": "Elige tu referencia:"},
    "search_ph": {
        "fr": "🔎 Rechercher une référence…",
        "en": "🔎 Search a reference…",
        "es": "🔎 Buscar una referencia…",
    },
    "no_image": {"fr": "(pas d'image)", "en": "(no image)", "es": "(sin imagen)"},
    "new_ref_ph": {"fr": "Nouvelle référence…", "en": "New reference…", "es": "Nueva referencia…"},
    "add": {"fr": "＋ Ajouter", "en": "＋ Add", "es": "＋ Añadir"},
    "remove": {"fr": "🗑 Retirer", "en": "🗑 Remove", "es": "🗑 Quitar"},
    "clear_all": {"fr": "🧹 Tout effacer", "en": "🧹 Clear all", "es": "🧹 Borrar todo"},
    "clear_all_tip": {
        "fr": "Vider toute la liste des références",
        "en": "Empty the whole reference list",
        "es": "Vaciar toda la lista de referencias",
    },
    # Options
    "options_title": {"fr": "2 · Options", "en": "2 · Options", "es": "2 · Opciones"},
    "nb_suffixes": {"fr": "Nombre de suffixes :", "en": "Number of suffixes:", "es": "Número de sufijos:"},
    "less_tip": {"fr": "Une case de moins", "en": "One box fewer", "es": "Una casilla menos"},
    "more_tip": {"fr": "Une case de plus", "en": "One box more", "es": "Una casilla más"},
    "output_dir": {"fr": "Dossier de sortie :", "en": "Output folder:", "es": "Carpeta de salida:"},
    "output_tip": {
        "fr": "Dossier de base : l'app y crée « {r} » (les copies renommées) et, si l'option est cochée, « {o} » (les images d'origine).",
        "en": "Base folder: the app creates “{r}” (the renamed copies) and, if the option is on, “{o}” (the original images).",
        "es": "Carpeta base: la app crea «{r}» (las copias renombradas) y, si la opción está activa, «{o}» (las imágenes originales).",
    },
    "browse": {"fr": "Parcourir…", "en": "Browse…", "es": "Examinar…"},
    "open": {"fr": "Ouvrir", "en": "Open", "es": "Abrir"},
    "preview_check": {
        "fr": "Demander un aperçu avant de copier",
        "en": "Ask for a preview before copying",
        "es": "Pedir una vista previa antes de copiar",
    },
    "move_check": {
        "fr": "Ranger les originaux dans le dossier « {o} »",
        "en": "Move originals to the “{o}” folder",
        "es": "Mover los originales a la carpeta «{o}»",
    },
    "move_tip": {
        "fr": "Après copie, déplace l'image d'origine dans le sous-dossier « {o} » du dossier de sortie (réversible via Annuler).",
        "en": "After copying, moves the original image to the “{o}” subfolder of the output folder (reversible via Undo).",
        "es": "Tras copiar, mueve la imagen original a la subcarpeta «{o}» de la carpeta de salida (reversible con Deshacer).",
    },
    # Grille / cases
    "grid_title": {
        "fr": "3 · Suffixes  ·  4 · Dépose tes images dans les cases",
        "en": "3 · Suffixes  ·  4 · Drop your images in the boxes",
        "es": "3 · Sufijos  ·  4 · Suelta tus imágenes en las casillas",
    },
    "open_pc_tip": {
        "fr": "Ouvrir l'explorateur de fichiers (Ce PC) pour trouver tes images",
        "en": "Open the file explorer (This PC) to find your images",
        "es": "Abrir el explorador de archivos (Este equipo) para encontrar tus imágenes",
    },
    "suffix_ph": {"fr": "suffixe {n}", "en": "suffix {n}", "es": "sufijo {n}"},
    "drop_caption": {"fr": "Déposez vos images", "en": "Drop your images", "es": "Suelta tus imágenes"},
    "drop_done": {
        "fr": "✓ {n} copié(s) — redéposez",
        "en": "✓ {n} copied — drop again",
        "es": "✓ {n} copiado(s) — suelta de nuevo",
    },
    "drop_invalid": {
        "fr": "Aucune image valide — réessaie",
        "en": "No valid image — try again",
        "es": "Ninguna imagen válida — reintenta",
    },
    "drop_tooltip": {
        "fr": "{n} image(s) copiée(s)\nDernière : {p}",
        "en": "{n} image(s) copied\nLast: {p}",
        "es": "{n} imagen(es) copiada(s)\nÚltima: {p}",
    },
    # Journal
    "journal_title": {"fr": "Journal", "en": "Log", "es": "Registro"},
    "undo_btn": {"fr": "↩ Annuler le dernier lot", "en": "↩ Undo last batch", "es": "↩ Deshacer el último lote"},
    "clear_log": {"fr": "Effacer", "en": "Clear", "es": "Borrar"},
    "log_ph": {
        "fr": "Le journal des renommages s'affichera ici…",
        "en": "The rename log will appear here…",
        "es": "El registro de cambios aparecerá aquí…",
    },
    # Dialogues / messages
    "warn_choose_ref": {
        "fr": "Choisis d'abord une référence (à gauche).",
        "en": "Choose a reference first (on the left).",
        "es": "Elige primero una referencia (a la izquierda).",
    },
    "warn_no_suffix": {
        "fr": "La case {n} n'a pas de suffixe. Saisis-en un sous la case.",
        "en": "Box {n} has no suffix. Enter one below the box.",
        "es": "La casilla {n} no tiene sufijo. Escribe uno debajo.",
    },
    "preview_title": {"fr": "Aperçu du renommage", "en": "Rename preview", "es": "Vista previa del renombrado"},
    "preview_msg": {
        "fr": "Copier {count} fichier(s) vers :\n{dir}\n\n{lst}",
        "en": "Copy {count} file(s) to:\n{dir}\n\n{lst}",
        "es": "Copiar {count} archivo(s) en:\n{dir}\n\n{lst}",
    },
    "preview_more": {"fr": "  … (+{n})", "en": "  … (+{n})", "es": "  … (+{n})"},
    "preview_cancelled": {"fr": "Aperçu annulé.", "en": "Preview cancelled.", "es": "Vista previa cancelada."},
    "write_fail": {
        "fr": "Impossible d'écrire dans le dossier de sortie :\n{dir}\n\n{err}",
        "en": "Cannot write to the output folder:\n{dir}\n\n{err}",
        "es": "No se puede escribir en la carpeta de salida:\n{dir}\n\n{err}",
    },
    "ko_files": {
        "fr": "{n} fichier(s) n'ont pas pu être copiés. Voir le journal.",
        "en": "{n} file(s) could not be copied. See the log.",
        "es": "{n} archivo(s) no se pudieron copiar. Ver el registro.",
    },
    "undo_title": {"fr": "Annuler le dernier lot", "en": "Undo last batch", "es": "Deshacer el último lote"},
    "undo_msg": {
        "fr": "Supprimer les fichiers créés par le dernier dépôt ?\n(Tes images d'origine ne sont jamais touchées.)",
        "en": "Delete the files created by the last drop?\n(Your original images are never touched.)",
        "es": "¿Eliminar los archivos creados por el último depósito?\n(Tus imágenes originales nunca se tocan.)",
    },
    "undo_removed": {
        "fr": "↩ {n} fichier(s) supprimé(s) (annulation).",
        "en": "↩ {n} file(s) deleted (undo).",
        "es": "↩ {n} archivo(s) eliminado(s) (deshacer).",
    },
    "undo_fail": {
        "fr": "Ces fichiers n'ont pas pu être supprimés (peut-être ouverts ailleurs).\nFerme-les puis réessaie l'annulation :\n\n{lst}",
        "en": "These files could not be deleted (maybe open elsewhere).\nClose them then retry the undo:\n\n{lst}",
        "es": "Estos archivos no se pudieron eliminar (quizá abiertos en otro lugar).\nCiérraLos y reintenta deshacer:\n\n{lst}",
    },
    "clear_confirm": {
        "fr": "Effacer TOUTES les références de la liste ?\n(Tes fichiers et tes images ne sont pas touchés.)",
        "en": "Clear ALL references from the list?\n(Your files and images are not touched.)",
        "es": "¿Borrar TODAS las referencias de la lista?\n(Tus archivos e imágenes no se tocan.)",
    },
    "import_choose": {"fr": "Importer un fichier Excel", "en": "Import an Excel file", "es": "Importar un archivo Excel"},
    "col_dialog_title": {"fr": "Choix des colonnes", "en": "Choose columns", "es": "Elegir columnas"},
    "col_sheet": {"fr": "Onglet :", "en": "Sheet:", "es": "Hoja:"},
    "col_text": {"fr": "Colonne texte (référence) :", "en": "Text column (reference):", "es": "Columna de texto (referencia):"},
    "col_image": {"fr": "Colonne image :", "en": "Image column:", "es": "Columna de imagen:"},
    "col_none": {"fr": "(aucune)", "en": "(none)", "es": "(ninguna)"},
    "import_filter": {"fr": "Fichiers Excel (*.xlsx)", "en": "Excel files (*.xlsx)", "es": "Archivos Excel (*.xlsx)"},
    "import_read": {"fr": "Lecture du fichier Excel…", "en": "Reading the Excel file…", "es": "Leyendo el archivo Excel…"},
    "import_extract": {"fr": "Extraction des images…", "en": "Extracting images…", "es": "Extrayendo imágenes…"},
    "import_fail": {
        "fr": "Impossible de lire le fichier Excel :\n{err}",
        "en": "Cannot read the Excel file:\n{err}",
        "es": "No se puede leer el archivo Excel:\n{err}",
    },
    "import_done": {
        "fr": "{added} référence(s) ajoutée(s) ({img} avec image).",
        "en": "{added} reference(s) added ({img} with image).",
        "es": "{added} referencia(s) añadida(s) ({img} con imagen).",
    },
    "choose_output": {"fr": "Choisir le dossier de sortie", "en": "Choose the output folder", "es": "Elegir la carpeta de salida"},
    "open_output_fail": {
        "fr": "Impossible d'ouvrir le dossier de sortie :\n{err}",
        "en": "Cannot open the output folder:\n{err}",
        "es": "No se puede abrir la carpeta de salida:\n{err}",
    },
    "explorer_fail": {
        "fr": "Impossible d'ouvrir l'explorateur de fichiers :\n{err}",
        "en": "Cannot open the file explorer:\n{err}",
        "es": "No se puede abrir el explorador de archivos:\n{err}",
    },
    # Noms de dossiers (suivent la langue)
    "dir_renamed": {"fr": "Renommés", "en": "Renamed", "es": "Renombrados"},
    "dir_originals": {"fr": "Originaux", "en": "Originals", "es": "Originales"},
}


def set_language(lang: str) -> None:
    global _current
    if lang in LANGUAGES:
        _current = lang


def current() -> str:
    return _current


def t(key: str, **kwargs) -> str:
    entry = STRINGS.get(key, {})
    text = entry.get(_current) or entry.get(_DEFAULT) or key
    return text.format(**kwargs) if kwargs else text

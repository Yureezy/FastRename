# 1. Choix technique

## Verdict

> **Python + PySide6 (Qt6), packagé avec PyInstaller.**
> Build macOS via un runner `macos-latest` sur GitHub Actions.

Pour **ce cas précis** — un utilitaire local simple dont la **fonction centrale est le drag & drop
d'images avec récupération du chemin réel sur disque**, développé sur Windows, pour des amis surtout
sur Mac — PySide6 gagne sur les trois critères qui comptent :

1. **Simplicité de développement** — tout le besoin existe nativement dans Qt6, sans bibliothèque tierce :
   - Menu déroulant des références → `QComboBox`
   - Nombre de suffixes (5 à 15) → `QSpinBox`
   - Génération **dynamique** des cases → une boucle qui ajoute des widgets dans un `QGridLayout`
   - Champ de suffixe sous chaque case → `QLineEdit`
   - Le code reste court et lisible en Python.

2. **Drag & drop fiable avec le vrai chemin** — c'est l'approche la plus robuste des 6 frameworks étudiés.
   Sur chaque case : `setAcceptDrops(True)`, puis dans `dropEvent` on lit
   `event.mimeData().urls()` → `url.toLocalFile()` qui donne **directement le chemin absolu**, prêt
   pour `os.replace()`. Pas de sandbox web, pas d'API tierce, multi-fichiers natif. Voir
   [la fiche Drag & drop](02-drag-and-drop.md).

3. **Exécutable propre Windows + Mac** — PyInstaller produit un `.exe` (Windows) et un bundle
   `.app`/`.dmg` (macOS), packaging bien documenté pour PySide6. Le **seul vrai défaut assumé** est
   le poids (~60-150 Mo, Qt embarqué), non bloquant pour une distribution à des amis.

> ⚖️ **Licence** : utiliser **PySide6** (licence **LGPL**, libre de distribution) et **non PyQt6**
> (GPL/commerciale).

## Tableau comparatif des 6 frameworks

| Framework | Langage | Drag & drop (récup. du chemin) | Poids binaire | Build Mac depuis Windows | Verdict |
|---|---|---|---|---|---|
| **PySide6 + PyInstaller** | Python | ✅ Le plus robuste : `url.toLocalFile()` donne le chemin absolu, multi-fichiers, aucune sandbox | ~60-150 Mo | Impossible → CI `macos-latest` | 🏆 **GAGNANT** : simplicité max + drag & drop le plus fiable |
| **Tauri v2** | Rust + JS/HTML/CSS | ✅ `onDragDropEvent` → `paths` (absolus). Pièges : events DOM neutralisés, régressions 2.6.x | **~8 Mo** | Impossible → CI obligatoire | 🥈 **RUNNER-UP** : binaire ultra-léger et natif, mais Rust requis + friction signature |
| **Electron** | JS/HTML/CSS | ❌ **Cassé ici** : `webUtils.getPathForFile()` renvoie `""` pour les fichiers **droppés** sur macOS Sequoia 15.1 (bug [#44600](https://github.com/electron/electron/issues/44600)) | ~165 Mo | `.app` non signé possible, mais signature impossible → CI | ⛔ **À ÉVITER** : path du fichier droppé non fiable sur Mac récent |
| **Tkinter + tkinterdnd2** | Python | ⚠️ Fragile : drop externe non natif, lib tierce (erreurs de chargement TkDND), parsing Tcl piégeux | ~10-30 Mo | Impossible → CI | ⛔ **À ÉVITER** : or le drop d'images est la fonction critique ; UI datée |
| **Flutter desktop** | Dart | ✅ `desktop_drop` → `detail.files[].path` | ~25 Mo | Xcode obligatoire → CI | Surdimensionné : pertinent surtout si on vise aussi le mobile |
| **Avalonia (.NET)** | C# | ✅ Drag & drop .NET correct, contrôles cohérents | Raisonnable | Build/signature → CI | Bon choix .NET desktop-first (vs MAUI mobile-first), mais hors stack « simple en Python » |

> ⚠️ Les chiffres de poids/RAM viennent de benchmarks de blogs : à traiter comme des **ordres de
> grandeur**, pas des valeurs exactes.

## Pourquoi pas les autres ?

- **Electron** est éliminé car l'extraction du chemin d'un fichier **droppé** est cassée sur macOS
  Sequoia 15.1 ([#44600](https://github.com/electron/electron/issues/44600),
  [#44370](https://github.com/electron/electron/issues/44370)) — c'est exactement la fonction
  centrale du produit. En prime : ~165 Mo pour un mini-outil.
- **Tauri** impose **Rust** (vraie barrière) et a des régressions récentes sur les chemins droppés
  (2.6.x, [#13698](https://github.com/tauri-apps/tauri/issues/13698)). Excellent si le poids du
  binaire prime, mais plus lent à mettre en route.
- **Tkinter** a un drag & drop externe **fragile** (lib `tkinterdnd2`, erreurs `Unable to load tkdnd
  library`, parsing Tcl piégeux) — risqué quand le drop est la fonction centrale.
- **Flutter** (Dart) et **Avalonia / MAUI** (C#) sont surdimensionnés et hors de la zone de confort
  d'un dev qui veut « du simple ».

## Le second choix : Tauri v2

À retenir **uniquement** si le poids/propreté du binaire (~8 Mo, vraiment natif) prime sur la rapidité
de développement, **et** que tu acceptes d'apprendre un peu de Rust. Dans ce cas :
- Drag & drop : utiliser **exclusivement** `getCurrentWebview().onDragDropEvent` et lire
  `event.payload.paths` ; renommer côté Rust via `std::fs::rename` dans un `#[tauri::command]`.
- Pièges à figer : **ne pas** compter sur les events DOM `ondrop` (neutralisés par le drop natif) ;
  **épingler** une version Tauri stable (régressions 2.6.x) ; dédupliquer côté code.

## Le point qui s'applique à TOUS les frameworks

Quel que soit le framework choisi, un exécutable macOS qui s'ouvre **sans avertissement** exige un
compte **Apple Developer (99 $/an)** + **signature** + **notarisation**. Aucun framework n'y échappe.
C'est le vrai « coût caché » d'une app Mac propre. Détails dans la
[fiche Distribution macOS](03-distribution-macos.md).

## Sources

- https://fyrosofttech.com/blog/cross-platform-desktop-apps-2026/
- https://www.dolthub.com/blog/2025-11-13-electron-vs-tauri/
- https://doc.qt.io/qtforpython-6/deployment/deployment-pyinstaller.html
- https://www.pythonguis.com/tutorials/packaging-pyside6-applications-pyinstaller-macos-dmg/
- https://avaloniaui.net/maui-compare
- https://docs.flutter.dev/platform-integration/desktop
- https://developer.apple.com/developer-id/

# 2. Drag & drop : récupérer le vrai chemin du fichier

C'est **le** point technique central du produit : quand on dépose une image dans une case, il faut
connaître le **chemin réel du fichier sur le disque** pour pouvoir le renommer. Tous les frameworks
savent recevoir un drop, mais peu donnent le chemin facilement.

## La règle d'or

> Le navigateur / la WebView **masque volontairement** le chemin disque réel (sécurité web).
> Pour renommer un fichier, il faut **toujours** passer par la **couche native** du framework,
> jamais par le seul `DataTransfer`/`File` du web.

C'est ce qui élimine Electron pour ce projet (voir [Choix technique](01-choix-technique.md)) et ce
qui rend **PySide6 idéal** : Qt est nativement « hors web », donc le chemin est disponible sans détour.

## En PySide6 (notre choix)

Chaque **case** est son propre widget « zone de dépôt ». Le principe :

```python
from PySide6.QtWidgets import QFrame
from PySide6.QtCore import Signal

class DropBox(QFrame):
    """Une case dans laquelle on dépose des images. Connaît son suffixe."""
    files_dropped = Signal(list)  # liste de chemins absolus

    def __init__(self, suffixe: str = ""):
        super().__init__()
        self.suffixe = suffixe
        self.setAcceptDrops(True)          # 1. activer la réception de drops

    def dragEnterEvent(self, event):       # 2. accepter le survol si ce sont des fichiers
        if event.mimeData().hasUrls():
            event.acceptProposedAction()
            # (ici : surligner la case pour le retour visuel)

    def dropEvent(self, event):            # 3. récupérer les chemins absolus
        chemins = [
            url.toLocalFile()              # ← LE chemin disque réel, prêt pour os.replace()
            for url in event.mimeData().urls()
            if url.isLocalFile()
        ]
        if chemins:
            self.files_dropped.emit(chemins)
        event.acceptProposedAction()
```

Points clés :
- `url.toLocalFile()` donne **directement** le chemin absolu local — aucune sandbox à contourner.
- `event.mimeData().urls()` est une **liste** → le **multi-fichiers** est géré nativement (on peut
  déposer 10 images d'un coup dans une case).
- Comme **chaque case est un widget distinct**, on sait toujours **dans quelle case** l'image a été
  déposée → on applique le bon suffixe. C'est exactement le modèle dont le produit a besoin.
- Identique sur Windows et macOS, même code.

## Les pièges à connaître (PySide6)

1. **Le drop marche en dev mais casse après PyInstaller.**
   Cause habituelle : les **plugins de plateforme Qt** ne sont pas embarqués. Solution : vérifier le
   `.spec` PyInstaller et, si besoin, `--add-data` les plugins. **Tester impérativement l'exécutable
   packagé**, pas seulement le mode `python app.py`.
   *(refs : cx_Freeze [#1910](https://github.com/marcelotduarte/cx_Freeze/issues/1910), forum Qt)*

2. **Windows : ne JAMAIS lancer l'app en administrateur.**
   À cause de l'isolation des privilèges d'interface (UIPI), une app lancée en admin **ne reçoit pas**
   les drops d'un Explorateur lancé en utilisateur normal → le drag & drop semble silencieusement KO.

3. **macOS sandboxé** (seulement si distribution Mac App Store, ce qui n'est pas notre cas) :
   il faudrait l'entitlement `com.apple.security.files.user-selected.read-write`, et l'accès ne
   persiste pas entre deux lancements (security-scoped bookmarks requis). **Hors App Store, non
   concerné.**

## Comment font les autres frameworks (pour mémoire)

| Framework | API | Donne le chemin ? |
|---|---|---|
| **PySide6 / PyQt6** | `event.mimeData().urls()` → `url.toLocalFile()` | ✅ Direct, le plus simple |
| **Tauri v2** | `getCurrentWebview().onDragDropEvent` → `event.payload.paths` | ✅ Direct (côté natif), mais events DOM neutralisés |
| **Flutter** | `DropTarget` + `onDragDone` → `detail.files[].path` | ✅ Sur desktop uniquement |
| **Tkinter** | `tkinterdnd2` : `dnd_bind('<<Drop>>')` → `tk.splitlist(event.data)` | ⚠️ Oui mais fragile, parsing piégeux |
| **Electron** | `webUtils.getPathForFile(file)` (preload) | ❌ Renvoie `""` pour les **drops** sur macOS Sequoia 15.1 |

## Sources

- https://doc.qt.io/qtforpython-6/PySide6/QtGui/QDropEvent.html
- https://wiki.qt.io/Drag_and_Drop_of_files
- https://v2.tauri.app/reference/javascript/api/namespacewebview/
- https://pub.dev/packages/desktop_drop
- https://github.com/electron/electron/issues/44600
- https://github.com/marcelotduarte/cx_Freeze/issues/1910

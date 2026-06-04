# 5. Bonnes pratiques de renommage de fichiers

Renommer des fichiers paraît trivial, mais c'est **destructif** si on s'y prend mal : on peut écraser
des images (collisions), corrompre un nom, ou perdre une extension. Comme l'app vise **Windows ET
macOS**, on applique partout les règles **Windows** (les plus strictes — elles couvrent macOS).

## Le pipeline en 5 étapes

```
fichier déposé  →  [1] construire le nom cible
                →  [2] assainir
                →  [3] détecter les conflits (sur tout le lot)
                →  [4] renommer en 2 phases (+ journal)
                →  [5] aperçu (dry-run) & undo
```

### 1. Construire le nom cible

```
nouveau_nom = sanitize(référence) + "_" + sanitize(suffixe) + extension_d_origine
```

- L'**extension** est extraite sur le **dernier point** (`Path.suffix`) et **réattachée verbatim**
  (casse comprise : `.JPG` reste `.JPG`), **après** une éventuelle troncature.
- Cas limites : fichier **sans extension** (ne rien ajouter), `.tar.gz` (gérer une liste de doubles
  extensions si besoin), `.gitignore` (= nom caché, **pas** une extension).

### 2. Assainir (sur la partie hors-extension)

- Retirer/remplacer les **9 caractères interdits Windows** : `\ / : * ? " < > |` et les **codes de
  contrôle** (0-31), par exemple par `_`.
- **Normaliser en Unicode NFC** (voir piège macOS ci-dessous).
- **Strip** des espaces et points en **fin** de nom (rejetés par le shell Windows).
- Si la référence (casse insensible) est un **nom réservé DOS** — `CON`, `PRN`, `AUX`, `NUL`,
  `COM1`-`COM9`, `LPT1`-`LPT9` — la préfixer (ex. `_CON`). ⚠️ `NUL.txt` **équivaut à** `NUL`, donc
  vérifier la **base** du nom, avant extension.
- Refuser un nom **vide** (prévoir un repli).
- **Tronquer** la référence pour que le nom complet fasse **≤ 255 octets en UTF-8** (limite APFS) —
  **jamais** l'extension.

### 3. Détecter les conflits — AVANT de toucher au disque

Sur **tout le lot**, avec des **clés normalisées** (casse repliée + NFC), détecter :
- la cible existe **déjà** sur le disque,
- **deux fichiers du lot** renommés vers le **même** nom (collision interne),
- nom résultant **vide**,
- fichier source **disparu**.

**Résolution de collision** : suffixe **numérique incrémental** inséré **avant l'extension** —
`référence_suffixe_1.ext`, `_2.ext`… — en vérifiant **le disque ET** les noms déjà attribués dans
le lot courant.

> 🔑 **Piège des collisions invisibles** : `Ref_1.JPG` et `ref_1.jpg` sont **en conflit** sur Windows
> et macOS (insensibles à la casse par défaut), bien que les chaînes diffèrent. D'où les clés
> « casse repliée ».

### 4. Renommer en deux phases (transactionnel)

Pour gérer les **cycles** (`A→B` pendant que `B→A`) et les **écrasements** :
- **Phase 1** : renommer chaque source vers un **nom temporaire unique**.
- **Phase 2** : renommer les temporaires vers les **noms finaux**.

Cela gère aussi le **renommage casse-seulement** (`Photo.jpg → photo.jpg`), qui sinon serait traité
comme une non-opération sur un système insensible à la casse.

Détails d'implémentation :
- Utiliser `os.replace()` (atomique, Python 3.3+) plutôt que `os.rename()`.
- **Refuser/avertir** si source et destination sont sur des **volumes différents** : sur Windows,
  un « renommage » cross-volume devient une **copie non atomique** (fenêtre de corruption).

### 5. Aperçu (dry-run) & annulation (undo)

- **Mode aperçu par défaut** : montrer `ancien → nouveau` ; l'exécution réelle exige une action
  explicite (un bouton « Renommer »). C'est le principal garde-fou.
- **Journal write-ahead** : écrire le mapping `original → nouveau` (JSON, chemins absolus +
  horodatage) **avant** d'agir.
- **Undo** : rejouer le journal en **sens inverse**. Conserver le journal en cas d'erreur, le
  supprimer après un undo réussi.

## Le piège macOS qui n'existe nulle part ailleurs : NFD vs NFC

macOS stocke les noms sous forme **décomposée** (NFD : `é` = `e` + accent combinant), alors que
Windows et le reste du monde utilisent **NFC** (`é` = un seul caractère). Conséquence : un nom
accentué peut différer **octet pour octet** entre les deux OS, ce qui casse les comparaisons et la
détection de doublons.

> **Règle** : normaliser **toutes** les chaînes en **NFC** avant comparaison **et** avant écriture.
> Ne **jamais** comparer des noms par octets bruts entre OS.

## Tableau des contraintes par OS

| Contrainte | Windows | macOS (APFS) |
|---|---|---|
| Caractères interdits | `\ / : * ? " < > \|` + ctrl 0-31 | `/` et `NUL` ; `:` à éviter |
| Noms réservés | `CON PRN AUX NUL COM1-9 LPT1-9` | aucun |
| Fin par espace/point | interdit (shell) | toléré |
| Longueur max du nom | 255 **unités UTF-16** | 255 **octets UTF-8** |
| Sensible à la casse | non (préserve) | non par défaut (préserve) |
| Normalisation Unicode | NFC | **NFD** ⚠️ |

## Ne pas réinventer la roue

S'inspirer des stratégies d'outils éprouvés cross-platform plutôt que tout réinventer :
- **F2** (ayoisaiah) — détection de conflits, undo : https://f2.freshman.tech/
- **Advanced Renamer**, **PowerRename** (PowerToys), **Bulk Rename Utility**.

## Sources

- https://learn.microsoft.com/en-us/windows/win32/fileio/naming-a-file
- https://learn.microsoft.com/en-us/windows/win32/fileio/maximum-file-path-limitation
- https://ss64.com/mac/syntax-filenames.html
- https://eclecticlight.co/2021/05/08/explainer-unicode-normalization-and-apfs/
- https://f2.freshman.tech/guide/conflict-detection.html
- https://f2.freshman.tech/guide/undoing-mistakes.html
- https://github.com/untitaker/python-atomicwrites

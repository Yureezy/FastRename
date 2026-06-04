# 6. Spécification produit

Ce que fait le logiciel, écran par écran. Sert de référence pour le développement.

## Schéma (d'après le croquis)

```
┌──────────────────────────────────────────────────────────┐
│  Référence : [ VD 1 JKT LEROY            ▼ ]   ← (1)       │
│                                                            │
│  Nombre de suffixes : [ 5 ⏶⏷ ]                 ← (2)       │
│                                                            │
│   ┌─────┐  ┌─────┐  ┌─────┐  ┌─────┐  ┌─────┐              │
│   │ ▒▒▒ │  │ ▒▒▒ │  │ ▒▒▒ │  │ ▒▒▒ │  │ ▒▒▒ │   ← (4)      │
│   └─────┘  └─────┘  └─────┘  └─────┘  └─────┘   drag&drop  │
│   [ F   ]  [ B   ]  [ TQD ]  [ TQB ]  [ D_1 ]   ← (3)      │
│                                                            │
│              [ Aperçu ]   [ Renommer ]                     │
└──────────────────────────────────────────────────────────┘
```

## Fonctionnalités

### (1) Choix de la référence — menu déroulant
- Liste de références prédéfinies, ex. :
  - `VD 1 JKT LEROY`
  - `VD 1 OSH 1929 K`
  - `VD 1 OSH KUST_`
- *À décider* : liste figée dans le code, ou éditable par l'utilisateur (ajouter/retirer/sauver).
  → **Recommandé** : stocker les références dans un fichier de config (JSON) modifiable depuis l'app,
  pour que tu n'aies pas à recompiler à chaque nouvelle référence.

### (2) Nombre de suffixes — sélecteur numérique
- Valeur de **5 à 15** (modifiable). Changer le nombre **régénère dynamiquement** les cases.
- *À décider* : que faire des suffixes déjà saisis si on change le nombre ? → **Recommandé** :
  conserver ceux qui existent, ajouter/retirer seulement la différence.

### (3) Saisie des suffixes — un champ texte sous chaque case
- Ex. : `F`, `B`, `TQD`, `TQB`, `D_1`, `D2`.
- Chaque case « connaît » son suffixe.

### (4) Drag & drop d'images → renommage automatique
- On dépose une ou plusieurs images dans une case.
- Le fichier est renommé en : **`référence` + `_` + `suffixe` + `extension d'origine`**.
- Exemple : référence `VD 1 JKT LEROY`, suffixe `TQG`, image `IMG_2931.jpeg`
  → **`VD 1 JKT LEROY_TQG.jpeg`**.
- Le renommage applique le pipeline de sécurité de la
  [fiche Bonnes pratiques](05-bonnes-pratiques-renommage.md) : assainissement, détection de
  collisions, renommage two-phase, journal pour undo.

## Décisions de comportement (actées)

| Sujet | Décision |
|---|---|
| **Sur place ou copier ?** | ✅ **Copier** dans un dossier de sortie. Les originaux ne sont jamais touchés. |
| **Dossier de sortie** | Configurable dans l'app. Défaut : `<Bureau>/Renommés` (résolu via l'API Qt, gère OneDrive). |
| **Plusieurs images dans une même case** | ✅ Accepté. Suffixe numérique `_1, _2`… en cas de collision. |
| **Références** | ✅ **Éditables dans l'app** (boutons Ajouter / Retirer), sauvegardées dans `~/.renommeur/config.json`. |
| **Undo** | ✅ Bouton « Annuler le dernier lot » (supprime les copies du dernier dépôt). |
| **Aperçu avant d'écrire** | Optionnel via une case à cocher (désactivé par défaut pour coller au « renommage automatique au drop »). |

## Garde-fous de sûreté (implémentés)

Détaillés dans [Bonnes pratiques de renommage](05-bonnes-pratiques-renommage.md), et vérifiés par les tests :
- Assainissement des noms (caractères interdits, noms réservés DOS, NFC, caractères invisibles, 255 octets).
- Détection des collisions (clés insensibles à la casse + NFC), suffixe incrémental.
- Copie en **création exclusive** : jamais d'écrasement d'un fichier existant.
- Chemins longs Windows (> 260) gérés via le préfixe `\\?\`.
- Config tolérante aux fichiers corrompus + écriture atomique.

## Stack retenue (rappel)

- **Langage / UI** : Python + PySide6 (Qt6) — voir [Choix technique](01-choix-technique.md).
- **Exécutable Windows** : PyInstaller, en local.
- **Exécutable macOS** : PyInstaller sur runner GitHub Actions — voir
  [Build multiplateforme](04-build-multiplateforme.md).
- **Distribution Mac** : `.zip` ad-hoc gratuit, ou `.dmg` signé+notarisé (99 $/an) — voir
  [Distribution macOS](03-distribution-macos.md).

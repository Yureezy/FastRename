# Renommeur

Petit logiciel de bureau pour **renommer des images en masse par glisser-déposer**.

1. Choisis une **référence** dans le menu déroulant (ex. `VD 1 JKT LEROY`).
2. Choisis le **nombre de suffixes** → autant de **cases** apparaissent.
3. Saisis un **suffixe** sous chaque case (ex. `TQG`).
4. **Glisse-dépose** tes images dans une case → elles sont **copiées et renommées** en
   `référence_suffixe.extension`.

> Exemple : référence `VD 1 JKT LEROY` + suffixe `TQG` + image `IMG_001.jpeg`
> → **`VD 1 JKT LEROY_TQG.jpeg`** dans le dossier de sortie.

Les fichiers d'origine ne sont **jamais** modifiés (mode copie). Un bouton **Annuler** permet de
supprimer le dernier lot copié.

## Import depuis Excel (.xlsx)

Le bouton **« 📄 Importer un Excel… »** ajoute des références depuis un classeur `.xlsx` :
- il repère automatiquement l'onglet qui contient la colonne **« Fichier »** (le texte de la référence) ;
- il extrait l'image **intégrée** de la colonne **« Photo »** (en ignorant les autres images, ex. QR code) ;
- l'image de la référence sélectionnée s'affiche sous la liste.

> Les panneaux (Référence / Options / Suffixes) sont **redimensionnables** en tirant sur les séparateurs.

---

## Lancer depuis le code (développement)

Prérequis : Python 3.10+.

```powershell
# Windows (PowerShell)
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe -m renommeur
```

```bash
# macOS / Linux
python3 -m venv .venv
.venv/bin/python -m pip install -r requirements.txt
.venv/bin/python -m renommeur
```

## Lancer les tests

```powershell
.\.venv\Scripts\python.exe -m pip install -r requirements-dev.txt
.\.venv\Scripts\python.exe -m pytest tests -q
```

---

## Fabriquer l'exécutable

### Windows (.exe) — sur ta machine

```powershell
.\.venv\Scripts\python.exe -m pip install pyinstaller
.\.venv\Scripts\pyinstaller.exe --name Renommeur --windowed --onefile --noconfirm main.py
# -> dist\Renommeur.exe
```

### macOS (.app) — PAS depuis Windows

⚠️ **On ne peut pas construire l'app macOS depuis Windows** (il faut Xcode/`codesign`, exclusifs à
macOS). Deux solutions :

- **Recommandé — gratuit, sans Mac :** pousser le projet sur **GitHub** (dépôt **public** = minutes
  macOS gratuites) ; le workflow [`.github/workflows/build.yml`](.github/workflows/build.yml)
  construit automatiquement le `.exe` **et** le `.app`/`.zip` macOS. Crée un tag pour publier une
  Release :
  ```bash
  git tag v0.1.0 && git push --tags
  ```
  Les deux exécutables apparaissent dans la **Release GitHub**.
- **Sur un Mac :** `pip install pyinstaller && pyinstaller --name Renommeur --windowed main.py`
  → `dist/Renommeur.app`.

---

## Donner l'app à des amis sur Mac

macOS bloque les apps non signées par Apple. **Sans payer les 99 $/an** d'Apple Developer, voici la
marche à suivre (à transmettre à l'ami, une seule fois) :

> 1. Glisse `Renommeur.app` dans le dossier **Applications**.
> 2. Ouvre **Terminal** (Cmd+Espace → « Terminal »).
> 3. Tape ceci **suivi d'un espace** : `xattr -dr com.apple.quarantine `
> 4. **Glisse-dépose l'icône de l'app** dans la fenêtre Terminal (le chemin s'insère), puis Entrée.
> 5. Double-clique sur l'app. C'est réglé définitivement.

❗ Ne **pas** dire « clic droit > Ouvrir » : Apple a supprimé cette astuce dans macOS Sequoia (2024).

Pour une expérience **« double-clic sans aucune alerte »**, il faut le compte Apple Developer
(99 $/an) + signature *Developer ID* + notarisation. Détails :
[docs/03-distribution-macos.md](docs/03-distribution-macos.md).

---

## Documentation

Tout l'audit technique et les bonnes pratiques sont dans [`docs/`](docs/) :

- [Choix technique](docs/01-choix-technique.md)
- [Drag & drop](docs/02-drag-and-drop.md)
- [Distribution macOS](docs/03-distribution-macos.md)
- [Build multiplateforme](docs/04-build-multiplateforme.md)
- [Bonnes pratiques de renommage](docs/05-bonnes-pratiques-renommage.md)
- [Spécification produit](docs/06-specification-produit.md)

## Structure du projet

```
renommeur/          le code de l'application
  naming.py         construction + assainissement des noms (Windows + macOS)
  renamer.py        moteur de copie-renommage sûr (collisions, undo)
  config.py         références & options (JSON dans ~/.renommeur)
  ui/               interface PySide6 (fenêtre, cases de dépôt)
tests/              tests (logique + intégration UI offscreen)
docs/               audit technique et bonnes pratiques
main.py             point d'entrée (lancement + PyInstaller)
.github/workflows/  build automatique Windows + macOS
```

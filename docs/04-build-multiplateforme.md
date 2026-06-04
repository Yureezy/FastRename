# 4. Build multiplateforme (tu es sur Windows, tes amis sur Mac)

## Le verdict, sans détour

> **On ne peut pas produire un `.app`/`.dmg` macOS depuis une machine Windows.**

Ce n'est pas une limite de PySide6 : c'est une contrainte d'Apple. Le packaging et **surtout la
signature** de code macOS exigent les outils natifs d'Apple (Xcode, `codesign`), qui n'existent que
sur macOS. Vérifié pour les 4 familles de frameworks :

| Framework | Build Mac depuis Windows ? |
|---|---|
| **PyInstaller** (notre cas) | ❌ Pas un cross-compilateur : « *PyInstaller does not directly support cross-compilation* ». Un build par OS. |
| **Tauri** | ❌ « *meaningful cross-compilation is not possible* ». CI recommandé officiellement. |
| **Flutter** | ❌ Xcode obligatoire (exclusif macOS). |
| **Electron** | ⚠️ Peut générer un `.app` non signé depuis Windows, mais **la signature reste impossible** → inutilisable en pratique (Gatekeeper). |

> Curiosité : l'**inverse** est plus facile (builder un `.exe` Windows **depuis** un Mac). Mais
> Mac-depuis-Windows reste impraticable.

## La solution : GitHub Actions (gratuit)

GitHub héberge des **runners macOS** dans le cloud (`macos-latest`, Apple Silicon arm64). On y lance
le build du `.app`/`.dmg` exactement comme sur un vrai Mac — **sans acheter de matériel Apple**.

### Étapes

1. **Dépôt GitHub PUBLIC** → les minutes macOS deviennent **gratuites et illimitées**.
   *(En privé, multiplicateur **x10** : 1 min réelle de build Mac = 10 min de quota ; ~200 min/mois
   épuisent le plan gratuit. Le public supprime totalement ce problème.)*

2. **Un seul fichier** `.github/workflows/build.yml` avec une **matrice 2 OS en parallèle** :

```yaml
name: build
on:
  push:
    tags: ['v*']          # ne build que sur une release (pas à chaque commit)
jobs:
  build:
    strategy:
      matrix:
        os: [windows-latest, macos-latest]
    runs-on: ${{ matrix.os }}
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: '3.12'
      - run: pip install pyside6 pyinstaller
      - run: pyinstaller app.spec          # → .exe (Windows) / .app (macOS)
      # macOS uniquement : créer le .dmg (create-dmg / hdiutil),
      # puis signer ad-hoc (Option A) OU Developer ID + notariser (Option B)
      - uses: actions/upload-artifact@v4
        with:
          name: renommeur-${{ matrix.os }}
          path: dist/*
      # OU publier dans une Release que les amis Mac téléchargent :
      # - uses: softprops/action-gh-release@v2
```

3. **Résultat** : le runner Windows crache le `.exe`, le runner macOS crache le `.app`/`.dmg`.
   Les deux atterrissent dans une **Release GitHub** où tes amis n'ont qu'à télécharger.

## Deux angles morts à connaître

1. **Architecture Mac : Apple Silicon vs Intel.**
   `macos-latest` est désormais **arm64 (Apple Silicon)**. Un binaire arm64 seul **ne tournera pas**
   sur d'anciens Mac Intel. Pour les couvrir :
   - soit ajouter un runner `macos-15-intel` à la matrice,
   - soit construire un binaire **universal2** (`PyInstaller --target-arch universal2` si
     l'environnement Python est universal).

2. **Tu ne peux pas tester l'app Mac toi-même.**
   Le CI **produit** le binaire, mais sur Windows tu ne peux **pas le lancer ni le déboguer**. Tu
   dépendras des retours de tes amis. Mitigation utile : **emprunter** ponctuellement un Mac, ou
   **louer** une instance à l'heure (AWS EC2 Mac, MacStadium) pour le debug final.
   ⛔ **Ne jamais** utiliser une VM macOS sur PC : viole la licence Apple **et** instable.

## Sources

- https://www.electron.build/multi-platform-build.html
- https://v2.tauri.app/distribute/pipelines/github/
- https://docs.flutter.dev/platform-integration/macos/building
- https://pyinstaller.org/en/stable/usage.html#supporting-multiple-operating-systems
- https://docs.github.com/en/actions/reference/runners/github-hosted-runners
- https://docs.github.com/en/billing/reference/actions-runner-pricing

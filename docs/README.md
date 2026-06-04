# Renommeur de fichiers — Documentation technique

> Audit réalisé le **4 juin 2026** via recherche web multi-sources (frameworks 2025-2026,
> distribution macOS, build cross-plateforme). Toutes les sources sont citées dans chaque fiche.

## Le projet en une phrase

Un petit logiciel de bureau **simple** où l'on choisit une **référence** dans un menu déroulant,
on définit un **nombre de suffixes** (5 à 15) qui génère autant de **cases**, on tape un suffixe
sous chaque case, et **le drag & drop d'une image dans une case la renomme** automatiquement en
`référence_suffixe.extension`.

> Exemple : référence `VD 1 JKT LEROY` + suffixe `TQG` → le fichier devient `VD 1 JKT LEROY_TQG.jpeg`.

## La décision, en bref

| Question | Réponse |
|---|---|
| **Quel langage / framework ?** | **Python + PySide6** (Qt6), packagé avec **PyInstaller**. |
| **Pourquoi ?** | Le plus simple à coder *et* le drag & drop le plus fiable pour récupérer le **vrai chemin** du fichier (la fonction centrale du produit). |
| **Comment faire l'exécutable Windows ?** | `PyInstaller` directement sur ta machine → `.exe`. |
| **Comment faire l'exécutable Mac (alors que tu es sur Windows) ?** | **Impossible depuis Windows.** On le construit gratuitement dans le cloud via **GitHub Actions** (runner `macos-latest`). |
| **Mes amis sur Mac pourront-ils l'ouvrir ?** | Oui, mais macOS bloque les apps non signées. Deux options : **gratuite** (un `.zip` + une commande Terminal) ou **propre** (compte Apple Developer à **99 $/an** → double-clic sans avertissement). |

## Les fiches

1. [**Choix technique**](01-choix-technique.md) — comparaison des 6 frameworks, pourquoi PySide6 gagne, et le second choix (Tauri).
2. [**Drag & drop**](02-drag-and-drop.md) — comment récupérer le chemin réel du fichier déposé, et les pièges.
3. [**Distribution macOS**](03-distribution-macos.md) — Gatekeeper, signature, notarisation, et comment tes amis ouvrent l'app.
4. [**Build multiplateforme**](04-build-multiplateforme.md) — pourquoi on ne peut pas builder Mac sur Windows, et la solution GitHub Actions.
5. [**Bonnes pratiques de renommage**](05-bonnes-pratiques-renommage.md) — assainir les noms, gérer les collisions, ne jamais perdre une image.
6. [**Spécification produit**](06-specification-produit.md) — ce que fait exactement le logiciel, écran par écran.

## Ce qui est possible / impossible (résumé)

**✅ Possible**
- Toute l'interface (menu déroulant, nombre de suffixes, cases dynamiques, champs de suffixe) en PySide6 sans aucune bibliothèque tierce.
- Drag & drop d'images depuis l'Explorateur **et** le Finder, avec récupération du chemin disque réel.
- Renommage `référence_suffixe.extension` avec extension préservée.
- `.exe` Windows construit localement, `.app`/`.dmg` macOS construit gratuitement dans le cloud.
- Distribution aux amis Mac, gratuite (avec une manip) ou propre (payante).

**❌ Impossible (ou à éviter)**
- Produire un `.app`/`.dmg` **directement sur Windows** → il faut un Mac, réel ou dans le cloud (GitHub Actions).
- Un Mac qui ouvre l'app **d'un double-clic sans aucun avertissement** sans payer les **99 $/an** Apple.
- Le contournement « **clic droit > Ouvrir** » : **supprimé** depuis macOS Sequoia 15 (2024).
- Une VM macOS sur PC pour builder : **interdit par la licence Apple** et instable.
- Un binaire PySide6 léger : il pèsera **~60-150 Mo** (Qt embarqué). Non bloquant pour des amis.

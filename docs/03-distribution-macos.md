# 3. Distribution macOS

C'est **la** vraie contrainte du projet, parce que la plupart de tes amis sont sur Mac. macOS bloque
par défaut toute application qui ne vient pas du Mac App Store et qui n'est pas signée + notarisée
par Apple. Voici exactement ce qui est possible.

## Le mécanisme : Gatekeeper

- Depuis **macOS Catalina (10.15)**, toute app distribuée hors App Store doit être **signée**
  (certificat *Developer ID Application*) **ET notarisée** par Apple pour s'ouvrir sans friction.
- Au téléchargement, le navigateur/Mail pose un attribut `com.apple.quarantine` sur le fichier.
  Au premier lancement, **Gatekeeper** vérifie la signature/notarisation. Si elle manque :
  > « *“App” ne peut pas être ouverte car le développeur ne peut pas être vérifié.* »
- La **notarisation** (scan anti-malware automatique d'Apple) **ne remplace pas** la signature :
  l'app **et** son installeur doivent être signés.
- ⚠️ **macOS Sequoia 15 (2024) a supprimé** le contournement « **clic droit > Ouvrir** ».
  Ne **jamais** donner cette instruction à un ami sur un Mac récent : elle ne marche plus.

## Le prérequis pour une expérience « propre »

- Signature + notarisation exigent l'**Apple Developer Program à 99 $/an**.
- Un **Apple ID gratuit** ne suffit **pas** pour distribuer : il ne donne qu'un certificat *Personal
  Team* valable **7 jours**, limité à tes propres appareils.

---

## Les deux options concrètes

### 🟢 Option A — GRATUITE (recommandée pour un cercle d'amis)

**Objectif** : 0 €, au prix d'une petite manip côté ami au premier lancement.

1. Construire l'app, puis la **signer ad-hoc** : `codesign -s - App.app`.
   *(Important : sur Mac Apple Silicon, une app **totalement** non signée peut être refusée même après
   avoir retiré la quarantaine. La signature ad-hoc est gratuite et règle ça.)*
2. Empaqueter en `.zip` avec la **bonne commande** (sinon la signature casse) :
   ```bash
   ditto -c -k --keepParent App.app App.zip
   ```
   ⚠️ Ne **pas** utiliser le « Compresser » du Finder ni un `zip` classique.
3. **Instructions à donner à l'ami** (à coller tel quel) :
   > 1. Glisse `App.app` dans le dossier **Applications**.
   > 2. Ouvre **Terminal** (Cmd+Espace → tape « Terminal »).
   > 3. Tape exactement ceci **suivi d'un espace** :
   >    ```
   >    xattr -dr com.apple.quarantine 
   >    ```
   > 4. **Glisse-dépose l'icône de l'app** dans la fenêtre Terminal (le chemin s'insère tout seul),
   >    puis appuie sur **Entrée**.
   > 5. Ouvre l'app normalement (double-clic). C'est fait une fois pour toutes.
4. **Secours** (si l'app est signée ad-hoc) : *Réglages Système → Confidentialité et sécurité →*
   section *Sécurité* (tout en bas) → **Ouvrir quand même** → authentification admin.
   *Attention : ce bouton n'apparaît pas toujours pour une app non signée ; la commande `xattr`
   du point 3, elle, marche toujours.*

> ⚠️ **À assumer** : `xattr -dr com.apple.quarantine` désactive une protection anti-malware sur ce
> fichier. C'est précisément le geste que les malwares cherchent à faire exécuter aux victimes.
> Acceptable **entre amis pour une source 100 % fiable**, pas pour une diffusion publique.

### 🔵 Option B — PROPRE (Apple Developer, 99 $/an)

**Objectif** : l'ami **double-clique**, aucune alerte, aucune manip. La seule façon d'y arriver.

1. **Signer** en *hardened runtime*, de bas en haut (helpers/frameworks d'abord, puis le bundle) :
   ```bash
   codesign -f -s "Developer ID Application" -o runtime App.app   # éviter --deep
   ```
2. **Notariser** :
   ```bash
   xcrun notarytool store-credentials "profil" --team-id XXXX --apple-id mail --password <app-specific>
   xcrun notarytool submit App.zip --keychain-profile "profil" --wait
   ```
3. **Attacher le ticket** (privilégier un `.dmg`) :
   ```bash
   xcrun stapler staple App.dmg
   ```
4. **Vérifier** : `spctl -a -vvv -t install App.app`.

> Toute cette chaîne tourne **sur le runner macOS de GitHub Actions** (`notarytool` y fonctionne).
> Le certificat `.p12` et les mots de passe se stockent dans **GitHub Actions Secrets**, jamais en
> clair. Voir la [fiche Build multiplateforme](04-build-multiplateforme.md).

---

## Quel format de fichier livrer ?

| Format | Avantages | Inconvénients |
|---|---|---|
| **`.dmg`** *(recommandé pour l'option B)* | Signable, notarisable, ticket *staplable*, l'utilisateur glisse vers Applications (évite l'« App Translocation ») | Un peu plus de mise en place |
| **`.zip`** *(pragmatique pour l'option A)* | Le plus simple à produire et envoyer | Pas *staplable* directement ; créer avec `ditto`, pas le Finder |
| **`.pkg`** | Installeur automatique, *staplable* | Le plus intimidant, plus sujet aux échecs |

## Récapitulatif de décision

- **Tu ne veux rien payer** → Option A, format `.zip` + instructions `xattr`. Suffisant entre amis.
- **Tu veux un double-clic sans aucune alerte** → Option B (99 $/an), format `.dmg` signé + notarisé.
- **Windows** : un certificat de signature *Authenticode* (payant, distinct d'Apple) éviterait
  l'alerte SmartScreen, mais c'est **optionnel** — l'app fonctionne sans.

## Sources

- https://support.apple.com/en-us/102445
- https://developer.apple.com/developer-id/
- https://developer.apple.com/documentation/security/notarizing-macos-software-before-distribution
- https://developer.apple.com/support/compare-memberships/
- https://gist.github.com/rsms/929c9c2fec231f0cf843a1a746a416f5
- https://mjtsai.com/blog/2024/07/05/sequoia-removes-gatekeeper-contextual-menu-override/
- https://wiki.hacks.guide/wiki/Open_unsigned_applications_on_macOS_Sequoia_and_newer

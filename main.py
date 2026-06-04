"""Point d'entrée pour le lancement direct et pour PyInstaller.

Utilise un import absolu (et non relatif) pour rester compatible avec PyInstaller,
qui exécute ce fichier comme script de premier niveau.
"""

from renommeur.app import main

raise SystemExit(main())

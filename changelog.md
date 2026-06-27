# Changelog PyManager

Toutes les modifications techniques du projet sont documentées ici.

## [Initial] - 2026-06-26
- Création de la documentation d'architecture.
- Initialisation du projet (gitignore, env, requirements).
- Développement du backend FastAPI asynchrone avec WebSockets (main.py).
- Développement du frontend réactif (index.html, style.css, app.js avec Alpine.js).
- Création du script de démarrage silencieux `pymanager_startup.vbs` (renommé par l'utilisateur).

## [v1.1.0] - 2026-06-26
- Ajout du support pour définir le Dossier de travail (`cwd`) d'un script.
- Ajout du support pour définir les Arguments (`args`) de ligne de commande d'un script.
- Remplacement de l'API Windows `ctypes` de sélection de dossier/fichier par une méthode robuste `subprocess` utilisant `tkinter.filedialog`.
- Résolution du problème de fuite des variables d'environnement (nettoyage de `PORT` et `HOST` avant de lancer un subprocess).
- Résolution du problème de buffer Python en injectant `PYTHONUNBUFFERED=1` pour forcer le streaming en direct des logs.
- Implémentation d'une auto-détection "magique" des URLs dans les logs avec Regex.
- Ajout d'un bouton "Web" automatique sur les cartes si une URL est détectée.
- Refonte esthétique majeure (Glow-up UI) des cartes de services pour un aspect plus "premium".

## [v2.0.0] - 2026-06-26
- Réécriture complète de `style.css` : nouveau design system avec palette indigo/vert, design tokens CSS, dot-grid background, custom scrollbar, stagger animations, responsive mobile.
- Réécriture complète de `templates/index.html` : structure sémantique propre, icônes SVG Lucide-style cohérentes, badges de statut (Actif/Inactif), boutons d'action distincts dans le footer, `x-cloak` pour éviter le flash de contenu non-stylé.
- Aucune modification au backend (`main.py`) ni à la logique frontend (`app.js`).

## [v3.0.0] - 2026-06-26
- Nouvelle refonte UI radicale axée sur le minimalisme, la compacité et un aspect très professionnel (style utilitaire de type OS natif / Vercel).
- Abandon des ombres prononcées, des dégradés, et des effets néon.
- Mise en place d'une structure en "liste" très dense, plutôt qu'en grosses cartes.
- Réduction des paddings et de la typographie (system-fonts) pour maximiser l'information affichée.
- Conservation de l'entièreté des fonctionnalités backend et JS.

## [v3.1.0] - 2026-06-26
- Renommage officiel du projet de PiManager vers **PyManager**.
- Ajout de la détection automatique des ports via `psutil` (affichage dynamique dans l'UI).
- Refonte de la logique du bouton "Web" pour supporter `0.0.0.0` intelligemment via `window.location.hostname`.
- Amélioration du parseur de logs : suppression des préfixes `[ERROR]` erronés pour les logs `INFO` de `stderr`.
- Persistance du thème clair/sombre via `localStorage` avec anti-flash script.
- Désactivation de la fermeture accidentelle de la modale d'édition en cliquant à l'extérieur.

## [v4.0.0] - 2026-06-26 (The "Anti-Zombie & Grid" Update)
- **Système Anti-Zombies :** Implémentation de `kill_process_tree` pour tuer récursivement les processus enfants lors du "Stop", empêchant la création de zombies.
- **Radar à Fantômes :** Création de `find_zombie_pid` pour scanner les processus en cours de façon stricte (normalisation des slashes et validation des arguments). Empêche l'auto-start de faire crasher les scripts en "adoptant" les processus existants.
- **Ajout champ GitHub :** Ajout d'un paramètre `github_url` optionnel pour chaque service. Affiche un badge GitHub cliquable avec le SVG officiel à côté du PID.
- **Mise à niveau UI (CSS Grid) :** Remplacement de la liste `flex` par `CSS Grid` pour afficher exactement 2 colonnes (`1fr 1fr`).
- **Correction CSS (Scroll Horizontal) :** Élargissement du container à `1600px` et ajout strict de `min-width: 0` sur les `.card`, `.card-info` et `.info-item` pour forcer la troncature (`text-overflow: ellipsis`) des longs chemins de fichiers sans briser la grille.
- **Correction Poke Minou (Bonus) :** Installation de `python-dotenv` dans l'environnement virtuel de Poke Minou et modification de `config.py` pour qu'il soit 100% autonome sans nécessiter de batch file intermédiaire.

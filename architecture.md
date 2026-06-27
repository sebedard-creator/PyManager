# Spécifications Architecturales : Dashboard Python "Control Center"

## 1. Vue d'ensemble du projet
L'objectif est de développer un tableau de bord web local (Dashboard) permettant d'orchestrer, gérer et surveiller de multiples scripts Python indépendants sur une machine Windows. L'application doit agir comme un "gestionnaire de zoo" pour des processus en arrière-plan.

## 2. Stack Technologique Exigée
- **Backend :** Python avec FastAPI (serveur Uvicorn).
- **Gestion des processus :** Librairies standards `subprocess` (avec `creationflags=subprocess.CREATE_NO_WINDOW` pour Windows) et `psutil` pour le suivi des PID.
- **Frontend :** HTML5, CSS3, et Vanilla JavaScript (ou Alpine.js pour la réactivité). Pas de framework lourd comme React ou Vue. Grille à 2 colonnes (CSS Grid).
- **Communication temps réel :** WebSockets (via FastAPI).
- **Persistance :** Fichier `config.json` local.

## 3. Contraintes Réseau et Système
- **Accessibilité LAN :** Le serveur Uvicorn doit écouter sur l'hôte `0.0.0.0` (ex: port 8000) pour être accessible depuis n'importe quel appareil sur le réseau local.
- **Démarrage Windows :** Le système est conçu pour que seul ce serveur FastAPI soit lancé au démarrage de Windows (via un script dans `shell:startup`). Le backend se chargera ensuite de lancer les processus enfants.

## 4. Fonctionnalités Principales (Backend & Frontend)

### A. Persistance et Configuration Dynamique
- L'interface web doit comporter un bouton "Ajouter un script".
- Ce bouton ouvre un formulaire demandant : Nom du service, Chemin absolu du fichier `.py`, Dossier de travail, Arguments, un lien GitHub, et un toggle "Démarrage automatique (Auto-start)".
- Ces données sont sauvegardées dans un fichier `config.json`.
- Le backend lit ce fichier au démarrage pour populer l'interface.

### B. Cycle de vie des processus et Anti-Zombies
- Au démarrage du serveur FastAPI, une routine lit `config.json` et démarre automatiquement tous les scripts marqués `auto_start: true`.
- **Radar Anti-Zombies :** Avant chaque démarrage automatique et lors des rafraîchissements, PyManager scanne `psutil.process_iter` en normalisant les barres obliques (`/` vs `\`) et les arguments. S'il trouve un processus existant correspondant au script, il "l'adopte" silencieusement au lieu de créer un doublon.
- L'interface affiche l'état en temps réel de chaque script (Pastille Verte = Actif/PID existant, Pastille Rouge = Inactif).
- L'arrêt d'un script utilise une fonction récursive `kill_process_tree` pour tuer le processus parent et tous ses enfants (pour éviter de laisser des fantômes).

### C. Gestion des Logs en Temps Réel (Le Terminal)
- L'interface doit inclure un bouton "Show Log" pour chaque service.
- Le clic sur ce bouton ouvre une fenêtre modale (ou un panneau latéral off-canvas) stylisée comme une console noire avec police monospace.
- **Implémentation technique :** 
  - FastAPI doit lire la sortie standard (`stdout` / `stderr`) des processus enfants de manière **asynchrone** (pour ne pas bloquer le thread principal).
  - Un tunnel **WebSocket** doit être ouvert entre le client et le serveur uniquement lorsque la modale est ouverte.
  - Le texte du terminal doit défiler automatiquement vers le bas à l'arrivée de nouvelles lignes.
  - Fermer la modale ferme la connexion WebSocket.

### D. Support Avancé (Dossiers, Arguments & Auto-détection)
- **Environnement d'exécution :** Support de la définition d'un dossier de travail (`cwd`) et d'arguments de ligne de commande (`args`).
- **Isolation :** Utilisation de `PYTHONUNBUFFERED=1` pour forcer le streaming des logs, et nettoyage des variables d'environnement (`PORT`, `HOST`) pour éviter les conflits (ex: Gradio).
- **Auto-détection d'URL :** Le backend analyse `stdout` avec des expressions régulières pour détecter automatiquement les URLs des interfaces web et affiche un bouton de raccourci.
- **Modales Natives :** Utilisation de `tkinter.filedialog` exécuté dans un `subprocess` pour une compatibilité totale avec les lecteurs réseaux sous Windows, sans bloquer les threads asynchrones de FastAPI.

## 5. Architecture des fichiers (Suggestion pour la génération)
```text
/python-dashboard
│
├── main.py               # Serveur FastAPI, logique de processus et WebSockets
├── config.json           # Fichier généré/modifié dynamiquement (ne pas hardcoder de services)
├── /templates
│   └── index.html        # Interface web principale
└── /static
    ├── style.css         # Design épuré, mode sombre (dark mode) recommandé
    └── app.js            # Logique front-end (fetch API, WebSockets, Modales)
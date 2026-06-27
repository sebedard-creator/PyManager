# PyManager ⚡

PyManager est un tableau de bord web local (Dashboard) ultra-léger permettant d'orchestrer, de gérer et de surveiller de multiples scripts et services Python indépendants sur une machine Windows. 

Agissant comme un véritable "gestionnaire de zoo" pour vos processus en arrière-plan, PyManager s'assure que vos services (serveurs web, bots, pipelines d'IA) tournent de manière fiable et transparente.

## ✨ Fonctionnalités Principales

*   **Orchestration Centralisée** : Lancez et arrêtez tous vos scripts Python (ou `.bat`) depuis une seule interface web esthétique et réactive.
*   **Système Anti-Zombies 🧟‍♂️** : Un puissant radar basé sur `psutil` scanne activement vos processus. PyManager ne crée pas de doublons si un service tourne déjà ; il "l'adopte" silencieusement. L'arrêt d'un script tue proprement l'arborescence complète du processus enfant pour garantir qu'aucun fantôme ne reste en arrière-plan.
*   **Terminal en Temps Réel** : Visualisez les logs (`stdout` / `stderr`) de chaque service en direct grâce à un terminal intégré alimenté par WebSockets.
*   **Détection Automatique (Auto-Discovery)** :
    *   **Ports & URLs** : Le système scanne les logs et les connexions réseau pour détecter automatiquement sur quel port vos services tournent, et crée des liens cliquables pour y accéder via votre LAN.
*   **Démarrage Automatique (Daemon)** : Configurez des services en `auto_start` pour qu'ils soient ressuscités automatiquement lors du démarrage de PyManager.
*   **Interface Moderne (UI/UX)** : Une grille dynamique (CSS Grid), un mode sombre/clair persistant, et un design minimaliste garantissant l'affichage sans défilement horizontal (auto-troncature des longs chemins).
*   **Intégration GitHub** : Liez directement vos services à leurs dépôts GitHub via un champ dédié, affichant un badge officiel dans l'interface.

## 🛠️ Stack Technologique

*   **Backend** : Python 3.10+, FastAPI, Uvicorn, `psutil` (pour la gestion avancée des PID).
*   **Frontend** : HTML5 sémantique, CSS3 (Variables, Grid), Vanilla JavaScript, et Alpine.js (pour la réactivité). Aucun framework lourd.
*   **Persistance** : Fichier local `config.json` mis à jour dynamiquement via l'API.

## 🚀 Installation & Utilisation

1.  Clonez ce dépôt.
2.  Créez un environnement virtuel (`python -m venv .venv`) et activez-le.
3.  Installez les dépendances : 
    ```bash
    pip install -r requirements.txt
    ```
4.  Lancez le gestionnaire :
    *   **Mode silencieux (Recommandé)** : Utilisez le script `pymanager_startup.vbs` pour lancer le serveur en arrière-plan sans fenêtre de console (idéal pour le dossier `shell:startup` de Windows).
    *   **Mode développeur** : Exécutez `python main.py` pour voir les logs du gestionnaire lui-même.
5.  Accédez à l'interface via `http://localhost:8000` (ou votre IP locale).

## 🛑 Arrêt Sécurisé

Pour arrêter complètement PyManager et tous les services enfants qu'il gère de façon propre :
Exécutez le script fourni `stop.bat`. Celui-ci enverra un signal d'extinction via l'API, tuant l'arborescence de tous les processus actifs avant de fermer PyManager.

---

Conçu par Sébastien Bédard

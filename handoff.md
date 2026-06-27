# Handoff PyManager (Session 2026-06-26 — Fin de la grande restructuration)

## Ce qui a été accompli
- **Immunité Anti-Zombies :** PyManager ne laisse plus jamais de processus orphelins (zombies) traîner en arrière-plan. La fonction `kill_process_tree` assassine proprement les parents et les enfants.
- **Radar d'Adoption Intelligente :** Au démarrage (ou au rafraîchissement), PyManager scanne activement tous les processus Windows avec `psutil` (en gérant les problèmes de barres obliques Windows `\`). S'il trouve un de vos services qui tourne déjà, il l'adopte en silence. Fini les crashs de l'`auto_start` qui essaye de lancer un doublon sur un port déjà occupé !
- **Lien GitHub :** Ajout d'un nouveau champ pour lier chaque service à son dépôt GitHub. Une petite icône SVG cliquable apparaît à côté du PID.
- **Refonte UI en 2 colonnes :** Utilisation de CSS Grid pour diviser la liste des services en 2 colonnes (sur les écrans larges) afin d'optimiser l'espace monumental.
- **Correction du Scroll Horizontal :** Application de `min-width: 0` sur les éléments flex de l'UI pour forcer la troncature des chemins de fichiers très longs, gardant l'UI stable et sans barre de défilement horizontale.
- **Correction Autonome de Poke Minou :** Installation de `python-dotenv` dans l'environnement de Poke Minou afin qu'il puisse charger `.env` par lui-même, rendant son exécution directe via PyManager robuste.

## État actuel
- PyManager gère désormais les processus d'une façon experte et hyper-sécurisée.
- L'interface s'adapte élégamment à 1 ou 2 colonnes sans déborder.
- Tous les fichiers `.md` (`architecture.md`, `changelog.md`, `handoff.md`) sont 100% synchronisés avec la réalité du code, selon les directives d'`agents.md`.

## Prochaines étapes
- Tout est stable. Si de nouveaux services sont ajoutés, configurer simplement l'exécutable et les arguments via l'interface UI (comme fait pour SebedSearch).
- L'ordinateur redémarrera automatiquement cette nuit, et PyManager ressuscitera tout silencieusement. Bonne nuit !

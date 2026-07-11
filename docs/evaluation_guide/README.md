# Guide d'évaluation Fly-in

Ce dossier regroupe un support de compréhension progressif du projet Fly-in, rédigé pour une peer-évaluation et pensé comme une présentation orale structurée.

## Ordre de lecture recommandé

1. `00_vue_globale.md`
2. `01_architecture_et_pipeline.md`
3. `02_models.md`
4. `03_parser.md`
5. `04_graph_et_pathfinder.md`
6. `05_scheduler_et_simulator.md`
7. `06_visualizer.md`
8. `07_tests_et_edge_cases.md`
9. `08_algorithmes_et_complexite.md`
10. `09_presentation_orale.md`
11. `10_questions_evaluation.md`
12. `11_fiche_revision.md`

## Ce que couvrent déjà les premiers fichiers

- `00_vue_globale.md` donne la vision d'ensemble : problème, vocabulaire métier, arborescence simplifiée et points d'attention.
- `01_architecture_et_pipeline.md` détaille le chemin complet d'une map, depuis le fichier d'entrée jusqu'à la simulation et à la visualisation.

## Vérification de cohérence avec le dépôt

- L'entrée du programme est `main.py`.
- Le moteur utilise `core/parser.py`, `core/graph.py`, `core/pathfinder.py`, `core/scheduler.py` et `core/simulator.py`.
- Le visualiseur réellement présent est `scripts/visualize.py` avec `visualizer/plotly_visualizer.py`.
- Il n'y a pas de `visualizer/terminal.py` dans l'arborescence actuelle.

## Remarque

Les autres documents seront ajoutés ensuite, mais ce sommaire permet déjà de lire le projet dans le bon ordre et de relier les fichiers entre eux.
# Vue globale du projet

## 1. Arborescence simplifiée du projet

```text
Fly-in/
├── main.py
├── Makefile
├── README.md
├── requirements.txt
├── setup.cfg
├── core/
│   ├── parser.py
│   ├── graph.py
│   ├── pathfinder.py
│   ├── scheduler.py
│   └── simulator.py
├── models/
│   ├── enums.py
│   ├── zone.py
│   ├── connection.py
│   └── drone.py
├── utils/
│   ├── colors.py
│   └── exceptions.py
├── visualizer/
│   └── plotly_visualizer.py
├── scripts/
│   └── visualize.py
├── tests/
│   ├── test_parser.py
│   ├── test_graph.py
│   ├── test_pathfinder.py
│   ├── test_scheduler.py
│   ├── test_simulator.py
│   └── test_drone.py
├── maps/
│   ├── easy/
│   ├── medium/
│   ├── hard/
│   └── challenger/
└── output/
```

## 2. Rôle de chaque dossier

- `core/` contient le moteur du projet : lecture, graphe, recherche de chemins, planification et simulation.
- `models/` contient les objets métier manipulés par le moteur : zones, connexions, drones et enums.
- `utils/` contient des outils transverses, surtout les couleurs terminal et les exceptions.
- `visualizer/` contient le rendu Plotly interactif.
- `scripts/` contient les points d'entrée utilitaires, notamment le script de visualisation.
- `tests/` contient les tests unitaires et quelques tests de validation rapide.
- `maps/` contient les cartes fournies pour valider le comportement du projet.
- `output/` reçoit les fichiers HTML générés par le visualiseur.

## 3. Ordre recommandé pour étudier le code

1. `README.md` racine pour le contexte général.
2. `main.py` pour voir le pipeline complet depuis la ligne de commande.
3. `models/enums.py`, `models/zone.py`, `models/connection.py`, `models/drone.py` pour comprendre les objets manipulés.
4. `core/parser.py` pour voir comment la map est lue et validée.
5. `core/graph.py` pour comprendre la structure de graphe.
6. `core/pathfinder.py` pour voir comment les chemins sont calculés.
7. `core/scheduler.py` pour comprendre la décision de mouvement tour par tour.
8. `core/simulator.py` pour voir comment tout est exécuté et résumé.
9. `scripts/visualize.py` puis `visualizer/plotly_visualizer.py` pour la couche visuelle.
10. `tests/` pour vérifier les comportements réellement couverts.

## 4. Ce que fait le projet

Fly-in simule des drones qui doivent quitter un start hub et atteindre un end hub sur un réseau de zones reliées par des connexions.

Le programme lit un fichier de map, construit les objets Python, calcule des chemins valides, répartit les drones, simule les tours un par un et produit une sortie terminal ainsi qu'une visualisation HTML.

L'objectif n'est pas seulement de trouver un chemin, mais de livrer tous les drones en respectant les contraintes de capacité et en minimisant le nombre de tours.

## 5. Vocabulaire simple

- Une `zone` est un nœud du réseau. Elle a un nom, des coordonnées, une capacité et parfois un type spécial.
- Une `connection` relie deux zones. Elle a aussi une capacité de passage.
- Un `drone` est l'unité mobile qui traverse les zones.
- Le `start hub` est la zone de départ, commune à tous les drones.
- Le `end hub` est la zone d'arrivée, commune à tous les drones.
- Un `graphe` est la structure qui relie toutes les zones entre elles pour permettre la recherche de chemin.

## 6. Analogie simple

On peut imaginer un réseau routier.

- Les zones sont des parkings ou des intersections.
- Les connexions sont des routes.
- Les drones sont des voitures.
- Une zone de capacité limitée ressemble à un parking avec peu de places.
- Une connexion de capacité limitée ressemble à un pont étroit ou un tunnel où l'on ne peut faire passer qu'un nombre limité de véhicules en même temps.
- Une zone blocked ressemble à une route fermée.
- Une zone restricted ressemble à un passage lent, par exemple un péage ou une zone de travaux qui prend plus de temps à traverser.
- Une zone priority ressemble à une voie plus favorable quand deux choix coûtent pareil.

## 7. Ce que le projet cherche à résoudre

Le but est de faire voyager tous les drones du départ à l'arrivée sans violer les contraintes suivantes :

- capacité maximale des zones,
- capacité maximale des connexions,
- interdiction d'entrer dans une zone blocked,
- coût de 2 tours pour une zone restricted,
- priorité donnée aux zones priority quand le coût est équivalent,
- gestion de plusieurs drones en même temps.

## 8. Points clés à connaître avant d'entrer dans le code

- Le projet utilise ses propres classes, pas une bibliothèque de graphe externe.
- Le chemin optimal est calculé avec Dijkstra dans `core/pathfinder.py`.
- La simulation n'est pas une simple liste de chemins statiques : elle se déroule tour par tour.
- Le scheduler doit arbitrer entre plusieurs drones qui veulent parfois entrer dans la même zone au même moment.
- Le visualiseur ne recalcule pas la logique métier : il affiche le résultat déjà produit par la simulation.

## 9. Fichiers à surveiller parce qu'ils structurent tout le projet

- `main.py`
- `core/parser.py`
- `core/graph.py`
- `core/pathfinder.py`
- `core/scheduler.py`
- `core/simulator.py`
- `models/zone.py`
- `models/connection.py`
- `models/drone.py`
- `scripts/visualize.py`
- `visualizer/plotly_visualizer.py`

## 10. Points d'attention pour l'évaluation

- Le dépôt contient aussi des classes d'exceptions homonymes dans `utils/exceptions.py` et dans certains modules `core/*` ; le flux réel utilise surtout les exceptions levées dans les modules appelants.
- Le visualiseur réellement présent est Plotly, pas un terminal viewer.
- `core/graph.py` parle parfois de graphe dirigé dans ses chaînes de documentation, mais le code manipule des connexions bidirectionnelles.
- Le projet privilégie une solution défendable et lisible plutôt qu'un solveur théorique maximaliste.

## 11. Résumé oral très court

Fly-in est une simulation de livraison de drones sur un graphe de zones. Le code lit une map, construit des objets métier, calcule des chemins avec Dijkstra, puis planifie les mouvements tour par tour en respectant les capacités des zones et des connexions. Ensuite, le simulateur produit la sortie terminal et le visualiseur Plotly montre l'évolution de la simulation.
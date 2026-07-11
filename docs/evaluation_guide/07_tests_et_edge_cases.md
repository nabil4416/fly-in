# Tests et cas limites

## A. Rôle général

Les tests vérifient les comportements essentiels du dépôt et montrent ce qui est couvert réellement par la suite présente dans `tests/`.

Ils sont utiles pour l'évaluation, parce qu'ils révèlent à la fois les garanties du code et les zones encore peu couvertes.

## B. Place dans le pipeline

- Ce qui appelle ces fichiers : la suite `pytest` et les commandes de `Makefile`.
- Ce qu'ils testent : le parser, le graphe, le pathfinder, le scheduler, le simulateur et les modèles `Drone`.
- Ce qu'ils ne font pas : ils ne couvrent pas le visualiseur Plotly ni les arguments de ligne de commande de `main.py`.

## C. Imports importants

- Les tests utilisent `unittest` ou des fonctions `pytest` simples.
- Ils importent directement les classes `Parser`, `Graph`, `Pathfinder`, `Scheduler`, `Simulator`, `Drone`, `Zone`, `Connection` et les enums.

## D. Catégories de tests présentes

### Parser valide

Couvert par `tests/test_parser.py`.

Il y a un test de fichier simple valide et un test qui vérifie qu'un même `Parser` peut être réutilisé deux fois.

### Parser invalide

Couvert partiellement par `tests/test_parser.py`.

On y vérifie : absence de `nb_drones`, type de zone invalide, nombre de drones négatif ou nul, zone dupliquée, connexion vers une zone inconnue, connexion inversée dupliquée, métadonnées invalides, capacité nulle, absence de start ou de end.

### Graphe

Couvert par `tests/test_graph.py`.

On y teste : création du graphe, voisins, récupération d'une connexion, reachability et coût de déplacement.

### Pathfinding

Couvert par `tests/test_pathfinder.py`.

On y teste : chemin simple, source égale destination, source invalide, destination inatteignable.

### Capacités des zones

Couvert indirectement par `tests/test_scheduler.py`.

On y teste qu'une zone libérée dans le même tour peut être réutilisée.

### Capacités des connexions

Couvert par `tests/test_scheduler.py`.

On y teste qu'une connexion de capacité 1 laisse passer un seul drone et qu'une capacité 2 permet deux passages.

### Zones blocked

Couvert partiellement dans le moteur, mais pas très bien dans les tests visibles.

Il n'y a pas de test dédié clair pour une zone blocked dans la suite actuelle.

### Zones restricted

Couvert par `tests/test_scheduler.py`.

Le test vérifie l'affichage et la progression en plusieurs tours : transit initial, arrivée intermédiaire, puis arrivée finale.

### Zones priority

Présentes dans le code et dans les maps, mais pas couvertes explicitement par un test visible ici.

### Déplacements simultanés

Couvert partiellement par `tests/test_scheduler.py`.

Le test sur la libération de capacité dans le même tour montre que les mouvements simultanés sont possibles si les contraintes le permettent.

### Deadlocks

Le moteur les détecte, mais il n'y a pas de test dédié visible dans la suite actuelle.

### Performances

Pas de vrai test de performance dans la suite visible.

### Visualisation

Pas de test visible pour `visualizer/plotly_visualizer.py` ou `scripts/visualize.py`.

### Interruption Ctrl+C

Pas de test visible.

### Arguments de ligne de commande

Pas de test visible.

## E. Ce qui n'est pas testé ou peu couvert

- Les couleurs terminal dans `utils/colors.py`.
- Les erreurs d'incompatibilité entre `main.py` et `scripts/visualize.py`.
- Les cas de `blocked` dans le scheduler avec une vraie map dédiée.
- Les conflits complexes avec plusieurs chemins et plusieurs zones partagées.
- La régression du visualiseur.
- La sortie exacte de `main.py` avec `--capacity-info`.

## F. Risques encore présents

- Le visualiseur peut diverger du moteur si la reconstruction de timeline n'est pas alignée.
- Les tests n'explorent pas toutes les variantes de maps fournies dans `maps/`.
- Le code de planning repose sur un ensemble de chemins candidats limité, donc certaines situations complexes peuvent rester sensibles.
- Les comportements de priorité sont présents dans le code de recherche, mais peu vérifiés par les tests.

## G. Comparaison avec les exigences du sujet Fly-in

Le dépôt couvre bien les points principaux attendus pour une solution défendable : lecture de map, validation, graphe, pathfinding, capacité des zones et des connexions, simulation et visualisation.

Les zones sensibles sont surtout les suivants :

- couverture incomplète des zones priority et blocked,
- absence de tests d'interface CLI,
- absence de tests de performance,
- couverture limitée du visualiseur.

## H. Ce que je dois dire à l'évaluation

La suite de tests vérifie le cœur du projet : parser, graphe, chemin, scheduler, simulateur et modèles. Elle montre bien les cas valides et plusieurs cas invalides importants, comme les doublons, les capacités nulles ou les connexions vers des zones inconnues. En revanche, le visualiseur, les arguments CLI et certains cas avancés comme les zones priority ou blocked restent peu testés.

## I. Questions probables des évaluateurs

1. Quels comportements sont les mieux testés ?
2. Quels sont les trous de couverture les plus visibles ?
3. Pourquoi les tests de `scheduler` sont-ils importants pour la capacité ?
4. Comment sais-tu que le parser est réutilisable ?
5. Quels risques restent malgré les tests ?

## J. Modification rapide possible

Une demande fréquente serait d'ajouter un test pour une zone blocked.

Le bon endroit est `tests/test_scheduler.py` ou `tests/test_parser.py`, selon qu'on veut tester la validation à l'entrée ou l'interdiction de déplacement dans la simulation. C'est une modification simple mais très utile pour l'évaluation.
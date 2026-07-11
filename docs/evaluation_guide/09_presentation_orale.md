# Présentation orale complète

## 1. Objectif du projet

Fly-in est une simulation de drones qui doivent aller d'un start hub à un end hub en respectant des capacités de zones et de connexions.

Le but n'est pas seulement de trouver un chemin. Il faut aussi faire passer plusieurs drones, limiter les blocages, gérer les zones spéciales et terminer en un nombre de tours raisonnable.

## 2. Format des maps

Une map commence par `nb_drones`, puis définit les zones avec leur type, leurs coordonnées et parfois leur capacité ou leur couleur. Ensuite, elle relie les zones avec des connexions.

Dans le code, c'est `core/parser.py` qui lit ce format et le transforme en objets `Zone` et `Connection`.

## 3. Architecture

Le projet est découpé en plusieurs couches.

- `models/` décrit les objets métier.
- `core/parser.py` lit la map.
- `core/graph.py` construit le réseau de navigation.
- `core/pathfinder.py` calcule les chemins.
- `core/scheduler.py` décide les mouvements.
- `core/simulator.py` rejoue la simulation.
- `visualizer/plotly_visualizer.py` affiche le résultat.

Cette séparation rend le code plus simple à comprendre et à défendre à l'oral.

## 4. Modèles

Les objets principaux sont `Zone`, `Connection` et `Drone`.

- `Zone` représente une case du graphe avec un type et une capacité.
- `Connection` relie deux zones et limite le trafic.
- `Drone` garde son état, sa position et son chemin.

Les enums `ZoneType`, `ZoneCategory` et `DroneState` servent à éviter les chaînes de caractères libres.

## 5. Parser

Le parser est le premier vrai filtre de qualité.

Il ignore les commentaires, lit le nombre de drones, crée les zones, crée les connexions et vérifie les erreurs comme les doublons, les références inconnues ou l'absence de start/end hub.

Si la map est invalide, le programme s'arrête tôt avec un message clair.

## 6. Graphe

Une fois la map validée, `Graph` construit une représentation en mémoire des voisinages.

Le projet n'utilise pas de bibliothèque de graphe externe. Il garde une liste d'adjacence et une map de connexions pour répondre vite aux questions : "qui est voisin de qui ?" et "quelle est la capacité de ce lien ?".

## 7. Algorithme de recherche

Le pathfinder utilise Dijkstra.

Cela permet de prendre en compte des coûts différents : normal et priority coûtent 1, restricted coûte 2, blocked est inaccessible. Si deux chemins ont le même coût, le code favorise les zones priority.

## 8. Scheduler

Le scheduler est la partie la plus importante pour la simulation.

Il répartit les drones sur plusieurs chemins candidats, vérifie les capacités et décide quels drones avancent, lesquels attendent et lesquels terminent leur trajet.

Il traite aussi les drones déjà en transit vers une zone restricted, parce qu'ils doivent terminer leur entrée au tour suivant.

## 9. Simulation

Le simulateur exécute les décisions du scheduler tour par tour.

Il enregistre l'historique, construit la sortie texte, calcule les métriques et s'arrête quand tous les drones sont livrés.

## 10. Visualisation

Le visualiseur Plotly ne change pas la logique de simulation.

Il affiche le graphe, les drones et l'évolution des tours à partir de l'historique produit par `Simulator`. Le script `scripts/visualize.py` sert de point d'entrée pour générer le HTML.

## 11. Tests et performances

Les tests couvrent surtout le parser, le graphe, le pathfinder, le scheduler, le simulateur et les modèles Drone.

La stratégie choisie est lisible et efficace pour les maps fournies, mais ce n'est pas un solveur optimal global comme un flot maximum.

## 12. Limites et améliorations possibles

- Ajouter plus de tests sur les zones priority et blocked.
- Tester davantage l'interface CLI de `main.py`.
- Améliorer la couverture du visualiseur.
- Ajuster le scheduler si l'on veut explorer plus de chemins candidats.

## 13. Script oral naturel

"Fly-in est un projet de simulation de drones sur un graphe. Le programme lit une map, valide les zones et les connexions, construit un graphe, calcule des chemins avec Dijkstra, puis utilise un scheduler pour faire avancer plusieurs drones en respectant les capacités. Ensuite, un simulateur rejoue les tours un par un et produit la sortie finale. Le visualiseur Plotly permet de voir la simulation sans modifier la logique."

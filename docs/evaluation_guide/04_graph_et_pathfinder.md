# Le graphe et le pathfinder

## A. Rôle général

`core/graph.py` transforme les zones et les connexions en structure navigable. `core/pathfinder.py` utilise ensuite cette structure pour calculer des chemins valides et les classer par coût.

Ces deux fichiers font la transition entre la description statique de la carte et la logique de navigation.

## B. Place dans le pipeline

- Ce qui appelle ces fichiers : `main.py`, `scripts/visualize.py` et `core/scheduler.py`.
- Ce qu'ils appellent : `models/zone.py`, `models/connection.py` et `utils/exceptions.py`.
- Ce qu'ils reçoivent : des zones et des connexions issues du parser, puis des noms de zones source et destination.
- Ce qu'ils retournent : des voisins, des connexions, des coûts, ou un chemin complet.

## C. Imports importants

- `deque` est utilisé pour la recherche en largeur dans `Graph.is_reachable()`.
- `heapq` est utilisé par `Pathfinder` pour Dijkstra.
- `Zone`, `Connection` et `ZoneType` permettent de lire les capacités et les types de zones.

## D. Classes, fonctions et méthodes principales

### `GraphError`

Exception levée quand la structure du graphe est invalide ou qu'une zone demandée n'existe pas.

### `Graph`

`Graph` stocke :

- `zones` : dictionnaire nom de zone -> objet `Zone`
- `connections` : liste des `Connection`
- `_adjacency` : liste des voisins pour chaque zone
- `_connection_map` : accès rapide à une connexion donnée dans les deux sens

Ses méthodes importantes :

- `get_neighbors(zone_name)` : retourne les voisins directs.
- `get_connection(zone_a, zone_b)` : retourne la connexion entre deux zones.
- `has_edge(zone_a, zone_b)` : vérifie si un lien existe.
- `is_reachable(start, end)` : teste l'existence d'un chemin par BFS.
- `get_zone(zone_name)` : renvoie un objet `Zone`.
- `get_movement_cost(zone_name)` : renvoie le coût d'entrée d'une zone.
- `get_connection_capacity(zone_a, zone_b)` : renvoie la capacité du lien.

### `PathfindingError`

Exception levée quand la recherche de chemin échoue.

### `PathfindingResult`

Contient un chemin calculé et son coût total.

### `Pathfinder.find_shortest_path(source, destination)`

C'est la recherche principale.

Elle utilise Dijkstra avec une file de priorité. Le coût d'un chemin est construit en additionnant le coût d'entrée des zones traversées.

Le code traite aussi les zones priority en leur donnant un score secondaire quand deux coûts sont égaux. Cela permet de préférer un chemin qui passe par plus de zones priority.

### `Pathfinder.find_all_shortest_paths(source, destination, max_paths=5)`

Cette méthode retourne plusieurs chemins candidats.

Elle sert surtout au scheduler pour répartir les drones sur plusieurs routes possibles. Elle explore des chemins simples sans repasser par une zone déjà présente dans le même chemin.

## E. Déroulement interne

### Côté graphe

1. Le constructeur vérifie qu'il existe au moins une zone et une connexion.
2. Il construit une liste d'adjacence.
3. Il construit une map de connexions pour les requêtes rapides.
4. Il valide que les connexions pointent vers des zones connues et qu'aucune zone blocked n'est reliée.

### Côté pathfinder

1. La méthode valide l'existence de la source et de la destination.
2. Elle initialise les distances, les prédécesseurs et la file de priorité.
3. Elle dépile le nœud de coût minimal.
4. Elle explore ses voisins.
5. Elle ignore les zones blocked.
6. Elle met à jour la meilleure distance connue.
7. Quand la destination est atteinte, elle reconstruit le chemin.

## F. Exemple concret

Avec une carte `start -> a -> goal` et `start -> b -> goal`, si `a` est normal et `b` est restricted, le pathfinder peut préférer `start -> a -> goal` car le coût total est plus faible.

Si deux chemins ont le même coût, la logique de score secondaire peut favoriser celui qui contient davantage de zones priority.

## G. Edge cases et erreurs

- Une zone demandée qui n'existe pas déclenche une erreur.
- Une carte vide ou sans connexion déclenche une erreur lors de la construction du graphe.
- Une connexion vers une zone blocked déclenche une erreur dans `Graph`.
- `is_reachable()` ne tient pas compte du type de zone pour la validité simple de la connexion ; il répond seulement à la question "un chemin topologique existe-t-il ?".
- `find_shortest_path()` ignore les zones blocked.
- `find_all_shortest_paths()` évite les cycles simples en n'ajoutant pas deux fois la même zone dans un chemin.

## H. Ce que je dois dire à l'évaluation

Le graphe est la structure de navigation du projet. Il transforme la carte en voisins et en accès rapides aux connexions. Ensuite, le pathfinder applique Dijkstra pour trouver le chemin le moins coûteux entre deux zones, en tenant compte des zones restricted, priority et blocked. C'est ce couple graphe plus pathfinder qui permet au scheduler de travailler sur de vraies routes plutôt que sur du texte brut.

## I. Questions probables des évaluateurs

1. Pourquoi utiliser une liste d'adjacence ?
2. À quoi sert `is_reachable()` si Dijkstra existe déjà ?
3. Comment la zone priority influence-t-elle la recherche ?
4. Pourquoi `find_all_shortest_paths()` est-elle utile au scheduler ?
5. Comment le code empêche-t-il de traverser une zone blocked ?

## J. Modification rapide possible

Une modification possible serait d'ajouter un coût différent pour un nouveau type de zone, par exemple `slow`.

Le changement se ferait dans `models/zone.py` pour le modèle de coût, puis dans `core/pathfinder.py` pour que la recherche le prenne en compte. C'est un bon exercice parce qu'il montre comment un changement de règle métier se propage dans le moteur.
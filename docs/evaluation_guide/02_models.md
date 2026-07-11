# Les modèles

## A. Rôle général

Les fichiers de `models/` définissent les objets métier de base du projet. Ils servent à représenter proprement les zones, les connexions, les drones et les enums partagées par le moteur.

Leur rôle est important parce que tout le reste du programme manipule ces objets. Le parser les construit, le graphe les stocke, le scheduler les met à jour et le visualiseur les lit.

## B. Place dans le pipeline

- Ce qui appelle ces fichiers : `core/parser.py`, `core/graph.py`, `core/pathfinder.py`, `core/scheduler.py`, `core/simulator.py` et `scripts/visualize.py`.
- Ce que ces fichiers appellent : surtout des validations internes, puis les autres modules du moteur.
- Ce qu'ils reçoivent : les données extraites de la map et les états de simulation.
- Ce qu'ils retournent ou modifient : des objets typés ou l'état d'un drone pendant la simulation.

## C. Imports importants

- `models/enums.py` est importé par `models/zone.py` et `models/drone.py` pour partager les états et les types.
- `models/zone.py` et `models/connection.py` sont les bases du graphe.
- `models/drone.py` est utilisé par le scheduler et le simulateur.

## D. Classes, fonctions et méthodes principales

### `models/enums.py` et `DroneState`

`DroneState` décrit les états possibles d'un drone : `idle`, `moving`, `waiting_for_capacity`, `in_transit_restricted` et `delivered`.

Ce type est nécessaire pour éviter de gérer des chaînes de caractères libres partout dans le code. Le scheduler et le simulateur s'en servent pour savoir si un drone a bougé, attend, traverse une zone restricted ou a déjà terminé.

### `models/zone.py` et `ZoneType`, `ZoneCategory`, `Zone`

`ZoneType` décrit le comportement d'une zone : `normal`, `restricted`, `priority` ou `blocked`.

`ZoneCategory` décrit sa place dans la carte : `start_hub`, `end_hub` ou `hub`.

`Zone` contient le nom, les coordonnées, le type, la catégorie, la capacité maximale, une couleur facultative et des métadonnées.

Ses méthodes et propriétés les plus importantes sont :

- `is_start`, `is_end`, `is_special_hub` pour reconnaître les hubs spéciaux.
- `is_blocked` pour interdire l'entrée dans une zone.
- `movement_cost` pour savoir combien de tours il faut pour entrer dans une zone.
- `has_capacity(current_occupancy)` pour vérifier s'il reste de la place.
- `position()` pour récupérer les coordonnées.

### `models/connection.py` et `Connection`

`Connection` représente un lien bidirectionnel entre deux zones.

Il stocke `zone_a`, `zone_b`, `max_link_capacity` et des métadonnées. Sa méthode `connects(zone_a, zone_b)` vérifie si la connexion relie bien deux zones dans n'importe quel ordre. `other_side(zone_name)` retourne l'autre extrémité du lien. `key()` produit une clé normalisée pour détecter les doublons comme `a-b` et `b-a`.

### `models/drone.py` et `Drone`

`Drone` représente un agent mobile. Il stocke son identifiant, sa zone actuelle, sa destination, son état, son chemin prévu, le nombre de tours restants pour arriver quand il traverse une zone restricted, et des métadonnées.

Les méthodes importantes sont :

- `next_zone` pour connaître la prochaine zone sur la route.
- `set_path(new_path)` pour enregistrer le chemin calculé.
- `move_to(next_zone)` pour faire un déplacement normal.
- `start_restricted_transit(connection_name)` pour commencer un transit de deux tours.
- `complete_restricted_transit(destination_zone)` pour finir ce transit.
- `mark_delivered()` pour marquer l'arrivée.
- `set_waiting()` pour signaler l'attente.

## E. Déroulement interne

1. Le parser lit la map et crée les `Zone` et `Connection`.
2. Il crée ensuite les `Drone` de départ avec `Parser.create_drones()`.
3. Le scheduler lit `Drone.next_zone` pour choisir les mouvements.
4. Quand un drone entre dans une zone restricted, il passe temporairement en `IN_TRANSIT_RESTRICTED`.
5. Quand il atteint le end hub, il passe en `DELIVERED`.

## F. Exemple concret

Une zone comme `hub: a 1 0 [max_drones=2 zone=priority color=blue]` devient un objet `Zone` avec :

- `name = "a"`
- `x = 1`
- `y = 0`
- `zone_type = ZoneType.PRIORITY`
- `category = ZoneCategory.HUB`
- `max_drones = 2`
- `color = "blue"`

Un drone créé au départ ressemble à : `Drone(D1 at start → goal [idle])`.

## G. Edge cases et erreurs

- `Zone` refuse un nom vide, contenant un tiret ou un espace.
- `Zone` refuse `max_drones < 1`.
- `Zone.has_capacity()` refuse une occupation négative.
- `Connection` refuse une connexion vide, auto-référente ou avec une capacité invalide.
- `Drone` refuse un identifiant vide, une zone vide ou un état qui n'est pas un `DroneState`.
- `Drone.set_path()` refuse un chemin vide ou ne commençant pas par la zone actuelle.
- `Drone.move_to()` refuse un déplacement qui ne suit pas le chemin prévu.

## H. Ce que je dois dire à l'évaluation

Les modèles sont les briques de base du projet. `Zone` décrit une case du graphe avec sa capacité et son type, `Connection` relie deux zones avec une capacité de passage, et `Drone` garde l'état d'un agent pendant toute la simulation. Les enums servent à éviter des chaînes libres partout dans le code et rendent les comparaisons plus sûres.

## I. Questions probables des évaluateurs

1. Pourquoi utiliser des enums ?
2. Quelle différence entre `ZoneType` et `ZoneCategory` ?
3. Pourquoi `Connection` est-elle bidirectionnelle ?
4. Que représente `turns_until_arrival` dans `Drone` ?
5. Pourquoi `Zone.has_capacity()` traite start et end différemment ?

## J. Modification rapide possible

Une modification simple serait de changer la capacité par défaut d'une zone dans `models/zone.py`, ou d'ajouter un nouveau type visuel dans `ZoneType`.

Le bon endroit est `models/zone.py` et, si la couleur est concernée, `utils/colors.py` ou `visualizer/plotly_visualizer.py`. C'est une bonne question d'évaluation parce qu'elle montre comment un changement de modèle se propage vers le reste du projet.
# Le scheduler et le simulateur

## A. Rôle général

`core/scheduler.py` décide quels drones peuvent bouger à chaque tour. `core/simulator.py` exécute ces décisions, maintient l'état global et produit la sortie finale.

Ces deux fichiers sont le cœur dynamique du projet. Ils transforment un ensemble de chemins en une simulation tour par tour.

## B. Place dans le pipeline

- Ce qui appelle ces fichiers : `main.py` et `scripts/visualize.py`.
- Ce qu'ils appellent : `core/pathfinder.py`, `core/graph.py`, `models/drone.py`, `models/enums.py` et `utils/exceptions.py`.
- Ce qu'ils reçoivent : une liste de drones, un graphe, un start hub et un end hub.
- Ce qu'ils retournent : une liste de résultats de planification, un état de simulation, une sortie terminal et des métriques.

## C. Imports importants

- `PathfindingResult` est utilisé par le scheduler pour distribuer les chemins.
- `DroneState` sert à distinguer les drones en transit, en attente ou livrés.
- `ZoneType` sert à gérer les zones restricted, priority et blocked.

## D. Classes, fonctions et méthodes principales

### `SchedulingError`

Exception levée quand le moteur de planification ne peut pas avancer de manière valide.

### `SchedulingResult`

Résultat d'un tour de planification.

Il contient :

- `moves` : dictionnaire `drone_id -> destination`
- `move_outputs` : chaînes à afficher dans la sortie terminal
- `waiting_drones`
- `completed_drones`
- `turn_number`
- `is_valid`
- `zone_occupancy`
- `connection_usage`

### `Scheduler.schedule_all_drones(drones, start_zone, end_zone)`

C'est le point d'entrée principal du scheduler.

Il récupère plusieurs chemins candidats auprès du pathfinder, essaye de répartir les drones, puis lance la boucle de tour. Si une tentative échoue, il peut réinitialiser les drones et essayer un plan plus simple.

### `Scheduler.schedule_turn(drones, turn_number)`

Cette méthode planifie un seul tour.

Elle :

1. filtre les drones actifs,
2. calcule l'occupation des zones,
3. détermine les mouvements candidats,
4. valide les capacités,
5. exécute les mouvements,
6. renvoie un `SchedulingResult`.

### `Scheduler._validate_and_assign_moves(...)`

Cette méthode gère le conflit entre drones.

Elle traite d'abord les drones déjà en transit restricted, puis les drones réguliers. Elle vérifie la capacité des zones, la capacité des connexions, et le fait qu'un drone ne doit pas entrer dans une zone blocked.

### `Scheduler._execute_move(drone, destination)`

Cette méthode applique réellement un déplacement.

Elle distingue trois cas :

- transit restricted en cours,
- entrée dans une zone restricted,
- déplacement normal.

### `Simulator.run()`

Le simulateur lance la boucle complète.

Il appelle `scheduler.schedule_all_drones()`, enregistre les résultats, met à jour les métriques et marque la simulation comme complétée quand tous les drones sont livrés.

### `Simulator.get_output()` et `Simulator.get_capacity_output()`

Ces méthodes renvoient respectivement la sortie textuelle des mouvements et la sortie détaillée des capacités par tour.

## E. Déroulement interne

### Côté scheduler

1. Les chemins candidats sont récupérés.
2. Les drones sont associés aux chemins.
3. À chaque tour, les drones en transit restricted sont traités en premier.
4. Ensuite, les autres drones sont triés selon leur progression sur le chemin.
5. Les mouvements sont acceptés seulement si la capacité de zone et de connexion le permet.
6. Les drones bloqués ou non prioritaires attendent.

### Côté simulateur

1. `run()` démarre la simulation.
2. Il reçoit la suite de `SchedulingResult`.
3. `_process_turn()` transforme chaque tour en sortie texte.
4. `_calculate_metrics()` calcule les statistiques finales.
5. `get_summary()` produit un résumé lisible pour l'utilisateur.

## F. Exemple concret

Si deux drones veulent entrer dans une zone `a` de capacité 1 au même tour, le scheduler peut laisser passer le drone qui est déjà plus avancé sur son chemin et faire attendre l'autre.

Si un drone entre dans une zone restricted, il n'affiche pas immédiatement une arrivée complète : la simulation le fait passer par un état intermédiaire pour représenter les deux tours nécessaires.

## G. Edge cases et erreurs

- Une liste vide de drones déclenche une erreur.
- Si aucun chemin n'existe, la planification échoue.
- Si une zone attendue n'existe pas dans le graphe, une erreur est levée.
- Si un drone en transit restricted n'a pas de prochaine zone, c'est une erreur de cohérence.
- Le scheduler a une limite de tours et une détection de starvation pour éviter les boucles infinies.
- Une zone blocked dans le chemin d'un drone déclenche une erreur.
- Une capacité de connexion atteinte empêche le mouvement pendant ce tour.

## H. Ce que je dois dire à l'évaluation

Le scheduler est le cerveau tactique du projet. Il prend les chemins calculés, répartit les drones et décide qui bouge à chaque tour en respectant les capacités des zones et des connexions. Le simulateur, lui, rejoue ces décisions et produit l'historique complet de la simulation, la sortie texte et les métriques. Autrement dit, le scheduler décide, le simulateur exécute.

## I. Questions probables des évaluateurs

1. Comment sais-tu qu'un drone doit attendre ?
2. Pourquoi traiter les drones en transit restricted avant les autres ?
3. Comment évites-tu qu'une zone pleine soit surchargée ?
4. Que se passe-t-il si la planification stagne trop longtemps ?
5. Comment le simulateur sait-il que tout est terminé ?

## J. Modification rapide possible

Une modification simple serait de changer la limite de détection de deadlock dans `Scheduler._run_turn_loop()`.

Le bon endroit est la variable `max_turns_without_delivery_progress`. C'est un bon sujet de live coding parce qu'il permet d'expliquer le compromis entre sécurité et tolérance avant de déclencher une erreur.
# Le parser

## A. Rôle général

`core/parser.py` lit le fichier de map, valide sa syntaxe et sa cohérence, puis le transforme en objets Python utilisables par le reste du programme.

Ce fichier est central, parce que toute la chaîne de traitement dépend de la qualité des données qu'il produit. S'il détecte une erreur, le programme doit s'arrêter proprement avec un message clair.

## B. Place dans le pipeline

- Ce qui appelle ce fichier : `main.py` et `scripts/visualize.py`.
- Ce que ce fichier appelle : `models/zone.py`, `models/connection.py`, `models/drone.py`, `models/enums.py` et `utils/exceptions.py`.
- Ce qu'il reçoit : un chemin vers un fichier texte.
- Ce qu'il retourne : un `InputData` contenant `num_drones`, `start_zone`, `end_zone`, `zones` et `connections`.

## C. Imports importants

- `re` sert à reconnaître les lignes par motifs.
- `Path` permet d'accepter un chemin de fichier.
- `Connection`, `Drone`, `Zone`, `ZoneCategory`, `ZoneType`, `DroneState` sont les objets construits par le parser.
- `ParsingError` sert à remonter les erreurs avec un numéro de ligne.

## D. Classes, fonctions et méthodes principales

### `InputData`

`InputData` est un conteneur simple. Il rassemble les données finales extraites du fichier avant qu'elles soient envoyées au graphe et au moteur.

Il contient :

- `num_drones`
- `start_zone`
- `end_zone`
- `zones`
- `connections`

### `Parser.parse_file(filepath)`

C'est la méthode principale.

Elle :

1. réinitialise l'état du parser,
2. lit toutes les lignes du fichier,
3. traite chaque ligne une par une,
4. vérifie l'état final,
5. retourne un `InputData`.

### `Parser._parse_line(line)`

Cette méthode enlève les commentaires inline, ignore les lignes vides, puis essaye de reconnaître une ligne `nb_drones`, une zone ou une connexion.

Si aucune forme ne correspond, elle lève une `ParsingError` avec le numéro de ligne.

### `Parser._try_parse_nb_drones(line)`

Cette méthode lit la première information utile de la map.

Elle vérifie qu'il n'y a qu'une seule déclaration, que la valeur est un entier positif et qu'elle est placée sur la première ligne non vide / non commentée.

### `Parser._try_parse_zone(line)`

Cette méthode reconnaît les lignes de zone.

Elle valide :

- le nom de zone,
- l'unicité du nom,
- les coordonnées entières,
- l'unicité du start hub,
- l'unicité du end hub,
- le type de zone,
- la capacité maximale,
- les métadonnées.

Elle crée ensuite un objet `Zone`.

### `Parser._try_parse_connection(line)`

Cette méthode reconnaît les lignes `connection: a-b`.

Elle vérifie :

- que les deux zones existent déjà,
- que la connexion n'est pas auto-référente,
- que le couple `a-b` n'a pas déjà été vu sous une autre forme,
- que la capacité de liaison est valide.

Elle crée ensuite un objet `Connection`.

### `Parser._parse_metadata(metadata_str)`

Cette méthode découpe les blocs entre crochets comme `[color=green max_drones=2]`.

Chaque paire doit avoir la forme `cle=valeur`. Les doublons de clés sont interdits.

### `Parser.create_drones(num_drones, start_zone, end_zone)`

Cette méthode fabrique la liste initiale des drones.

Tous les drones démarrent dans la zone de départ, avec l'état `IDLE` et un chemin initial contenant seulement le start hub.

## E. Déroulement interne

1. `parse_file()` ouvre le fichier et lit toutes les lignes.
2. `._parse_line()` nettoie les commentaires et décide quel type d'information la ligne contient.
3. `._try_parse_nb_drones()` initialise le nombre de drones.
4. `._try_parse_zone()` crée les zones et enregistre le start/end hub.
5. `._try_parse_connection()` enregistre les liens entre zones.
6. `._validate_final_state()` vérifie qu'il reste bien un nombre de drones, un start et un end.
7. `parse_file()` renvoie un `InputData` prêt à être utilisé.

## F. Exemple concret

Avec une map comme :

```text
nb_drones: 2
start_hub: start 0 0 [color=green]
hub: mid 1 0 [max_drones=1 zone=restricted]
end_hub: goal 2 0 [color=red]
connection: start-mid [max_link_capacity=2]
connection: mid-goal
```

le parser produit :

- `num_drones = 2`
- une zone `start` de catégorie `START_HUB`
- une zone `mid` de type `RESTRICTED`
- une zone `goal` de catégorie `END_HUB`
- deux connexions bidirectionnelles

## G. Edge cases et erreurs

- Les lignes vides et les commentaires sont ignorés.
- Le premier contenu utile doit être `nb_drones`.
- `nb_drones` doit être strictement positif.
- Les noms de zones et de connexions ne peuvent pas contenir de tiret ou d'espace.
- Les coordonnées négatives sont acceptées car les motifs `-?\d+` les autorisent.
- Une zone dupliquée déclenche une erreur.
- Une connexion vers une zone inconnue déclenche une erreur.
- Une connexion inverse déjà vue, par exemple `a-b` puis `b-a`, déclenche une erreur.
- Une métadonnée mal formée déclenche une erreur avec la ligne concernée.
- Une valeur `max_drones` ou `max_link_capacity` nulle ou négative déclenche une erreur.
- L'absence de start ou de end hub déclenche une erreur à la fin.

## H. Ce que je dois dire à l'évaluation

Le parser est la porte d'entrée du projet. Il lit le fichier ligne par ligne, ignore ce qui est décoratif comme les commentaires, crée les zones et les connexions, puis vérifie les règles de cohérence de la map. Son rôle est d'empêcher que des données invalides entrent dans le moteur de simulation.

## I. Questions probables des évaluateurs

1. Pourquoi imposer `nb_drones` en premier ?
2. Comment détectes-tu une connexion dupliquée ?
3. Comment le parser gère-t-il les commentaires inline ?
4. Que se passe-t-il si le start hub manque ?
5. Pourquoi les coordonnées négatives sont-elles acceptées ici ?

## J. Modification rapide possible

Une demande fréquente serait d'ajouter une nouvelle métadonnée sur les zones, par exemple `label=...`.

Le changement se fait dans `_parse_metadata()` et dans `_try_parse_zone()` si cette donnée doit être stockée dans `Zone`. C'est une bonne modification de live coding parce qu'elle teste la compréhension du flot de données du parser vers les modèles.
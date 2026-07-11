# Questions d'évaluation

## Questions simples

### Pourquoi utiliser des classes ?

Pour séparer les responsabilités et rendre les données plus claires. `Zone`, `Connection` et `Drone` représentent des objets du monde du projet, ce qui rend le code plus lisible qu'une suite de dictionnaires ou de tuples.

### Quelle différence entre `Zone` et `Connection` ?

`Zone` est un nœud du graphe, avec une position, un type et une capacité. `Connection` relie deux zones et limite le nombre de drones qui peuvent la traverser.

### Pourquoi les connexions sont-elles bidirectionnelles ?

Parce que le code les modélise comme des liens non orientés. La même connexion peut être utilisée dans les deux sens, et `Graph` stocke les deux ordres pour simplifier les recherches.

### Que contient un objet `Drone` ?

Son identifiant, sa zone actuelle, sa destination, son état, son chemin, son compteur de transit restricted et quelques métadonnées.

## Questions intermédiaires

### Comment empêches-tu deux drones d'entrer dans une zone de capacité 1 ?

Le scheduler calcule l'occupation des zones pendant le tour et n'autorise un mouvement que si `Zone.has_capacity()` reste vraie après les mouvements déjà attribués.

### Pourquoi une zone restricted coûte-t-elle deux tours ?

Parce que `Zone.movement_cost` la définit ainsi et que le scheduler la traite comme un transit en deux étapes : entrée puis arrivée au tour suivant.

### Comment détectes-tu une connexion dupliquée ?

Le parser normalise la paire de zones avec un tri alphabétique et stocke cette clé dans un ensemble. Ainsi `a-b` et `b-a` sont considérés comme identiques.

### Comment répartis-tu les drones sur plusieurs chemins ?

Le pathfinder fournit plusieurs chemins candidats, puis le scheduler les attribue aux drones de façon simple et stable, en visant une répartition qui évite les congestions.

### Pourquoi le graphe a-t-il besoin d'une map de connexions en plus de la liste d'adjacence ?

La liste d'adjacence sert à trouver les voisins. La map de connexions sert à retrouver rapidement la capacité exacte d'un lien précis.

## Questions difficiles

### Quelle est la complexité du pathfinding ?

Pour Dijkstra, la complexité est approximativement `O((V + E) log V)` avec une file de priorité.

### Comment garantis-tu l'absence de deadlock ?

Le code ne garantit pas une absence absolue dans un sens théorique. Il réduit le risque avec des règles de priorité, une limite de tours sans progrès et des erreurs explicites si la simulation stagne.

### Pourquoi ton algorithme n'est-il pas nécessairement optimal globalement ?

Parce qu'il combine un plus court chemin local et un scheduler glouton. Il cherche une solution valable et défendable, pas un optimum mathématique global sur tous les drones simultanément.

### Que se passe-t-il si plusieurs drones libèrent et occupent une zone pendant le même tour ?

Le scheduler suit l'ordre de traitement du tour et met à jour l'occupation projetée. Cela permet de considérer qu'une sortie peut libérer de la place avant qu'un autre drone entre, si les règles du tour le permettent.

### Comment adapter le programme à des connexions dirigées ?

Il faudrait modifier `Connection`, `Graph._build_adjacency_list()`, `Graph._build_connection_map()` et les vérifications associées pour ne stocker qu'un seul sens.

### Comment ajouter une nouvelle zone coûtant trois tours ?

Il faudrait ajouter un nouveau type dans `ZoneType`, lui donner un coût dans `Zone.movement_cost` et adapter `Pathfinder._get_movement_cost()` ainsi que les tests associés.

## Questions pièges possibles

### Est-ce que `main.py` recalcule les chemins ?

Non, `main.py` orchestre seulement les étapes. Les chemins sont calculés dans `Pathfinder`.

### Le visualiseur modifie-t-il la simulation ?

Non. Il lit l'état de simulation et le rend en HTML.

### Le parser accepte-t-il les coordonnées négatives ?

Oui, la regex les autorise et les objets `Zone` les stockent sans restriction supplémentaire.

### Les hubs start et end ont-ils une capacité limitée ?

Non, le code les traite comme des hubs spéciaux à capacité pratique illimitée.

## Réponses courtes à mémoriser

- Classes : pour structurer les objets du projet.
- Graph : pour naviguer dans la map.
- Dijkstra : pour trouver le chemin le moins coûteux.
- Scheduler : pour éviter les conflits de capacité.
- Simulator : pour rejouer la simulation et produire la sortie.

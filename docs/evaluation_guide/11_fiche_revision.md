# Fiche de révision condensée

## 1. Les 15 notions à retenir

1. `nb_drones` ouvre la map.
2. Une `Zone` est un nœud du graphe.
3. Une `Connection` relie deux zones.
4. Un `Drone` garde un état et un chemin.
5. `start_hub` et `end_hub` sont spéciaux.
6. `normal` et `priority` coûtent 1 tour.
7. `restricted` coûte 2 tours.
8. `blocked` est inaccessible.
9. Le parser valide les données avant tout.
10. Le graphe stocke les voisins et les connexions.
11. Dijkstra trouve le meilleur chemin.
12. Le scheduler décide qui bouge à chaque tour.
13. Le simulateur rejoue et historise la simulation.
14. Le visualiseur affiche sans modifier la logique.
15. Le projet vise une solution valable et défendable, pas un optimum global théorique.

## 2. Les 10 fichiers à maîtriser absolument

1. [main.py](../../main.py)
2. [core/parser.py](../../core/parser.py)
3. [core/graph.py](../../core/graph.py)
4. [core/pathfinder.py](../../core/pathfinder.py)
5. [core/scheduler.py](../../core/scheduler.py)
6. [core/simulator.py](../../core/simulator.py)
7. [models/zone.py](../../models/zone.py)
8. [models/connection.py](../../models/connection.py)
9. [models/drone.py](../../models/drone.py)
10. [visualizer/plotly_visualizer.py](../../visualizer/plotly_visualizer.py)

## 3. Les 10 fonctions ou méthodes à retrouver vite

1. `main.main()`
2. `Parser.parse_file()`
3. `Parser.create_drones()`
4. `Graph.is_reachable()`
5. `Graph.get_neighbors()`
6. `Pathfinder.find_shortest_path()`
7. `Pathfinder.find_all_shortest_paths()`
8. `Scheduler.schedule_all_drones()`
9. `Scheduler.schedule_turn()`
10. `Simulator.run()`

## 4. Les 10 risques principaux à l'évaluation

1. Confondre `ZoneType` et `ZoneCategory`.
2. Oublier que les connexions sont bidirectionnelles.
3. Dire que le visualiseur recalcule la simulation.
4. Expliquer un BFS à la place de Dijkstra pour le chemin le moins coûteux.
5. Affirmer une optimalité globale que le scheduler n'a pas.
6. Oublier la règle spéciale des zones restricted.
7. Oublier la vérification de doublon `a-b` / `b-a`.
8. Mélanger parser et graphe dans les responsabilités.
9. Négliger les limites de capacité des connexions.
10. Oublier de parler des tests manquants, surtout visualisation et CLI.

## 5. Les 10 petites modifications de live coding les plus probables

1. Ajouter un champ de métadonnées dans le parser.
2. Changer une capacité par défaut dans `Zone`.
3. Ajouter un nouveau type de zone.
4. Modifier une couleur de zone dans le visualiseur.
5. Ajouter un test pour une connexion dupliquée.
6. Ajouter un test pour une zone blocked.
7. Changer le message d'erreur d'une validation.
8. Modifier le nombre de chemins candidats dans le scheduler.
9. Ajouter une information dans la sortie capacité.
10. Ajuster la limite de détection de deadlock.

## 6. Mini-quiz de 20 questions

1. Quel fichier est le point d'entrée ?
2. Quel objet résume le résultat du parser ?
3. Quelle différence entre `ZoneType` et `ZoneCategory` ?
4. Pourquoi `Connection` est-elle bidirectionnelle ?
5. Qu'est-ce qu'une zone restricted ?
6. Qu'est-ce qu'une zone blocked ?
7. Pourquoi utiliser un graphe ?
8. Quel algorithme est utilisé pour le chemin le moins coûteux ?
9. Pourquoi BFS ne suffit-il pas ici ?
10. Quel composant gère les conflits de capacité ?
11. Quel composant exécute la simulation ?
12. Quel composant affiche le résultat ?
13. Le visualiseur modifie-t-il la logique métier ?
14. Comment le parser détecte-t-il les doublons de connexion ?
15. Que signifie `IN_TRANSIT_RESTRICTED` ?
16. Que fait `Graph.is_reachable()` ?
17. Pourquoi les hubs start/end sont-ils spéciaux ?
18. Quelle est la complexité approximative de Dijkstra ?
19. Quels tests sont les plus présents ?
20. Quel est le plus grand risque d'oral ?

## 7. Réponses du quiz

1. `main.py`.
2. `InputData`.
3. `ZoneType` décrit le comportement, `ZoneCategory` décrit le rôle dans la carte.
4. Parce que le projet les modélise comme des liens non orientés.
5. Une zone qui demande deux tours pour être traversée.
6. Une zone interdite à l'entrée.
7. Pour naviguer proprement entre les zones.
8. Dijkstra.
9. Parce que les coûts ne sont pas tous égaux.
10. Le scheduler.
11. Le simulateur.
12. Le visualiseur Plotly.
13. Non.
14. Avec une clé normalisée triée alphabétiquement.
15. Le drone est en transit vers une zone restricted.
16. Il vérifie seulement qu'un chemin topologique existe.
17. Parce qu'ils sont traités comme des hubs spéciaux à capacité pratique illimitée.
18. Environ `O((V + E) log V)`.
19. Les tests du parser, du graphe, du pathfinder, du scheduler, du simulateur et du drone.
20. Oublier les limites du scheduler et prétendre à une optimalité globale.

## 8. Fiche de révision en une page

Fly-in lit une map texte, crée des `Zone` et des `Connection`, construit un `Graph`, cherche des chemins avec Dijkstra, puis planifie les drones tour par tour avec un scheduler glouton. Les zones ont des types : `normal` et `priority` coûtent 1, `restricted` coûte 2, `blocked` est interdit. Les drones ont un état, un chemin et peuvent être en transit restricted pendant deux tours.

Le plus important à l'oral est d'expliquer la chaîne complète : parser -> graphe -> pathfinder -> scheduler -> simulator -> visualiseur. Il faut aussi rappeler que le projet ne cherche pas un optimum mathématique global, mais une solution valide, lisible et défendable pour les maps fournies.

En cas de question, pense aux mots-clés suivants : capacité des zones, capacité des connexions, bidirectionnel, Dijkstra, chemin candidat, attente, deadlock, simulation tour par tour, visualisation non intrusive.
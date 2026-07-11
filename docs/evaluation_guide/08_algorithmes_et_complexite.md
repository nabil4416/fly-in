# Algorithmes et complexité

## A. Rôle général

Ce document résume les algorithmes réellement visibles dans le dépôt et donne leur complexité approximative. Il reste volontairement fidèle au code, sans ajouter d'algorithme qui ne serait pas confirmé.

## B. Algorithmes confirmés dans le code

### 1. BFS dans `Graph.is_reachable()`

Objectif : vérifier qu'un chemin topologique existe entre deux zones.

Pourquoi ce choix : c'est simple, lisible et suffisant pour valider la connectivité brute avant de lancer la simulation.

Structures utilisées : `deque`, `set` pour les zones visitées.

Complexité temporelle : environ `O(V + E)`.

Complexité mémoire : environ `O(V)`.

Limites : cette vérification ne tient pas compte des types de zones, seulement de l'existence d'un chemin dans le graphe.

### 2. Dijkstra dans `Pathfinder.find_shortest_path()`

Objectif : trouver un chemin de coût minimal entre une source et une destination.

Pourquoi ce choix : les zones ont des coûts différents, donc un simple BFS ne suffit pas.

Structures utilisées : dictionnaire de distances, dictionnaire de prédécesseurs, `heapq` pour la file de priorité, `set` pour les visites.

Complexité temporelle : environ `O((V + E) log V)`.

Complexité mémoire : environ `O(V)`.

Optimisations présentes :

- utilisation d'un tas binaire,
- arrêt immédiat quand la destination est extraite du tas,
- filtrage des zones blocked.

Heuristique : le code ajoute un score secondaire pour favoriser les chemins contenant des zones priority lorsque les coûts sont égaux.

### 3. Recherche multi-chemins dans `Pathfinder.find_all_shortest_paths()`

Objectif : produire plusieurs routes candidates pour répartir les drones.

Pourquoi ce choix : le scheduler a besoin de plusieurs options pour éviter les congestions.

Structures utilisées : tas de priorité, liste de chemins, ensemble des chemins déjà vus.

Complexité temporelle : supérieure à Dijkstra simple, car elle explore plusieurs chemins, mais reste bornée par `max_paths` et par l'interdiction de répétition dans un même chemin.

Complexité mémoire : dépend du nombre de chemins en file, donc approximativement `O(K * V)` dans le pire cas pour `K = max_paths`.

Limites : ce n'est pas un algorithme exhaustif de tous les plus courts chemins. C'est un générateur pratique de candidats.

### 4. Planification gloutonne dans `Scheduler`

Objectif : choisir les mouvements de chaque tour en respectant les contraintes.

Pourquoi ce choix : il est simple à défendre, évite les dépendances externes et permet une simulation lisible.

Structures utilisées : dictionnaires d'occupation, dictionnaires d'utilisation des connexions, listes ordonnées de drones.

Complexité temporelle : environ `O(T * D * C)` dans l'esprit, où `T` est le nombre de tours, `D` le nombre de drones et `C` le nombre de contrôles de capacité / connexions par tour. Dans la pratique, le code parcourt surtout les drones actifs et les connexions utiles.

Complexité mémoire : environ `O(D + V + E)` pour les structures de suivi du tour.

Optimisations présentes :

- traitement prioritaire des drones déjà en transit restricted,
- tri des drones réguliers par progression,
- arrêt si la simulation stagne trop longtemps,
- nombre limité de chemins candidats (`max_paths <= 8`).

### 5. Simulation tour par tour

Objectif : rejouer la décision du scheduler et produire une trace exploitable.

Pourquoi ce choix : cela rend la logique observable et permet de calculer des métriques.

Complexité temporelle : proportionnelle au nombre de tours multiplié par le coût de traitement d'un tour.

Complexité mémoire : stocke l'historique des `SchedulingResult`, donc dépend du nombre de tours.

## C. Comment les chemins sont comparés

Le pathfinder compare principalement :

1. le coût total,
2. puis un score secondaire lié aux zones priority.

Le scheduler, lui, compare les drones selon leur progression dans le chemin et l'identifiant du drone pour stabiliser les choix.

## D. Comment les drones sont répartis entre les chemins

Le scheduler récupère plusieurs chemins candidats, puis attribue les drones de manière cyclique selon leur identifiant. En pratique, le but est de répartir les drones sur quelques routes différentes pour réduire les blocages.

Ce n'est pas un solveur global de flot maximum. C'est une stratégie gloutonne et pragmatique.

## E. Caches et optimisations

- `Graph` garde un dictionnaire de connexions pour les accès rapides.
- `Pathfinder` conserve les distances, les prédécesseurs et les priorités pendant une recherche.
- `Scheduler` limite le nombre de chemins candidats à examiner.
- `Scheduler` détecte les situations de stagnation prolongée.

## F. Limites générales

- La stratégie n'optimise pas globalement tous les drones de manière théorique.
- Le nombre de chemins candidats reste limité.
- Les conflits très denses peuvent encore produire des attentes.
- Les zones priority sont favorisées, mais pas par une preuve d'optimalité globale.

## G. Ce que je dois dire à l'évaluation

Les deux algorithmes principaux sont BFS pour tester la connectivité et Dijkstra pour calculer les chemins. Ensuite, le scheduler applique une stratégie gloutonne pour répartir les drones et gérer les conflits de capacité tour par tour. Le choix est cohérent avec le projet : il reste lisible, défendable et suffisamment efficace sur les maps fournies, sans dépendre d'une bibliothèque externe.

## H. Questions probables des évaluateurs

1. Pourquoi BFS pour `is_reachable()` et pas Dijkstra ?
2. Quelle est la complexité de Dijkstra ici ?
3. Pourquoi la solution n'est-elle pas un flot maximum ?
4. Comment le score priority agit-il sur les chemins ?
5. Quelle optimisation t'aide le plus au scheduler ?

## I. Modification rapide possible

Une modification possible serait d'augmenter le nombre de chemins candidats autorisés dans `Scheduler.schedule_all_drones()`.

Le bon endroit est la valeur `max_paths=max(1, min(len(drones), 8))`. C'est une modification simple qui permet d'expliquer le compromis entre exploration, performance et stabilité.
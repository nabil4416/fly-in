# Fly-in Notes

## Project Goal
Move multiple drones from a start hub to an end hub through a graph while minimizing total simulation turns.

## Main Constraints
- Python 3.10+
- Fully object-oriented
- flake8 + mypy
- No graph libraries
- Explainable code for 42 evaluation

## Important Rules
- blocked zones are inaccessible
- restricted zones require 2 turns
- priority zones should be preferred
- default zone capacity = 1
- default connection capacity = 1
- start/end hubs allow multiple drones
- drones move simultaneously
- no collisions
- no capacity overflow

## Planned Architecture
core/
models/
visualizer/
utils/

## Main Components
- parser
- graph representation
- pathfinding
- scheduler
- simulator
- visualizer

## Pathfinding Ideas
- Dijkstra
- A*
- path caching
- heuristic optimization

## Important Evaluation Topics
- explain algorithm clearly
- complexity analysis
- edge cases
- parser robustness
- live coding modifications
- conflict resolution

## Edge Cases To Test
- blocked zones
- disconnected graph
- duplicate connections
- invalid metadata
- restricted zone congestion
- simultaneous arrivals
- capacity overflow
- deadlocks

## Notes
Keep code simple, typed, modular and easy to explain.
Avoid giant functions and hidden logic.
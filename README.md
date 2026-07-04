_This project has been created as part of the 42 curriculum by nkhotbi_

# Fly-in

## Description

Fly-in is a Python 3.10 drone routing simulation.

The program reads a map file, builds a custom bidirectional graph of zones,
computes valid paths from the start hub to the end hub, and schedules several
drones turn by turn while respecting:

- zone capacity (`max_drones`)
- connection capacity (`max_link_capacity`)
- blocked zones
- restricted zones that take 2 turns to enter
- unlimited capacity for the start and end hubs

The goal is to deliver all drones in as few turns as possible while keeping the
simulation valid and easy to explain.

## Instructions

Install dependencies:

```bash
make install
```

Run a simulation:

```bash
make run FILE=maps/easy/01_linear_path.txt
```

Run with Python directly:

```bash
python3 main.py maps/easy/01_linear_path.txt
```

Show capacity information per turn:

```bash
python3 main.py --capacity-info maps/easy/01_linear_path.txt
```

Run in the Python debugger:

```bash
make debug FILE=maps/easy/01_linear_path.txt
```

Run tests:

```bash
make test
```

Run style and type checks:

```bash
make lint
```

Remove Python caches:

```bash
make clean
```

Generate the graphical visualization:

```bash
make viz FILE=maps/easy/01_linear_path.txt
```

## Input Example

```text
nb_drones: 2
start_hub: start 0 0 [color=green]
hub: mid 1 0 [max_drones=1 color=blue]
end_hub: goal 2 0 [color=red]
connection: start-mid
connection: mid-goal
```

## Expected Output Example

```text
D1-mid
D1-goal D2-mid
D2-goal
```

Each line is one simulation turn. Stationary drones are omitted.

## Algorithm Explanation

The project uses only custom graph logic. No graph library such as `networkx`
or `graphlib` is used.

1. The parser validates the input file and creates `Zone` and `Connection`
   objects.
2. The graph stores neighbors in an adjacency list:
   `dict[str, list[str]]`.
3. The pathfinder uses Dijkstra with a heap priority queue.
   Movement cost depends on the destination zone:
   - `normal`: 1 turn
   - `priority`: 1 turn, preferred when costs are equal
   - `restricted`: 2 turns
   - `blocked`: inaccessible
4. The scheduler assigns drones to a small set of simple candidate paths.
   It then resolves each turn greedily:
   - drones already in restricted transit arrive first
   - drones farther along their path move before drones behind them
   - leaving a zone frees capacity in the same turn
   - connection capacity is checked before each move
5. The simulator stops as soon as all drones reach the end hub.

Complexity for one Dijkstra run is `O((V + E) log V)`, where `V` is the number
of zones and `E` the number of connections. Scheduling is roughly
`O(T * D * E)` for `T` turns and `D` drones, which is acceptable for the
provided 42 maps.

This is a simple and robust strategy. It is not an optimal max-flow solver, but
it avoids forbidden libraries and stays easy to defend in peer review.

## Visual Representation

The project provides a Plotly HTML visualizer in `scripts/visualize.py`.

It displays:

- zones at their map coordinates
- bidirectional connections
- zone categories and zone types with colors
- drone positions over simulation turns
- occupancy information in hover tooltips

Zone metadata colors are also preserved on the model and used where possible by
the visualization layer.

## Project Structure

```text
core/parser.py       input validation
core/graph.py        custom adjacency-list graph
core/pathfinder.py   Dijkstra pathfinding
core/scheduler.py    turn scheduling and conflict resolution
core/simulator.py    simulation lifecycle and output
models/              Zone, Drone, Connection and enums
visualizer/          Plotly visual feedback
tests/               pytest test suite
maps/                provided validation maps
```

## Resources

- Python `heapq` documentation:
  https://docs.python.org/3/library/heapq.html
- Python `dataclasses` documentation:
  https://docs.python.org/3/library/dataclasses.html
- Dijkstra algorithm overview:
  https://en.wikipedia.org/wiki/Dijkstra%27s_algorithm
- Pytest documentation:
  https://docs.pytest.org/
- Mypy documentation:
  https://mypy.readthedocs.io/
- Plotly documentation:
  https://plotly.com/python/

## AI Usage

AI was used as a review and debugging assistant for:

- checking the project against the Fly-in subject and Intra scale
- identifying weak edge cases in parser, scheduler, and simulator output
- proposing focused tests for invalid input and capacity conflicts
- helping rewrite this README in simple English

All code was reviewed, tested locally, and kept small enough to explain during
peer evaluation.

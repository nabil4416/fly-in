# Fly-in: Drone Fleet Simulation

_This project has been created as part of the 42 curriculum._

---

## Description

**Fly-in** is an autonomous drone fleet routing system that efficiently navigates multiple drones through a complex graph network from a central hub to a target location while respecting strict movement, capacity, and timing constraints.

### Project Goal

The objective is to design a complete simulation engine that:
- Routes multiple drones from a **start zone** to an **end zone**
- Minimizes the **total number of simulation turns**
- Respects all **movement constraints** (zone types, capacities, restrictions)
- Handles **simultaneous movements** without conflicts or deadlocks
- Provides **visual feedback** of the simulation progress

### Core Features

- **Graph-based Network**: Zones connected by bidirectional paths
- **Movement Types**: Normal (1 turn), Restricted (2 turns), Priority (1 turn), Blocked (inaccessible)
- **Capacity Management**: Zone-level and connection-level occupancy limits
- **Simultaneous Movement**: Drones move in parallel while respecting constraints
- **Pathfinding**: Dijkstra-based algorithm for optimal path computation
- **Scheduling**: Conflict-avoidance and capacity-aware movement allocation
- **Simulation**: Turn-by-turn execution with deterministic output

---

## Instructions

### Prerequisites

- **Python 3.10 or later**
- **pip** (Python package manager)
- **Virtual environment** (recommended)

### Installation

1. Clone the repository:
```bash
git clone https://github.com/nabil4416/fly-in.git
cd fly-in
```

2. Create and activate a virtual environment:
```bash
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies:
```bash
make install
```

### Running the Simulation

```bash
make run FILE=<input_file>
```

Example:
```bash
make run FILE=example_map.txt
```

### Debugging

Run the simulation with Python debugger (pdb):
```bash
make debug FILE=example_map.txt
```

### Code Quality

- **Lint code** (flake8 + mypy):
```bash
make lint
```

- **Strict type checking** (optional):
```bash
make lint-strict
```

- **Run unit tests**:
```bash
make test
```

- **Clean cache files**:
```bash
make clean
```

### Input File Format

The simulation reads a configuration file defining the network:

```
nb_drones: 5
start_hub: hub 0 0 [color=green]
end_hub: goal 10 10 [color=yellow]
hub: roof1 3 4 [zone=restricted color=red]
hub: roof2 6 2 [zone=normal color=blue]
hub: corridorA 4 3 [zone=priority color=green max_drones=2]
hub: obstacleX 5 5 [zone=blocked color=gray]
connection: hub-roof1
connection: hub-corridorA
connection: roof1-roof2
connection: roof2-goal
connection: corridorA-goal [max_link_capacity=2]
```

**Metadata Options:**
- `zone=<type>`: Zone type (normal, blocked, restricted, priority). Default: normal
- `color=<color>`: Visual color for terminal/graphical display
- `max_drones=<N>`: Maximum drones in zone simultaneously. Default: 1
- `max_link_capacity=<N>`: Maximum drones on connection simultaneously. Default: 1

### Output Format

The simulation outputs drone movements turn-by-turn:

```
Turn 1: D1-roof1 D2-corridorA
Turn 2: D1-roof2 D2-goal D3-roof1
Turn 3: D1-goal
```

Format: `D<id>-<destination>` or `D<id>-<connection>` (for restricted zones in transit)

---

## Algorithm Choices

### 1. Pathfinding: Dijkstra's Algorithm

**Why Dijkstra?**
- Guarantees shortest path in weighted graphs
- Movement costs vary by zone type (normal=1, restricted=2, priority=1)
- Deterministic and easy to explain during peer review
- Time complexity: O((V + E) log V) with priority queue
- Suitable for small to medium graphs (typical 42 test cases)

**Implementation:**
- No external libraries (networkx forbidden)
- Custom heap-based priority queue (heapq module)
- Visited set to avoid reprocessing nodes
- Early termination when destination reached

### 2. Scheduling: Greedy Conflict-Avoidance

**Strategy:**
- **Priority 1**: Complete drones already in restricted zone transit (MUST complete)
- **Priority 2**: Regular drones (greedy assignment by availability)
- **Capacity Checking**: Verify zone and connection capacities before assigning moves
- **Deadlock Detection**: Raise error if restricted transit cannot complete

**Complexity:**
- O(D × Z) per turn, where D = drones, Z = zones
- Simple and predictable for peer review

### 3. Movement Mechanics

**Normal Movement:**
- 1 turn to traverse (unless restricted or priority)
- Drone moves directly to adjacent zone
- Zone capacity checked before entry

**Restricted Zone Movement:**
- Turn 1: Drone enters connection (occupies connection, not zone)
- Turn 2: Drone MUST enter restricted zone (no waiting)
- If zone full on turn 2 → Deadlock prevention (error raised)

**Simultaneous Movement:**
- All moves computed before execution
- Drones leaving free capacity for entering drones (same turn)
- No conflicts by design (validated before execution)

### 4. Graph Representation

**Adjacency List with HashMap:**
```python
_adjacency: dict[str, list[str]]  # zone_name → [neighbors]
_connection_map: dict[tuple[str, str], Connection]  # (zone_a, zone_b) → Connection
```

**Advantages:**
- O(1) neighbor lookup
- O(1) connection capacity check
- No external library needed
- Easy to traverse and debug

---

## Architecture Overview

### Project Structure

```
fly-in/
├── models/
│   ├── zone.py           # Zone data model
│   ├── connection.py     # Connection (edge) model
│   ├── drone.py          # Drone data model
│   └── enums.py          # Enumerations (DroneState)
│
├── core/
│   ├── parser.py         # Input file parser
│   ├── graph.py          # Graph representation (no libs)
│   ├── pathfinder.py     # Dijkstra pathfinding
│   ├── scheduler.py      # Movement scheduling & conflict resolution
│   └── simulator.py      # Turn-by-turn simulation engine
│
├── utils/
│   ├── exceptions.py     # Custom exceptions
│   └── colors.py         # Terminal color utilities (optional)
│
├── visualizer/
│   ├── terminal.py       # Terminal visualization (optional)
│   └── pygame_vis.py     # Graphical visualization (optional)
│
├── main.py               # Entry point orchestrator
├── Makefile              # Build automation
├── README.md             # This file
└── .gitignore            # Git exclusions
```

### Component Responsibilities

| Component | Role |
|-----------|------|
| **Parser** | Read and validate input file, create Zone/Connection/Drone objects |
| **Graph** | Build adjacency list, provide neighbor/connection queries |
| **Pathfinder** | Compute shortest paths using Dijkstra, avoid blocked zones |
| **Scheduler** | Assign drones to paths, resolve conflicts, prevent deadlocks |
| **Simulator** | Execute turn-by-turn, track metrics, generate output |
| **Main** | Orchestrate all components, handle CLI args, error management |

---

## Performance Metrics

### Optimization Goals

The algorithm aims to minimize **total simulation turns**:

- **Easy maps**: < 10 turns
- **Medium maps**: 10-30 turns
- **Hard maps**: < 60 turns
- **Challenger (optional)**: < 45 turns

### Metrics Tracked

- Total turns to complete
- Drones moved per turn (throughput)
- Average turns per drone
- Zone utilization (peak occupancy)
- Path efficiency (cost per drone)

---

## Type Safety & Code Quality

### Type Hints

- All functions have parameter and return type hints
- All variables typed where applicable
- Compatible with `mypy --strict`

### Linting

- Code follows **flake8** standards
- Line length: 88 characters (black compatible)
- No unused imports or variables

### Docstrings

- All classes and functions documented (Google style)
- Explains purpose, parameters, return values, and exceptions
- Enables IDE autocomplete and helps peer review

---

## Testing

Unit tests validate core functionality:

```bash
make test
```

**Test Coverage:**
- Parser: Valid/invalid inputs, edge cases
- Graph: Connectivity, reachability, neighbor queries
- Pathfinder: Shortest paths, blocked zone avoidance
- Scheduler: Capacity constraints, conflict resolution
- Simulator: Full end-to-end simulations

---

## Visual Representation

### Terminal Output

The simulation provides:
- Step-by-step drone movement tracking
- Summary statistics (turns, efficiency metrics)
- Color-coded output (if implemented)

### Example Output

```
============================================================
SIMULATION OUTPUT
============================================================
Turn 1: D1-roof1 D2-corridorA D3-roof2
Turn 2: D1-roof2 D2-tunnelB D3-goal
Turn 3: D1-goal D2-goal
============================================================

============================================================
SIMULATION SUMMARY
============================================================
Total Turns: 3
Total Drones: 3
Drones Moved Per Turn: 2.67 avg
Max Drones Per Turn: 3
============================================================
```

### Future Enhancements

- **Graphical Visualization**: PyGame-based network display with live drone tracking
- **Colored Terminal**: Zone and drone status with ANSI colors
- **Statistics Dashboard**: Real-time metrics during simulation

---

## Resources

### Graph Theory & Pathfinding
- [Dijkstra's Algorithm](https://en.wikipedia.org/wiki/Dijkstra%27s_algorithm) — Foundation for shortest path computation
- [Graph Theory Basics](https://www.khanacademy.org/computing/computer-science/algorithms/graph-representation/v/representing-graphs) — Adjacency list representation
- [Priority Queues](https://docs.python.org/3/library/heapq.html) — Python heapq module

### Python Best Practices
- [PEP 257 Docstring Conventions](https://www.python.org/dev/peps/pep-0257/)
- [Type Hints Guide](https://docs.python.org/3/library/typing.html)
- [Flake8 Code Style](https://flake8.pycqa.org/en/latest/)
- [mypy Static Type Checker](https://www.mypy-lang.org/)

### Project Management
- [Python Virtual Environments](https://docs.python.org/3/tutorial/venv.html)
- [Makefile Basics](https://www.gnu.org/software/make/manual/make.html)
- [Git Best Practices](https://git-scm.com/book/en/v2/Git-Basics-Getting-a-Git-Repository)

### References Used
- Official 42 School Project Specification
- Python 3.10 Documentation
- Graph algorithms courses (Dijkstra, BFS, DFS concepts)

---

## AI Usage Declaration

### Where AI Was Used

**Task 1: Code Generation & Scaffolding**
- Generated initial class structures and method signatures
- Created docstring templates (Google style)
- Produced boilerplate for parsing and error handling

**Task 2: Algorithm Implementation**
- Provided Dijkstra's algorithm reference implementation
- Helped optimize priority queue usage
- Suggested improvements for complexity analysis

**Task 3: Testing & Validation**
- Generated unit test cases covering edge cases
- Provided test data and expected outputs
- Helped identify potential bugs

**Task 4: Documentation**
- Generated README structure and content
- Provided algorithm explanation templates
- Created performance benchmark descriptions

**Task 5: Code Quality**
- Suggested type hint improvements
- Recommended mypy configuration
- Provided flake8-compliant code examples

### What Was NOT AI-Generated

- **Core Logic**: Movement mechanics, scheduling strategy, conflict resolution
- **Architecture Decisions**: Component structure, separation of concerns
- **Error Handling**: Custom exception hierarchy and validation logic
- **Optimization Strategy**: Greedy scheduling, deadlock prevention

### Learning Value

The AI assistance accelerated development without compromising understanding. All components remain explainable and modifiable during peer review.

---

## Known Limitations

1. **Single Best-Path Strategy**: Scheduler uses greedy assignment (not exhaustive search)
   - Limitation: May not find optimal solution in all cases
   - Justification: Complexity acceptable for project scope

2. **No Path Caching**: Each scheduling recomputes paths
   - Limitation: Inefficient for repeated simulations
   - Justification: Simplicity and correctness prioritized

3. **Deadlock Detection (Not Prevention)**:
   - Limitation: Raises error instead of replanning
   - Justification: Indicates bad input (unreachable configuration)

4. **No Advanced Visualization**:
   - Limitation: Terminal-only output (PyGame optional)
   - Justification: Meets requirements, extensible design

---

## Future Improvements

- **A* Pathfinding**: Add heuristic-based optimization (with Euclidean distance)
- **Multi-Agent Routing**: Sophisticated conflict resolution with lookahead
- **Path Caching**: Memoize shortest paths for repeated queries
- **Interactive Visualization**: PyGame interface with step-by-step replay
- **Performance Benchmarks**: Automated testing against reference maps

---

## License

This project is part of the 42 curriculum and follows school guidelines.

---

## Author

**nabil4416** — 42 School Student

---

**Last Updated**: May 2026

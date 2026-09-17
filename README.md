*This project has been created as part of the 42 curriculum by okhouya.*

# Fly-in — Drone Fleet Simulation

## Description

**Fly-in** is a turn-based drone fleet routing and simulation engine developed in Python 3.10+. The objective is to navigate a fleet of autonomous drones from a designated starting zone (`start_hub`) to a target destination (`end_hub`) across a network of interconnected zones in the minimum possible simulation turns.

The simulation models a dynamic graph under strict physical and topological constraints:
- **Zone Types & Movement Costs**:
  - `normal`: Standard zone requiring **1 turn** traversal cost.
  - `priority`: Preferred zone requiring **1 turn** traversal cost, prioritized during pathfinding.
  - `restricted`: High-risk or complex zone requiring **2 turns** to enter (1 turn occupying the connecting link in transit, 1 turn arriving at the destination).
  - `blocked`: Impassable zone completely excluded from all valid flight paths.
- **Zone Occupancy (`max_drones`)**: Maximum number of drones that may simultaneously occupy a zone (default: 1). Start and end hubs have unlimited capacity.
- **Connection Capacity (`max_link_capacity`)**: Maximum number of drones that may traverse a bidirectional connection during the same turn (default: 1).
- **Simultaneous Movement**: Drones moving out of a zone free up capacity for other drones entering that zone during the same turn.
- **Conflict Resolution**: Active drones closest to the target are prioritized when competing for limited capacity.

---

## Instructions

### Requirements

- Python 3.10 or later
- Standard library dependencies (`heapq`, `dataclasses`, `sys`, `typing`)
- Development packages: `flake8`, `mypy`

### Installation

Install developer dependencies using the Makefile:

```bash
make install
```

Or manually via pip:

```bash
pip install -r requirements.txt
```

### Execution

Run the simulation on any valid map file:

```bash
python3 main.py maps/easy/01_linear_path.txt
```

Or using the Makefile shortcut:

```bash
make run MAP=maps/easy/01_linear_path.txt
```

### Debugging

Launch the interactive Python debugger (`pdb`) through the Makefile:

```bash
make debug MAP=maps/easy/01_linear_path.txt
```

### Code Style & Type Safety

Check PEP 8 adherence and static typing:

```bash
make lint
make lint-strict
```

### Cleanup

Remove compiled bytecode and cache directories:

```bash
make clean
```

---

## Algorithm Explanation

### 1. Custom Graph Architecture

In strict compliance with project constraints, Fly-in avoids external graph libraries (such as `networkx` or `graphlib`). The graph topology is custom-implemented using an adjacency list representation:
- **`Zone`**: Represents a node with integer coordinates, zone type (`normal`, `restricted`, `priority`, `blocked`), visual color, and maximum drone capacity.
- **`Connection`**: Represents an undirected edge with a unique canonical tuple key and link capacity constraint.
- **`Graph`**: Maintains zone lookups, neighbor mappings, and bidirectional edge definitions.

### 2. Pathfinding: Dijkstra's Algorithm with Edge Penalization

Rather than unweighted BFS, Fly-in uses **Dijkstra's Algorithm** backed by a min-heap priority queue (`heapq`):
- **Zone Weights**:
  - `priority`: Cost 5 (incentivizes the pathfinder to utilize priority corridors).
  - `normal`: Cost 10 (baseline cost).
  - `restricted`: Cost 20 (penalizes multi-turn zones unless necessary).
  - `blocked`: Skipped entirely.
- **Dynamic Edge Penalization**:
  To distribute multiple drones across diverse parallel paths without causing severe bottlenecks, the pathfinder dynamically penalizes previously selected connections:
  $$\text{Effective Cost} = \text{Base Cost} + (\text{Connection Usage Count} \times 100)$$
  Each time a connection is included in a path, its penalty increases, nudging subsequent drone paths toward alternative available routes.
- **Detour Filtering**:
  To prevent excessively long detour paths that increase overall turns, discovered paths are filtered to retain only those within a competitive threshold of the shortest path.
- **Time Complexity**:
  For $K$ drones on a graph with $V$ zones and $E$ connections, the algorithm runs in $O(K \cdot (V + E) \log V)$ time with $O(V + E)$ spatial complexity.

### 3. Simulation Engine: Two-Phase Turn Execution

Each discrete simulation turn executes in two distinct phases:
1. **Phase 1 — In-Flight Arrivals**:
   Drones currently in transit to `restricted` zones (floating mid-air on the connection) complete their movement and land in their destination zone.
2. **Phase 2 — Active Drone Movements**:
   - Drones not yet delivered are sorted by **proximity to the goal** ($\text{path length} - \text{current index}$), ensuring drones furthest along move first to prevent gridlocks.
   - Each movement validates that connection usage does not exceed `max_link_capacity` and destination occupancy does not exceed `max_drones`.
   - Normal/priority movements update the drone position immediately (1 turn).
   - Restricted movements mark the drone as in-flight (`D<ID>-<from>-<to>`) for arrival on the subsequent turn.
   - If capacity is exhausted, the drone waits in place without generating output.

---

## Visual Representation

Fly-in incorporates built-in terminal visual feedback:
- **ANSI Color Coding**: Zone movements are dynamically rendered in the terminal using ANSI escape codes corresponding to the `color` metadata specified in the map file (supporting `green`, `blue`, `red`, `yellow`, `cyan`, `magenta`, `orange`, `purple`, and more).
- **Turn-by-Turn Tracking**: Drones traveling into colored zones immediately reflect that zone's color, enabling reviewers to visually differentiate drone flows through fast corridors, bottlenecks, and restricted zones at a glance.

---

## Example Input and Expected Output

### Input Map (`maps/easy/01_linear_path.txt`)

```text
# Easy Level 1: Simple linear path
nb_drones: 2

start_hub: start 0 0 [color=green]
hub: waypoint1 1 0 [color=blue]
hub: waypoint2 2 0 [color=blue]
end_hub: goal 3 0 [color=red]

connection: start-waypoint1
connection: waypoint1-waypoint2
connection: waypoint2-goal
```

### Expected Output

```text
D1-waypoint1
D1-waypoint2 D2-waypoint1
D1-goal D2-waypoint2
D2-goal
number of turns : 4
```

- Each line represents one discrete turn.
- Active movements follow `D<ID>-<destination>` (or `D<ID>-<connection>` for restricted transit).
- Stationary drones are omitted from output lines.
- The simulation completes as soon as all drones arrive at `goal`.

---

## Performance Benchmarks

All benchmark maps provided in the curriculum have been verified against their official reference targets:

| Map Category | Map File | Drones | Target Turns | Actual Turns | Result |
|--------------|----------|--------|--------------|--------------|--------|
| **Easy** | `01_linear_path.txt` | 2 | $\le 6$ | **4** | **PASS** |
| **Easy** | `02_simple_fork.txt` | 4 | $\le 8$ | **4** | **PASS** |
| **Easy** | `03_basic_capacity.txt` | 4 | $\le 6$ | **4** | **PASS** |
| **Medium** | `01_dead_end_trap.txt` | 5 | $\le 12$ | **8** | **PASS** |
| **Medium** | `02_circular_loop.txt` | 6 | $\le 15$ | **15** | **PASS** |
| **Medium** | `03_priority_puzzle.txt` | 5 | $\le 12$ | **7** | **PASS** |
| **Hard** | `01_maze_nightmare.txt` | 8 | $\le 30$ | **13** | **PASS** |
| **Hard** | `02_capacity_hell.txt` | 12 | $\le 35$ | **16** | **PASS** |
| **Hard** | `03_ultimate_challenge.txt` | 15 | $\le 45$ | **29** | **PASS** |
| **Challenger** | `01_the_impossible_dream.txt` | 25 | $\le 45$ | **45** | **PASS (BONUS)** |

---

## Project Structure

```
.
├── Makefile                # Build and test automation
├── README.md               # Project documentation
├── requirements.txt        # Python linters and type checker
├── display.py              # Visual representation and ANSI terminal colorization
├── graph.py                # Graph data structure (adjacency list, connections)
├── main.py                 # Application entry point and orchestrator
├── models.py               # Data classes (Zone, Connection, Drone) and exceptions
├── parser.py               # Map file parsing and comprehensive validation
├── pathfinder.py           # Dijkstra pathfinding with edge penalization
├── scheduler.py            # Path assignment scheduler
├── simulation.py           # Turn-by-turn simulation execution engine
└── maps/                   # Benchmark test maps
    ├── easy/
    ├── medium/
    ├── hard/
    └── challenger/
```

---

## Resources

### References
- **Dijkstra's Shortest Path Algorithm**: Cormen, Leiserson, Rivest, Stein (CLRS), *Introduction to Algorithms*, Chapter 24 (Single-Source Shortest Paths).
- **Network Flow & Path Congestion**: Multi-commodity flow and edge congestion routing techniques.
- **Python Documentation**: `heapq` priority queues, `dataclasses`, and PEP 257 / PEP 484 standards.

### AI Usage
As required by Chapter VIII of the project subject:
- **Conceptual Clarification**: AI was consulted to clarify edge cases regarding zone movement rules, capacity exhaustion, and restricted zone turn transitions.
- **Quality & Standard Compliance**: AI assisted in auditing PEP 8 formatting rules (`flake8`) and strict type annotations (`mypy --strict`).
- **Edge Case Test Formulation**: AI was used to draft test scenarios for parsing validation (e.g. metadata syntax, dash checks, coordinate collisions).

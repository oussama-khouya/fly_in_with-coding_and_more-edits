*This project has been created as part of the 42 curriculum by okhouya.*

# Fly-in — Drone Simulation

## Description

**Fly-in** is a turn-based drone fleet simulation engine built in Python. The project models a spatial graph of connected zones and navigates a fleet of drones from a specified `start_hub` to an `end_hub` in the fewest possible turns.

The simulation enforces strict physical and capacity constraints, including:
- **Zone Occupancy (`max_drones`)**: Maximum concurrent drones inside a zone (unlimited for start/end hubs).
- **Connection Capacity (`max_link_capacity`)**: Maximum drones crossing a link in a single turn.
- **Zone Types**: Different traversal speeds and costs (`normal`, `priority`, `restricted`, `blocked`).
- **Conflict Resolution**: Sorting movement attempts so drones closest to the goal move first.

---

## Architecture & Pipeline

The project follows a clean 5-component modular design:

```
Map File (.txt) ──► [ Parser ] ──► Graph
                                    │
                                    ▼
                             [ Pathfinder ] (Dijkstra + Edge Penalization)
                                    │
                                    ▼
                              [ Scheduler ] (Round-Robin Assignment)
                                    │
                                    ▼
                             [ Simulation ] (2-Phase Turn Engine)
                                    │
                                    ▼
                              [ Display ] (Colored ANSI Output)
```

1. **Parser (`src/parser.py`)**: Reads map definition files, validates syntax/metadata, checks for errors (duplicate coordinates, invalid zone types, missing hubs), and constructs the `Graph`.
2. **Pathfinder (`src/pathfinder.py`)**: Computes optimal paths for each drone using **Dijkstra's Algorithm** with edge penalization.
3. **Scheduler (`src/scheduler.py`)**: Assigns precomputed paths to drones using round-robin distribution.
4. **Simulation (`src/simulation.py`)**: Executes turn-by-turn simulation enforcing zone/connection capacities and 2-turn restricted movements.
5. **Display (`src/display.py`)**: Formats machine-readable output and renders human-readable colored terminal output.

---

## Algorithm Explanation

### Pathfinding: Dijkstra's Algorithm (with Min-Heap & Edge Penalization)

Instead of unweighted algorithms like BFS, **Fly-in uses Dijkstra's Algorithm** using Python's `heapq` priority queue ($O((V + E) \log V)$ complexity). Dijkstra is required because different zone types have different traversal costs:

| Zone Type | Move Cost | Description |
|-----------|-----------|-------------|
| `priority` | **5** | Preferred routes — pathfinder prioritizes these zones |
| `normal` | **10** | Standard zone |
| `restricted` | **20** | High-cost zone — takes 2 turns to enter |
| `blocked` | **∞** | Impassable — pathfinder completely avoids these zones |

#### Multi-Drone Path Diversification (Edge Penalization)

To prevent all drones from crowding into a single path and causing bottlenecks, Pathfinder runs Dijkstra once for each drone and penalizes previously used connections:

$$\text{Weight}(u, v) = \text{Base Cost} + (\text{Edge Usage Count} \times 100)$$

Every time a path uses connection $(u, v)$, its cost increases by $+100$ for subsequent searches. This forces Dijkstra to discover alternative parallel routes across the network.

---

### Simulation Engine: 2-Phase Turn Execution

Each turn in the simulation executes in two distinct phases:

- **Phase 1 (Restricted Transit Completion)**: Drones floating mid-air inside 2-turn restricted connections land at their destination zone without capacity checks (they are already in motion).
- **Phase 2 (Active Drone Movement)**:
  1. Active drones are sorted by **closest to goal first** ($\text{path length} - \text{path index}$).
  2. For each drone:
     - Check connection capacity (`max_link_capacity`).
     - Check destination zone capacity (`max_drones`).
     - If destination is `restricted`, enter connection (mid-air state for 1 turn).
     - If `normal` or `priority`, arrive immediately (1 turn).
     - If destination or link is full, the drone **waits** in place.

---

## Project Structure

```
flyin/
├── main.py              # Application entry point
├── src/
│   ├── models.py        # Data classes (Zone, Connection, Drone) & custom exceptions
│   ├── graph.py         # Graph structure & adjacency management
│   ├── parser.py        # Map file parsing & validation
│   ├── pathfinder.py    # Weighted Dijkstra pathfinding engine
│   ├── scheduler.py     # Round-robin path assigner
│   ├── simulation.py    # Turn-by-turn simulation execution engine
│   └── display.py       # Terminal ANSI color visualizer
├── tests/
│   └── test_all.py      # Unit test suite (73 tests)
├── maps/                # Map benchmark test cases (easy, medium, hard)
├── Makefile             # Automation targets (run, test, lint, clean)
├── README.md            # Project documentation
└── requirements.txt     # Developer tools (flake8, mypy)
```

---

## Usage Instructions

### Requirements

- Python 3.10+

### Installation

```bash
make install
```

### Running the Simulation

```bash
python3 main.py maps/easy/01_linear_path.txt
```

Or using Makefile:

```bash
make run MAP=maps/easy/01_linear_path.txt
```

### Capacity Info Mode

To view live zone occupancy after each turn:

```bash
python3 main.py maps/easy/01_linear_path.txt --capacity-info
```

### Testing

Run the full automated test suite (73 unit & benchmark tests):

```bash
make test
```

### Linting & Type Checking

Verify clean PEP 8 code style and strict typing:

```bash
make lint
```

---

## Output Example

For a linear map (`01_linear_path.txt`) with 3 drones:

```text
D1-A
D1-B D2-A
D1-goal D2-B D3-A
D2-goal D3-B
D3-goal
```

- Each line represents one turn.
- `D1-A` means Drone 1 moved to zone A.
- Turns stop when all drones reach the goal.

---

## AI Usage

AI was used as a pair-programming assistant for:
- Understanding project concepts and map constraint edge cases.
- Debugging simulation state transitions and linting cleanups.

All code logic was thoroughly reviewed, verified, and can be fully explained during evaluation.
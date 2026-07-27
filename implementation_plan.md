# Fly-in — Complete Architecture Design

## Requirement Extraction

### Sources Analyzed
- [flyin.pdf](file:///Users/okhouya/Documents/flyin/flyin.pdf) — Official subject (23 pages)
- [Intra Projects Fly-in Edit.pdf](file:///Users/okhouya/Documents/flyin/Intra%20Projects%20Fly-in%20Edit.pdf) — Official correction sheet (7 pages)
- All 11 provided map files

---

### Mandatory Requirements (MUST pass)

| # | Requirement | Source |
|---|-------------|--------|
| M1 | Python 3.10+ | Subject III.1 |
| M2 | flake8 compliance | Subject III.1 |
| M3 | mypy type checking (all functions typed) | Subject III.1 |
| M4 | Completely object-oriented | Subject V |
| M5 | No graph libraries (networkx, graphlib…) | Subject V |
| M6 | Graceful exception handling (no crashes) | Subject III.1 |
| M7 | Context managers for resources | Subject III.1 |
| M8 | Docstrings (PEP 257) | Subject III.1 |
| M9 | Makefile with: install, run, debug, clean, lint | Subject III.2 |
| M10 | Parser: nb_drones, start_hub, end_hub, hub, connection | Subject VI |
| M11 | Parser: comments (#) ignored | Subject VI |
| M12 | Parser: metadata [zone=, color=, max_drones=, max_link_capacity=] | Subject VI |
| M13 | Parser: error messages with line and cause | Subject VII.4 |
| M14 | Zone types: normal (1 turn), restricted (2 turns), priority (1 turn preferred), blocked (inaccessible) | Subject VII.3 |
| M15 | Zone occupancy: default max_drones=1, start/end unlimited | Subject VII.2 |
| M16 | Connection capacity: default max_link_capacity=1 | Subject VI |
| M17 | Simultaneous drone movement | Subject VII.1 |
| M18 | Restricted zones: 2-turn movement, drone MUST arrive next turn, cannot wait on connection | Subject VII.3 |
| M19 | Output format: `D<ID>-<zone>` or `D<ID>-<connection>` per line | Subject VII.5 |
| M20 | Stationary drones omitted from output | Subject VII.5 |
| M21 | Simulation ends when all drones reach end zone | Subject VII.5 |
| M22 | Visual representation (colored terminal output OR graphical) | Subject VII.1, Correction |
| M23 | README.md with: Description, Instructions, Algorithm explanation, Visual docs, Example I/O | Correction sheet |
| M24 | Pathfinding: finds valid paths from start to end | Correction |
| M25 | Conflict resolution: capacity-aware | Correction |
| M26 | Easy maps < 10 turns | Subject VII.7 / Correction |
| M27 | Medium maps 10–30 turns | Subject VII.7 / Correction |
| M28 | Hard maps < 60 turns | Subject VII.7 / Correction |

### Correction Sheet Evaluation Sections (Yes/No checkboxes)

| Section | What they check |
|---------|----------------|
| README.md | Description, Instructions, Algorithm explanation, Visual docs, Example I/O |
| OOP | Completely object-oriented, proper class design |
| Type safe | Passes `mypy .` — type hints everywhere |
| Graph implementation | Custom-built, no forbidden libraries, can explain |
| Parser: Input files | nb_drones, zone defs, connections, metadata, comments (4/5 pass) |
| Parser: Error handling | Malformed files, invalid types, missing start/end, invalid capacity, duplicates (4/5 pass) |
| Zone occupancy | max_drones respected, start/end unlimited |
| Movement costs | normal=1, restricted=2, priority=1, blocked=inaccessible |
| Connection capacity | max_link_capacity enforced |
| Visualization | Colored terminal output, zone colors used, shows drone positions |
| Basic functionality | Single drone linear, multi-drone paths, example maps, output format, stationary omitted (4/5) |
| Simulation ends | Stops when all drones arrive |
| Valid path | Finds paths for simple, multi-path, bottleneck, different zone types |
| Conflict resolution | Drones compete for capacity, simultaneous handling, restricted zone movement |
| Performance | Higher drone counts, complex maps, minimizes turns |
| Algorithm explanation | Explain complexity, design decisions, trade-offs |
| Easy benchmarks | < 10 turns average |
| Medium benchmarks | 10–30 turns average |
| Hard benchmarks | < 60 turns average |
| Edge cases | Single drone, bottlenecks, disconnected graphs, invalid connections, extreme capacity (4/5) |
| Error handling | Malformed files, missing start/end, invalid capacity, disconnected, invalid types |
| Code quality | Structured, OOP, comments, consistent style |
| **Live coding** | Add `--capacity-info` flag in ≤ 10 minutes |

### Bonus (IGNORE completely)

| Bonus | Description |
|-------|-------------|
| B1 | "Perfectly" meet ALL reference targets (exact turns) |
| B2 | Solve Challenger map < 45 turns |

### Hidden Expectations (derived from correction sheet)

1. **Live coding task**: Add `--capacity-info` flag. Code must be organized so output and parsing are easy to locate and modify.
2. **Algorithm explanation during defense**: Must understand and explain your own algorithm.
3. **Evaluation maps may differ**: Must work with maps you've never seen.
4. **4/5 threshold**: Many sections require only 4 out of 5 tests to pass.

---

## 1. Overall Architecture

### Plain English

The program reads a map file, builds an in-memory graph, finds paths for all drones using BFS-based pathfinding, then simulates turn-by-turn movement respecting all capacity rules, and outputs each turn's movements.

### Data Flow

```
Input File (.txt)
      │
      ▼
   Parser ──── reads lines, builds Zone and Connection objects
      │
      ▼
    Graph ──── stores zones (dict) and adjacency (dict of lists)
      │
      ▼
  Pathfinder ── BFS from start to end, finds multiple paths
      │
      ▼
  Scheduler ─── assigns drones to paths, plans turn-by-turn movement
      │
      ▼
  Simulation ── executes turns, enforces capacity, tracks state
      │
      ▼
   Output ───── prints D<ID>-<zone> lines + colored visualization
```

### Why This Is The Smallest Architecture

- **6 logical modules** map directly to 6 stages of the pipeline.
- No abstract base classes, no interfaces, no factories.
- Each module does one thing. No module knows about modules it shouldn't.
- The Graph is the only shared data structure.

---

## 2. Folder Structure

```
flyin/
├── Makefile
├── README.md
├── requirements.txt
├── main.py              ← Entry point
├── src/
│   ├── __init__.py
│   ├── models.py        ← Zone, Connection, Drone classes
│   ├── parser.py        ← File parsing
│   ├── graph.py         ← Graph representation
│   ├── pathfinder.py    ← BFS pathfinding
│   ├── scheduler.py     ← Drone-to-path assignment + turn planning
│   ├── simulation.py    ← Turn-by-turn execution
│   └── display.py       ← Colored terminal output
├── maps/                ← Provided map files
│   ├── easy/
│   ├── medium/
│   ├── hard/
│   └── challenger/
└── tests/               ← Test files (not graded but needed for dev)
    ├── __init__.py
    ├── test_parser.py
    ├── test_graph.py
    ├── test_pathfinder.py
    ├── test_simulation.py
    └── test_maps/
        └── (custom test maps)
```

### Why each folder exists

| Folder | Reason |
|--------|--------|
| Root | Makefile, README.md, main.py — required by subject |
| `src/` | All source modules — one flat folder, no nesting |
| `maps/` | Provided test maps — used by `make run` |
| `tests/` | Testing — not graded but correction checks behavior |

### Why no extra folders

- No `utils/`, `helpers/`, `services/`, `interfaces/` — there is nothing that needs them.
- No `config/` — configuration is just CLI args.
- No nested packages inside `src/` — 7 files is manageable flat.

---

## 3. File Structure

### `main.py`
- **Purpose**: Entry point. Parses CLI arguments, orchestrates the pipeline.
- **Responsibility**: Read args → call parser → build graph → find paths → schedule → simulate → output.
- **Owns**: The main execution flow.
- **Should never**: Contain business logic, parsing logic, or graph algorithms.

### `src/models.py`
- **Purpose**: Data classes for Zone, Connection, Drone.
- **Responsibility**: Define the shape of data. Nothing else.
- **Owns**: All data class definitions.
- **Should never**: Contain algorithms, I/O, or validation beyond type constraints.

### `src/parser.py`
- **Purpose**: Read and validate the input file.
- **Responsibility**: Turn raw text into Zone, Connection objects + drone count.
- **Owns**: All parsing and validation logic.
- **Should never**: Build the graph or run the simulation.

### `src/graph.py`
- **Purpose**: Store zones and connections as an adjacency structure.
- **Responsibility**: Provide neighbor lookup, capacity queries.
- **Owns**: The graph data structure.
- **Should never**: Do pathfinding or simulation.

### `src/pathfinder.py`
- **Purpose**: Find paths from start to end.
- **Responsibility**: BFS traversal, path discovery.
- **Owns**: The pathfinding algorithm.
- **Should never**: Move drones or manage simulation state.

### `src/scheduler.py`
- **Purpose**: Assign drones to paths and plan their movement.
- **Responsibility**: Decide which drone goes where each turn, respecting capacity.
- **Owns**: The scheduling/assignment logic.
- **Should never**: Parse files or draw output.

### `src/simulation.py`
- **Purpose**: Execute the turn-by-turn simulation.
- **Responsibility**: Apply movements, enforce rules, generate output lines.
- **Owns**: The simulation loop and state.
- **Should never**: Find paths (that's done before simulation starts).

### `src/display.py`
- **Purpose**: Colored terminal visualization.
- **Responsibility**: Print simulation state with ANSI colors.
- **Owns**: All display/formatting logic.
- **Should never**: Modify simulation state.

---

## 4. Classes

### Class: `Zone`
```python
@dataclass
class Zone:
    name: str
    x: int
    y: int
    zone_type: str        # "normal", "restricted", "priority", "blocked"
    color: str            # e.g. "red", "blue", or ""
    max_drones: int       # default 1, ignored for start/end
    is_start: bool
    is_end: bool
```
- **Purpose**: Represents one node in the graph.
- **Why it exists**: The subject defines zones with these exact attributes.
- **Methods**: None needed. It's a data container.

### Class: `Connection`
```python
@dataclass
class Connection:
    zone1: str            # name of first zone
    zone2: str            # name of second zone
    max_link_capacity: int  # default 1
```
- **Purpose**: Represents one edge in the graph.
- **Why it exists**: Connections have their own capacity metadata.
- **Methods**: `name` property → returns `"zone1-zone2"` (sorted alphabetically for consistency).

### Class: `Drone`
```python
@dataclass
class Drone:
    id: int               # 1-based
    path: list[str]       # assigned path (list of zone names)
    position: str         # current zone name
    path_index: int       # how far along the path
    in_transit: bool      # True if on a connection (restricted zone movement)
    transit_dest: str     # destination zone name when in transit
    delivered: bool       # True if reached end zone
```
- **Purpose**: Tracks one drone's state during simulation.
- **Why it exists**: Need to track position, movement progress, and delivery status.

### Class: `Graph`
```python
class Graph:
    zones: dict[str, Zone]
    adjacency: dict[str, list[str]]         # zone_name → [neighbor_names]
    connections: dict[tuple[str, str], Connection]  # (sorted pair) → Connection
    start: str
    end: str
```
- **Purpose**: The complete graph structure.
- **Why it exists**: Central data structure that parser builds and everything else reads.
- **Methods**:
  - `get_neighbors(zone_name) → list[str]`
  - `get_connection(zone1, zone2) → Connection`
  - `get_zone(name) → Zone`

### Class: `Parser`
```python
class Parser:
    def parse(self, filepath: str) → tuple[int, Graph]
```
- **Purpose**: Reads file, returns (drone_count, graph).
- **Why it exists**: Parsing is complex enough to warrant its own class. Correction explicitly tests it.

### Class: `Pathfinder`
```python
class Pathfinder:
    def find_paths(self, graph: Graph, count: int) → list[list[str]]
```
- **Purpose**: Finds multiple paths from start to end.
- **Why it exists**: Pathfinding is a distinct algorithm. Correction explicitly tests it.

### Class: `Scheduler`
```python
class Scheduler:
    def assign_drones(self, drones: list[Drone], paths: list[list[str]], graph: Graph) → None
```
- **Purpose**: Assigns each drone a path.
- **Why it exists**: Separates path assignment from simulation execution.

### Class: `Simulation`
```python
class Simulation:
    def run(self, drones: list[Drone], graph: Graph) → list[str]
```
- **Purpose**: Executes the simulation turn by turn.
- **Why it exists**: Core simulation logic. Returns list of output lines.

### Class: `Display`
```python
class Display:
    def show_turn(self, turn: int, movements: list[str], drones: list[Drone], graph: Graph) → None
    def show_summary(self, total_turns: int, drones: list[Drone]) → None
```
- **Purpose**: Colored terminal output.
- **Why it exists**: Correction explicitly checks visualization.

### Total: 9 classes. No inheritance between them. All use composition.

### Why no other classes are needed
- No `ZoneFactory` — zones are created directly by the parser.
- No `SimulationState` class — the Simulation class tracks state internally.
- No `PathValidator` — validation is done inline in the scheduler.
- No `EventEmitter` — no observer pattern needed.

---

## 5. Data Structures

| Structure | Used For | Why |
|-----------|----------|-----|
| `dict[str, Zone]` | Store zones by name | O(1) lookup by name — needed constantly |
| `dict[str, list[str]]` | Adjacency list | O(1) neighbor lookup — standard for BFS |
| `dict[tuple[str, str], Connection]` | Connection lookup | O(1) by sorted pair of zone names |
| `list[str]` | A path (sequence of zone names) | Ordered sequence — simplest representation |
| `list[Drone]` | All drones | Small count, iteration is fine |
| `collections.deque` | BFS queue | O(1) popleft — standard for BFS |
| `set[str]` | BFS visited set | O(1) membership test |
| `dict[str, int]` | Zone occupancy counter (zone_name → current count) | O(1) lookup during simulation |
| `dict[tuple[str,str], int]` | Connection usage counter | O(1) lookup during simulation |

### Why no priority queue
- BFS is sufficient because all normal/priority edges cost 1 turn.
- Restricted edges cost 2 turns but BFS can handle this by treating the path cost correctly.
- If we need weighted shortest path, a simple modified BFS (or Dijkstra with `heapq`) can be used, but only if performance demands it.

### Why no custom containers
- Python built-in `dict`, `list`, `set`, `deque` cover every need.
- Custom containers add complexity without adding clarity.

---

## 6. Graph Representation

### Storage

```python
# Zones: dict mapping name → Zone object
zones = {
    "start": Zone(name="start", x=0, y=0, zone_type="normal", ...),
    "waypoint1": Zone(...),
    "goal": Zone(...)
}

# Adjacency: dict mapping zone name → list of neighbor names
adjacency = {
    "start": ["waypoint1"],
    "waypoint1": ["start", "waypoint2"],
    "waypoint2": ["waypoint1", "goal"],
    "goal": ["waypoint2"]
}

# Connections: dict mapping sorted tuple → Connection
connections = {
    ("start", "waypoint1"): Connection(zone1="start", zone2="waypoint1", max_link_capacity=1),
    ("waypoint1", "waypoint2"): Connection(...),
    ("waypoint2", "goal"): Connection(...)
}
```

### How lookup works
- **Get zone**: `zones["name"]` → O(1)
- **Get neighbors**: `adjacency["name"]` → O(1)
- **Get connection**: `connections[tuple(sorted(["a", "b"]))]` → O(1)

### Why this is enough
- Adjacency list is the textbook representation for BFS.
- Separate connections dict allows capacity lookup without traversing adjacency lists.
- All operations needed during simulation are O(1).

---

## 7. Parser Design

### Step-by-step

```
1. Open file with context manager
2. Read all lines
3. For each line:
   a. Strip whitespace
   b. If empty or starts with '#' → skip
   c. If starts with 'nb_drones:' → parse drone count
   d. If starts with 'start_hub:' → parse zone (mark is_start=True)
   e. If starts with 'end_hub:' → parse zone (mark is_end=True)
   f. If starts with 'hub:' → parse zone
   g. If starts with 'connection:' → parse connection
   h. Otherwise → error: "Line {n}: Unknown line format"
4. After all lines:
   a. Validate drone count was found and > 0
   b. Validate exactly one start_hub exists
   c. Validate exactly one end_hub exists
   d. Validate no duplicate zone names
   e. Validate no duplicate connections (a-b == b-a)
   f. Validate all connection endpoints exist as zones
   g. Build and return Graph
```

### Zone parsing (`start_hub:`, `end_hub:`, `hub:`)

```
Format: prefix: name x y [metadata]

1. Split the line after the colon
2. Extract name (first token) → validate no dashes
3. Extract x, y (next two tokens) → validate integers
4. If '[' exists → parse metadata block
5. Metadata parsing:
   a. Extract content between '[' and ']'
   b. Split by whitespace
   c. For each key=value:
      - zone=<type> → validate type in {normal, restricted, priority, blocked}
      - color=<value> → store as string
      - max_drones=<n> → validate positive integer
      - unknown key → error
6. Apply defaults: zone_type="normal", color="", max_drones=1
```

### Connection parsing

```
Format: connection: zone1-zone2 [metadata]

1. Extract the part after 'connection: '
2. Split on '-' → exactly 2 parts (zone1, zone2)
3. If '[' exists → parse metadata:
   - max_link_capacity=<n> → validate positive integer
4. Apply defaults: max_link_capacity=1
5. Check both zone names exist
6. Check connection not duplicate (sort pair, check set)
```

### Error handling

Every error raises a `ParserError` exception with the message:
```
Error on line {line_number}: {description}
```

Examples:
- `"Error on line 1: nb_drones must be a positive integer"`
- `"Error on line 5: Duplicate zone name 'hub1'"`
- `"Error on line 8: Unknown zone type 'fast'"`
- `"Error: Missing start_hub definition"`
- `"Error: Missing end_hub definition"`
- `"Error on line 10: Connection references undefined zone 'unknown'"`
- `"Error on line 12: Duplicate connection 'a-b'"`
- `"Error on line 3: max_drones must be a positive integer"`

### When parsing should stop
On the **first** error. Raise exception immediately.

---

## 8. Internal Models

### Drone
```python
@dataclass
class Drone:
    id: int                # 1, 2, 3... (1-based)
    path: list[str]        # Assigned path: ["start", "A", "B", "goal"]
    position: str          # Current zone name (or "" if in transit)
    path_index: int        # Index into path (0 = start)
    in_transit: bool       # True = on a connection heading to restricted zone
    transit_connection: str # "zone1-zone2" when in transit
    transit_dest: str      # Destination zone name when in transit
    delivered: bool        # True = reached end zone
```

### Zone
```python
@dataclass
class Zone:
    name: str
    x: int
    y: int
    zone_type: str         # "normal" | "restricted" | "priority" | "blocked"
    color: str             # "" if not specified
    max_drones: int        # Default 1; unlimited for start/end
    is_start: bool         # True if start_hub
    is_end: bool           # True if end_hub
```

### Connection
```python
@dataclass
class Connection:
    zone1: str
    zone2: str
    max_link_capacity: int  # Default 1

    @property
    def name(self) -> str:
        return f"{self.zone1}-{self.zone2}"

    def key(self) -> tuple[str, str]:
        return tuple(sorted([self.zone1, self.zone2]))
```

### Graph
```python
class Graph:
    zones: dict[str, Zone]
    adjacency: dict[str, list[str]]
    connections: dict[tuple[str, str], Connection]
    start: str              # Name of start zone
    end: str                # Name of end zone
    nb_drones: int          # Number of drones
```

### Simulation State (tracked inside Simulation class, not a separate class)
```
- drones: list[Drone]
- zone_occupancy: dict[str, int]       # zone_name → current drone count
- connection_usage: dict[tuple[str,str], int]  # connection key → drones using it this turn
- turn_number: int
- output_lines: list[str]
```

---

## 9. Pathfinding

### Algorithm Choice: BFS (Breadth-First Search)

> **Why BFS**: BFS finds the shortest path in an unweighted graph. Since normal and priority zones both cost 1 turn, and restricted zones cost 2 turns, we can use a modified BFS that treats restricted zone movement as a 2-step hop. This is simpler than Dijkstra and sufficient for all test cases.

### How it works

```
1. Standard BFS from start to end
2. Skip blocked zones
3. For path cost calculation: 
   - normal/priority zones = 1 turn per hop
   - restricted zones = 2 turns per hop
4. Priority zones are "preferred" → when multiple shortest paths exist, 
   prefer paths that go through priority zones
```

### Finding Multiple Paths

The scheduler needs multiple paths to distribute drones. Use **iterative BFS with edge removal**:

```
1. Find shortest path P1 using BFS
2. For drones that need different paths:
   - Temporarily reduce capacity / mark edges as less desirable
   - Find next shortest path P2
   - Repeat
3. If only one path exists, all drones use it (they queue up)
```

A simpler approach that works well enough:

```
1. BFS to find ALL shortest paths (store all parents in BFS, not just one)
2. Extract K distinct paths from the BFS tree
3. Assign drones round-robin to paths
```

### Why BFS is sufficient
- All provided maps are small (< 60 zones).
- BFS complexity: O(V + E) — completely fine.
- No map requires optimal weighted shortest path that BFS can't handle.
- The correction only checks "finds valid paths" and "meets turn benchmarks" — BFS easily achieves this.

### What happens if several paths exist
- Find multiple paths via BFS.
- Assign drones to paths in a balanced way (round-robin or greedy by capacity).
- The scheduler handles timing/staggering.

---

## 10. Scheduler

### Design: Simple Round-Robin + Staggered Departure

```
1. Receive: list of paths, list of drones, graph
2. Assign paths:
   - Sort paths by cost (turns needed)
   - Assign drones to paths round-robin (distribute evenly)
   - Prefer shorter paths first
3. Stagger departures:
   - Drones on the same path depart in sequence
   - Gap between departures = determined by bottleneck capacity
   - If a path has max_drones=1 at every zone, drones depart 1 per turn
   - If capacity allows, multiple drones can follow the same path simultaneously
```

### How turns are processed
```
For each turn:
  1. Identify which drones can move (not delivered, not blocked)
  2. For each drone, determine next zone on its path
  3. Check capacity of destination zone AND connection
  4. If capacity allows → mark drone for movement
  5. If capacity blocked → drone waits (stays in place)
  6. Apply all valid movements simultaneously
```

### How conflicts are detected
```
- Count planned arrivals per zone
- If zone_current_count + planned_arrivals > max_drones → conflict
- Resolve by priority: drones closer to goal get priority
- Others wait
```

### How waiting works
- Drone stays in current position. Not included in output for that turn.

### How occupancy works
```
- Drones moving OUT of a zone free up capacity for that same turn
- Count: current occupants - leaving + arriving ≤ max_drones
```

### How restricted movement works
```
Turn N:   Drone moves to CONNECTION (in transit)
          Output: D1-connection_name
Turn N+1: Drone MUST arrive at restricted zone destination
          Output: D1-restricted_zone_name
          Drone cannot stay on connection
```

### How connection capacity works
```
- Count drones using each connection this turn
- If count ≥ max_link_capacity → additional drones cannot use it
- Check before allowing movement
```

### How simultaneous movement works
```
- All movements in a turn happen simultaneously
- A drone leaving zone A frees capacity for another drone to enter A
- Calculate all movements first, validate, then apply all at once
```

---

## 11. Simulation

### The Simulation Loop

```python
def run(self, drones: list[Drone], graph: Graph) -> list[str]:
    output_lines = []
    turn = 0
    
    while not all(d.delivered for d in drones):
        turn += 1
        movements = []
        
        # Phase 1: Determine which drones want to move
        planned_moves = self._plan_moves(drones, graph)
        
        # Phase 2: Validate capacity constraints
        valid_moves = self._validate_moves(planned_moves, drones, graph)
        
        # Phase 3: Apply valid movements
        for drone, destination, is_transit in valid_moves:
            if is_transit:
                # Drone enters connection toward restricted zone
                conn_name = get_connection_name(drone.position, destination)
                drone.in_transit = True
                drone.transit_dest = destination
                drone.transit_connection = conn_name
                drone.position = ""  # No longer in a zone
                movements.append(f"D{drone.id}-{conn_name}")
            else:
                # Drone arrives at zone
                drone.position = destination
                drone.in_transit = False
                drone.path_index += 1
                
                if destination == graph.end:
                    drone.delivered = True
                
                movements.append(f"D{drone.id}-{destination}")
        
        # Phase 4: Generate output
        if movements:
            output_lines.append(" ".join(movements))
    
    return output_lines
```

### Stop condition
- `all(drone.delivered for drone in drones)` → stop.
- Safety: if a turn produces no movements and not all delivered → deadlock → error.

---

## 12. Restricted Zones

### State Transitions

```
State 1: Drone at zone A (normal)
         Next zone on path: zone B (restricted)
         
State 2: Drone in transit on connection A-B
         drone.in_transit = True
         drone.position = "" (not in any zone — on connection)
         drone.transit_dest = "B"
         Output: "D1-A-B"
         
State 3: (MUST happen next turn) Drone arrives at zone B
         drone.in_transit = False
         drone.position = "B"
         Output: "D1-B"
```

### Critical Rules
1. When entering transit, the drone **leaves** its current zone → frees capacity.
2. The drone **occupies the connection** during transit → counts against `max_link_capacity`.
3. The drone **MUST** arrive at the destination next turn — cannot wait on the connection.
4. Therefore: before entering transit, you MUST verify the destination will have capacity next turn.
5. If destination won't be available → drone should **not** enter transit (wait at current zone instead).

### Implementation
```python
# When planning moves for a drone heading to restricted zone:
if next_zone.zone_type == "restricted" and not drone.in_transit:
    # Start transit: drone moves to the connection
    # But first check: will destination have space next turn?
    # Conservative: check current capacity of destination
    return (drone, next_zone.name, True)  # is_transit=True

elif drone.in_transit:
    # MUST complete transit this turn
    return (drone, drone.transit_dest, False)  # is_transit=False, arriving
```

---

## 13. Output

### Format Rules

Each turn → one line. Each line contains space-separated movements.

```
D<ID>-<zone_name>           ← drone moved to a zone
D<ID>-<zone1>-<zone2>       ← drone in transit on connection (restricted)
```

### Building each line
```python
line_parts = []
for drone, dest, is_transit in turn_movements:
    if is_transit:
        conn_name = f"{drone.current_zone}-{dest}"
        line_parts.append(f"D{drone.id}-{conn_name}")
    else:
        line_parts.append(f"D{drone.id}-{dest}")

line = " ".join(line_parts)
print(line)
```

### When drones disappear from output
- Once a drone reaches the end zone (delivered), it is never mentioned again.

### When no output is printed
- If no drone moves in a turn (all waiting), that turn still exists but the line is empty.
- However, if all waiting drones are stuck and none can ever move → deadlock → error.
- In practice, the simulation should always make progress.

### Keep formatting simple
- Just `" ".join(movements)` per line.
- No headers, no footers, no turn numbers in the simulation output itself.
- The visualization (display module) can show more detail separately.

---

## 14. Visualization

### Choice: Colored Terminal Output (ANSI escape codes)

This is the simplest choice that satisfies the correction sheet.

### How colors are mapped

```python
COLOR_MAP: dict[str, str] = {
    "red":     "\033[91m",
    "green":   "\033[92m",
    "yellow":  "\033[93m",
    "blue":    "\033[94m",
    "magenta": "\033[95m",
    "cyan":    "\033[96m",
    "white":   "\033[97m",
    "orange":  "\033[38;5;208m",
    "gray":    "\033[90m",
    "purple":  "\033[35m",
}
RESET = "\033[0m"
```

### What to display each turn
```
Turn 1:
  [green]start[/] (3 drones) → [blue]waypoint1[/] (1 drone)
  Movements: D1-waypoint1 D2-waypoint1
```

### Implementation
```python
def show_turn(self, turn: int, movements: list[str], 
              drones: list[Drone], graph: Graph) -> None:
    """Display one turn with colored zone names."""
    print(f"\n--- Turn {turn} ---")
    for m in movements:
        parts = m.split("-", 1)
        drone_id = parts[0]
        dest = parts[1]
        zone = graph.zones.get(dest)
        if zone and zone.color in COLOR_MAP:
            colored = f"{COLOR_MAP[zone.color]}{dest}{RESET}"
        else:
            colored = dest
        print(f"  {drone_id} → {colored}")
```

### Why not a GUI
- The subject says "colored terminal output and/or graphical interface."
- Terminal output is dramatically simpler.
- Correction sheet says "colored terminal output and/or graphical interface" — terminal is sufficient.

---

## 15. Memory

### Ownership

| Object | Created by | Stored in | Lifetime |
|--------|-----------|-----------|----------|
| Zone | Parser | Graph.zones dict | Entire program |
| Connection | Parser | Graph.connections dict | Entire program |
| Graph | Parser | main.py local variable | Entire program |
| Drone | main.py (after parsing) | list in main.py | Entire program |
| Pathfinder | main.py | local variable | Used once |
| Scheduler | main.py | local variable | Used once |
| Simulation | main.py | local variable | Used for simulation |
| Display | main.py | local variable | Used for simulation |

### No circular references
- Graph owns Zones and Connections.
- Drones reference zone names (strings), not Zone objects.
- No object references its owner.
- Python garbage collector handles everything.

### Cleanup
- No manual cleanup needed (Python GC).
- File handles: use `with open(...)` context manager.

---

## 16. Error Handling

### Strategy: One Custom Exception Class

```python
class FlyinError(Exception):
    """Base exception for all Fly-in errors."""
    pass

class ParserError(FlyinError):
    """Raised when the input file is invalid."""
    pass

class SimulationError(FlyinError):
    """Raised when the simulation encounters an unrecoverable state."""
    pass
```

### Error Cases

| Error | Exception | Message |
|-------|-----------|---------|
| File not found | `ParserError` | `"Error: File '{path}' not found"` |
| No nb_drones line | `ParserError` | `"Error: Missing nb_drones definition"` |
| Invalid drone count | `ParserError` | `"Error on line {n}: nb_drones must be a positive integer"` |
| Missing start_hub | `ParserError` | `"Error: Missing start_hub definition"` |
| Missing end_hub | `ParserError` | `"Error: Missing end_hub definition"` |
| Duplicate zone name | `ParserError` | `"Error on line {n}: Duplicate zone name '{name}'"` |
| Invalid zone type | `ParserError` | `"Error on line {n}: Invalid zone type '{type}'"` |
| Invalid capacity | `ParserError` | `"Error on line {n}: {field} must be a positive integer"` |
| Zone name with dash | `ParserError` | `"Error on line {n}: Zone name cannot contain dashes"` |
| Unknown connection zone | `ParserError` | `"Error on line {n}: Unknown zone '{name}' in connection"` |
| Duplicate connection | `ParserError` | `"Error on line {n}: Duplicate connection '{z1}-{z2}'"` |
| Invalid metadata syntax | `ParserError` | `"Error on line {n}: Invalid metadata syntax"` |
| No path exists | `SimulationError` | `"Error: No valid path from '{start}' to '{end}'"` |
| Deadlock detected | `SimulationError` | `"Error: Simulation deadlock — no drone can move"` |
| Disconnected graph | `SimulationError` | `"Error: Graph is disconnected — no path from start to end"` |

### In main.py
```python
try:
    # ... run everything
except FlyinError as e:
    print(str(e), file=sys.stderr)
    sys.exit(1)
except Exception as e:
    print(f"Unexpected error: {e}", file=sys.stderr)
    sys.exit(1)
```

---

## 17. README Outline

```markdown
*This project has been created as part of the 42 curriculum by <login1>.*

# Fly-in — Drone Simulation

## Description
[2-3 sentences: what it does, what problem it solves]

## Instructions

### Requirements
- Python 3.10+

### Installation
make install

### Running
make run MAP=maps/easy/01_linear_path.txt

### Debug Mode
make debug MAP=maps/easy/01_linear_path.txt

### Linting
make lint

## Algorithm Explanation

### Pathfinding
[Explain BFS approach, why BFS, how multiple paths are found]

### Scheduling
[Explain drone assignment, staggering, conflict resolution]

### Zone Types
[Table: normal/restricted/priority/blocked with costs]

## Visual Representation
[Explain colored terminal output, what colors mean, how to read it]

## Example
### Input
[Show a small map file]

### Output
[Show the simulation output]

## Resources
[References, 42 subject, graph theory links]
[How AI was used: which tasks, which parts]
```

---

## 18. Makefile

```makefile
MAP ?= maps/easy/01_linear_path.txt

install:
	pip install -r requirements.txt

run:
	python3 main.py $(MAP)

debug:
	python3 -m pdb main.py $(MAP)

clean:
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name .mypy_cache -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete 2>/dev/null || true

lint:
	flake8 .
	mypy . --warn-return-any --warn-unused-ignores --ignore-missing-imports --disallow-untyped-defs --check-untyped-defs

lint-strict:
	flake8 .
	mypy . --strict
```

| Target | Purpose |
|--------|---------|
| `install` | Install dependencies (flake8, mypy — minimal) |
| `run` | Execute with a map file |
| `debug` | Run under Python debugger (pdb) |
| `clean` | Remove __pycache__, .mypy_cache, .pyc files |
| `lint` | flake8 + mypy with mandatory flags |
| `lint-strict` | flake8 + mypy --strict (optional, recommended) |

---

## 19. Implementation Roadmap

### Step 1: Project Setup
- [ ] Create folder structure
- [ ] Create `requirements.txt` (flake8, mypy)
- [ ] Create `Makefile`
- [ ] Create empty `main.py` with `if __name__ == "__main__"` and `sys.argv` parsing
- [ ] Create `src/__init__.py`
- [ ] **Test**: `make install` and `make lint` pass on empty project

### Step 2: Models
- [ ] Create `src/models.py` with `Zone`, `Connection`, `Drone` dataclasses
- [ ] Add all type hints and docstrings
- [ ] **Test**: `make lint` passes. Import models in a test script.

### Step 3: Parser — Basic
- [ ] Create `src/parser.py` with `Parser` class
- [ ] Implement: read file, skip comments, parse `nb_drones`
- [ ] Implement: parse `start_hub`, `end_hub`, `hub` lines (no metadata yet)
- [ ] Implement: parse `connection` lines (no metadata yet)
- [ ] **Test**: Parse `01_linear_path.txt` successfully, print zones and connections.

### Step 4: Parser — Metadata
- [ ] Add metadata parsing: `[zone=... color=... max_drones=...]`
- [ ] Add connection metadata: `[max_link_capacity=...]`
- [ ] Apply defaults
- [ ] **Test**: Parse `02_simple_fork.txt` and `03_basic_capacity.txt`.

### Step 5: Parser — Validation
- [ ] Add all error checks (duplicates, missing start/end, invalid types, etc.)
- [ ] Add `ParserError` exception with line numbers
- [ ] **Test**: Create invalid map files, verify correct error messages.

### Step 6: Graph
- [ ] Create `src/graph.py` with `Graph` class
- [ ] Build adjacency list from parsed zones and connections
- [ ] Add `get_neighbors()`, `get_connection()`, `get_zone()` methods
- [ ] **Test**: Build graph from parsed data, print adjacency.

### Step 7: Pathfinder
- [ ] Create `src/pathfinder.py` with `Pathfinder` class
- [ ] Implement BFS from start to end
- [ ] Skip blocked zones
- [ ] Account for restricted zone costs
- [ ] Find multiple distinct paths
- [ ] **Test**: Find paths on all easy maps, verify they reach the goal.

### Step 8: Scheduler
- [ ] Create `src/scheduler.py` with `Scheduler` class
- [ ] Assign drones to paths (round-robin)
- [ ] Implement staggered departure logic
- [ ] **Test**: Assign 4 drones to 2 paths, verify assignment.

### Step 9: Simulation — Basic Movement
- [ ] Create `src/simulation.py` with `Simulation` class
- [ ] Implement basic turn loop: plan → validate → move
- [ ] Handle normal zone movement (1 turn)
- [ ] Track zone occupancy
- [ ] Generate output lines
- [ ] **Test**: Simulate `01_linear_path.txt` with 2 drones.

### Step 10: Simulation — Restricted Zones
- [ ] Implement 2-turn movement for restricted zones
- [ ] Track in-transit state on connections
- [ ] Enforce "must arrive next turn" rule
- [ ] **Test**: Simulate `02_circular_loop.txt` with restricted zones.

### Step 11: Simulation — Capacity
- [ ] Enforce zone max_drones capacity
- [ ] Enforce connection max_link_capacity
- [ ] Handle simultaneous movement (departing frees capacity)
- [ ] Handle waiting (drone stays, omitted from output)
- [ ] **Test**: Simulate `03_basic_capacity.txt`.

### Step 12: Display
- [ ] Create `src/display.py` with `Display` class
- [ ] Map zone colors to ANSI escape codes
- [ ] Show turn-by-turn colored output
- [ ] Show summary at end (total turns)
- [ ] **Test**: Run simulation with display on easy maps.

### Step 13: Main Integration
- [ ] Wire everything together in `main.py`
- [ ] Add CLI argument parsing (`sys.argv` or `argparse`)
- [ ] Add `--capacity-info` flag support (prepare for live coding!)
- [ ] Add error handling (try/except)
- [ ] **Test**: `make run MAP=maps/easy/01_linear_path.txt` works end-to-end.

### Step 14: Medium Maps
- [ ] Run on all medium maps
- [ ] Debug and fix any issues
- [ ] Verify turn counts are in 10–30 range
- [ ] **Test**: All medium maps solve within benchmark.

### Step 15: Hard Maps
- [ ] Run on all hard maps
- [ ] Optimize scheduler/pathfinder if turn counts are too high
- [ ] Verify turn counts < 60
- [ ] **Test**: All hard maps solve within benchmark.

### Step 16: Edge Cases
- [ ] Test single drone scenarios
- [ ] Test disconnected graphs → graceful error
- [ ] Test invalid connections → error
- [ ] Test zero/high capacity values
- [ ] Test maps with all zone types
- [ ] **Test**: All edge cases handled.

### Step 17: Polish
- [ ] Run `make lint` → fix all flake8/mypy issues
- [ ] Add docstrings to every function and class
- [ ] Write README.md
- [ ] Final test of all maps
- [ ] **Test**: `make lint` passes cleanly.

---

## 20. Testing

### Parser Tests (`tests/test_parser.py`)

```python
# Valid files
test_parse_linear_path()           # Parse 01_linear_path.txt
test_parse_simple_fork()           # Parse 02_simple_fork.txt with metadata
test_parse_all_zone_types()        # normal, restricted, priority, blocked
test_parse_comments_ignored()      # Lines starting with # skipped
test_parse_metadata_any_order()    # [color=red zone=normal] vs [zone=normal color=red]

# Error cases
test_error_missing_nb_drones()     # No nb_drones line
test_error_invalid_nb_drones()     # nb_drones: -1 or nb_drones: abc
test_error_missing_start()         # No start_hub
test_error_missing_end()           # No end_hub
test_error_duplicate_zone()        # Two zones with same name
test_error_duplicate_connection()  # a-b and b-a
test_error_invalid_zone_type()     # zone=fast
test_error_invalid_capacity()      # max_drones=0 or max_drones=-1
test_error_unknown_zone_in_conn()  # Connection references nonexistent zone
test_error_zone_name_with_dash()   # Zone name contains '-'
test_error_malformed_line()        # Random text that doesn't match any format
```

### Graph Tests (`tests/test_graph.py`)

```python
test_build_graph()                 # Build from parsed data
test_get_neighbors()               # Adjacency correct
test_get_connection()              # Connection lookup works
test_blocked_zones_in_graph()      # Blocked zones exist but pathfinder skips them
test_start_end_identified()        # start and end correctly set
```

### Pathfinder Tests (`tests/test_pathfinder.py`)

```python
test_find_path_linear()            # Simple A→B→C→D
test_find_path_fork()              # Two possible paths
test_find_multiple_paths()         # Returns multiple distinct paths
test_skip_blocked_zones()          # Path avoids blocked zones
test_priority_preferred()          # Priority zones chosen over normal when same length
test_no_path_exists()              # Disconnected graph → error
test_restricted_zone_cost()        # Path through restricted costs 2 turns
```

### Simulation Tests (`tests/test_simulation.py`)

```python
# Movement
test_single_drone_linear()         # 1 drone, straight line
test_multiple_drones_same_path()   # Queue up on same path
test_multiple_paths()              # Drones use different paths

# Occupancy
test_zone_capacity_enforced()      # Can't exceed max_drones
test_start_zone_unlimited()        # All drones start together
test_end_zone_unlimited()          # Multiple drones arrive together
test_departing_frees_capacity()    # Leaving drone frees space same turn

# Connections
test_connection_capacity()         # max_link_capacity enforced
test_restricted_two_turns()        # Restricted zone takes 2 turns
test_must_arrive_after_transit()   # Can't wait on connection

# Output
test_output_format()               # D1-zone format correct
test_stationary_omitted()          # Waiting drones not in output
test_delivered_removed()           # Drones at end zone not mentioned again
test_simulation_ends()             # Stops when all delivered

# Edge cases
test_single_drone_single_hop()     # Start directly connected to end
test_deadlock_detection()          # All drones stuck → error
```

### Map Integration Tests

```python
test_easy_01_linear()              # ≤ 6 turns
test_easy_02_fork()                # ≤ 8 turns
test_easy_03_capacity()            # ≤ 6 turns
test_medium_01_dead_end()          # ≤ 12 turns
test_medium_02_circular()          # ≤ 15 turns
test_medium_03_priority()          # ≤ 12 turns
test_hard_01_maze()                # ≤ 30 turns (< 60)
test_hard_02_capacity()            # ≤ 35 turns (< 60)
test_hard_03_ultimate()            # ≤ 45 turns (< 60)
```

---

## 21. Defense Preparation

### Questions the evaluator will likely ask

| # | Question | How to answer |
|---|----------|---------------|
| 1 | "Explain your pathfinding algorithm." | "I use BFS (Breadth-First Search). It explores all zones level by level from start to end. It guarantees finding the shortest path. I find multiple paths by running BFS repeatedly, removing edges from previously found paths." |
| 2 | "Why BFS and not Dijkstra or A*?" | "BFS finds the shortest path in graphs where edge weights are uniform. Normal and priority zones cost 1 turn. For restricted zones (2 turns), I handle them by treating the transit as a 2-step process. This is simpler than Dijkstra and sufficient for all test maps." |
| 3 | "How do you handle restricted zones?" | "When a drone needs to enter a restricted zone, it first moves to the connection (turn 1, output D1-connection), then it MUST arrive at the destination (turn 2, output D1-zone). It cannot wait on the connection. I check destination capacity before starting transit." |
| 4 | "What is the complexity of your algorithm?" | "Pathfinding: O(V + E) per BFS call, where V = zones, E = connections. Finding K paths: O(K × (V + E)). Simulation: O(T × D) where T = turns and D = drones. Total is very fast for all provided maps." |
| 5 | "How do you handle capacity conflicts?" | "Each turn, I count how many drones want to enter each zone. If the count would exceed max_drones, I prioritize drones closer to the goal. The rest wait. Same logic for connection capacity." |
| 6 | "How does simultaneous movement work?" | "All movements in a turn happen at once. A drone leaving zone A frees up a slot. Another drone can enter A in the same turn. I calculate all moves first, check all constraints, then apply all valid moves together." |
| 7 | "Show me your graph implementation." | Open `src/graph.py`. Show the `zones` dict, `adjacency` dict, `connections` dict. Explain O(1) lookups. |
| 8 | "How do you handle errors?" | "I have a `ParserError` exception that includes the line number and cause. The main function catches all exceptions and prints a clear message. The program never crashes." |
| 9 | "What is OOP in your project?" | "Every logical component is a class: Zone, Connection, Drone are data classes. Parser, Graph, Pathfinder, Scheduler, Simulation, Display are behavior classes. Each has a single responsibility." |
| 10 | "Why didn't you use networkx?" | "The subject forbids graph libraries. My graph is a simple adjacency list stored as a dict. It's ~30 lines of code." |
| 11 | "How does your visualization work?" | "I use ANSI escape codes to color zone names in terminal output. Each zone's color from the map file maps to an ANSI color code. The display shows drone positions each turn." |
| 12 | "Can you add the --capacity-info flag?" | *This is the live coding task!* "Yes. I add an argparse flag, then in the simulation output loop, I print zone and connection occupancy alongside the movements." |

### Live Coding Preparation

The correction sheet asks you to add `--capacity-info` that shows:
```
Zone X: Y/Z drones, Connection A-B: Y/Z capacity used
```

**Preparation**:
1. Use `argparse` in `main.py` so adding a flag is trivial.
2. The `Simulation` class already tracks `zone_occupancy` and `connection_usage`.
3. Add to `Display` class: a method `show_capacity_info()` that prints occupancy.
4. In `main.py`, if `args.capacity_info`, call display method after each turn.

---

## 22. Simplicity Audit

### Removed during audit

| What | Why removed |
|------|-------------|
| `SimulationState` class | State is simple enough to track as instance variables in `Simulation` |
| `PathValidator` class | Validation is 5 lines inline in `Pathfinder` |
| `ZoneFactory` | Zones are created by one `Zone(...)` call in the parser |
| `EventSystem` / Observer | Nothing observes anything — just sequential calls |
| `Strategy pattern` for pathfinding | Only one algorithm (BFS) — no need for swappable strategies |
| `Abstract base classes` | No inheritance hierarchy exists — no ABCs needed |
| Separate `validators/` module | Validation happens inline where data is created |
| `config.py` | Configuration is just CLI args — no config file needed |
| `constants.py` | Only a few constants (ZONE_TYPES, COLOR_MAP) — they go in their respective modules |
| `exceptions.py` as separate file | 3 exception classes fit in `models.py` or at module level |
| `utils.py` | No shared utility functions exist |

### Final Class Count: 9

```
Zone, Connection, Drone       → 3 data classes (models.py)
FlyinError, ParserError,      → 3 exception classes (models.py)
  SimulationError
Parser                        → 1 class (parser.py)
Graph                         → 1 class (graph.py)
Pathfinder                    → 1 class (pathfinder.py)
Scheduler                     → 1 class (scheduler.py)
Simulation                    → 1 class (simulation.py)
Display                       → 1 class (display.py)
```

### Final File Count: 9 (in `src/`)

```
src/__init__.py
src/models.py
src/parser.py
src/graph.py
src/pathfinder.py
src/scheduler.py
src/simulation.py
src/display.py
```

Plus `main.py` at root = **10 Python files total**.

### Complexity Check

- Deepest import chain: `main.py` → `src/simulation.py` → `src/models.py` (2 levels)
- No circular imports possible
- Every file can be understood independently
- Every class fits on one screen (< 100 lines)
- Total estimated LOC: ~800–1000 lines

### Final Simplicity Statement

> This architecture has the minimum number of files, classes, and abstractions needed to satisfy every mandatory requirement and pass every checkbox on the correction sheet. Nothing can be removed without losing a required feature. Nothing is added that isn't explicitly required.

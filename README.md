*This project has been created as part of the 42 curriculum by \<login1\>.*

# Fly-in — Drone Simulation

## Description

Fly-in is a drone fleet simulation that routes multiple drones from a start zone to an end zone through a network of connected zones. The program reads a map file defining zones with different types (normal, restricted, priority, blocked), capacity constraints, and connections, then simulates turn-by-turn movement to deliver all drones in the fewest turns possible.

The simulation respects zone occupancy limits, connection capacity, multi-turn movement for restricted zones, and simultaneous drone movement — all while avoiding conflicts and deadlocks.

## Instructions

### Requirements

- Python 3.10+

### Installation

```bash
make install
```

### Running

```bash
make run MAP=maps/easy/01_linear_path.txt
```

Or directly:

```bash
python3 main.py maps/easy/01_linear_path.txt
```

### Capacity Info Mode

```bash
python3 main.py maps/easy/01_linear_path.txt --capacity-info
```

### Debug Mode

```bash
make debug MAP=maps/easy/01_linear_path.txt
```

### Linting

```bash
make lint
```

### Clean

```bash
make clean
```

## Algorithm Explanation

### Pathfinding: BFS (Breadth-First Search)

The pathfinder uses BFS to find shortest paths from the start zone to the end zone. BFS guarantees the shortest path in terms of hops, and is the simplest correct pathfinding algorithm for this problem.

**Why BFS**: All normal and priority zones cost 1 turn per hop. Restricted zones cost 2 turns but are handled as a 2-step process (enter connection → arrive). BFS finds optimal paths efficiently in O(V + E) time.

**Multiple paths**: To find K different paths, we run BFS K times. After each path is found, we penalize the used edges so the next BFS naturally finds an alternative route. This distributes drones across different paths.

**Priority zones**: When multiple paths have equal cost, paths through priority zones are preferred (they receive a negative score bonus in the BFS scoring).

### Scheduling

Drones are assigned to paths using simple round-robin distribution. This ensures even distribution across available paths without complex optimization.

### Simulation

The simulation runs turn by turn:

1. **Phase 1**: Drones in transit (restricted zones) MUST complete their movement
2. **Phase 2**: Other drones attempt to move to the next zone on their path
3. **Conflict resolution**: Drones closer to their goal get priority
4. **Capacity check**: Zone and connection capacity are enforced before each move
5. **Waiting**: Drones that can't move stay in place (omitted from output)

### Zone Types

| Type | Movement Cost | Behavior |
|------|--------------|----------|
| `normal` | 1 turn | Standard zone (default) |
| `restricted` | 2 turns | Drone enters connection on turn 1, arrives on turn 2 |
| `priority` | 1 turn | Same as normal but preferred by pathfinder |
| `blocked` | N/A | Cannot be entered — pathfinder avoids these |

## Visual Representation

The program provides colored terminal output to enhance understanding of the simulation:

- **Zone colors**: Each zone's color from the map file is mapped to ANSI terminal colors
- **Turn display**: Each turn shows drone movements with colored destination names
- **Summary**: After simulation, total turns and delivery count are displayed

The colored output appears below the raw simulation output, making it easy to see both the machine-readable format and the human-readable visualization.

## Example

### Input (01_linear_path.txt)

```
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

### Output

```
D1-waypoint1
D1-waypoint2 D2-waypoint1
D1-goal D2-waypoint2
D2-goal
```

## Resources

- [Graph Theory - BFS](https://en.wikipedia.org/wiki/Breadth-first_search)
- [42 Fly-in Subject](./flyin.pdf)

### AI Usage

AI was used as a coding assistant for:
- Architecture design and planning
- Code generation following the planned architecture
- Documentation writing

All generated code was reviewed, understood, and can be fully explained during peer evaluation.

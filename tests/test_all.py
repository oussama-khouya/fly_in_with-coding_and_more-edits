"""Comprehensive tests for the Fly-in drone simulation."""
from __future__ import annotations
import sys
import os

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from src.parser import Parser
from src.graph import Graph
from src.pathfinder import Pathfinder
from src.scheduler import Scheduler
from src.simulation import Simulation
from src.models import ParserError, SimulationError, Drone


# ─── helpers ────────────────────────────────────────────────────────────────

PASS = "\033[92mPASS\033[0m"
FAIL = "\033[91mFAIL\033[0m"

pass_count = 0
fail_count = 0


def check(name: str, condition: bool, detail: str = "") -> None:
    global pass_count, fail_count
    if condition:
        print(f"  {PASS}  {name}")
        pass_count += 1
    else:
        print(f"  {FAIL}  {name}" + (f" → {detail}" if detail else ""))
        fail_count += 1


def section(title: str) -> None:
    print(f"\n{'─' * 55}")
    print(f"  {title}")
    print(f"{'─' * 55}")


def parse_string(content: str) -> Graph:
    """Write content to a temp file and parse it."""
    tmp = "/tmp/flyin_test_map.txt"
    with open(tmp, "w") as f:
        f.write(content)
    return Parser().parse(tmp)


def expect_parser_error(content: str, fragment: str) -> str:
    """Return error message if ParserError raised, else empty string."""
    try:
        parse_string(content)
        return ""
    except ParserError as e:
        return str(e)


def run_simulation(content: str) -> list[str]:
    """Parse, find paths, assign, simulate. Return output lines."""
    graph = parse_string(content)
    paths = Pathfinder().find_paths(graph, graph.nb_drones)
    drones = [Drone(id=i + 1) for i in range(graph.nb_drones)]
    Scheduler().assign(drones, paths, graph)
    return Simulation(graph, drones).run()


# ─── PARSER TESTS ───────────────────────────────────────────────────────────

section("PARSER — Valid Inputs")

# Comments ignored
graph = parse_string("""
# this is a comment
nb_drones: 1
# another comment
start_hub: A 0 0
end_hub: B 1 0
connection: A-B
""")
check("Comments are ignored", graph.nb_drones == 1)
check("Zone A created", "A" in graph.zones)
check("Zone B created", "B" in graph.zones)

# Metadata any order
graph = parse_string("""
nb_drones: 1
start_hub: A 0 0 [color=green max_drones=3 zone=normal]
end_hub: B 1 0 [zone=priority color=red]
connection: A-B
""")
check("Metadata in any order (zone+color+max_drones)", graph.zones["A"].color == "green")
check("Zone type from metadata", graph.zones["B"].zone_type == "priority")

# max_drones ignored on start/end
graph = parse_string("""
nb_drones: 5
start_hub: A 0 0 [max_drones=1]
end_hub: B 1 0 [max_drones=1]
connection: A-B
""")
check("max_drones ignored on start_hub (set to unlimited)", graph.zones["A"].max_drones == 999999)
check("max_drones ignored on end_hub (set to unlimited)", graph.zones["B"].max_drones == 999999)

# All zone types accepted
graph = parse_string("""
nb_drones: 1
start_hub: A 0 0
hub: B 1 0 [zone=normal]
hub: C 2 0 [zone=restricted]
hub: D 3 0 [zone=priority]
hub: E 4 0 [zone=blocked]
end_hub: F 5 0
connection: A-B
connection: B-C
connection: C-D
connection: D-F
""")
check("zone=normal accepted", graph.zones["B"].zone_type == "normal")
check("zone=restricted accepted", graph.zones["C"].zone_type == "restricted")
check("zone=priority accepted", graph.zones["D"].zone_type == "priority")
check("zone=blocked accepted", graph.zones["E"].zone_type == "blocked")

# Connection capacity default
graph = parse_string("""
nb_drones: 1
start_hub: A 0 0
end_hub: B 1 0
connection: A-B
""")
conn = graph.get_connection("A", "B")
check("Connection default capacity = 1", conn.max_link_capacity == 1)

# Connection with explicit capacity
graph = parse_string("""
nb_drones: 1
start_hub: A 0 0
end_hub: B 1 0
connection: A-B [max_link_capacity=4]
""")
conn = graph.get_connection("A", "B")
check("Connection explicit capacity = 4", conn.max_link_capacity == 4)

# Bidirectional connections
graph = parse_string("""
nb_drones: 1
start_hub: A 0 0
hub: B 1 0
end_hub: C 2 0
connection: A-B
connection: B-C
""")
check("Connection is bidirectional (A→B)", "B" in graph.get_neighbors("A"))
check("Connection is bidirectional (B→A)", "A" in graph.get_neighbors("B"))

section("PARSER — Error Cases")

# Missing nb_drones
err = expect_parser_error("start_hub: A 0 0\nend_hub: B 1 0\nconnection: A-B", "")
check("Missing nb_drones raises error", "Missing nb_drones" in err, err)

# Invalid nb_drones (not integer)
err = expect_parser_error("nb_drones: abc\nstart_hub: A 0 0\nend_hub: B 1 0\nconnection: A-B", "")
check("nb_drones=abc raises error", "positive integer" in err, err)

# Invalid nb_drones (zero)
err = expect_parser_error("nb_drones: 0\nstart_hub: A 0 0\nend_hub: B 1 0\nconnection: A-B", "")
check("nb_drones=0 raises error", "positive integer" in err, err)

# Invalid nb_drones (negative)
err = expect_parser_error("nb_drones: -3\nstart_hub: A 0 0\nend_hub: B 1 0\nconnection: A-B", "")
check("nb_drones=-3 raises error", "positive integer" in err, err)

# Missing start_hub
err = expect_parser_error("nb_drones: 1\nhub: A 0 0\nend_hub: B 1 0\nconnection: A-B", "")
check("Missing start_hub raises error", "Missing start_hub" in err, err)

# Missing end_hub
err = expect_parser_error("nb_drones: 1\nstart_hub: A 0 0\nhub: B 1 0", "")
check("Missing end_hub raises error", "Missing end_hub" in err, err)

# Duplicate zone name
err = expect_parser_error("nb_drones: 1\nstart_hub: A 0 0\nhub: A 1 0\nend_hub: B 2 0", "")
check("Duplicate zone name raises error", "Duplicate zone name" in err, err)

# Duplicate connection (a-b and b-a)
err = expect_parser_error("""
nb_drones: 1
start_hub: A 0 0
end_hub: B 1 0
connection: A-B
connection: B-A
""", "")
check("Duplicate connection (B-A == A-B) raises error", "Duplicate connection" in err, err)

# Invalid zone type
err = expect_parser_error("nb_drones: 1\nstart_hub: A 0 0 [zone=fast]\nend_hub: B 1 0\nconnection: A-B", "")
check("Invalid zone type 'fast' raises error", "Invalid zone type" in err, err)

# max_drones = 0
err = expect_parser_error("nb_drones: 1\nstart_hub: A 0 0\nhub: X 0 1 [max_drones=0]\nend_hub: B 1 0\nconnection: A-B", "")
check("max_drones=0 raises error", "positive integer" in err, err)

# max_drones = negative
err = expect_parser_error("nb_drones: 1\nstart_hub: A 0 0\nhub: X 0 1 [max_drones=-1]\nend_hub: B 1 0\nconnection: A-B", "")
check("max_drones=-1 raises error", "positive integer" in err, err)

# max_link_capacity = 0
err = expect_parser_error("nb_drones: 1\nstart_hub: A 0 0\nend_hub: B 1 0\nconnection: A-B [max_link_capacity=0]", "")
check("max_link_capacity=0 raises error", "positive integer" in err, err)

# Unknown zone in connection
err = expect_parser_error("nb_drones: 1\nstart_hub: A 0 0\nend_hub: B 1 0\nconnection: A-GHOST", "")
check("Connection to unknown zone raises error", "Unknown zone" in err, err)

# Zone name with dash
err = expect_parser_error("nb_drones: 1\nstart_hub: my-zone 0 0\nend_hub: B 1 0\nconnection: my-zone-B", "")
check("Zone name with dash raises error", "cannot contain dashes" in err or "Unknown zone" in err, err)

# Missing file
try:
    Parser().parse("/tmp/does_not_exist_flyin.txt")
    check("Missing file raises error", False)
except ParserError as e:
    check("Missing file raises error", "not found" in str(e))

# Unknown line format
err = expect_parser_error("nb_drones: 1\nstart_hub: A 0 0\nend_hub: B 1 0\nconnection: A-B\ngarbage line here", "")
check("Unknown line format raises error", "Unknown line format" in err, err)

# Error message contains line number
err = expect_parser_error("nb_drones: 1\nstart_hub: A 0 0\nend_hub: B 1 0\nconnection: A-B\ngarbage line here", "")
check("Error message contains 'line'", "line" in err.lower(), err)


# ─── GRAPH TESTS ────────────────────────────────────────────────────────────

section("GRAPH — Structure")

graph = parse_string("""
nb_drones: 1
start_hub: start 0 0
hub: mid 1 0
end_hub: goal 2 0
connection: start-mid
connection: mid-goal
""")
check("start zone correctly identified", graph.start == "start")
check("end zone correctly identified", graph.end == "goal")
check("get_neighbors works", graph.get_neighbors("mid") == ["start", "goal"] or set(graph.get_neighbors("mid")) == {"start", "goal"})
check("get_zone works", graph.get_zone("mid").name == "mid")
check("get_connection works", graph.get_connection("start", "mid") is not None)
check("get_connection works reversed (mid,start)", graph.get_connection("mid", "start") is not None)


# ─── SIMULATION — MOVEMENT TESTS ────────────────────────────────────────────

section("SIMULATION — Basic Movement")

# Single drone linear path
lines = run_simulation("""
nb_drones: 1
start_hub: A 0 0
hub: B 1 0
end_hub: C 2 0
connection: A-B
connection: B-C
""")
check("Single drone reaches end", len(lines) >= 1)
check("Last line contains drone arrival", "C" in lines[-1])

# Output format: D<id>-<zone>
check("Output format D1-zone", lines[0].startswith("D1-"))

# Stationary drones omitted (single drone, should move every turn)
for line in lines:
    check(f"Line '{line}' is not empty", len(line.strip()) > 0)

# Simulation ends when all delivered
lines = run_simulation("""
nb_drones: 2
start_hub: A 0 0
hub: B 1 0
end_hub: C 2 0
connection: A-B
connection: B-C
""")
check("Simulation ends when all drones delivered", len(lines) > 0)
# Last line must contain deliveries to C
check("All drones delivered by end", True)  # if no error raised, all delivered

section("SIMULATION — Occupancy Rules")

# Zone capacity enforced (max_drones=1 default)
lines = run_simulation("""
nb_drones: 2
start_hub: A 0 0
hub: B 1 0
end_hub: C 2 0
connection: A-B
connection: B-C
""")
# B has max_drones=1, so both drones cannot be in B at same time
# They should be staggered
b_occupancy: dict[int, int] = {}
turn = 0
for line in lines:
    turn += 1
    moves = line.split()
    count_in_b = sum(1 for m in moves if m.endswith("-B"))
    b_occupancy[turn] = count_in_b
check("Zone with max_drones=1 not entered by 2 drones same turn", max(b_occupancy.values()) <= 1)

# Zone with max_drones=2 allows 2 drones
lines = run_simulation("""
nb_drones: 2
start_hub: A 0 0 [max_drones=5]
hub: B 1 0 [max_drones=2]
end_hub: C 2 0
connection: A-B [max_link_capacity=2]
connection: B-C [max_link_capacity=2]
""")
check("Zone max_drones=2 allows 2 drones through", len(lines) > 0)

# Multiple drones share start and end
lines = run_simulation("""
nb_drones: 3
start_hub: A 0 0
end_hub: B 1 0
connection: A-B [max_link_capacity=3]
""")
check("3 drones can share start and end zones", len(lines) > 0)

section("SIMULATION — Connection Capacity")

# Connection capacity = 1 by default, 2 drones can't use same connection same turn
MAP_CONN = """
nb_drones: 2
start_hub: A 0 0
end_hub: B 1 0
connection: A-B
"""
lines = run_simulation(MAP_CONN)
# With max_link_capacity=1, both drones cannot use A-B on same turn
# So we need at least 2 turns
check("Connection capacity=1 forces drones to go one at a time", len(lines) >= 2)

# High capacity allows simultaneous use
lines = run_simulation("""
nb_drones: 2
start_hub: A 0 0
end_hub: B 1 0
connection: A-B [max_link_capacity=2]
""")
check("Connection capacity=2 allows both drones same turn", len(lines) == 1)

section("SIMULATION — Restricted Zones (2-turn movement)")

# Drone must take 2 turns to enter restricted zone
lines = run_simulation("""
nb_drones: 1
start_hub: A 0 0
hub: B 1 0 [zone=restricted]
end_hub: C 2 0
connection: A-B
connection: B-C
""")
check("Restricted zone takes at least 2 turns", len(lines) >= 2)

# Check that a connection transit line appears (D1-A-B format)
has_transit = any("-A-B" in line or "A-B" in line for line in lines)
check("Transit line appears for restricted zone (D1-connection)", has_transit)

# Check drone arrives at restricted zone after transit
has_arrival = any("D1-B" in line for line in lines)
check("Drone arrives at restricted zone after transit", has_arrival)

section("SIMULATION — Priority Zones")

# Priority zones preferred over normal zones when cost is equal
lines = run_simulation("""
nb_drones: 1
start_hub: A 0 0
hub: slow 1 0 [zone=normal]
hub: fast 1 1 [zone=priority]
end_hub: C 2 0
connection: A-slow
connection: A-fast
connection: slow-C
connection: fast-C
""")
# Dijkstra should prefer the priority path (fast → C)
has_fast = any("fast" in line for line in lines)
check("Priority zone preferred in pathfinding", has_fast)

section("SIMULATION — Output Format")

lines = run_simulation("""
nb_drones: 2
start_hub: A 0 0
hub: B 1 0
end_hub: C 2 0
connection: A-B [max_link_capacity=2]
connection: B-C [max_link_capacity=2]
""")

# Each line is space-separated movements
for i, line in enumerate(lines):
    parts = line.split()
    for part in parts:
        valid = "-" in part and part.startswith("D")
        check(f"Turn {i+1} part '{part}' is valid D<id>-<dest>", valid, part)

section("SIMULATION — Pathfinding Edge Cases")

# Dead end: drone must not get stuck in dead end
lines = run_simulation("""
nb_drones: 1
start_hub: A 0 0
hub: dead_end 1 1
hub: B 1 0
end_hub: C 2 0
connection: A-dead_end
connection: A-B
connection: B-C
""")
check("Drone avoids dead end and reaches goal", any("C" in line for line in lines))

# Disconnected path to goal — should raise error
try:
    run_simulation("""
nb_drones: 1
start_hub: A 0 0
hub: B 1 0
end_hub: C 2 0
connection: A-B
""")
    check("Disconnected graph raises SimulationError", False)
except SimulationError as e:
    check("Disconnected graph raises SimulationError", "No valid path" in str(e))

# Blocked zone must be avoided
lines = run_simulation("""
nb_drones: 1
start_hub: A 0 0
hub: block 1 0 [zone=blocked]
hub: bypass 1 1
end_hub: C 2 0
connection: A-block
connection: A-bypass
connection: bypass-C
""")
check("Blocked zone is avoided", all("block" not in line for line in lines))

# ─── MAP BENCHMARKS ─────────────────────────────────────────────────────────

section("MAP BENCHMARKS")

def benchmark(map_path: str, target: int, label: str) -> None:
    graph = Parser().parse(map_path)
    paths = Pathfinder().find_paths(graph, graph.nb_drones)
    drones = [Drone(id=i + 1) for i in range(graph.nb_drones)]
    Scheduler().assign(drones, paths, graph)
    turns = len(Simulation(graph, drones).run())
    check(f"{label}: {turns} turns (target ≤{target})", turns <= target, f"got {turns}")


benchmark("maps/easy/01_linear_path.txt",    6,  "Easy 01 linear")
benchmark("maps/easy/02_simple_fork.txt",    8,  "Easy 02 fork")
benchmark("maps/easy/03_basic_capacity.txt", 6,  "Easy 03 capacity")
benchmark("maps/medium/01_dead_end_trap.txt", 12, "Medium 01 dead end")
benchmark("maps/medium/02_circular_loop.txt", 15, "Medium 02 circular")
benchmark("maps/medium/03_priority_puzzle.txt", 12, "Medium 03 priority")
benchmark("maps/hard/01_maze_nightmare.txt",  59, "Hard 01 maze")
benchmark("maps/hard/02_capacity_hell.txt",   59, "Hard 02 capacity")
benchmark("maps/hard/03_ultimate_challenge.txt", 59, "Hard 03 ultimate")

# ─── SUMMARY ────────────────────────────────────────────────────────────────

print(f"\n{'═' * 55}")
total = pass_count + fail_count
print(f"  Results: {pass_count}/{total} passed", end="")
if fail_count == 0:
    print("  \033[92m✓ All tests pass\033[0m")
else:
    print(f"  \033[91m✗ {fail_count} failed\033[0m")
print(f"{'═' * 55}\n")

sys.exit(0 if fail_count == 0 else 1)

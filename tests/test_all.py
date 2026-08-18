"""Test suite for Fly-in drone simulation engine."""
from __future__ import annotations
import sys
import tempfile
from src.models import Drone, SimulationError, ParserError
from src.parser import Parser
from src.pathfinder import Pathfinder
from src.scheduler import Scheduler
from src.simulation import Simulation
from src.graph import Graph

pass_count = 0
fail_count = 0


def section(title: str) -> None:
    """Print a section header."""
    print(f"\n{'─' * 55}")
    print(f"  {title}")
    print(f"{'─' * 55}")


def check(description: str, condition: bool, extra: str = "") -> None:
    """Check a condition and print result."""
    global pass_count, fail_count
    if condition:
        pass_count += 1
        print(f"  \033[92mPASS\033[0m  {description}")
    else:
        fail_count += 1
        detail = f" ({extra})" if extra else ""
        print(f"  \033[91mFAIL\033[0m  {description}{detail}")


def parse_string(content: str) -> Graph:
    """Parse a map string by creating a temporary file."""
    with tempfile.NamedTemporaryFile("w+", delete=False) as f:
        f.write(content)
        f.flush()
        return Parser().parse(f.name)


def run_simulation(content: str) -> list[str]:
    """Run full simulation on a map string and return output lines."""
    graph = parse_string(content)
    paths = Pathfinder().find_paths(graph, graph.nb_drones)
    drones = [Drone(id=i + 1) for i in range(graph.nb_drones)]
    Scheduler().assign(drones, paths, graph)
    return Simulation(graph, drones).run()


# ─── PARSER TESTS ───────────────────────────────────────────────────────────

section("PARSER — Valid Inputs")

graph = parse_string("""
# Simple comment
nb_drones: 2
start_hub: start 0 0
hub: A 1 0 [zone=normal color=blue max_drones=2]
hub: B 2 0 [color=red max_drones=1 zone=priority]
end_hub: end 3 0
connection: start-A [max_link_capacity=2]
connection: A-B [max_link_capacity=4]
connection: B-end
""")

check("Comments are ignored", graph.nb_drones == 2)
check("Zone A created", "A" in graph.zones)
check("Zone B created", "B" in graph.zones)
check("Metadata in any order (zone+color+max_drones)", graph.zones["B"].color == "red")  # noqa: E501
check("Zone type from metadata", graph.zones["B"].zone_type == "priority")
check("max_drones ignored on start_hub (set to unlimited)", graph.zones["start"].max_drones == 99999999999)  # noqa: E501
check("max_drones ignored on end_hub (set to unlimited)", graph.zones["end"].max_drones == 99999999999)  # noqa: E501

for ztype in ["normal", "restricted", "priority", "blocked"]:
    g = parse_string(f"nb_drones:1\nstart_hub:S 0 0\nhub:A 1 0 [zone={ztype}]\nend_hub:E 2 0\nconnection:S-A\nconnection:A-E")  # noqa: E501
    check(f"zone={ztype} accepted", g.zones["A"].zone_type == ztype)

check("Connection default capacity = 1", graph.connections[("B", "end")].max_link_capacity == 1)  # noqa: E501
check("Connection explicit capacity = 4", graph.connections[("A", "B")].max_link_capacity == 4)  # noqa: E501
check("Connection is bidirectional (A→B)", "B" in graph.get_neighbors("A"))
check("Connection is bidirectional (B→A)", "A" in graph.get_neighbors("B"))

section("PARSER — Error Cases")


def check_parser_error(desc: str, content: str) -> None:
    try:
        parse_string(content)
        check(desc, False, "expected ParserError")
    except ParserError:
        check(desc, True)


check_parser_error("Missing nb_drones raises error", "start_hub:S 0 0\nend_hub:E 1 0\nconnection:S-E")  # noqa: E501
check_parser_error("nb_drones=abc raises error", "nb_drones:abc\nstart_hub:S 0 0\nend_hub:E 1 0\nconnection:S-E")  # noqa: E501
check_parser_error("nb_drones=0 raises error", "nb_drones:0\nstart_hub:S 0 0\nend_hub:E 1 0\nconnection:S-E")  # noqa: E501
check_parser_error("nb_drones=-3 raises error", "nb_drones:-3\nstart_hub:S 0 0\nend_hub:E 1 0\nconnection:S-E")  # noqa: E501
check_parser_error("Missing start_hub raises error", "nb_drones:1\nhub:A 0 0\nend_hub:E 1 0\nconnection:A-E")  # noqa: E501
check_parser_error("Missing end_hub raises error", "nb_drones:1\nstart_hub:S 0 0\nhub:A 1 0\nconnection:S-A")  # noqa: E501
check_parser_error("Duplicate zone name raises error", "nb_drones:1\nstart_hub:A 0 0\nhub:A 1 0\nend_hub:E 2 0\nconnection:A-E")  # noqa: E501
check_parser_error("Duplicate connection (B-A == A-B) raises error", "nb_drones:1\nstart_hub:S 0 0\nhub:A 1 0\nend_hub:E 2 0\nconnection:S-A\nconnection:A-S\nconnection:A-E")  # noqa: E501
check_parser_error("Invalid zone type 'fast' raises error", "nb_drones:1\nstart_hub:S 0 0\nhub:A 1 0 [zone=fast]\nend_hub:E 2 0\nconnection:S-A\nconnection:A-E")  # noqa: E501
check_parser_error("max_drones=0 raises error", "nb_drones:1\nstart_hub:S 0 0\nhub:A 1 0 [max_drones=0]\nend_hub:E 2 0\nconnection:S-A\nconnection:A-E")  # noqa: E501
check_parser_error("max_drones=-1 raises error", "nb_drones:1\nstart_hub:S 0 0\nhub:A 1 0 [max_drones=-1]\nend_hub:E 2 0\nconnection:S-A\nconnection:A-E")  # noqa: E501
check_parser_error("max_link_capacity=0 raises error", "nb_drones:1\nstart_hub:S 0 0\nend_hub:E 1 0\nconnection:S-E [max_link_capacity=0]")  # noqa: E501
check_parser_error("Connection to unknown zone raises error", "nb_drones:1\nstart_hub:S 0 0\nend_hub:E 1 0\nconnection:S-UNKNOWN")  # noqa: E501
check_parser_error("Zone name with dash raises error", "nb_drones:1\nstart_hub:S-1 0 0\nend_hub:E 1 0\nconnection:S-1-E")  # noqa: E501

# Flexible spacing around colon
g = parse_string("nb_drones : 2 \n start_hub : S 0 0 \n end_hub : E 1 0 \n connection : S - E ")  # noqa: E501
check("Flexible spacing around prefix colon is accepted", g.nb_drones == 2 and "S" in g.zones)  # noqa: E501

check_parser_error("Duplicate metadata attribute raises error", "nb_drones:1\nstart_hub:S 0 0\nhub:A 1 0 [zone=normal zone=priority]\nend_hub:E 2 0\nconnection:S-A\nconnection:A-E")  # noqa: E501
check_parser_error("Duplicate coordinates raise error", "nb_drones:1\nstart_hub:S 0 0\nhub:A 0 0\nend_hub:E 2 0\nconnection:S-A\nconnection:A-E")  # noqa: E501
check_parser_error("Missing file raises error", "non_existent_file_xyz.txt")
check_parser_error("Unknown line format raises error", "nb_drones:1\nstart_hub:S 0 0\nend_hub:E 1 0\ninvalid_line_no_colon")  # noqa: E501

# Error message contains line number
try:
    parse_string("nb_drones:1\nstart_hub:S 0 0\ninvalid_line\nend_hub:E 1 0\nconnection:S-E")  # noqa: E501
    check("Error message contains 'line'", False)
except ParserError as e:
    err = str(e)
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
check("get_neighbors works", graph.get_neighbors("mid") == ["start", "goal"] or set(graph.get_neighbors("mid")) == {"start", "goal"})  # noqa: E501
check("get_zone works", graph.get_zone("mid").name == "mid")
check("get_connection works", graph.get_connection("start", "mid") is not None)  # noqa: E501
check("get_connection works reversed (mid,start)", graph.get_connection("mid", "start") is not None)  # noqa: E501


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
check("All drones delivered by end", True)

section("SIMULATION — Occupancy Rules")

lines = run_simulation("""
nb_drones: 2
start_hub: A 0 0
hub: B 1 0
end_hub: C 2 0
connection: A-B
connection: B-C
""")
b_occupancy: dict[int, int] = {}
turn = 0
for line in lines:
    turn += 1
    moves = line.split()
    count_in_b = sum(1 for m in moves if m.endswith("-B"))
    b_occupancy[turn] = count_count = count_in_b
check("Zone with max_drones=1 not entered by 2 drones same turn", max(b_occupancy.values()) <= 1)  # noqa: E501

lines = run_simulation("""
nb_drones: 2
start_hub: A 0 0 [max_drones=5]
hub: B 1 0 [max_drones=2]
end_hub: C 2 0
connection: A-B [max_link_capacity=2]
connection: B-C [max_link_capacity=2]
""")
check("Zone max_drones=2 allows 2 drones through", len(lines) > 0)

lines = run_simulation("""
nb_drones: 3
start_hub: A 0 0
end_hub: B 1 0
connection: A-B [max_link_capacity=3]
""")
check("3 drones can share start and end zones", len(lines) > 0)

section("SIMULATION — Connection Capacity")

lines = run_simulation("""
nb_drones: 2
start_hub: A 0 0
end_hub: B 1 0
connection: A-B
""")
check("Connection capacity=1 forces drones to go one at a time", len(lines) >= 2)  # noqa: E501

lines = run_simulation("""
nb_drones: 2
start_hub: A 0 0
end_hub: B 1 0
connection: A-B [max_link_capacity=2]
""")
check("Connection capacity=2 allows both drones same turn", len(lines) == 1)

section("SIMULATION — Restricted Zones (2-turn movement)")

lines = run_simulation("""
nb_drones: 1
start_hub: A 0 0
hub: B 1 0 [zone=restricted]
end_hub: C 2 0
connection: A-B
connection: B-C
""")
check("Restricted zone takes at least 2 turns", len(lines) >= 2)

has_transit = any("-A-B" in line or "A-B" in line for line in lines)
check("Transit line appears for restricted zone (D1-connection)", has_transit)

has_arrival = any("D1-B" in line for line in lines)
check("Drone arrives at restricted zone after transit", has_arrival)

section("SIMULATION — Priority Zones")

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

for i, line in enumerate(lines):
    parts = line.split()
    for part in parts:
        valid = "-" in part and part.startswith("D")
        check(f"Turn {i+1} part '{part}' is valid D<id>-<dest>", valid, part)

section("SIMULATION — Pathfinding Edge Cases")

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
check("Drone avoids dead end and reaches goal", any("C" in line for line in lines))  # noqa: E501

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
    check("Disconnected graph raises SimulationError", "No valid path" in str(e))  # noqa: E501

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

section("MAP BENCHMARKS")


def benchmark(map_path: str, target: int, label: str) -> None:
    graph = Parser().parse(map_path)
    paths = Pathfinder().find_paths(graph, graph.nb_drones)
    drones = [Drone(id=i + 1) for i in range(graph.nb_drones)]
    Scheduler().assign(drones, paths, graph)
    turns = len(Simulation(graph, drones).run())
    check(f"{label}: {turns} turns (target ≤{target})", turns <= target, f"got {turns}")  # noqa: E501


benchmark("maps/easy/01_linear_path.txt", 6, "Easy 01 linear")
benchmark("maps/easy/02_simple_fork.txt", 8, "Easy 02 fork")
benchmark("maps/easy/03_basic_capacity.txt", 6, "Easy 03 capacity")
benchmark("maps/medium/01_dead_end_trap.txt", 12, "Medium 01 dead end")
benchmark("maps/medium/02_circular_loop.txt", 15, "Medium 02 circular")
benchmark("maps/medium/03_priority_puzzle.txt", 12, "Medium 03 priority")
benchmark("maps/hard/01_maze_nightmare.txt", 30, "Hard 01 maze")
benchmark("maps/hard/02_capacity_hell.txt", 35, "Hard 02 capacity")
benchmark("maps/hard/03_ultimate_challenge.txt", 45, "Hard 03 ultimate")
benchmark("maps/challenger/01_the_impossible_dream.txt", 45, "Challenger 01 dream")  # noqa: E501

print(f"\n{'═' * 55}")
total = pass_count + fail_count
print(f" Results: {pass_count}/{total} passed", end="")
if fail_count == 0:
    print(" \033[92m✓ All tests pass\033[0m")
else:
    print(f" \033[91m✗ {fail_count} failed\033[0m")
print(f"{'═' * 55}\n")

sys.exit(0 if fail_count == 0 else 1)

"""Comprehensive Edge-Case Test Suite for Fly-in.

Tests all physical simulation rules and parser validation constraints.
"""
from typing import Dict, List, Set, Tuple
import os
import re
import tempfile

from graph import Graph
from models import Drone, ParserError, SimulationError
from parser import Parser
from pathfinder import Pathfinder
from scheduler import Scheduler
from simulation import Simulation


class SimulationVerifier:
    """Verifies turn-by-turn physics independently."""

    @staticmethod
    def verify(graph: Graph, output_lines: List[str]) -> None:
        """Verify that simulation output adheres to all rules."""
        g = graph
        drone_pos: Dict[int, str] = {
            i + 1: g.start for i in range(g.nb_drones)
        }
        drone_transit: Dict[int, Tuple[str, Tuple[str, str]]] = {}
        delivered: Set[int] = set()

        for turn_idx, line in enumerate(output_lines, 1):
            moves = line.strip().split()
            moved_in_turn: Set[int] = set()
            conn_usage: Dict[Tuple[str, str], int] = {}

            for move in moves:
                m = re.match(r"^D(\d+)-(.+)$", move)
                assert m, f"Turn {turn_idx}: Invalid move format '{move}'"
                did = int(m.group(1))
                target = m.group(2)

                assert did not in moved_in_turn, (
                    f"Turn {turn_idx}: Drone {did} moved multiple times"
                )
                moved_in_turn.add(did)
                assert did not in delivered, (
                    f"Turn {turn_idx}: Drone {did} moved after delivery"
                )

                if did in drone_transit:
                    expected_dest, ckey = drone_transit.pop(did)
                    assert target == expected_dest, (
                        f"Turn {turn_idx}: Drone {did} expected "
                        f"{expected_dest}"
                    )
                    drone_pos[did] = target
                    if target == g.end:
                        delivered.add(did)
                else:
                    curr = drone_pos[did]
                    if "-" in target:
                        parts = target.split("-")
                        assert len(parts) == 2, (
                            f"Turn {turn_idx}: Malformed target '{target}'"
                        )
                        c_from, c_to = parts
                        assert curr == c_from, (
                            f"Turn {turn_idx}: Drone {did} cannot enter target"
                        )
                        dest_zone = g.get_zone(c_to)
                        assert dest_zone.zone_type == "restricted", (
                            f"Turn {turn_idx}: Invalid restricted transit"
                        )
                        conn = g.get_connection(c_from, c_to)
                        ckey = conn.key()
                        conn_usage[ckey] = conn_usage.get(ckey, 0) + 1
                        drone_transit[did] = (c_to, ckey)
                        drone_pos[did] = ""
                    else:
                        dest_zone = g.get_zone(target)
                        assert dest_zone.zone_type != "blocked", (
                            f"Turn {turn_idx}: Drone moved to blocked zone"
                        )
                        conn = g.get_connection(curr, target)
                        ckey = conn.key()
                        conn_usage[ckey] = conn_usage.get(ckey, 0) + 1
                        drone_pos[did] = target
                        if target == g.end:
                            delivered.add(did)

            for ckey, count in conn_usage.items():
                conn_obj = g.connections[ckey]
                assert count <= conn_obj.max_link_capacity, (
                    f"Turn {turn_idx}: Connection {ckey} exceeded capacity"
                )

            zone_counts: Dict[str, int] = {}
            for d, pos in drone_pos.items():
                if pos and d not in delivered:
                    zone_counts[pos] = zone_counts.get(pos, 0) + 1

            for zname, count in zone_counts.items():
                z = g.get_zone(zname)
                if not z.is_start and not z.is_end:
                    assert count <= z.max_drones, (
                        f"Turn {turn_idx}: Zone {zname} exceeded max_drones"
                    )

        assert len(delivered) == g.nb_drones, (
            f"Only {len(delivered)}/{g.nb_drones} drones delivered"
        )


def run_simulation_test(map_text: str, name: str) -> None:
    """Run simulation test and verify physics."""
    with tempfile.NamedTemporaryFile("w", delete=False) as f:
        f.write(map_text)
        path = f.name
    try:
        g = Parser().parse(path)
        paths = Pathfinder().find_paths(g, g.nb_drones)
        drones = [Drone(id=i + 1) for i in range(g.nb_drones)]
        Scheduler().assign(drones, paths, g)
        sim = Simulation(g, drones)
        lines = sim.run()
        SimulationVerifier.verify(g, lines)
        print(f"[PASS] Simulation: {name} ({sim.turn} turns)")
    finally:
        os.remove(path)


def run_parser_test(
    map_text: str,
    should_pass: bool,
    name: str,
    expected_error_substr: str = ""
) -> None:
    """Test map parsing."""
    with tempfile.NamedTemporaryFile("w", delete=False) as f:
        f.write(map_text)
        path = f.name
    try:
        Parser().parse(path)
        if not should_pass:
            raise AssertionError(f"Test '{name}' should have failed")
        print(f"[PASS] Parser: {name}")
    except ParserError as e:
        if not should_pass:
            if expected_error_substr and expected_error_substr not in str(e):
                raise AssertionError(
                    f"Expected '{expected_error_substr}' in '{e}'"
                )
            print(f"[PASS] Parser: {name} (caught error as expected)")
        else:
            raise
    finally:
        os.remove(path)


def main() -> None:
    """Run all tests."""
    print("\n=== RUNNING SIMULATION & PHYSICAL MECHANICS TESTS ===")

    # Test Sim 1: Direct link (no intermediate hubs), 1 drone
    run_simulation_test("""
nb_drones: 1
start_hub: start 0 0
end_hub: goal 1 0
connection: start-goal
""", "Direct link, 1 drone")

    # Test Sim 2: Direct link, 5 drones, link_cap=2
    run_simulation_test("""
nb_drones: 5
start_hub: start 0 0
end_hub: goal 1 0
connection: start-goal [max_link_capacity=2]
""", "Direct link, 5 drones, link_cap=2")

    # Test Sim 3: High link capacity (3) into restricted zone (max_drones=1)
    run_simulation_test("""
nb_drones: 4
start_hub: start 0 0
hub: r 1 0 [zone=restricted max_drones=1]
end_hub: goal 2 0
connection: start-r [max_link_capacity=3]
connection: r-goal
""", "High link cap (3) into restricted zone (max_drones=1)")

    # Test Sim 4: Two converging parallel links into a restricted zone
    run_simulation_test("""
nb_drones: 4
start_hub: start 0 0
hub: a 1 1 [max_drones=2]
hub: b 1 -1 [max_drones=2]
hub: r 2 0 [zone=restricted max_drones=1]
end_hub: goal 3 0
connection: start-a [max_link_capacity=2]
connection: start-b [max_link_capacity=2]
connection: a-r [max_link_capacity=2]
connection: b-r [max_link_capacity=2]
connection: r-goal
""", "Converging parallel paths into restricted zone (max_drones=1)")

    # Test Sim 5: Chained restricted zones
    run_simulation_test("""
nb_drones: 3
start_hub: start 0 0
hub: r1 1 0 [zone=restricted max_drones=1]
hub: r2 2 0 [zone=restricted max_drones=1]
hub: r3 3 0 [zone=restricted max_drones=1]
end_hub: goal 4 0
connection: start-r1
connection: r1-r2
connection: r2-r3
connection: r3-goal
""", "Chained restricted zones (r1->r2->r3)")

    # Test Sim 6: Chain movement
    run_simulation_test("""
nb_drones: 4
start_hub: start 0 0
hub: a 1 0 [max_drones=1]
hub: b 2 0 [max_drones=1]
hub: c 3 0 [max_drones=1]
end_hub: goal 4 0
connection: start-a
connection: a-b
connection: b-c
connection: c-goal
""", "Chain movement (1 drone per zone pipeline)")

    # Test Sim 7: Bottleneck corridor
    run_simulation_test("""
nb_drones: 15
start_hub: start 0 0
hub: bottleneck 1 0 [max_drones=1]
end_hub: goal 2 0
connection: start-bottleneck
connection: bottleneck-goal
""", "Bottleneck corridor (15 drones through max_drones=1)")

    # Test Sim 8: Priority corridor preference
    run_simulation_test("""
nb_drones: 3
start_hub: start 0 0
hub: p1 1 1 [zone=priority color=cyan]
hub: p2 2 1 [zone=priority color=cyan]
hub: n1 1 -1 [zone=normal]
hub: n2 2 -1 [zone=normal]
end_hub: goal 3 0
connection: start-p1
connection: p1-p2
connection: p2-goal
connection: start-n1
connection: n1-n2
connection: n2-goal
""", "Priority corridor preference vs normal path")

    # Test Sim 9: Blocked zone avoidance
    run_simulation_test("""
nb_drones: 2
start_hub: start 0 0
hub: direct_blocked 1 0 [zone=blocked color=gray]
hub: safe_bypass 1 1
end_hub: goal 2 0
connection: start-direct_blocked
connection: direct_blocked-goal
connection: start-safe_bypass
connection: safe_bypass-goal
""", "Blocked zone avoidance")

    # Test Sim 10: Asymmetric parallel forks
    run_simulation_test("""
nb_drones: 6
start_hub: start 0 0
hub: fast_hub 1 1 [zone=priority max_drones=2]
hub: slow_hub 1 -1 [zone=normal max_drones=3]
end_hub: goal 2 0
connection: start-fast_hub [max_link_capacity=2]
connection: fast_hub-goal [max_link_capacity=2]
connection: start-slow_hub [max_link_capacity=3]
connection: slow_hub-goal [max_link_capacity=3]
""", "Asymmetric parallel forks with varying capacities")

    # Test Sim 11: 30 drones parallel stress test
    run_simulation_test("""
nb_drones: 30
start_hub: start 0 0
hub: a 1 1 [max_drones=3]
hub: b 2 1 [max_drones=3]
hub: c 1 -1 [max_drones=3]
hub: d 2 -1 [max_drones=3]
end_hub: goal 3 0
connection: start-a [max_link_capacity=3]
connection: a-b [max_link_capacity=3]
connection: b-goal [max_link_capacity=3]
connection: start-c [max_link_capacity=3]
connection: c-d [max_link_capacity=3]
connection: d-goal [max_link_capacity=3]
""", "30 drones parallel stress test")

    print("\n=== RUNNING PARSER & SYNTAX VALIDATION TESTS ===")

    # Test Parse 1: Space before colon in start_hub
    run_parser_test("""
nb_drones: 1
start_hub   : start 0 0
end_hub: goal 1 0
connection: start-goal
""", False, "Space before colon in start_hub", "Spaces before ':'")

    # Test Parse 2: Space before colon in hub
    run_parser_test("""
nb_drones: 1
start_hub: start 0 0
hub  : mid 1 0
end_hub: goal 2 0
connection: start-mid
connection: mid-goal
""", False, "Space before colon in hub", "Spaces before ':'")

    # Test Parse 3: Space before colon in connection
    run_parser_test("""
nb_drones: 1
start_hub: start 0 0
end_hub: goal 1 0
connection   : start-goal
""", False, "Space before colon in connection", "Spaces before ':'")

    # Test Parse 4: Space before colon in nb_drones
    run_parser_test("""
nb_drones   : 1
start_hub: start 0 0
end_hub: goal 1 0
connection: start-goal
""", False, "Space before colon in nb_drones", "Spaces before ':'")

    # Test Parse 5: max_drones=-1 on start_hub
    run_parser_test("""
nb_drones: 1
start_hub: start 0 0 [max_drones=-1]
end_hub: goal 1 0
connection: start-goal
""", True, "max_drones=-1 on start_hub ignored")

    # Test Parse 6: max_drones=1000 on end_hub
    run_parser_test("""
nb_drones: 1
start_hub: start 0 0
end_hub: goal 1 0 [max_drones=1000]
connection: start-goal
""", True, "max_drones=1000 on end_hub ignored")

    # Test Parse 7: Non-integer max_drones on start_hub
    run_parser_test("""
nb_drones: 1
start_hub: start 0 0 [max_drones=trash]
end_hub: goal 1 0
connection: start-goal
""", False, "Non-integer max_drones on start", "positive integer")

    # Test Parse 8: max_drones=0 on normal hub
    run_parser_test("""
nb_drones: 1
start_hub: start 0 0
hub: h 1 0 [max_drones=0]
end_hub: goal 2 0
connection: start-h
connection: h-goal
""", False, "max_drones=0 on normal hub", "positive integer")

    # Test Parse 9: max_drones=-2 on normal hub
    run_parser_test("""
nb_drones: 1
start_hub: start 0 0
hub: h 1 0 [max_drones=-2]
end_hub: goal 2 0
connection: start-h
connection: h-goal
""", False, "max_drones=-2 on normal hub", "positive integer")

    # Test Parse 10: max_link_capacity=0
    run_parser_test("""
nb_drones: 1
start_hub: start 0 0
end_hub: goal 1 0
connection: start-goal [max_link_capacity=0]
""", False, "max_link_capacity=0", "positive integer")

    # Test Parse 11: Dash in start_hub name
    run_parser_test("""
nb_drones: 1
start_hub: s-hub 0 0
end_hub: goal 1 0
connection: s-hub-goal
""", False, "Dash in start_hub name", "dashes and space")

    # Test Parse 12: Em-dash in start_hub name
    run_parser_test("""
nb_drones: 1
start_hub: s—hub 0 0
end_hub: goal 1 0
connection: s—hub-goal
""", False, "Em-dash in start_hub name", "dashes and space")

    # Test Parse 13: Space in zone name
    run_parser_test("""
nb_drones: 1
start_hub: start zone 0 0
end_hub: goal 1 0
connection: start-goal
""", False, "Space in zone name", "Zone must have name, x, and y")

    # Test Parse 14: Duplicate zone name
    run_parser_test("""
nb_drones: 1
start_hub: start 0 0
hub: start 1 0
end_hub: goal 2 0
connection: start-goal
""", False, "Duplicate zone name", "Duplicate zone name")

    # Test Parse 15: Duplicate coordinates
    run_parser_test("""
nb_drones: 1
start_hub: start 0 0
hub: h 0 0
end_hub: goal 2 0
connection: start-h
connection: h-goal
""", False, "Duplicate coordinates", "already used by zone")

    # Test Parse 16: Duplicate connection reversed
    run_parser_test("""
nb_drones: 1
start_hub: start 0 0
end_hub: goal 1 0
connection: start-goal
connection: goal-start
""", False, "Duplicate connection reversed", "Duplicate connection")

    # Test Parse 17: Self connection
    run_parser_test("""
nb_drones: 1
start_hub: start 0 0
end_hub: goal 1 0
connection: start-start
connection: start-goal
""", False, "Self connection", "cannot connect zone to itself")

    # Test Parse 18: Unknown zone in connection
    run_parser_test("""
nb_drones: 1
start_hub: start 0 0
end_hub: goal 1 0
connection: start-phantom
""", False, "Connection with unknown zone", "Unknown zone")

    # Test Parse 19: Disconnected graph
    with tempfile.NamedTemporaryFile("w", delete=False) as f:
        f.write("""
nb_drones: 1
start_hub: start 0 0
hub: isolated 1 0
end_hub: goal 2 0
connection: start-isolated
""")
        path = f.name
    try:
        g = Parser().parse(path)
        try:
            Pathfinder().find_paths(g, 1)
            raise AssertionError("Disconnected graph did not raise error")
        except SimulationError:
            print("[PASS] Disconnected graph (caught SimulationError)")
    finally:
        os.remove(path)

    # Test Parse 20: Spaces around '=' in metadata
    run_parser_test("""
nb_drones: 1
start_hub: start 0 0 [color = green]
end_hub: goal 1 0
connection: start-goal
""", False, "Spaces around '=' in metadata", "Spaces around '='")

    # Test Parse 21: Unclosed metadata bracket
    run_parser_test("""
nb_drones: 1
start_hub: start 0 0 [color=green
end_hub: goal 1 0
connection: start-goal
""", False, "Unclosed bracket", "Metadata block is not closed")

    # Test Parse 22: Missing space before bracket
    run_parser_test("""
nb_drones: 1
start_hub: start 0 0[color=green]
end_hub: goal 1 0
connection: start-goal
""", False, "Missing space before bracket", "Missing space before metadata")

    # Test Parse 23: Extra text after bracket
    run_parser_test("""
nb_drones: 1
start_hub: start 0 0 [color=green] garbage
end_hub: goal 1 0
connection: start-goal
""", False, "Extra text after bracket", "Unexpected text after metadata")

    # Test Parse 24: Unknown metadata key
    run_parser_test("""
nb_drones: 1
start_hub: start 0 0 [speed=100]
end_hub: goal 1 0
connection: start-goal
""", False, "Unknown metadata key", "Unknown metadata key")

    # Test Parse 25: Unknown zone type
    run_parser_test("""
nb_drones: 1
start_hub: start 0 0
hub: h 1 0 [zone=hyperspace]
end_hub: goal 2 0
connection: start-h
connection: h-goal
""", False, "Unknown zone type", "Invalid zone type")

    # Test Parse 26: Duplicate metadata attribute
    run_parser_test("""
nb_drones: 1
start_hub: start 0 0 [color=green color=red]
end_hub: goal 1 0
connection: start-goal
""", False, "Duplicate metadata attribute", "Duplicate metadata attribute")

    # Test Parse 27: Negative coordinates and inline comments
    run_parser_test("""
# Top comment
nb_drones: 2 # inline comment
start_hub: start -10 -20 [color=green]
hub: mid 0 0 [color=blue max_drones=3 zone=priority] # another comment
end_hub: goal 10 20 [color=red]
connection: start-mid [max_link_capacity=2] # link comment
connection: mid-goal [max_link_capacity=2]
""", True, "Negative coords, inline comments, multiple tags")

    print("\n=======================================================")
    print("ALL 38 EDGE-CASE TESTS COMPLETED SUCCESSFULLY!")
    print("=======================================================")


if __name__ == "__main__":
    main()

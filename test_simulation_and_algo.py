"""Intensive Simulation & Algorithm Test Suite for Fly-in.

Tests complex graph topologies, capacity limits, restricted zone dynamics,
bottlenecks, priority routing, deadlock avoidance, and large fleets.
"""
from typing import Dict, List, Set, Tuple
import os
import re
import tempfile

from graph import Graph
from models import Drone
from parser import Parser
from pathfinder import Pathfinder
from scheduler import Scheduler
from simulation import Simulation


class StrictSimulationVerifier:
    """Verifies that EVERY movement rule is respected at EVERY turn."""

    @staticmethod
    def verify(graph: Graph, output_lines: List[str]) -> int:
        """Verify turn-by-turn physics."""
        drone_pos: Dict[int, str] = {
            i + 1: graph.start for i in range(graph.nb_drones)
        }
        drone_transit: Dict[int, Tuple[str, Tuple[str, str]]] = {}
        delivered: Set[int] = set()

        for turn_idx, line in enumerate(output_lines, 1):
            moves = line.strip().split()
            assert moves, f"Turn {turn_idx}: Line is empty"
            moved_in_turn: Set[int] = set()
            conn_usage: Dict[Tuple[str, str], int] = {}

            for move in moves:
                m = re.match(r"^D(\d+)-(.+)$", move)
                assert m, f"Turn {turn_idx}: Invalid move syntax '{move}'"
                did = int(m.group(1))
                target = m.group(2)

                assert did not in moved_in_turn, (
                    f"Turn {turn_idx}: Drone {did} moved twice in same turn!"
                )
                moved_in_turn.add(did)

                assert did not in delivered, (
                    f"Turn {turn_idx}: Drone {did} moved after "
                    f"being delivered!"
                )

                if did in drone_transit:
                    expected_dest, ckey = drone_transit.pop(did)
                    assert target == expected_dest, (
                        f"Turn {turn_idx}: Drone {did} expected "
                        f"'{expected_dest}', got '{target}'!"
                    )
                    drone_pos[did] = target
                    if target == graph.end:
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
                            f"Turn {turn_idx}: Drone {did} at '{curr}' "
                            f"cannot enter '{target}'"
                        )
                        dest_zone = graph.get_zone(c_to)
                        assert dest_zone.zone_type == "restricted", (
                            f"Turn {turn_idx}: '{target}' used for "
                            f"non-restricted zone!"
                        )
                        conn = graph.get_connection(c_from, c_to)
                        ckey = conn.key()
                        conn_usage[ckey] = conn_usage.get(ckey, 0) + 1
                        drone_transit[did] = (c_to, ckey)
                        drone_pos[did] = ""
                    else:
                        dest_zone = graph.get_zone(target)
                        assert dest_zone.zone_type != "blocked", (
                            f"Turn {turn_idx}: Drone entered BLOCKED zone!"
                        )
                        conn = graph.get_connection(curr, target)
                        ckey = conn.key()
                        conn_usage[ckey] = conn_usage.get(ckey, 0) + 1
                        drone_pos[did] = target
                        if target == graph.end:
                            delivered.add(did)

            for ckey, usage in conn_usage.items():
                conn_obj = graph.connections[ckey]
                assert usage <= conn_obj.max_link_capacity, (
                    f"Turn {turn_idx}: Link {ckey} exceeded capacity! "
                    f"({usage} > {conn_obj.max_link_capacity})"
                )

            zone_counts: Dict[str, int] = {}
            for d, pos in drone_pos.items():
                if pos and d not in delivered:
                    zone_counts[pos] = zone_counts.get(pos, 0) + 1

            for zname, count in zone_counts.items():
                z = graph.get_zone(zname)
                if not z.is_start and not z.is_end:
                    assert count <= z.max_drones, (
                        f"Turn {turn_idx}: Zone '{zname}' exceeded "
                        f"capacity! ({count} > {z.max_drones})"
                    )

        assert not drone_transit, (
            f"Drones {list(drone_transit.keys())} stuck in transit!"
        )
        assert len(delivered) == graph.nb_drones, (
            f"Only {len(delivered)}/{graph.nb_drones} drones arrived at goal!"
        )
        return len(output_lines)


def run_test(
    map_text: str, test_name: str, expected_max_turns: int = 100
) -> int:
    """Run a single test case."""
    with tempfile.NamedTemporaryFile("w", delete=False) as f:
        f.write(map_text.strip())
        path = f.name
    try:
        g = Parser().parse(path)
        paths = Pathfinder().find_paths(g, g.nb_drones)
        assert len(paths) > 0, f"Pathfinder found 0 paths for '{test_name}'"
        drones = [Drone(id=i + 1) for i in range(g.nb_drones)]
        Scheduler().assign(drones, paths, g)
        sim = Simulation(g, drones)
        lines = sim.run()
        turns = StrictSimulationVerifier.verify(g, lines)
        assert turns <= expected_max_turns, (
            f"'{test_name}' took {turns} turns (max {expected_max_turns})"
        )
        print(
            f"[PASS] {test_name}: {turns} turns "
            f"(paths: {len(paths)}, drones: {g.nb_drones})"
        )
        return turns
    finally:
        os.remove(path)


def main() -> None:
    """Run all simulation and algorithm test cases."""
    print("=" * 65)
    print("STARTING INTENSIVE SIMULATION & ALGORITHM TESTS")
    print("=" * 65 + "\n")

    # TEST 1: Direct Start to End (No intermediate hubs)
    run_test("""
nb_drones: 8
start_hub: start 0 0
end_hub: goal 1 0
connection: start-goal [max_link_capacity=3]
""", "Test 1: Direct link (8 drones, link cap 3)", 5)

    # TEST 2: Single Drone Minimal Path
    run_test("""
nb_drones: 1
start_hub: start 0 0
hub: a 1 0
hub: b 2 0
end_hub: goal 3 0
connection: start-a
connection: a-b
connection: b-goal
""", "Test 2: Single drone linear traversal", 3)

    # TEST 3: User's Case - High Link Cap (4) into Restricted Zone (Cap 1)
    run_test("""
nb_drones: 5
start_hub: start 0 0
hub: r 1 0 [zone=restricted max_drones=1]
end_hub: goal 2 0
connection: start-r [max_link_capacity=4]
connection: r-goal
""", "Test 3: High link cap (4) into restricted zone (cap 1)", 12)

    # TEST 4: Three Parallel Branches Converging on a Restricted Zone (Cap 2)
    run_test("""
nb_drones: 6
start_hub: start 0 0
hub: branch1 1 2 [max_drones=2]
hub: branch2 1 0 [max_drones=2]
hub: branch3 1 -2 [max_drones=2]
hub: r_converge 2 0 [zone=restricted max_drones=2]
end_hub: goal 3 0
connection: start-branch1 [max_link_capacity=2]
connection: start-branch2 [max_link_capacity=2]
connection: start-branch3 [max_link_capacity=2]
connection: branch1-r_converge [max_link_capacity=2]
connection: branch2-r_converge [max_link_capacity=2]
connection: branch3-r_converge [max_link_capacity=2]
connection: r_converge-goal [max_link_capacity=2]
""", "Test 4: 3 parallel branches converging on restricted zone (cap 2)", 12)

    # TEST 5: Deep Chained Restricted Zones (R1 -> R2 -> R3 -> R4)
    run_test("""
nb_drones: 3
start_hub: start 0 0
hub: r1 1 0 [zone=restricted max_drones=1]
hub: r2 2 0 [zone=restricted max_drones=1]
hub: r3 3 0 [zone=restricted max_drones=1]
hub: r4 4 0 [zone=restricted max_drones=1]
end_hub: goal 5 0
connection: start-r1
connection: r1-r2
connection: r2-r3
connection: r3-r4
connection: r4-goal
""", "Test 5: Deep chained restricted zones (R1->R2->R3->R4)", 15)

    # TEST 6: Single-File Chain Movement (1 drone per zone pipeline)
    run_test("""
nb_drones: 6
start_hub: start 0 0
hub: p1 1 0 [max_drones=1]
hub: p2 2 0 [max_drones=1]
hub: p3 3 0 [max_drones=1]
hub: p4 4 0 [max_drones=1]
end_hub: goal 5 0
connection: start-p1
connection: p1-p2
connection: p2-p3
connection: p3-p4
connection: p4-goal
""", "Test 6: Single-file pipeline chain movement (6 drones, cap 1 each)", 10)

    # TEST 7: Diamond Graph Balancing (Priority vs Normal vs Restricted)
    run_test("""
nb_drones: 12
start_hub: start 0 0
hub: prio1 1 2 [zone=priority max_drones=2 color=cyan]
hub: prio2 2 2 [zone=priority max_drones=2 color=cyan]
hub: norm1 1 0 [zone=normal max_drones=3 color=blue]
hub: norm2 2 0 [zone=normal max_drones=3 color=blue]
hub: restr1 1 -2 [zone=restricted max_drones=4 color=red]
hub: restr2 2 -2 [zone=restricted max_drones=4 color=red]
end_hub: goal 3 0
connection: start-prio1 [max_link_capacity=2]
connection: prio1-prio2 [max_link_capacity=2]
connection: prio2-goal [max_link_capacity=2]
connection: start-norm1 [max_link_capacity=3]
connection: norm1-norm2 [max_link_capacity=3]
connection: norm2-goal [max_link_capacity=3]
connection: start-restr1 [max_link_capacity=4]
connection: restr1-restr2 [max_link_capacity=4]
connection: restr2-goal [max_link_capacity=4]
""", "Test 7: Diamond load balancing (Priority vs Normal vs Restricted)", 15)

    # TEST 8: Central Bottleneck Star Topology
    run_test("""
nb_drones: 6
start_hub: start 0 0
hub: in1 1 1 [max_drones=2]
hub: in2 1 -1 [max_drones=2]
hub: central_eye 2 0 [max_drones=1 color=orange]
hub: out1 3 1 [max_drones=2]
hub: out2 3 -1 [max_drones=2]
end_hub: goal 4 0
connection: start-in1 [max_link_capacity=2]
connection: start-in2 [max_link_capacity=2]
connection: in1-central_eye
connection: in2-central_eye
connection: central_eye-out1
connection: central_eye-out2
connection: out1-goal [max_link_capacity=2]
connection: out2-goal [max_link_capacity=2]
""", "Test 8: Central bottleneck star hub (max_drones=1 in center)", 12)

    # TEST 9: Attractive Dead-End Trap
    run_test("""
nb_drones: 4
start_hub: start 0 0
hub: trap_prio1 1 2 [zone=priority color=cyan]
hub: trap_prio2 2 2 [zone=priority color=cyan]
hub: trap_dead 3 2 [max_drones=1 color=black]
hub: real1 1 0 [zone=normal color=green]
hub: real2 2 0 [zone=normal color=green]
end_hub: goal 3 0
connection: start-trap_prio1
connection: trap_prio1-trap_prio2
connection: trap_prio2-trap_dead
connection: start-real1
connection: real1-real2
connection: real2-goal
""", "Test 9: Attractive dead-end trap with priority lures", 8)

    # TEST 10: Circular Loop with Restricted Shortcut
    run_test("""
nb_drones: 5
start_hub: start 0 0
hub: c1 1 1 [max_drones=2]
hub: c2 2 1 [max_drones=2]
hub: c3 3 1 [max_drones=2]
hub: shortcut 2 0 [zone=restricted max_drones=1]
end_hub: goal 4 0
connection: start-c1 [max_link_capacity=2]
connection: c1-c2 [max_link_capacity=2]
connection: c2-c3 [max_link_capacity=2]
connection: c3-goal [max_link_capacity=2]
connection: start-shortcut
connection: shortcut-goal
""", "Test 10: Circular loop with restricted shortcut", 15)

    # TEST 11: Blocked Zone Squeeze (Blocked zones forcing detours)
    run_test("""
nb_drones: 4
start_hub: start 0 0
hub: b1 1 0 [zone=blocked]
hub: b2 2 0 [zone=blocked]
hub: b3 3 0 [zone=blocked]
hub: detour_up1 1 1 [max_drones=2]
hub: detour_up2 2 1 [max_drones=2]
hub: detour_up3 3 1 [max_drones=2]
hub: detour_dn1 1 -1 [max_drones=2]
hub: detour_dn2 2 -1 [max_drones=2]
hub: detour_dn3 3 -1 [max_drones=2]
end_hub: goal 4 0
connection: start-b1
connection: b1-b2
connection: b2-b3
connection: b3-goal
connection: start-detour_up1 [max_link_capacity=2]
connection: detour_up1-detour_up2 [max_link_capacity=2]
connection: detour_up2-detour_up3 [max_link_capacity=2]
connection: detour_up3-goal [max_link_capacity=2]
connection: start-detour_dn1 [max_link_capacity=2]
connection: detour_dn1-detour_dn2 [max_link_capacity=2]
connection: detour_dn2-detour_dn3 [max_link_capacity=2]
connection: detour_dn3-goal [max_link_capacity=2]
""", "Test 11: Blocked zones wall with split bypass", 6)

    # TEST 12: 4x4 Grid / Mesh Network (12 drones)
    run_test("""
nb_drones: 12
start_hub: start 0 0
hub: x0_y1 0 1 [max_drones=2]
hub: x0_y2 0 2 [max_drones=2]
hub: x1_y0 1 0 [max_drones=2]
hub: x1_y1 1 1 [zone=priority max_drones=2 color=cyan]
hub: x1_y2 1 2 [max_drones=2]
hub: x2_y0 2 0 [max_drones=2]
hub: x2_y1 2 1 [zone=restricted max_drones=2 color=red]
hub: x2_y2 2 2 [zone=priority max_drones=2 color=cyan]
end_hub: goal 3 2
connection: start-x0_y1 [max_link_capacity=2]
connection: start-x1_y0 [max_link_capacity=2]
connection: x0_y1-x0_y2 [max_link_capacity=2]
connection: x0_y1-x1_y1 [max_link_capacity=2]
connection: x1_y0-x1_y1 [max_link_capacity=2]
connection: x1_y0-x2_y0 [max_link_capacity=2]
connection: x0_y2-x1_y2 [max_link_capacity=2]
connection: x1_y1-x2_y1 [max_link_capacity=2]
connection: x1_y1-x1_y2 [max_link_capacity=2]
connection: x2_y0-x2_y1 [max_link_capacity=2]
connection: x1_y2-x2_y2 [max_link_capacity=2]
connection: x2_y1-x2_y2 [max_link_capacity=2]
connection: x2_y2-goal [max_link_capacity=3]
connection: x2_y1-goal [max_link_capacity=2]
connection: x0_y2-goal [max_link_capacity=1]
""", "Test 12: 4x4 Grid / Mesh Network (12 drones, mixed types)", 12)

    # TEST 13: Crossroads / Two Paths Crossing at a Single Point
    run_test("""
nb_drones: 4
start_hub: start 0 0
hub: nw 1 1 [max_drones=2]
hub: sw 1 -1 [max_drones=2]
hub: cross 2 0 [max_drones=1]
hub: ne 3 1 [max_drones=2]
hub: se 3 -1 [max_drones=2]
end_hub: goal 4 0
connection: start-nw [max_link_capacity=2]
connection: start-sw [max_link_capacity=2]
connection: nw-cross
connection: sw-cross
connection: cross-ne
connection: cross-se
connection: ne-goal [max_link_capacity=2]
connection: se-goal [max_link_capacity=2]
""", "Test 13: Crossroads intersection (single hub crossing point)", 8)

    # TEST 14: Severe Asymmetric Bottlenecks
    run_test("""
nb_drones: 10
start_hub: start 0 0
hub: short_neck 1 1 [max_drones=1]
hub: long1 1 -1 [max_drones=4]
hub: long2 2 -1 [max_drones=4]
hub: long3 3 -1 [max_drones=4]
end_hub: goal 4 0
connection: start-short_neck
connection: short_neck-goal
connection: start-long1 [max_link_capacity=4]
connection: long1-long2 [max_link_capacity=4]
connection: long2-long3 [max_link_capacity=4]
connection: long3-goal [max_link_capacity=4]
""", "Test 14: Asymmetric bottlenecks (Short cap-1 vs Long cap-4)", 15)

    # TEST 15: High Fleet Density (40 Drones on Multi-Channel Network)
    run_test("""
nb_drones: 40
start_hub: start 0 0
hub: ch1_a 1 2 [max_drones=4]
hub: ch1_b 2 2 [max_drones=4]
hub: ch2_a 1 0 [max_drones=4]
hub: ch2_b 2 0 [max_drones=4]
hub: ch3_a 1 -2 [max_drones=4]
hub: ch3_b 2 -2 [max_drones=4]
end_hub: goal 3 0
connection: start-ch1_a [max_link_capacity=4]
connection: ch1_a-ch1_b [max_link_capacity=4]
connection: ch1_b-goal [max_link_capacity=4]
connection: start-ch2_a [max_link_capacity=4]
connection: ch2_a-ch2_b [max_link_capacity=4]
connection: ch2_b-goal [max_link_capacity=4]
connection: start-ch3_a [max_link_capacity=4]
connection: ch3_a-ch3_b [max_link_capacity=4]
connection: ch3_b-goal [max_link_capacity=4]
""", "Test 15: 40 Drones fleet on 3 parallel 4-capacity channels", 8)

    # TEST 16: Sequential Restricted Gates with High Link Capacities
    run_test("""
nb_drones: 4
start_hub: start 0 0
hub: g1 1 0 [zone=restricted max_drones=2]
hub: g2 2 0 [zone=restricted max_drones=2]
end_hub: goal 3 0
connection: start-g1 [max_link_capacity=3]
connection: g1-g2 [max_link_capacity=3]
connection: g2-goal [max_link_capacity=3]
""", "Test 16: Sequential restricted gates (G1->G2 with link cap 3)", 10)

    print("\n" + "=" * 65)
    print("ALL 16 INTENSIVE SIMULATION & ALGORITHM TESTS PASSED!")
    print("=" * 65)


if __name__ == "__main__":
    main()

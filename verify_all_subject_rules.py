"""Exhaustive Subject Rules & Capacity Verification Script.

Tests all 22 map files (10 curriculum maps + 12 imaginative edge-case maps)
against every single constraint, capacity rule, and physical movement rule
defined in the Fly-in subject (fly.pdf).
"""
from typing import Dict, List, Set, Tuple
import glob
import os
import re
import sys

from graph import Graph
from models import Drone
from parser import Parser
from pathfinder import Pathfinder
from scheduler import Scheduler
from simulation import Simulation


class SubjectRuleViolation(Exception):
    """Raised when any rule from the subject is violated."""
    pass


class MasterSubjectRuleValidator:
    """Rigorous turn-by-turn validator checking 100% of subject rules."""

    @staticmethod
    def validate_simulation(
        graph: Graph,
        output_lines: List[str],
        map_name: str
    ) -> int:
        """Validate entire simulation against all subject rules.

        Returns total_turns.
        """
        nb_drones = graph.nb_drones
        start_hub = graph.start
        end_hub = graph.end

        # Rule 1 & 10: Check output lines
        if not output_lines:
            raise SubjectRuleViolation(
                f"[{map_name}] Simulation produced 0 output lines!"
            )

        # State tracking
        drone_positions: Dict[int, str] = {
            i + 1: start_hub for i in range(nb_drones)
        }
        # In-transit tracker:
        # drone_id -> (dest_zone, connection_key, turn_entered)
        in_transit: Dict[int, Tuple[str, Tuple[str, str], int]] = {}
        delivered: Set[int] = set()

        # Stats
        max_zone_occupancies: Dict[str, int] = {
            z: 0 for z in graph.zones
        }
        max_link_usages: Dict[Tuple[str, str], int] = {
            k: 0 for k in graph.connections
        }

        for turn_idx, line in enumerate(output_lines, 1):
            line_str = line.strip()
            if not line_str:
                raise SubjectRuleViolation(
                    f"[{map_name}] Turn {turn_idx}: Empty output line."
                )

            moves = line_str.split()
            moved_this_turn: Set[int] = set()
            conn_usage_this_turn: Dict[Tuple[str, str], int] = {}

            for move in moves:
                # Rule: Move syntax format D<id>-<target>
                m = re.match(r"^D(\d+)-(.+)$", move)
                if not m:
                    raise SubjectRuleViolation(
                        f"[{map_name}] Turn {turn_idx}: Invalid move '{move}'"
                    )
                did = int(m.group(1))
                target = m.group(2)

                # Rule: Drone ID must be valid (1 <= did <= nb_drones)
                if not (1 <= did <= nb_drones):
                    raise SubjectRuleViolation(
                        f"[{map_name}] Turn {turn_idx}: Invalid drone ID {did}"
                    )

                # Rule: One move per turn
                if did in moved_this_turn:
                    raise SubjectRuleViolation(
                        f"[{map_name}] Turn {turn_idx}: Drone {did} moved "
                        f"more than once in the same turn!"
                    )
                moved_this_turn.add(did)

                # Rule: Delivered drones cannot move
                if did in delivered:
                    raise SubjectRuleViolation(
                        f"[{map_name}] Turn {turn_idx}: Drone {did} moved "
                        f"after reaching destination!"
                    )

                # Handle in-flight landing vs new move
                if did in in_transit:
                    expected_dest, expected_conn, entry_turn = in_transit.pop(
                        did
                    )
                    # Rule: Drone must complete restricted entry on turn + 1
                    if turn_idx != entry_turn + 1:
                        raise SubjectRuleViolation(
                            f"[{map_name}] Turn {turn_idx}: Drone {did} in "
                            f"transit from turn {entry_turn} arrived at "
                            f"turn {turn_idx} (must take 2 turns)!"
                        )
                    if target != expected_dest:
                        raise SubjectRuleViolation(
                            f"[{map_name}] Turn {turn_idx}: Drone {did} "
                            f"expected to land in '{expected_dest}', got "
                            f"'{target}'!"
                        )
                    drone_positions[did] = target
                    if target == end_hub:
                        delivered.add(did)
                else:
                    curr = drone_positions[did]
                    if not curr:
                        raise SubjectRuleViolation(
                            f"[{map_name}] Turn {turn_idx}: Drone {did} is "
                            f"currently mid-air, cannot start new move"
                        )

                    # Check whether this is a restricted 2-turn movement entry
                    if "-" in target:
                        parts = target.split("-")
                        if len(parts) != 2:
                            raise SubjectRuleViolation(
                                f"[{map_name}] Turn {turn_idx}: Malformed "
                                f"transit string '{target}'"
                            )
                        c_from, c_to = parts

                        # Rule: Origin must match current drone position
                        if c_from != curr:
                            raise SubjectRuleViolation(
                                f"[{map_name}] Turn {turn_idx}: "
                                f"Drone {did} at '{curr}', not '{c_from}'!"
                            )

                        # Rule: Connection must exist in graph
                        ckey = (
                            (c_from, c_to) if c_from < c_to else (c_to, c_from)
                        )
                        if ckey not in graph.connections:
                            raise SubjectRuleViolation(
                                f"[{map_name}] Turn {turn_idx}: Connection "
                                f"'{c_from}-{c_to}' does not exist!"
                            )

                        # Rule: Target must be a restricted zone
                        target_zone = graph.get_zone(c_to)
                        if target_zone.zone_type != "restricted":
                            raise SubjectRuleViolation(
                                f"[{map_name}] Turn {turn_idx}: Transit "
                                f"for non-restricted zone '{c_to}'!"
                            )

                        # Rule: Target cannot be blocked
                        if target_zone.zone_type == "blocked":
                            raise SubjectRuleViolation(
                                f"[{map_name}] Turn {turn_idx}: Drone {did} "
                                f"attempting to enter BLOCKED zone '{c_to}'!"
                            )

                        conn = graph.get_connection(c_from, c_to)
                        ckey = conn.key()
                        conn_usage_this_turn[ckey] = (
                            conn_usage_this_turn.get(ckey, 0) + 1
                        )
                        in_transit[did] = (c_to, ckey, turn_idx)
                        drone_positions[did] = ""
                    else:
                        # Direct 1-turn move (normal or priority)
                        c_to = target
                        # Rule: Connection must exist
                        ckey = (curr, c_to) if curr < c_to else (c_to, curr)
                        if ckey not in graph.connections:
                            raise SubjectRuleViolation(
                                f"[{map_name}] Turn {turn_idx}: No connection "
                                f"'{curr}-{c_to}' for Drone {did}"
                            )

                        dest_zone = graph.get_zone(c_to)
                        # Rule: Target cannot be blocked
                        if dest_zone.zone_type == "blocked":
                            raise SubjectRuleViolation(
                                f"[{map_name}] Turn {turn_idx}: Drone {did} "
                                f"attempted to enter BLOCKED zone '{c_to}'!"
                            )

                        # Rule: Restricted zones CANNOT be entered in 1 turn
                        if dest_zone.zone_type == "restricted":
                            raise SubjectRuleViolation(
                                f"[{map_name}] Turn {turn_idx}: Restricted "
                                f"zone '{c_to}' entered in 1 turn by Drone "
                                f"{did}! (Must take 2 turns)"
                            )

                        conn = graph.get_connection(curr, c_to)
                        ckey = conn.key()
                        conn_usage_this_turn[ckey] = (
                            conn_usage_this_turn.get(ckey, 0) + 1
                        )
                        drone_positions[did] = c_to
                        if c_to == end_hub:
                            delivered.add(did)

            # Rule: Connection capacity (max_link_capacity)
            for ckey, usage in conn_usage_this_turn.items():
                conn_obj = graph.connections[ckey]
                max_link_usages[ckey] = max(max_link_usages[ckey], usage)
                if usage > conn_obj.max_link_capacity:
                    raise SubjectRuleViolation(
                        f"[{map_name}] Turn {turn_idx}: Connection {ckey} "
                        f"CAPACITY VIOLATION! ({usage} > "
                        f"{conn_obj.max_link_capacity})"
                    )

            # Rule: Zone capacity (max_drones) at end of turn
            # Count drones currently occupying each zone (excluding floating)
            current_zone_counts: Dict[str, int] = {}
            for did_val, pos in drone_positions.items():
                if pos and did_val not in delivered:
                    current_zone_counts[pos] = (
                        current_zone_counts.get(pos, 0) + 1
                    )

            for zname, count in current_zone_counts.items():
                zone_obj = graph.get_zone(zname)
                max_zone_occupancies[zname] = max(
                    max_zone_occupancies[zname], count
                )
                # start_hub and end_hub have unlimited capacity
                if not (zone_obj.is_start or zone_obj.is_end):
                    if count > zone_obj.max_drones:
                        raise SubjectRuleViolation(
                            f"[{map_name}] Turn {turn_idx}: Zone '{zname}' "
                            f"CAPACITY VIOLATION! ({count} drones > "
                            f"max_drones={zone_obj.max_drones})"
                        )

        # Rule: All drones must be delivered
        if len(delivered) != nb_drones:
            undelivered = [
                d for d in range(1, nb_drones + 1) if d not in delivered
            ]
            raise SubjectRuleViolation(
                f"[{map_name}] Not all drones delivered! Delivered: "
                f"{len(delivered)}/{nb_drones}. Undelivered: {undelivered}"
            )

        # Rule: No drones left hanging in transit
        if in_transit:
            raise SubjectRuleViolation(
                f"[{map_name}] Drones left floating in transit: {in_transit}"
            )

        return len(output_lines)


def test_single_map(map_path: str) -> Tuple[bool, str, int]:
    """Test a single map and validate all rules."""
    map_name = os.path.basename(map_path)
    try:
        parser = Parser()
        graph = parser.parse(map_path)

        pathfinder = Pathfinder()
        paths = pathfinder.find_paths(graph, graph.nb_drones)
        if not paths:
            return False, f"[{map_name}] No valid paths found!", 0

        drones = [Drone(id=i + 1) for i in range(graph.nb_drones)]
        Scheduler().assign(drones, paths, graph)

        sim = Simulation(graph, drones)
        output_lines = sim.run()

        turns = MasterSubjectRuleValidator.validate_simulation(
            graph, output_lines, map_name
        )
        return True, f"PASS ({turns} turns)", turns
    except Exception as e:
        return False, f"FAILED: {e}", 0


def main() -> None:
    """Run verification across all maps."""
    print("=" * 80)
    print("EXHAUSTIVE SUBJECT RULES & CAPACITY VERIFICATION")
    print("=" * 80)

    # Categories to check
    categories = [
        ("EASY MAPS", "maps/easy/*.txt"),
        ("MEDIUM MAPS", "maps/medium/*.txt"),
        ("HARD MAPS", "maps/hard/*.txt"),
        ("CHALLENGER MAPS", "maps/challenger/*.txt"),
        ("CUSTOM IMAGINATIVE EDGE-CASE MAPS", "maps/edge_cases/*.txt"),
    ]

    total_tested = 0
    total_passed = 0
    failures: List[Tuple[str, str]] = []

    # Benchmark targets for official maps
    benchmarks = {
        "01_linear_path.txt": 6,
        "02_simple_fork.txt": 8,
        "03_basic_capacity.txt": 6,
        "01_dead_end_trap.txt": 12,
        "02_circular_loop.txt": 15,
        "03_priority_puzzle.txt": 12,
        "01_maze_nightmare.txt": 30,
        "02_capacity_hell.txt": 35,
        "03_ultimate_challenge.txt": 45,
        "01_the_impossible_dream.txt": 45,
    }

    for cat_name, pattern in categories:
        print(f"\n--- {cat_name} ---")
        map_files = sorted(glob.glob(pattern))
        if not map_files:
            print(f"Warning: No maps found matching '{pattern}'")
            continue

        for map_file in map_files:
            total_tested += 1
            bname = os.path.basename(map_file)
            passed, msg, turns = test_single_map(map_file)
            if passed:
                bench_str = ""
                if bname in benchmarks:
                    target = benchmarks[bname]
                    if turns <= target:
                        bench_str = f" [Benchmark: <= {target} -> MET]"
                    else:
                        bench_str = (
                            f" [Benchmark: <= {target} -> EXCEEDED ({turns})]"
                        )
                print(f"  [OK]   {bname:40s} | {turns:2d} turns | {bench_str}")
                total_passed += 1
            else:
                print(f"  [FAIL] {bname:40s} | {msg}")
                failures.append((map_file, msg))

    print("\n" + "=" * 80)
    print(f"SUMMARY: {total_passed}/{total_tested} MAPS PASSED ALL RULES!")
    print("=" * 80)

    if failures:
        print("\nFAILURES:")
        for path, reason in failures:
            print(f" - {path}: {reason}")
        sys.exit(1)
    else:
        print("ALL CAPACITY CONSTRAINTS, RESTRICTED DELAYS, AND MOVEMENT")
        print("RULES ARE 100% RESPECTED ACROSS EVERY TURN OF EVERY MAP!")
        sys.exit(0)


if __name__ == "__main__":
    main()

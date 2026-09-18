"""Automated verification test suite for imaginative edge case maps.

Verifies parser, pathfinder, and simulation execution across all custom
edge-case maps in maps/edge_cases/.
"""
from typing import Dict, List, Set, Tuple
import os
import re
import unittest

from display import Display
from graph import Graph
from models import Connection, Drone, SimulationError, Zone
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

            zone_occupancy: Dict[str, int] = {}
            for did_val, pos in drone_pos.items():
                if pos != "" and did_val not in delivered:
                    zone_occupancy[pos] = zone_occupancy.get(pos, 0) + 1

            for zname, occ in zone_occupancy.items():
                zone_obj = graph.get_zone(zname)
                if not (zone_obj.is_start or zone_obj.is_end):
                    assert occ <= zone_obj.max_drones, (
                        f"Turn {turn_idx}: Zone '{zname}' exceeded "
                        f"capacity! ({occ} > {zone_obj.max_drones})"
                    )

        assert len(delivered) == graph.nb_drones, (
            f"Not all drones delivered! ({len(delivered)}/{graph.nb_drones})"
        )
        assert len(drone_transit) == 0, (
            f"Drones still in transit at end: {drone_transit}"
        )
        return len(output_lines)


class TestImaginativeEdgeCaseMaps(unittest.TestCase):
    """Test suite running all imaginative edge case maps in maps/edge_cases."""

    def _run_map(self, map_filename: str) -> int:
        """Run full simulation pipeline on a given map file."""
        map_path = os.path.join("maps", "edge_cases", map_filename)
        self.assertTrue(os.path.exists(map_path), f"Map not found: {map_path}")

        parser = Parser()
        graph = parser.parse(map_path)

        pathfinder = Pathfinder()
        paths = pathfinder.find_paths(graph, graph.nb_drones)
        self.assertTrue(len(paths) > 0, f"No paths found for {map_filename}")

        drones = [Drone(id=i + 1) for i in range(graph.nb_drones)]
        Scheduler().assign(drones, paths, graph)

        sim = Simulation(graph, drones)
        output_lines = sim.run()

        turns = StrictSimulationVerifier.verify(graph, output_lines)
        return turns

    def test_01_restricted_funnel_hazard(self) -> None:
        """Test high-throughput link into single-capacity restricted zone."""
        turns = self._run_map("01_restricted_funnel_hazard.txt")
        self.assertEqual(turns, 8)

    def test_02_chained_restricted_corridor(self) -> None:
        """Test 4 drones caterpillar through 3 chained restricted zones."""
        turns = self._run_map("02_chained_restricted_corridor.txt")
        self.assertEqual(turns, 13)

    def test_03_triple_convergence_bottleneck(self) -> None:
        """Test 3 feeder paths converging on 1-drone restricted bottleneck."""
        turns = self._run_map("03_triple_convergence_bottleneck.txt")
        self.assertEqual(turns, 14)

    def test_04_priority_express_vs_bulk_freeway(self) -> None:
        """Test priority express vs 3-drone capacity bulk freeway."""
        turns = self._run_map("04_priority_express_vs_bulk_freeway.txt")
        self.assertEqual(turns, 6)

    def test_05_accordion_capacity_shock(self) -> None:
        """Test alternating wide reservoirs and strict single-drone needles."""
        turns = self._run_map("05_accordion_capacity_shock.txt")
        self.assertEqual(turns, 11)

    def test_06_star_crossroads_junction(self) -> None:
        """Test 2-in, 2-out crossroads through 2-drone restricted hub."""
        turns = self._run_map("06_star_crossroads_junction.txt")
        self.assertEqual(turns, 11)

    def test_07_single_drone_tactical_puzzle(self) -> None:
        """Test single drone bypassing blocked obstacle and choosing prio."""
        turns = self._run_map("07_single_drone_tactical_puzzle.txt")
        self.assertEqual(turns, 3)

    def test_08_high_concurrency_dual_freeway(self) -> None:
        """Test 24 drones streaming across 2 parallel dual freeways."""
        turns = self._run_map("08_high_concurrency_dual_freeway.txt")
        self.assertEqual(turns, 9)

    def test_09_zigzag_dead_end_maze(self) -> None:
        """Test pathfinder ignoring dead-end traps and following zigzag."""
        turns = self._run_map("09_zigzag_dead_end_maze.txt")
        self.assertEqual(turns, 6)

    def test_10_diamond_mesh_weave(self) -> None:
        """Test braided diamond network with alternating zone types."""
        turns = self._run_map("10_diamond_mesh_weave.txt")
        self.assertEqual(turns, 6)

    def test_11_restricted_island_hop(self) -> None:
        """Test alternating chain normal->restricted->priority->restricted."""
        turns = self._run_map("11_restricted_island_hop.txt")
        self.assertEqual(turns, 16)

    def test_12_mega_swarm_tritrack(self) -> None:
        """Test 30 drones flooding 3 parallel conduits with concurrency."""
        turns = self._run_map("12_mega_swarm_tritrack.txt")
        self.assertEqual(turns, 8)

    def test_13_deadlock_detection(self) -> None:
        """Test that an unresolvable cycle raises SimulationError cleanly."""
        graph = Graph()
        graph.nb_drones = 2
        graph.start = "start"
        graph.end = "goal"
        graph.add_zone(Zone("start", 0, 0, is_start=True))
        graph.add_zone(Zone("A", 1, 0, max_drones=1))
        graph.add_zone(Zone("B", 2, 0, max_drones=1))
        graph.add_zone(Zone("goal", 3, 0, is_end=True))
        graph.add_connection(Connection("start", "A"))
        graph.add_connection(Connection("A", "B"))
        graph.add_connection(Connection("B", "goal"))

        # D1 is at A (wants B), D2 is at B (wants A) -> mutual deadlock
        d1 = Drone(
            id=1,
            path=["start", "A", "B", "goal"],
            position="A",
            path_index=1
        )
        d2 = Drone(
            id=2,
            path=["start", "B", "A", "goal"],
            position="B",
            path_index=1
        )
        sim = Simulation(graph, [d1, d2])
        with self.assertRaises(SimulationError) as ctx:
            sim.run()
        self.assertIn("Deadlock detected", str(ctx.exception))

    def test_14_multi_pass_simultaneous_movement(self) -> None:
        """Test multi-pass resolves same-distance tie without losing turns."""
        graph = Graph()
        graph.nb_drones = 2
        graph.start = "start"
        graph.end = "goal"
        graph.add_zone(Zone("start", 0, 0, is_start=True))
        graph.add_zone(Zone("A", 1, 0, max_drones=1))
        graph.add_zone(Zone("B", 2, 0, max_drones=1))
        graph.add_zone(Zone("C", 3, 0, max_drones=1))
        graph.add_zone(Zone("X", 1, 1, max_drones=1))
        graph.add_zone(Zone("goal", 4, 0, is_end=True))
        graph.add_connection(Connection("start", "A"))
        graph.add_connection(Connection("start", "X"))
        graph.add_connection(Connection("A", "B"))
        graph.add_connection(Connection("X", "B"))
        graph.add_connection(Connection("B", "C"))
        graph.add_connection(Connection("B", "goal"))
        graph.add_connection(Connection("C", "goal"))

        # Both drones have remaining steps = 3
        d1 = Drone(
            id=1,
            path=["start", "A", "B", "goal"],
            position="A",
            path_index=1
        )
        d2 = Drone(
            id=2,
            path=["start", "X", "B", "C", "goal"],
            position="B",
            path_index=2
        )
        sim = Simulation(graph, [d1, d2])
        moves = sim._do_turn()
        # Both drones must move in turn 1 (D2 to C, D1 to B)
        self.assertIn("D2-C", moves)
        self.assertIn("D1-B", moves)
        self.assertEqual(len(moves), 2)

    def test_15_arbitrary_single_word_color_display(self) -> None:
        """Test that non-standard single-word colors get ANSI color codes."""
        graph = Graph()
        graph.add_zone(Zone("goal", 0, 0, color="turquoise", is_end=True))
        display = Display(graph)
        output = display.colorize_line("D1-goal")
        self.assertIn("\033[38;5;", output)
        self.assertIn("D1-goal", output)

    def test_16_pulsing_chokepoint_resistor(self) -> None:
        """Test Wheatstone bridge lattice with diagonal interconnects."""
        turns = self._run_map("13_pulsing_chokepoint_resistor.txt")
        self.assertEqual(turns, 4)

    def test_17_priority_switchback_detour(self) -> None:
        """Test Dijkstra cost parity between short normal and long priority."""
        turns = self._run_map("14_priority_switchback_detour.txt")
        self.assertEqual(turns, 7)

    def test_18_hourglass_funnel_surge(self) -> None:
        """Test hourglass 3-in-1-out funnel into restricted waist."""
        turns = self._run_map("15_hourglass_funnel_surge.txt")
        self.assertEqual(turns, 15)

    def test_19_dead_end_decoy_galaxy(self) -> None:
        """Test pathfinder immunity to 4 distinct dead-end lures."""
        turns = self._run_map("16_dead_end_decoy_galaxy.txt")
        self.assertEqual(turns, 5)

    def test_20_fifty_drone_tsunami(self) -> None:
        """Test 50 drones streaming across 4 high-concurrency corridors."""
        turns = self._run_map("17_fifty_drone_tsunami.txt")
        self.assertEqual(turns, 6)

    def test_21_nested_restricted_loops(self) -> None:
        """Test concentric rings with inner restricted and outer normal."""
        turns = self._run_map("18_nested_restricted_loops.txt")
        self.assertEqual(turns, 4)

    # Added: Unit tests for newly created edge-case maps 19 to 26 and
    # advanced physical constraints (multi-inbound restricted reservation
    # and connection capacity throttling).
    def test_22_reverse_funnel_expansion(self) -> None:
        """Test reverse funnel from needle chokepoint to 4 parallel lanes."""
        turns = self._run_map("19_reverse_funnel_expansion.txt")
        self.assertEqual(turns, 13)

    def test_23_bidirectional_corridor_squeeze(self) -> None:
        """Test parallel multi-lane highways with capacity-1 cross-switches."""
        turns = self._run_map("20_bidirectional_corridor_squeeze.txt")
        self.assertEqual(turns, 6)

    def test_24_restricted_tollbooth_cluster(self) -> None:
        """Test 3 restricted tollbooths feeding common plaza to exit gates."""
        turns = self._run_map("21_restricted_tollbooth_cluster.txt")
        self.assertEqual(turns, 10)

    def test_25_asymmetric_bipartite_mesh(self) -> None:
        """Test fully connected bipartite mesh between mixed zone types."""
        turns = self._run_map("22_asymmetric_bipartite_mesh.txt")
        self.assertEqual(turns, 8)

    def test_26_cascading_priority_waterfall(self) -> None:
        """Test 3-stage cascade with dynamic spillover to normal bypass."""
        turns = self._run_map("23_cascading_priority_waterfall.txt")
        self.assertEqual(turns, 11)

    def test_27_labyrinth_of_knossos(self) -> None:
        """Test maze with blocked obstacles, decoy lures, and snake path."""
        turns = self._run_map("24_labyrinth_of_knossos.txt")
        self.assertEqual(turns, 13)

    def test_28_massive_link_choke_high_zone_cap(self) -> None:
        """Test link capacity throttling independently of large zone space."""
        turns = self._run_map("25_massive_link_choke_high_zone_cap.txt")
        self.assertEqual(turns, 11)

    def test_29_single_drone_marathon(self) -> None:
        """Test single drone 10-hop marathon with alternating zone types."""
        turns = self._run_map("26_single_drone_marathon.txt")
        self.assertEqual(turns, 14)

    def test_30_multi_inbound_restricted_reservation(self) -> None:
        """Test multi-inbound restricted zone reservation."""
        graph = Graph()
        graph.nb_drones = 2
        graph.start = "start"
        graph.end = "goal"
        graph.add_zone(Zone("start", 0, 0, is_start=True))
        graph.add_zone(Zone("A", 1, 1, max_drones=2))
        graph.add_zone(Zone("B", 1, -1, max_drones=2))
        graph.add_zone(Zone("R", 2, 0, zone_type="restricted", max_drones=1))
        graph.add_zone(Zone("goal", 3, 0, is_end=True))
        graph.add_connection(Connection("start", "A", max_link_capacity=2))
        graph.add_connection(Connection("start", "B", max_link_capacity=2))
        graph.add_connection(Connection("A", "R", max_link_capacity=2))
        graph.add_connection(Connection("B", "R", max_link_capacity=2))
        graph.add_connection(Connection("R", "goal", max_link_capacity=2))

        # D1 is at A, D2 is at B, both targeting R (max_drones=1)
        d1 = Drone(
            id=1,
            path=["start", "A", "R", "goal"],
            position="A",
            path_index=1
        )
        d2 = Drone(
            id=2,
            path=["start", "B", "R", "goal"],
            position="B",
            path_index=1
        )
        sim = Simulation(graph, [d1, d2])
        moves = sim._do_turn()

        # Only one drone can enter transit to R in turn 1
        in_transit_moves = [m for m in moves if "-R" in m]
        self.assertEqual(len(in_transit_moves), 1)

    def test_31_link_capacity_throttling_strictness(self) -> None:
        """Test that link capacity strictly limits simultaneous traversals."""
        graph = Graph()
        graph.nb_drones = 3
        graph.start = "start"
        graph.end = "goal"
        graph.add_zone(Zone("start", 0, 0, is_start=True))
        graph.add_zone(Zone("A", 1, 0, max_drones=10))
        graph.add_zone(Zone("B", 2, 0, max_drones=10))
        graph.add_zone(Zone("goal", 3, 0, is_end=True))
        graph.add_connection(Connection("start", "A", max_link_capacity=3))
        graph.add_connection(Connection("A", "B", max_link_capacity=1))
        graph.add_connection(Connection("B", "goal", max_link_capacity=3))

        # 3 drones at A wanting to go to B, but link cap is 1
        drones = [
            Drone(
                id=i,
                path=["start", "A", "B", "goal"],
                position="A",
                path_index=1
            )
            for i in range(1, 4)
        ]
        sim = Simulation(graph, drones)
        moves = sim._do_turn()
        # Exactly 1 drone moves to B
        b_moves = [m for m in moves if m.endswith("-B")]
        self.assertEqual(len(b_moves), 1)


if __name__ == "__main__":
    unittest.main()

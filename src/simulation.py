"""Simulation: runs the turn-by-turn drone movement."""
from __future__ import annotations
from src.models import Drone, SimulationError
from src.graph import Graph


class Simulation:
    """Executes the simulation turn by turn."""

    def __init__(self, graph: Graph, drones: list[Drone]) -> None:
        """Initialize simulation."""
        self.graph = graph
        self.drones = drones
        self.turn: int = 0
        self.output_lines: list[str] = []

    def run(self) -> list[str]:
        """Run the full simulation. Returns list of output lines, one per turn."""
        max_turns = 10000

        while not all(d.delivered for d in self.drones):
            self.turn += 1
            if self.turn > max_turns:
                raise SimulationError("Error: Simulation exceeded max turns")
            movements = self._do_turn()
            if movements:
                self.output_lines.append(" ".join(movements))

        return self.output_lines

    def _do_turn(self) -> list[str]:
        """Execute one simulation turn. Returns list of movement strings."""
        movements: list[str] = []

        # Count current zone occupancy
        zone_occ: dict[str, int] = {}
        for drone in self.drones:
            if not drone.delivered and not drone.in_transit:
                zone_occ[drone.position] = zone_occ.get(drone.position, 0) + 1

        conn_usage: dict[tuple[str, str], int] = {}
        moved_this_turn: set[int] = set()

        # Phase 1: Complete restricted zone transit (these drones MUST arrive)
        for drone in self.drones:
            if drone.delivered or not drone.in_transit:
                continue
            dest = drone.transit_dest
            drone.in_transit = False
            drone.position = dest
            drone.path_index += 1
            zone_occ[dest] = zone_occ.get(dest, 0) + 1
            if dest == self.graph.end:
                drone.delivered = True
            movements.append(f"D{drone.id}-{dest}")
            moved_this_turn.add(drone.id)

        # Phase 2: Move waiting drones (closest to goal moves first)
        active = [d for d in self.drones if not d.delivered and d.id not in moved_this_turn and d.path_index < len(d.path) - 1]
        active.sort(key=lambda d: len(d.path) - d.path_index)

        for drone in active:
            next_zone_name = drone.path[drone.path_index + 1]
            next_zone = self.graph.get_zone(next_zone_name)
            conn = self.graph.get_connection(drone.position, next_zone_name)
            conn_key = conn.key()

            # Check connection capacity
            if conn_usage.get(conn_key, 0) >= conn.max_link_capacity:
                continue

            # Check destination zone capacity
            dest_occ = zone_occ.get(next_zone_name, 0)
            if not next_zone.is_start and not next_zone.is_end and dest_occ >= next_zone.max_drones:
                continue

            if next_zone.zone_type == "restricted":
                # Restricted: takes 2 turns — enter connection this turn, arrive next turn
                conn_name = f"{drone.position}-{next_zone_name}"
                zone_occ[drone.position] = zone_occ.get(drone.position, 0) - 1
                drone.in_transit = True
                drone.transit_dest = next_zone_name
                drone.position = ""
                conn_usage[conn_key] = conn_usage.get(conn_key, 0) + 1
                movements.append(f"D{drone.id}-{conn_name}")
            else:
                # Normal or priority: move in one turn
                zone_occ[drone.position] = zone_occ.get(drone.position, 0) - 1
                drone.position = next_zone_name
                drone.path_index += 1
                zone_occ[next_zone_name] = dest_occ + 1
                conn_usage[conn_key] = conn_usage.get(conn_key, 0) + 1
                if next_zone_name == self.graph.end:
                    drone.delivered = True
                movements.append(f"D{drone.id}-{next_zone_name}")

        return movements

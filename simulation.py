"""Simulation: runs the turn-by-turn drone movement."""
from __future__ import annotations
from models import Drone, SimulationError
from graph import Graph


class Simulation:
    """Executes the simulation turn by turn."""

    def __init__(self, graph: Graph, drones: list[Drone]) -> None:
        """Initialize simulation."""
        self.graph = graph
        self.drones = drones
        self.turn: int = 0
        self.output_lines: list[str] = []
        self.capacity_history = []


    # main methode
    def run(self) -> list[str]:
        """Run the full simulation. Returns list of output lines, one per turn."""

        while not all(d.delivered for d in self.drones):
            self.turn += 1
            movements = self._do_turn()
            if movements:
                self.output_lines.append(" ".join(movements))

        return self.output_lines

    def _do_turn(self) -> list[str]:
        """Execute one simulation turn. Returns list of movement strings of that turn""" 
        movements: list[str] = []

        # Count current each zone occupancy how many drones are in each zone
        zone_occ: dict[str, int] = {}
        for drone in self.drones:
            # Count drones that are not delivered and not in traveling,
            # we only count drones that are in a zone
            if not drone.delivered and not drone.in_traveling:
                zone_occ[drone.position] = zone_occ.get(drone.position, 0) + 1

        # we initialize the cnx usaage and moved turn by turn to keep track of
        # the connections used in this turn and the drones that have moved in
        # this turn
        conn_usage: dict[tuple[str, str], int] = {}
        moved_this_turn: set[int] = set()

        # Phase 1: check for floating drones traveling to there destination
        # zones (for restricted zones that take 2 turns to enter
        for drone in self.drones:
            # only traveling drones
            if drone.delivered or not drone.in_traveling:
                continue
            dest = drone.travel_dest
            drone.in_traveling = False
            drone.position = dest
            drone.path_index += 1
            zone_occ[dest] = zone_occ.get(dest, 0) + 1
            if dest == self.graph.end:
                drone.delivered = True
            movements.append(f"D{drone.id}-{dest}")
            moved_this_turn.add(drone.id)

        # Phase 2: Move waiting drones (closest to goal moves first)
        active = [
            d for d in self.drones
            if not d.delivered
            and d.id not in moved_this_turn
            and d.path_index < len(d.path) - 1
        ]
        # here we sort the active drones based how they are close to
        # their goal small first the closest to goal first
        active.sort(key=lambda d: len(d.path) - d.path_index)

        for drone in active:
            next_zone_name = drone.path[drone.path_index + 1]
            next_zone = self.graph.get_zone(next_zone_name)
            conn = self.graph.get_connection(drone.position, next_zone_name)
            conn_key = conn.key()

            # Check connection capacity conn_usage{(zone1, zone2): number of
            # drones using this connection in this turn}
            if conn_usage.get(conn_key, 0) >= conn.max_link_capacity:
                continue

            # Check destination zone capacity
            # zone_occ{zone_name: number of drones in this zone}
            dest_occ = zone_occ.get(next_zone_name, 0)
            is_unlimited_start_or_end = next_zone.is_start or next_zone.is_end
            if not is_unlimited_start_or_end and dest_occ >= next_zone.max_drones:
                continue

            if next_zone.zone_type == "restricted":
                # Restricted: takes 2 turns — enter connection this turn,
                # arrive next turn
                conn_name = f"{drone.position}-{next_zone_name}"
                # The drone is leaving its current zone. Subtract 1 from that
                # zone's occupancy. This frees up a spot
                zone_occ[drone.position] = (
                    zone_occ.get(drone.position, 0) - 1
                )
                drone.in_traveling = True
                drone.travel_dest = next_zone_name
                # between two zones. Empty string means "not in a zone".
                drone.position = ""
                conn_usage[conn_key] = conn_usage.get(conn_key, 0) + 1
                # "D1-A-restricted_zone"
                movements.append(f"D{drone.id}-{conn_name}")
            else:
                # Normal or priority: move in one turn
                # Leave the current zone. Subtract 1 from occupancy.
                zone_occ[drone.position] = (
                    zone_occ.get(drone.position, 0) - 1
                )
                # Move to the next zone. Add 1 to occupancy.
                drone.position = next_zone_name
                drone.path_index += 1
                zone_occ[next_zone_name] = dest_occ + 1
                conn_usage[conn_key] = conn_usage.get(conn_key, 0) + 1
                if next_zone_name == self.graph.end:
                    drone.delivered = True
                    # "D1-waypoint1"
                movements.append(f"D{drone.id}-{next_zone_name}")
        self.capacity_history.append((dict(zone_occ), dict(conn_usage)))
    
        return movements

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

        # Count current each zone occupancy ho wmany drones are in each zone 
        zone_occ: dict[str, int] = {}
        for drone in self.drones:
            # Count drones that are not delivered and not in traveling, we only count drones that are in a zone, if the drone is in traveling we don't count it because it's not in a zone
            if not drone.delivered and not drone.in_traveling:
                zone_occ[drone.position] = zone_occ.get(drone.position, 0) + 1
        # we initialize the cnx usaage and moved this turn to keep track of the connections used in this turn and the drones that have moved in this turn, we do that because we want to make sure that we don't exceed the max_link_capacity of the connection and we don't move the same drone twice in the same turn
        conn_usage: dict[tuple[str, str], int] = {}
        moved_this_turn: set[int] = set()

        # Phase 1: check for floating drones traveling to there destination zones and move them to their destination (for restricted zones that take 2 turns to enter)
        for drone in self.drones:
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
        active = [d for d in self.drones if not d.delivered and d.id not in moved_this_turn and d.path_index < len(d.path) - 1]
        # here we sort the active drones based how they are cloase to their goal small first the closest to the goal and the largest last the farthest from the goal, we do that because we want to move the closest drones first so they can reach their destination faster and we can free up space for the other drones to move
        active.sort(key=lambda d: len(d.path) - d.path_index)

        for drone in active:
            next_zone_name = drone.path[drone.path_index + 1]
            next_zone = self.graph.get_zone(next_zone_name)
            conn = self.graph.get_connection(drone.position, next_zone_name)
            conn_key = conn.key()

            # Check connection capacity conn_usage{(zone1, zone2): number of drones using this connection in this turn} if the number of drones using this connection is greater than or equal to the max_link_capacity of the connection we skip this drone and move to the next one
            if conn_usage.get(conn_key, 0) >= conn.max_link_capacity:
                continue

            # Check destination zone capacity
            # zone_occ{zone_name: number of drones in this zone} if the number of drones in the dest zone is greater than or equal to the max_drones of the zone we skip this drone and move to the next one
            dest_occ = zone_occ.get(next_zone_name, 0)
            if not next_zone.is_start and not next_zone.is_end and dest_occ >= next_zone.max_drones:
                continue

            if next_zone.zone_type == "restricted":
                # Restricted: takes 2 turns — enter connection this turn, arrive next turn
                conn_name = f"{drone.position}-{next_zone_name}"
                # The drone is leaving its current zone. Subtract 1 from that zone's occupancy. This frees up a spot 
                zone_occ[drone.position] = zone_occ.get(drone.position, 0) - 1
                drone.in_traveling = True
                drone.travel_dest = next_zone_name
                # The drone is no longer in any zone — it's on the connection between two zones. Empty string means "not in a zone". 
                drone.position = ""
                # we mark this conx as used so that we can check the capacity of the connection in the next turn and we can skip drones that want to use this connection if the capacity is full
                conn_usage[conn_key] = conn_usage.get(conn_key, 0) + 1
                # "D1-A-restricted_zone"
                movements.append(f"D{drone.id}-{conn_name}")
            else:
                # Normal or priority: move in one turn
                # Leave the current zone. Subtract 1 from occupancy.
                zone_occ[drone.position] = zone_occ.get(drone.position, 0) - 1
                # Move to the next zone. Add 1 to occupancy.
                drone.position = next_zone_name
                drone.path_index += 1
                # Add 1 to occupancy of the destination zone. This is important for capacity checks for other drones in this turn.
                zone_occ[next_zone_name] = dest_occ + 1
                conn_usage[conn_key] = conn_usage.get(conn_key, 0) + 1
                if next_zone_name == self.graph.end:
                    drone.delivered = True
                    # "D1-waypoint1"
                movements.append(f"D{drone.id}-{next_zone_name}")

        return movements

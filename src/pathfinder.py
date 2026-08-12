"""Pathfinder: Dijkstra to find paths from start to end."""
from __future__ import annotations
import heapq
from src.graph import Graph
from src.models import SimulationError


class Pathfinder:
    """Finds paths using Dijkstra. Handles zone costs and priority zones correctly."""

    def find_paths(self, graph: Graph, num_drones: int) -> list[list[str]]:
        """Find multiple paths from start to end using Dijkstra with edge penalization."""
        paths: list[list[str]] = []
        count_cnx_used: dict[tuple[str, str], int] = {}

        for _ in range(num_drones):
            path = self._dijkstra(graph, count_cnx_used)
            if path is None:
                break
            paths.append(path)
            # Mark connection as used so next search tries different route
            # len(path) - 1 cause we do i + 1 adn i starts at 0 so we go beyound the path index 
            for i in range(len(path) - 1):
                connection_tuple = (path[i], path[i + 1]) if path[i] < path[i + 1] else (path[i + 1], path[i])
                count_cnx_used[connection_tuple] = count_cnx_used.get(connection_tuple, 0) + 1

        if not paths:
            raise SimulationError(f"Error: No valid path from '{graph.start}' to '{graph.end}'")

        return paths
 
    def _dijkstra(self, graph: Graph, count_cnx_used: dict[tuple[str, str], int]) -> list[str] | None:
        """Dijkstra from start to end. Considers zone costs, prefers priority zones, skips blocked."""
        start = graph.start
        end = graph.end

        # Priority queue: (cost, zone_name)
        heap: list[tuple[int, str]] = [(0, start)]
        best_cost: dict[str, int] = {start: 0}
        parent: dict[str, str] = {start: ""}

        while heap:
            cost, current = heapq.heappop(heap)

            # Skip if we already found a better path to this node
            if cost > best_cost.get(current, float("inf")):
                continue

            if current == end:
                # Build path by backtracking
                path: list[str] = []
                node = end
                while node:
                    path.append(node)
                    node = parent[node]
                path.reverse()
                return path

            for neighbor in graph.get_neighbors(current):
                zone = graph.get_zone(neighbor) # we start with A

                # Skip blocked zones
                if zone.zone_type == "blocked":
                    continue

                # Move cost: priority=5, normal=10, restricted=20
                if zone.zone_type == "restricted":
                    move_cost = 20
                elif zone.zone_type == "priority":
                    move_cost = 5
                else:
                    move_cost = 10

                # Penalize reused paths so we find different paths for every drone
                # why we use that (current, neighbor) if current < neighbor else (neighbor, current)
                connection_tuple = (current, neighbor) if current < neighbor else (neighbor, current)
                penalty = count_cnx_used.get(connection_tuple, 0) * 100

                new_cost = cost + move_cost + penalty #new_cost = 100

                if new_cost < best_cost.get(neighbor, float("inf")): # why we do that check is it for reached zones that we should not go back to them because they are already reached and we have a better cost for them or what
                    best_cost[neighbor] = new_cost
                    parent[neighbor] = current
                    heapq.heappush(heap, (new_cost, neighbor))

        return None

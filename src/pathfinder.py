"""Pathfinder: Dijkstra to find paths from start to end."""
from __future__ import annotations
import heapq
from src.graph import Graph
from src.models import SimulationError


class Pathfinder:
    """Finds paths using Dijkstra. Handles zone costs correctly."""

    def find_paths(self, graph: Graph, num_paths: int) -> list[list[str]]:
        """Find multiple paths from start to end using Dijkstra with edge penalization."""
        paths: list[list[str]] = []
        edge_usage: dict[tuple[str, str], int] = {}

        for _ in range(num_paths):
            path = self._dijkstra(graph, edge_usage)
            if path is None:
                break
            paths.append(path)
            # Mark edges as used so next search tries different route
            for i in range(len(path) - 1):
                key = (path[i], path[i + 1]) if path[i] < path[i + 1] else (path[i + 1], path[i])
                edge_usage[key] = edge_usage.get(key, 0) + 1

        if not paths:
            raise SimulationError(f"Error: No valid path from '{graph.start}' to '{graph.end}'")

        return paths

    def _dijkstra(self, graph: Graph, edge_usage: dict[tuple[str, str], int]) -> list[str] | None:
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
                zone = graph.get_zone(neighbor)

                # Skip blocked zones
                if zone.zone_type == "blocked":
                    continue

                # Zone cost: restricted = 2, everything else = 1
                move_cost = 2 if zone.zone_type == "restricted" else 1

                # Penalize reused edges so we find different paths
                edge_key = (current, neighbor) if current < neighbor else (neighbor, current)
                penalty = edge_usage.get(edge_key, 0) * 10

                # Bonus for priority zones (small negative to prefer them)
                bonus = -1 if zone.zone_type == "priority" else 0

                new_cost = cost + move_cost + penalty + bonus

                if new_cost < best_cost.get(neighbor, float("inf")):
                    best_cost[neighbor] = new_cost
                    parent[neighbor] = current
                    heapq.heappush(heap, (new_cost, neighbor))

        return None

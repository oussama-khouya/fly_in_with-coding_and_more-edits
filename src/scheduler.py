"""Scheduler: assigns drones to paths."""
from __future__ import annotations
from src.models import Drone
from src.graph import Graph


class Scheduler:
    """Assigns drones to paths, simple round-robin."""

    def assign(self, drones: list[Drone], paths: list[list[str]], graph: Graph) -> None:
        """Assign each drone a path using round-robin distribution."""
        for i, drone in enumerate(drones):
            drone.path = list(paths[i % len(paths)])
            drone.position = graph.start
            drone.path_index = 0
            drone.delivered = False

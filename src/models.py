"""Data models for the Fly-in drone simulation."""
from __future__ import annotations
from dataclasses import dataclass, field


class FlyinError(Exception):
    """Base error for all Fly-in errors."""
    pass


class ParserError(FlyinError):
    """Raised when the input file is invalid."""
    pass


class SimulationError(FlyinError):
    """Raised when simulation hits an unrecoverable state."""
    pass


@dataclass
class Zone:
    """One zone (node) in the graph."""
    name: str
    x: int
    y: int
    zone_type: str = "normal"
    color: str = ""
    max_drones: int = 1
    is_start: bool = False
    is_end: bool = False


@dataclass
class Connection:
    """One connection (edge) between two zones."""
    zone1: str
    zone2: str
    max_link_capacity: int = 1

    def key(self) -> tuple[str, str]:
        """Return sorted tuple for consistent lookup."""
        if self.zone1 < self.zone2:
            return (self.zone1, self.zone2)
        return (self.zone2, self.zone1)


@dataclass
class Drone:
    """One drone in the simulation."""
    id: int
    path: list[str] = field(default_factory=list)
    position: str = ""
    path_index: int = 0
    in_transit: bool = False
    transit_dest: str = ""
    delivered: bool = False

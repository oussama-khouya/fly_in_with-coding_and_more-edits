"""Data models we use them to store the data for the simulation"""
from dataclasses import dataclass, field
from typing import List, Tuple


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
    # metadata
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
    # metadata
    max_link_capacity: int = 1

    # the conx zones in bidirectinal a-b same as b-a
    # so just always sort them alph
    def key(self) -> Tuple[str, str]:
        """Return sorted tuple for consistent lookup."""
        if self.zone1 < self.zone2:
            return (self.zone1, self.zone2)
        return (self.zone2, self.zone1)


@dataclass
class Drone:
    """One drone in the simulation."""
    id: int
    path: List[str] = field(default_factory=list)
    position: str = ""
    path_index: int = 0
    in_traveling: bool = False
    travel_dest: str = ""
    delivered: bool = False

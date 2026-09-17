"""
Graph: stores zones and connections just the important data
 its our data container for pathfinder and simulation.
"""
from typing import Dict, List, Tuple
from models import Zone, Connection


class Graph:
    """Simple graph with adjacency list.

    adjacency is the connected zones to that zone
    """
    # save the important data
    def __init__(self) -> None:
        """Initialize empty graph."""
        self.zones: Dict[str, Zone] = {}
        self.neighbors: Dict[str, List[str]] = {}
        self.connections: Dict[Tuple[str, str], Connection] = {}
        self.start: str = ""
        self.end: str = ""
        self.nb_drones: int = 0

    # we will build methodes to store data inside the graph and also get
    # the data from that graph
    # we add the zone name to the graph and also to the neighbors and
    # start and end
    # for parser
    def add_zone(self, zone: Zone) -> None:
        """Add a zone to the graph."""
        self.zones[zone.name] = zone
        if zone.name not in self.neighbors:
            self.neighbors[zone.name] = []
        if zone.is_start:
            self.start = zone.name
        if zone.is_end:
            self.end = zone.name

    #  add the connection and also add them togther as neighbors
    # for parser
    def add_connection(self, conn: Connection) -> None:
        """Add a connection (bidirectional edge)."""
        self.connections[conn.key()] = conn
        if conn.zone1 not in self.neighbors[conn.zone2]:
            self.neighbors[conn.zone2].append(conn.zone1)
        if conn.zone2 not in self.neighbors[conn.zone1]:
            self.neighbors[conn.zone1].append(conn.zone2)

    # get neighbors of a zone using adjacency
    # for path finder algho
    def get_neighbors(self, zone_name: str) -> List[str]:
        """Get all neighbors of a zone."""
        # we get the neighbor zones of that zone, if the zone is not in the
        # adjacency list, we return an empty list
        return self.neighbors.get(zone_name, [])

    # get connection betweeen two zones
    def get_connection(self, z1: str, z2: str) -> Connection:
        """Get connection between two zones."""
        key = (z1, z2) if z1 < z2 else (z2, z1)
        return self.connections[key]

    # get the zone obj using just zone.name
    def get_zone(self, name: str) -> Zone:
        """Get a zone by name."""
        return self.zones[name]

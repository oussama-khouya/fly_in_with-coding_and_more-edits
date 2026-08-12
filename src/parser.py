"""Parser: reads a map file and builds a Graph. to put the data inside the graph"""  # noqa: E501
from __future__ import annotations
from src.models import Zone, Connection, ParserError
from src.graph import Graph


class Parser:
    """Parses a Fly-in map file into a Graph."""

    def parse(self, filepath: str) -> Graph:
        """Parse a map file and return a Graph."""
        graph = Graph()
        has_drones = False
        has_start = False
        has_end = False
        # just added those for the duplicate connections and coords
        seen_connections: set[tuple[str, str]] = set()
        seen_coords: dict[tuple[int, int], str] = {}

        try:
            with open(filepath, "r") as f:
                # we read file lines and we return a list of line sep by new
                # line
                lines: list[str] = f.readlines()
        except FileNotFoundError:
            raise ParserError(f"Error: File '{filepath}' not found")

        for line_num, raw_line in enumerate(lines, start=1):
            line = raw_line.strip()

            if not line or line.startswith("#"):
                continue

            if ":" not in line:
                err = f"Error on line {line_num}: Unknown line format"
                raise ParserError(err)

            prefix, rest = line.split(":", 1)
            prefix = prefix.strip()
            rest = rest.strip()

            try:
                if prefix == "nb_drones":
                    if has_drones:
                        err = (f"Error on line {line_num}: "
                               f"Duplicate nb_drones definition")
                        raise ParserError(err)
                    graph.nb_drones = self._parse_drone_count(rest, line_num)
                    has_drones = True

                elif prefix == "start_hub":
                    if has_start:
                        err = (f"Error on line {line_num}: "
                               f"Duplicate start_hub definition")
                        raise ParserError(err)
                    zone = self._parse_zone(rest, line_num, is_start=True)
                    self._check_duplicate_zone(zone.name, graph, line_num)
                    self._check_duplicate_coords(
                        zone.x, zone.y, zone.name, seen_coords, line_num
                    )
                    graph.add_zone(zone)
                    has_start = True

                elif prefix == "end_hub":
                    if has_end:
                        err = (f"Error on line {line_num}: "
                               f"Duplicate end_hub definition")
                        raise ParserError(err)
                    zone = self._parse_zone(rest, line_num, is_end=True)
                    self._check_duplicate_zone(zone.name, graph, line_num)
                    self._check_duplicate_coords(
                        zone.x, zone.y, zone.name, seen_coords, line_num
                    )
                    graph.add_zone(zone)
                    has_end = True

                elif prefix == "hub":
                    zone = self._parse_zone(rest, line_num)
                    self._check_duplicate_zone(zone.name, graph, line_num)
                    self._check_duplicate_coords(
                        zone.x, zone.y, zone.name, seen_coords, line_num
                    )
                    graph.add_zone(zone)

                elif prefix == "connection":
                    conn = self._parse_connection(rest, line_num, graph)
                    conn_key = conn.key()
                    if conn_key in seen_connections:
                        err = (f"Error on line {line_num}: Duplicate "
                               f"connection '{conn.zone1}-{conn.zone2}'")
                        raise ParserError(err)
                    seen_connections.add(conn_key)
                    graph.add_connection(conn)

                else:
                    err = f"Error on line {line_num}: Unknown line format"
                    raise ParserError(err)

            except ParserError:
                raise
            except Exception as e:
                raise ParserError(f"Error on line {line_num}: {e}")

        if not has_drones:
            raise ParserError("Error: Missing nb_drones definition")
        if not has_start:
            raise ParserError("Error: Missing start_hub definition")
        if not has_end:
            raise ParserError("Error: Missing end_hub definition")

        # it feeds / stores the data to the graph class
        return graph

    # helper methodes
    # parse the nb_drones count
    def _parse_drone_count(self, content: str, line_num: int) -> int:
        """Parse drone count value."""
        try:
            count = int(content)
        except ValueError:
            err = (f"Error on line {line_num}: "
                   f"nb_drones must be a positive integer")
            raise ParserError(err)
        if count <= 0:
            err = (f"Error on line {line_num}: "
                   f"nb_drones must be a positive integer")
            raise ParserError(err)
        return count

    def _parse_zone(
        self,
        content: str,
        line_num: int,
        is_start: bool = False,
        is_end: bool = False
    ) -> Zone:
        """Parse a zone definition line content."""
        metadata_str = ""
        if "[" in content:
            bracket_start = content.index("[")
            if "]" not in content:
                err = (f"Error on line {line_num}: "
                       f"Metadata block is not closed, missing ']'")
                raise ParserError(err)
            bracket_end = content.index("]")
            # here is the metadata str
            metadata_str = content[bracket_start + 1:bracket_end]
            # in case we put we add somth ouside the brackets
            trash = content[bracket_end + 1:].strip()
            if trash:
                err = (f"Error on line {line_num}: "
                       f"Unexpected text after metadata: '{trash}'")
                raise ParserError(err)
            content = content[:bracket_start].strip()

        zocor = content.split()
        if len(zocor) < 3:
            err = f"Error on line {line_num}: Zone must have name, x, and y"
            raise ParserError(err)

        zone_name = zocor[0]
        if "-" in zone_name:
            err = (f"Error on line {line_num}: "
                   f"Zone name cannot contain dashes")
            raise ParserError(err)

        try:
            x = int(zocor[1])
            y = int(zocor[2])
        except ValueError:
            err = f"Error on line {line_num}: Coordinates must be integers"
            raise ParserError(err)

        # we start with as default zone
        zone_type = "normal"
        color = ""
        max_drones = 1
        seen_keys: set[str] = set()

        if metadata_str:
            for attrib in metadata_str.split():
                if "=" not in attrib:
                    err = (f"Error on line {line_num}: "
                           f"Invalid metadata syntax '{attrib}'")
                    raise ParserError(err)
                key, value = attrib.split("=", 1)
                # we check if that key is duplicated in seen_keys
                if key in seen_keys:
                    err = (f"Error on line {line_num}: "
                           f"Duplicate metadata attribute '{key}'")
                    raise ParserError(err)
                seen_keys.add(key)

                if key == "zone":
                    valid_types = {"normal", "restricted",
                                   "priority", "blocked"}
                    if value not in valid_types:
                        err = (f"Error on line {line_num}: "
                               f"Invalid zone type '{value}'")
                        raise ParserError(err)
                    zone_type = value
                elif key == "color":
                    color = value
                elif key == "max_drones":
                    try:
                        max_drones = int(value)
                    except ValueError:
                        err = (f"Error on line {line_num}: "
                               f"max_drones must be a positive integer")
                        raise ParserError(err)
                    if max_drones <= 0:
                        err = (f"Error on line {line_num}: "
                               f"max_drones must be a positive integer")
                        raise ParserError(err)
                else:
                    err = (f"Error on line {line_num}: "
                           f"Unknown metadata key '{key}'")
                    raise ParserError(err)

        if is_start or is_end:
            max_drones = 999999

        return Zone(
            name=zone_name,
            x=x,
            y=y,
            zone_type=zone_type,
            color=color,
            max_drones=max_drones,
            is_start=is_start,
            is_end=is_end
        )

    def _parse_connection(
        self, content: str, line_num: int, graph: Graph
    ) -> Connection:
        """Parse connection definition line content."""
        metadata_str = ""
        if "[" in content:
            bracket_start = content.index("[")
            if "]" not in content:
                err = (f"Error on line {line_num}: "
                       f"Metadata block is not closed, missing ']'")
                raise ParserError(err)
            bracket_end = content.index("]")
            metadata_str = content[bracket_start + 1:bracket_end]
            trailing = content[bracket_end + 1:].strip()
            if trailing:
                err = (f"Error on line {line_num}: "
                       f"Unexpected text after metadata: '{trailing}'")
                raise ParserError(err)
            content = content[:bracket_start].strip()

        parts = content.split("-")
        if len(parts) != 2:
            err = (f"Error on line {line_num}: "
                   f"Connection must be 'zone1-zone2'")
            raise ParserError(err)

        zone1 = parts[0].strip()
        zone2 = parts[1].strip()

        if zone1 not in graph.zones:
            err = (f"Error on line {line_num}: "
                   f"Unknown zone '{zone1}' in connection")
            raise ParserError(err)
        if zone2 not in graph.zones:
            err = (f"Error on line {line_num}: "
                   f"Unknown zone '{zone2}' in connection")
            raise ParserError(err)

        # its one by default
        max_link_capacity = 1
        # for duplicate metadata conn keys
        seen_keys: set[str] = set()

        if metadata_str:
            for attrib in metadata_str.split():
                if "=" not in attrib:
                    err = (f"Error on line {line_num}: "
                           f"Invalid metadata syntax '{attrib}'")
                    raise ParserError(err)
                key, value = attrib.split("=", 1)
                if key in seen_keys:
                    err = (f"Error on line {line_num}: "
                           f"Duplicate metadata attribute '{key}'")
                    raise ParserError(err)
                seen_keys.add(key)

                if key == "max_link_capacity":
                    try:
                        max_link_capacity = int(value)
                    except ValueError:
                        err = (f"Error on line {line_num}: "
                               f"max_link_capacity must be a positive integer")
                        raise ParserError(err)
                    if max_link_capacity <= 0:
                        err = (f"Error on line {line_num}: "
                               f"max_link_capacity must be a positive integer")
                        raise ParserError(err)
                else:
                    err = (f"Error on line {line_num}: "
                           f"Unknown connection metadata key '{key}'")
                    raise ParserError(err)

        return Connection(
            zone1=zone1,
            zone2=zone2,
            max_link_capacity=max_link_capacity
        )

    def _check_duplicate_zone(
        self, name: str, graph: Graph, line_num: int
    ) -> None:
        """Check if zone name already exists."""
        if name in graph.zones:
            err = f"Error on line {line_num}: Duplicate zone name '{name}'"
            raise ParserError(err)

    def _check_duplicate_coords(
        self,
        x: int,
        y: int,
        zone_name: str,
        seen_coords: dict[tuple[int, int], str],
        line_num: int
    ) -> None:
        """Check if zone coordinates already exist."""
        coords = (x, y)
        if coords in seen_coords:
            existing = seen_coords[coords]
            err = (f"Error on line {line_num}: Duplicate coordinates "
                   f"({x}, {y}) already used by zone '{existing}'")
            raise ParserError(err)
        seen_coords[coords] = zone_name

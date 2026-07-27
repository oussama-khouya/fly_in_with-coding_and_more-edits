"""Parser: reads a map file and builds a Graph."""
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
        seen_connections: set[tuple[str, str]] = set()

        try:
            with open(filepath, "r") as f:
                lines = f.readlines()
        except FileNotFoundError:
            raise ParserError(f"Error: File '{filepath}' not found")

        for line_num, raw_line in enumerate(lines, start=1):
            line = raw_line.strip()

            if not line or line.startswith("#"):
                continue

            try:
                if line.startswith("nb_drones:"):
                    if has_drones:
                        raise ParserError(f"Error on line {line_num}: Duplicate nb_drones definition")
                    graph.nb_drones = self._parse_drone_count(line, line_num)
                    has_drones = True

                elif line.startswith("start_hub:"):
                    if has_start:
                        raise ParserError(f"Error on line {line_num}: Duplicate start_hub definition")
                    zone = self._parse_zone(line, "start_hub:", line_num, is_start=True)
                    self._check_duplicate_zone(zone.name, graph, line_num)
                    graph.add_zone(zone)
                    has_start = True

                elif line.startswith("end_hub:"):
                    if has_end:
                        raise ParserError(f"Error on line {line_num}: Duplicate end_hub definition")
                    zone = self._parse_zone(line, "end_hub:", line_num, is_end=True)
                    self._check_duplicate_zone(zone.name, graph, line_num)
                    graph.add_zone(zone)
                    has_end = True

                elif line.startswith("hub:"):
                    zone = self._parse_zone(line, "hub:", line_num)
                    self._check_duplicate_zone(zone.name, graph, line_num)
                    graph.add_zone(zone)

                elif line.startswith("connection:"):
                    conn = self._parse_connection(line, line_num, graph)
                    conn_key = conn.key()
                    if conn_key in seen_connections:
                        raise ParserError(f"Error on line {line_num}: Duplicate connection '{conn.zone1}-{conn.zone2}'")
                    seen_connections.add(conn_key)
                    graph.add_connection(conn)

                else:
                    raise ParserError(f"Error on line {line_num}: Unknown line format")

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

        return graph

    def _parse_drone_count(self, line: str, line_num: int) -> int:
        """Parse 'nb_drones: <number>'."""
        parts = line.split(":", 1)
        try:
            count = int(parts[1].strip())
        except (ValueError, IndexError):
            raise ParserError(f"Error on line {line_num}: nb_drones must be a positive integer")
        if count <= 0:
            raise ParserError(f"Error on line {line_num}: nb_drones must be a positive integer")
        return count

    def _parse_zone(self, line: str, prefix: str, line_num: int, is_start: bool = False, is_end: bool = False) -> Zone:
        """Parse a zone line like 'hub: name x y [metadata]'."""
        after_prefix = line[len(prefix):].strip()

        # Separate metadata if present
        metadata_str = ""
        if "[" in after_prefix:
            bracket_start = after_prefix.index("[")
            if "]" not in after_prefix:
                raise ParserError(f"Error on line {line_num}: Metadata block is not closed, missing ']'")
            bracket_end = after_prefix.index("]")
            metadata_str = after_prefix[bracket_start + 1:bracket_end]
            # Anything after the closing ] is invalid
            trailing = after_prefix[bracket_end + 1:].strip()
            if trailing:
                raise ParserError(f"Error on line {line_num}: Unexpected text after metadata: '{trailing}'")
            after_prefix = after_prefix[:bracket_start].strip()

        tokens = after_prefix.split()
        if len(tokens) < 3:
            raise ParserError(f"Error on line {line_num}: Zone must have name, x, and y")

        name = tokens[0]
        if "-" in name:
            raise ParserError(f"Error on line {line_num}: Zone name cannot contain dashes")

        try:
            x = int(tokens[1])
            y = int(tokens[2])
        except ValueError:
            raise ParserError(f"Error on line {line_num}: Coordinates must be integers")

        # Parse metadata with defaults
        zone_type = "normal"
        color = ""
        max_drones = 1

        if metadata_str:
            for tag in metadata_str.split():
                if "=" not in tag:
                    raise ParserError(f"Error on line {line_num}: Invalid metadata syntax '{tag}'")
                key, value = tag.split("=", 1)
                if key == "zone":
                    if value not in {"normal", "restricted", "priority", "blocked"}:
                        raise ParserError(f"Error on line {line_num}: Invalid zone type '{value}'")
                    zone_type = value
                elif key == "color":
                    color = value
                elif key == "max_drones":
                    try:
                        max_drones = int(value)
                    except ValueError:
                        raise ParserError(f"Error on line {line_num}: max_drones must be a positive integer")
                    if max_drones <= 0:
                        raise ParserError(f"Error on line {line_num}: max_drones must be a positive integer")
                else:
                    raise ParserError(f"Error on line {line_num}: Unknown metadata key '{key}'")

        # Start and end zones have unlimited capacity
        if is_start or is_end:
            max_drones = 999999

        return Zone(name=name, x=x, y=y, zone_type=zone_type, color=color, max_drones=max_drones, is_start=is_start, is_end=is_end)

    def _parse_connection(self, line: str, line_num: int, graph: Graph) -> Connection:
        """Parse 'connection: zone1-zone2 [metadata]'."""
        after_prefix = line[len("connection:"):].strip()

        # Separate metadata if present
        metadata_str = ""
        if "[" in after_prefix:
            bracket_start = after_prefix.index("[")
            if "]" not in after_prefix:
                raise ParserError(f"Error on line {line_num}: Metadata block is not closed, missing ']'")
            bracket_end = after_prefix.index("]")
            metadata_str = after_prefix[bracket_start + 1:bracket_end]
            trailing = after_prefix[bracket_end + 1:].strip()
            if trailing:
                raise ParserError(f"Error on line {line_num}: Unexpected text after metadata: '{trailing}'")
            after_prefix = after_prefix[:bracket_start].strip()

        parts = after_prefix.split("-")
        if len(parts) != 2:
            raise ParserError(f"Error on line {line_num}: Connection must be 'zone1-zone2'")

        zone1 = parts[0].strip()
        zone2 = parts[1].strip()

        if zone1 not in graph.zones:
            raise ParserError(f"Error on line {line_num}: Unknown zone '{zone1}' in connection")
        if zone2 not in graph.zones:
            raise ParserError(f"Error on line {line_num}: Unknown zone '{zone2}' in connection")

        # Parse metadata
        max_link_capacity = 1
        if metadata_str:
            for tag in metadata_str.split():
                if "=" not in tag:
                    raise ParserError(f"Error on line {line_num}: Invalid metadata syntax '{tag}'")
                key, value = tag.split("=", 1)
                if key == "max_link_capacity":
                    try:
                        max_link_capacity = int(value)
                    except ValueError:
                        raise ParserError(f"Error on line {line_num}: max_link_capacity must be a positive integer")
                    if max_link_capacity <= 0:
                        raise ParserError(f"Error on line {line_num}: max_link_capacity must be a positive integer")
                else:
                    raise ParserError(f"Error on line {line_num}: Unknown connection metadata key '{key}'")

        return Connection(zone1=zone1, zone2=zone2, max_link_capacity=max_link_capacity)

    def _check_duplicate_zone(self, name: str, graph: Graph, line_num: int) -> None:
        """Check if zone name already exists."""
        if name in graph.zones:
            raise ParserError(f"Error on line {line_num}: Duplicate zone name '{name}'")

"""Display: colored terminal output for visualization."""
from __future__ import annotations
from graph import Graph

# ANSI color codes
COLORS: dict[str, str] = {
    "red": "\033[91m", "green": "\033[92m", "yellow": "\033[93m",
    "blue": "\033[94m", "magenta": "\033[95m", "cyan": "\033[96m",
    "white": "\033[97m", "orange": "\033[38;5;208m", "gray": "\033[90m",
    "purple": "\033[35m", "brown": "\033[38;5;130m",
    "gold": "\033[38;5;220m", "lime": "\033[38;5;118m",
    "crimson": "\033[38;5;196m", "violet": "\033[38;5;135m",
    "black": "\033[30m", "maroon": "\033[38;5;88m", "darkred": "\033[38;5;52m",
    "rainbow": "\033[38;5;201m",
}
RESET = "\033[0m"


class Display:
    """Colored terminal output for the simulation."""

    def __init__(self, graph: Graph) -> None:
        self.graph = graph

    def colorize_line(self, line: str) -> str:
        """Apply zone color to each move token in the turn line."""
        colored_moves = []
        for move in line.split():
            dest = move.split("-")[-1]
            zone = self.graph.zones.get(dest)
            if zone and zone.color in COLORS:
                colored_moves.append(f"{COLORS[zone.color]}{move}{RESET}")
            else:
                colored_moves.append(move)
        return " ".join(colored_moves)



    def show_capacity(self, zone_capp: dict[str, int], cnx_usage: dict[tuple[str, str], int]) -> None:
        """Display capacity info for --capacity-info flag."""
        for zone_name, count in zone_capp.items():
            zone = self.graph.zones[zone_name]
            if zone.is_start or zone.is_end:
                continue
            print(f"zone {zone_name} : {count}/{zone.max_drones}")
        for (a, b), count in cnx_usage.items():
            conn = self.graph.get_connection(a, b)
            print(f"connection {a}-{b} : {count}/{conn.max_link_capacity}")

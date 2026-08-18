"""Display: colored terminal output for visualization."""
from __future__ import annotations
from src.models import Drone
from src.graph import Graph

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
BOLD = "\033[1m"


class Display:
    """Colored terminal output for the simulation."""

    def __init__(self, graph: Graph) -> None:
        """Initialize display."""
        self.graph = graph

    def colorize(self, zone_name: str) -> str:
        """Apply color to a zone name."""
        if zone_name in self.graph.zones:
            zone = self.graph.zones[zone_name]
            if zone.color in COLORS:
                return f"{COLORS[zone.color]}{zone_name}{RESET}"
        return zone_name

    # move_line in that turn like D1-A D2-B D3-END
    def show_turn(self, turn: int, move_line: str) -> None:
        """Display one turn with colors."""
        print(f"\n{BOLD}--- Turn {turn} ---{RESET}")
        for part in move_line.split():
            dash_idx = part.index("-")
            drone_id = part[:dash_idx]
            dest = part[dash_idx + 1:]
            print(f"  {drone_id} → {self.colorize(dest)}")

    def show_summary(self, total_turns: int, drones: list[Drone]) -> None:
        """Display summary after simulation."""
        delivered = sum(1 for d in drones if d.delivered)
        print(f"\n{BOLD}=== Simulation Complete ==={RESET}")
        print(f"  Total turns: {total_turns}")
        print(f"  Drones delivered: {delivered}/{len(drones)}")

    # Live coding: display capacity info for --capacity-info flag
    def show_capacity(
        self,
        zone_capp: dict[str, int],
        cnx_usage: dict[tuple[str, str], int]
    ) -> None:
        """Display capacity info for --capacity-info flag."""
        for zone_name, count in zone_capp.items():
            zone = self.graph.zones[zone_name]
            print(f"zone {zone_name} : {count}/{zone.max_drones}")
        for (a, b), count in cnx_usage.items():
            conn = self.graph.get_connection(a, b)
            print(f"connection {a}-{b} : {count}/{conn.max_link_capacity}")

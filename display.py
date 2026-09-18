"""Display: colored terminal output for visualization."""
from typing import Dict, List
from graph import Graph

# ANSI color codes
COLORS: Dict[str, str] = {
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

    # Added: Fallback for arbitrary single-word colors as mandated by fly.pdf
    # (Page 11: "Accepted values for color are any valid single-word strings...
    # There is no fixed list of allowed colors.")
    def get_color_code(self, color_name: str) -> str:
        """Get ANSI color escape code, falling back to 256-color hash."""
        if color_name in COLORS:
            return COLORS[color_name]
        # Deterministic 256-color ANSI code for any arbitrary single-word color
        code = 16 + (abs(hash(color_name)) % 216)
        return f"\033[38;5;{code}m"

    def colorize_line(self, line: str) -> str:
        """Apply zone color to each move token in the turn line."""
        colored_moves: List[str] = []
        for move in line.split():
            dest = move.split("-")[-1]
            zone = self.graph.zones.get(dest)
            if zone and zone.color:
                color_code = self.get_color_code(zone.color)
                colored_moves.append(f"{color_code}{move}{RESET}")
            else:
                colored_moves.append(move)
        return " ".join(colored_moves)

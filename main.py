"""Fly-in: Drone simulation - Entry point."""
from __future__ import annotations
import sys
from models import Drone, FlyinError
from parser import Parser
from pathfinder import Pathfinder
from scheduler import Scheduler
from simulation import Simulation
from display import Display


def main() -> None:
    capacity_info = "--capacity-info" in sys.argv
    args = [a for a in sys.argv[1:] if a != "--capacity-info"]

    if not args:
        if not sys.stdin.isatty():
            map_file = "-"
        else:
            msg = "Usage: python3 main.py <map_file> [--capacity-info]"
            print(msg, file=sys.stderr)
            sys.exit(1)
    else:
        map_file = args[0]

    try:
        # Step 1: Parse the map file
        graph = Parser().parse(map_file)

        # Step 2: Find paths
        paths = Pathfinder().find_paths(graph, graph.nb_drones)

        # Step 3: Create drones and assign paths
        drones: list[Drone] = [
            Drone(id=i + 1) for i in range(graph.nb_drones)
        ]
        Scheduler().assign(drones, paths, graph)

        # Step 4: Run simulation
        sim = Simulation(graph, drones, capacity_info=capacity_info)
        output_lines = sim.run()

        # Step 5: Output results colorized
        display = Display(graph)
        for i, line in enumerate(output_lines):
            print(display.colorize_line(line))
            if capacity_info and i < len(sim.capacity_lines):
                print(f"  [Capacity] {sim.capacity_lines[i]}")

    except KeyboardInterrupt:
        print("Error: Execution interrupted by user", file=sys.stderr)
        sys.exit(1)
    except EOFError:
        print("Error: Unexpected end of input", file=sys.stderr)
        sys.exit(1)
    except FlyinError as e:
        print(str(e), file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"Unexpected error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()

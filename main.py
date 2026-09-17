"""Fly-in: Drone simulation - Entry point."""
import sys
from typing import List
from models import Drone, FlyinError
from parser import Parser
from pathfinder import Pathfinder
from scheduler import Scheduler
from simulation import Simulation
from display import Display


def main() -> None:
    if len(sys.argv) < 2:
        msg = "Usage: python3 main.py <map_file>"
        print(msg, file=sys.stderr)
        sys.exit(1)

    map_file = sys.argv[1]

    try:
        # Step 1: Parse the map file
        graph = Parser().parse(map_file)

        # Step 2: Find pathsshow_capacity
        paths = Pathfinder().find_paths(graph, graph.nb_drones)

        # Step 3: Create drones and assign paths
        drones: List[Drone] = [Drone(id=i + 1) for i in range(graph.nb_drones)]
        Scheduler().assign(drones, paths, graph)

        # Step 4: Run simulation
        sim = Simulation(graph, drones)
        output_lines = sim.run()
        # for how many turns we get
        turn = sim.turn

        # Step 5: Output results colorized
        display = Display(graph)
        for line in output_lines:
            print(display.colorize_line(line))

        print(f"number of turns : {turn}")

    except KeyboardInterrupt:
        print("Error: Execution interrupted by user", file=sys.stderr)
        sys.exit(1)
    except FlyinError as e:
        print(str(e), file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"Unexpected error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()

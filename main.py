"""Fly-in: Drone simulation - Entry point."""
from __future__ import annotations
import sys
from src.models import Drone, FlyinError
from src.parser import Parser
from src.pathfinder import Pathfinder
from src.scheduler import Scheduler
from src.simulation import Simulation
from src.display import Display


def main() -> None:
    """Main entry point. Usage: python3 main.py <map_file> [--capacity-info]"""
    if len(sys.argv) < 2:
        msg = "Usage: python3 main.py <map_file> [--capacity-info]"
        print(msg, file=sys.stderr)
        sys.exit(1)

    map_file = sys.argv[1]
    show_capacity = "--capacity-info" in sys.argv

    try:
        # Step 1: Parse the map file
        graph = Parser().parse(map_file)

        # Step 2: Find paths
        paths = Pathfinder().find_paths(graph, graph.nb_drones)

        # Step 3: Create drones and assign paths
        drones = [Drone(id=i + 1) for i in range(graph.nb_drones)]
        Scheduler().assign(drones, paths, graph)

        # Step 4: Run simulation
        sim = Simulation(graph, drones)
        output_lines = sim.run()

        # Step 5: Output results
        display = Display(graph)

        # Raw simulation output (required format)
        for line in output_lines:
            print(line)

        # Colored visualization below
        print()
        for i, line in enumerate(output_lines, start=1):
            display.show_turn(i, line)
            # Live coding: pass turn's capacity snapshot (zone_occ, conn_usage)  # noqa: E501
            if show_capacity:
                z_occ, c_used = sim.capacity_history[i - 1]
                display.show_capacity_info(z_occ, c_used)

        display.show_summary(len(output_lines), drones)

    except FlyinError as e:
        print(str(e), file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"Unexpected error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()

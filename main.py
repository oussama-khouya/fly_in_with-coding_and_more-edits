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
   
    """Main entry point. Usage: python3 main.py <map_file> [--capacity-info]"""
    if len(sys.argv) < 2:
        msg = "Usage: python3 main.py <map_file> [--capacity-info]"
        print(msg, file=sys.stderr)
        sys.exit(1)

    cap_flag = "--capacity-info" in sys.argv    
    map_file = sys.argv[1]

    try:
        # Step 1: Parse the map file
        graph = Parser().parse(map_file)

        # Step 2: Find paths
        paths = Pathfinder().find_paths(graph, graph.nb_drones)

        # Step 3: Create drones and assign paths
        drones: list[Drone] = [Drone(id=i + 1) for i in range(graph.nb_drones)]
        Scheduler().assign(drones, paths, graph)

        # Step 4: Run simulation
        sim = Simulation(graph, drones)
        output_lines = sim.run()
        # for how many turns we get
        turn = sim.turn

        # Step 5: Output results colorized
        display = Display(graph)
        for i, line in enumerate(output_lines):
            print(display.colorize_line(line))

            # Live coding: pass turn's capacity snapshot (zone_occ, conn_usage)  # noqa: E501
            if cap_flag:
                zone_cap, cnx_usage = sim.capacity_history[i - 1]
                # we reate the the methode that will print that
                display.show_capacity(zone_cap, cnx_usage)


        print(f"number of turns : {turn}")

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

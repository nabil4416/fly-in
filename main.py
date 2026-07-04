"""Main entry point for the Fly-in drone simulation.

This script orchestrates the entire simulation pipeline:
1. Parse command-line arguments
2. Load and validate the input file
3. Build the graph representation
4. Initialize pathfinder and scheduler
5. Run the simulation
6. Output results
"""

import sys
import argparse
from pathlib import Path

from core.graph import Graph, GraphError
from core.parser import Parser
from core.pathfinder import Pathfinder
from core.scheduler import Scheduler, SchedulingError
from core.simulator import Simulator, SimulationError
from utils.exceptions import ParsingError


def print_error(message: str) -> None:
    """Print error message to stderr.

    Args:
        message: Error message to display.
    """
    print(f"❌ Error: {message}", file=sys.stderr)


def print_info(message: str) -> None:
    """Print info message to stdout.

    Args:
        message: Info message to display.
    """
    print(f"ℹ️  {message}")


def main() -> int:
    """Main entry point for the simulation.

    Returns:
        Exit code: 0 if successful, 1 if error occurred.
    """
    arg_parser = argparse.ArgumentParser(
        description="Run the Fly-in drone simulation"
    )
    arg_parser.add_argument(
        "--capacity-info",
        action="store_true",
        help="print zone and connection capacity usage after simulation",
    )
    arg_parser.add_argument("input_file", help="path to a Fly-in map file")
    args = arg_parser.parse_args()

    input_file = args.input_file

    # Check file exists
    if not Path(input_file).exists():
        print_error(f"File not found: {input_file}")
        return 1

    # ========== STEP 1: PARSE INPUT ==========
    print_info(f"Loading input file: {input_file}")
    try:
        parser = Parser()
        input_data = parser.parse_file(input_file)
        print_info(
            f"✓ Parsed: {input_data.num_drones} drones, "
            f"{len(input_data.zones)} zones, "
            f"{len(input_data.connections)} connections"
        )
    except ParsingError as e:
        print_error(f"Parsing failed: {e}")
        return 1
    except Exception as e:
        print_error(f"Unexpected error during parsing: {e}")
        return 1

    # ========== STEP 2: BUILD GRAPH ==========
    print_info("Building graph representation...")
    try:
        graph = Graph(input_data.zones, input_data.connections)
        print_info("✓ Graph built successfully")
    except GraphError as e:
        print_error(f"Graph construction failed: {e}")
        return 1
    except Exception as e:
        print_error(f"Unexpected error during graph construction: {e}")
        return 1

    # ========== STEP 3: VALIDATE CONNECTIVITY ==========
    print_info("Validating path connectivity...")
    try:
        if not graph.is_reachable(
            input_data.start_zone.name,
            input_data.end_zone.name,
        ):
            print_error(
                f"No path exists from {input_data.start_zone.name} "
                f"to {input_data.end_zone.name}"
            )
            return 1
        print_info("✓ Path exists from start to end zone")
    except GraphError as e:
        print_error(f"Connectivity validation failed: {e}")
        return 1

    # ========== STEP 4: CREATE DRONES ==========
    print_info("Creating drones...")
    try:
        drones = Parser.create_drones(
            input_data.num_drones,
            input_data.start_zone,
            input_data.end_zone,
        )
        print_info(f"✓ Created {len(drones)} drones")
    except Exception as e:
        print_error(f"Drone creation failed: {e}")
        return 1

    # ========== STEP 5: INITIALIZE PATHFINDER ==========
    print_info("Initializing pathfinder...")
    try:
        pathfinder = Pathfinder(graph)
        print_info("✓ Pathfinder ready")
    except Exception as e:
        print_error(f"Pathfinder initialization failed: {e}")
        return 1

    # ========== STEP 6: INITIALIZE SCHEDULER ==========
    print_info("Initializing scheduler...")
    try:
        scheduler = Scheduler(graph, pathfinder)
        print_info("✓ Scheduler ready")
    except Exception as e:
        print_error(f"Scheduler initialization failed: {e}")
        return 1

    # ========== STEP 7: RUN SIMULATION ==========
    print_info("Running simulation...")
    try:
        simulator = Simulator(
            graph,
            scheduler,
            drones,
            input_data.start_zone.name,
            input_data.end_zone.name,
        )
        state = simulator.run()
        print_info(
            f"✓ Simulation completed in {state.metrics.total_turns} turns"
        )
    except SchedulingError as e:
        print_error(f"Scheduling failed: {e}")
        return 1
    except SimulationError as e:
        print_error(f"Simulation failed: {e}")
        return 1
    except Exception as e:
        print_error(f"Unexpected error during simulation: {e}")
        return 1

    # ========== STEP 8: OUTPUT RESULTS ==========
    print_info("Generating output...")
    try:
        output = simulator.get_output()
        if output:
            print("\n" + "=" * 60)
            print("SIMULATION OUTPUT")
            print("=" * 60)
            print(output)
            print("=" * 60)
        else:
            print("⚠️  No movement output generated")

        if args.capacity_info:
            capacity_output = simulator.get_capacity_output()
            if capacity_output:
                print("\n" + "=" * 60)
                print("CAPACITY INFO")
                print("=" * 60)
                print(capacity_output)
                print("=" * 60)

        # Print summary
        summary = simulator.get_summary()
        print("\n" + summary)

    except Exception as e:
        print_error(f"Output generation failed: {e}")
        return 1

    print_info("✓ All done!")
    return 0


if __name__ == "__main__":
    sys.exit(main())

#!/usr/bin/env python3
"""Generate Plotly HTML visualization for Fly-in simulation.

Usage:
    python3 scripts/visualize.py maps/challenger/01_the_impossible_dream.txt
    python3 scripts/visualize.py <input_file> --output output/my_viz.html
"""

from __future__ import annotations

import sys
from pathlib import Path
import argparse

# Ensure project root is importable when running this file directly.
PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from core.graph import Graph
from core.parser import Parser
from core.pathfinder import Pathfinder
from core.scheduler import Scheduler
from core.simulator import Simulator
from models.drone import Drone
from models.zone import ZoneCategory
from visualizer.plotly_visualizer import PlotlyVisualizer


def resolve_start_end(parsed) -> tuple[str, str]:
    start_zone = next(
        (z.name for z in parsed.zones.values() if z.category == ZoneCategory.START_HUB),
        None,
    )
    end_zone = next(
        (z.name for z in parsed.zones.values() if z.category == ZoneCategory.END_HUB),
        None,
    )

    if not start_zone or not end_zone:
        raise ValueError(
            f"Could not resolve start/end zones: start={start_zone}, end={end_zone}"
        )
    return start_zone, end_zone


def run_visualization(input_file: str, output_file: str) -> None:
    parsed = Parser().parse_file(input_file)

    graph = Graph(parsed.zones, parsed.connections)
    pathfinder = Pathfinder(graph)
    scheduler = Scheduler(graph, pathfinder)

    start_zone, end_zone = resolve_start_end(parsed)

    drones = [
        Drone(
            drone_id=f"D{i+1}",
            current_zone=start_zone,
            destination_zone=end_zone,
        )
        for i in range(parsed.num_drones)
    ]

    simulator = Simulator(
        graph=graph,
        scheduler=scheduler,
        drones=drones,
        start_zone=start_zone,
        end_zone=end_zone,
    )

    state = simulator.run()

    viz = PlotlyVisualizer(
        graph=graph,
        simulation_results=state,
        start_zone=start_zone,
        end_zone=end_zone,
    )
    viz.save(output_file)

    print(f"Saved visualization: {output_file}")


def main() -> None:
    parser = argparse.ArgumentParser(description="Fly-in Plotly visualizer")
    parser.add_argument("input_file", help="Path to input map file")
    parser.add_argument(
        "--output",
        default="output/flyin_visualization.html",
        help="Output HTML path (default: output/flyin_visualization.html)",
    )
    args = parser.parse_args()

    input_path = Path(args.input_file)
    if not input_path.is_file():
        raise FileNotFoundError(f"Input file not found: {args.input_file}")

    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    run_visualization(args.input_file, str(output_path))


if __name__ == "__main__":
    main()

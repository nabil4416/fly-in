"""Simulation engine for coordinating drone movements turn-by-turn.

The simulator manages the complete lifecycle of a simulation, tracking
drone states, enforcing constraints, and generating output in the
specified format.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional

from core.graph import Graph
from core.scheduler import Scheduler, SchedulingResult
from models.drone import Drone
from models.enums import DroneState
from models.zone import ZoneType
from utils.exceptions import FlyInException


class SimulationError(FlyInException):
    """Exception raised during simulation execution."""

    pass


@dataclass
class SimulationMetrics:
    """Track performance metrics during simulation.

    Attributes:
        total_turns: Number of turns to complete simulation.
        total_drones_moved: Total number of drone movements across all turns.
        drones_per_turn: List of drone counts moved in each turn.
        max_drones_per_turn: Maximum drones moved in any single turn.
        avg_drones_per_turn: Average drones moved per turn.
        zone_utilization: Dictionary mapping zone names to max occupancy.
    """

    total_turns: int = 0
    total_drones_moved: int = 0
    drones_per_turn: list[int] = field(default_factory=list)
    max_drones_per_turn: int = 0
    avg_drones_per_turn: float = 0.0
    zone_utilization: dict[str, int] = field(default_factory=dict)

    def calculate_averages(self) -> None:
        """Calculate derived metrics from raw data."""
        if not self.drones_per_turn:
            self.avg_drones_per_turn = 0.0
            return

        self.total_drones_moved = sum(self.drones_per_turn)
        self.max_drones_per_turn = max(self.drones_per_turn)
        self.avg_drones_per_turn = self.total_drones_moved / len(
            self.drones_per_turn
        )

    def __repr__(self) -> str:
        """Return readable representation."""
        return (
            f"SimulationMetrics("
            f"turns={self.total_turns}, "
            f"total_moved={self.total_drones_moved}, "
            f"avg_per_turn={self.avg_drones_per_turn:.2f})"
        )


@dataclass
class SimulationState:
    """Complete state snapshot at a given point in simulation.

    Attributes:
        turn_number: Current turn number (0 if not started).
        drones: List of all drone objects.
        is_running: Whether simulation is still executing.
        is_completed: Whether all drones have been delivered.
        moves: List of SchedulingResult for each completed turn.
        metrics: Performance metrics.
    """

    turn_number: int = 0
    drones: list[Drone] = field(default_factory=list)
    is_running: bool = False
    is_completed: bool = False
    moves: list[SchedulingResult] = field(default_factory=list)
    metrics: SimulationMetrics = field(default_factory=SimulationMetrics)

    def __repr__(self) -> str:
        """Return readable representation."""
        return (
            f"SimulationState("
            f"turn={self.turn_number}, "
            f"drones={len(self.drones)}, "
            f"completed={self.is_completed})"
        )


class Simulator:
    """Coordinate drone movements and manage simulation lifecycle.

    The simulator orchestrates the scheduler to produce valid movements,
    tracks drone states through the entire execution, and generates
    output in the required format.

    Responsibilities:
    - Initialize and manage simulation state
    - Execute turn-by-turn movements via scheduler
    - Track metrics and performance
    - Generate formatted output
    - Validate constraints and prevent conflicts
    """

    def __init__(
        self,
        graph: Graph,
        scheduler: Scheduler,
        drones: list[Drone],
        start_zone: str,
        end_zone: str,
    ) -> None:
        """Initialize simulator.

        Args:
            graph: Graph representation of zones and connections.
            scheduler: Scheduler for computing movements.
            drones: List of drones to simulate.
            start_zone: Name of the starting zone.
            end_zone: Name of the ending zone.

        Raises:
            SimulationError: If initialization fails.
        """
        if not drones:
            raise SimulationError("Cannot simulate with no drones")

        self.graph = graph
        self.scheduler = scheduler
        self.start_zone = start_zone
        self.end_zone = end_zone

        # State tracking
        self.state = SimulationState(
            drones=[d for d in drones],  # Copy list
            metrics=SimulationMetrics(),
        )

        # Output history
        self.turn_output: list[str] = []

    def run(self) -> SimulationState:
        """Execute the complete simulation.

        Runs the simulation until all drones reach the end zone or
        an error occurs.

        Returns:
            Final SimulationState with all metrics.

        Raises:
            SimulationError: If simulation fails during execution.
        """
        self.state.is_running = True

        try:
            result = self.scheduler.schedule_all_drones(
                self.state.drones,
                self.start_zone,
                self.end_zone,
            )

            # Record all scheduling results
            self.state.moves = result

            # Process each turn for metrics and output
            for turn_idx, scheduling_result in enumerate(result, start=1):
                self._process_turn(scheduling_result, turn_idx)

            # Mark simulation as complete
            if all(d.is_delivered for d in self.state.drones):
                self.state.is_completed = True
                self.state.turn_number = len(result)
            else:
                raise SimulationError(
                    "Simulation ended but not all drones delivered"
                )

        except Exception as e:
            self.state.is_running = False
            raise SimulationError(f"Simulation failed: {e}") from e

        finally:
            self.state.is_running = False
            self._calculate_metrics()

        return self.state

    def _process_turn(
        self, scheduling_result: SchedulingResult, turn_number: int
    ) -> None:
        """Process a single turn and generate output.

        Args:
            scheduling_result: Result from scheduler for this turn.
            turn_number: Current turn number (1-indexed).
        """
        # Build output line for this turn
        output_parts = []

        for drone_id, destination in scheduling_result.moves.items():
            # Find the drone
            drone = None
            for d in self.state.drones:
                if d.drone_id == drone_id:
                    drone = d
                    break

            if drone is None:
                continue

            # Determine movement type
            if drone.state == DroneState.IN_TRANSIT_RESTRICTED:
                # In transit to restricted zone, show connection
                output_parts.append(
                    f"{drone_id}-{drone.current_zone}-{destination}"
                )
            else:
                # Normal movement
                output_parts.append(f"{drone_id}-{destination}")

        # Add turn to output if there were movements
        if output_parts:
            turn_line = f"Turn {turn_number}: {' '.join(output_parts)}"
            self.turn_output.append(turn_line)

        # Track metrics
        self.state.metrics.drones_per_turn.append(
            len(scheduling_result.moves)
        )
        self.state.metrics.total_turns = turn_number

    def _calculate_metrics(self) -> None:
        """Calculate final simulation metrics."""
        self.state.metrics.calculate_averages()

        # Track zone utilization by analyzing drone paths
        zone_peak_occupancy: dict[str, int] = {}
        for drone in self.state.drones:
            for zone_name in drone.path:
                zone_peak_occupancy[zone_name] = (
                    zone_peak_occupancy.get(zone_name, 0) + 1
                )

        self.state.metrics.zone_utilization = zone_peak_occupancy

    def get_output(self) -> str:
        """Get formatted simulation output.

        Returns:
            Multi-line string with turn-by-turn drone movements.
        """
        return "\n".join(self.turn_output)

    def get_summary(self) -> str:
        """Get simulation summary with metrics.

        Returns:
            Formatted summary string.
        """
        if not self.state.is_completed:
            return "Simulation not completed"

        lines = [
            "=" * 60,
            "SIMULATION SUMMARY",
            "=" * 60,
            f"Total Turns: {self.state.metrics.total_turns}",
            f"Total Drones: {len(self.state.drones)}",
            f"Drones Moved Per Turn: {self.state.metrics.avg_drones_per_turn:.2f} avg",
            f"Max Drones Per Turn: {self.state.metrics.max_drones_per_turn}",
            "=" * 60,
        ]

        return "\n".join(lines)

    def get_state(self) -> SimulationState:
        """Get current simulation state snapshot.

        Returns:
            Current SimulationState.
        """
        return self.state

    def __repr__(self) -> str:
        """Return readable representation."""
        return (
            f"Simulator("
            f"drones={len(self.state.drones)}, "
            f"state={self.state})"
        )

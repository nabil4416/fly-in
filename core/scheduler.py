"""Scheduler for coordinating drone movements in the simulation.

The scheduler assigns drones to optimal paths, manages zone and connection
capacities, and prevents deadlocks while ensuring simultaneous movement.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

from core.graph import Graph
from core.pathfinder import Pathfinder, PathfindingResult
from models.drone import Drone
from models.enums import DroneState
from models.zone import ZoneType
from utils.exceptions import FlyInException


class SchedulingError(FlyInException):
    """Exception raised when scheduling operations fail."""

    pass


@dataclass
class SchedulingResult:
    """Result of a scheduling operation for a single turn.

    Attributes:
        moves: Dictionary mapping drone_id to destination zone name.
        waiting_drones: List of drone IDs that are waiting this turn.
        completed_drones: List of drone IDs that reached the end zone.
        turn_number: Current simulation turn number.
        is_valid: Whether all moves respect constraints.
    """

    moves: dict[str, str]
    waiting_drones: list[str]
    completed_drones: list[str]
    turn_number: int
    is_valid: bool

    def has_moves(self) -> bool:
        """Check if any drones moved in this turn."""
        return len(self.moves) > 0

    def __repr__(self) -> str:
        """Return readable representation."""
        return (
            f"SchedulingResult(turn={self.turn_number}, "
            f"moves={len(self.moves)}, waiting={len(self.waiting_drones)}, "
            f"completed={len(self.completed_drones)})"
        )


class Scheduler:
    """Coordinate drone movements while respecting all constraints.

    Responsibilities:
    - Assign drones to paths computed by pathfinder
    - Respect zone capacity constraints
    - Respect connection capacity constraints
    - Prevent deadlocks and conflicts
    - Handle restricted zone 2-turn movements
    """

    def __init__(self, graph: Graph, pathfinder: Pathfinder) -> None:
        """Initialize scheduler with graph and pathfinder.

        Args:
            graph: Graph representation of zones and connections.
            pathfinder: Pathfinder for computing optimal paths.
        """
        self.graph = graph
        self.pathfinder = pathfinder

    def schedule_all_drones(
        self,
        drones: list[Drone],
        start_zone: str,
        end_zone: str,
    ) -> list[SchedulingResult]:
        """Schedule all drones from start to end zone.

        Args:
            drones: List of drones to schedule.
            start_zone: Name of the starting zone.
            end_zone: Name of the ending zone.

        Returns:
            List of SchedulingResult objects, one per turn.

        Raises:
            SchedulingError: If scheduling fails.
        """
        if not drones:
            raise SchedulingError("Cannot schedule empty drone list")

        # Initialize paths for all drones
        for drone in drones:
            try:
                result = self.pathfinder.find_shortest_path(
                    start_zone, end_zone
                )
                if result is None:
                    raise SchedulingError(
                        f"No path found from {start_zone} to {end_zone}"
                    )
                drone.set_path(result.path)
            except Exception as e:
                raise SchedulingError(
                    f"Failed to compute path for {drone.drone_id}: {e}"
                ) from e

        # Simulate turn by turn
        results: list[SchedulingResult] = []
        turn = 0
        max_turns = 10000  # Prevent infinite loops

        while (
            not all(drone.is_delivered for drone in drones)
            and turn < max_turns
        ):
            turn += 1
            result = self.schedule_turn(drones, turn)
            results.append(result)

            if turn >= max_turns:
                raise SchedulingError(
                    f"Simulation exceeded {max_turns} turns (possible deadlock)"
                )

        return results

    def schedule_turn(
        self, drones: list[Drone], turn_number: int
    ) -> SchedulingResult:
        """Schedule movements for a single turn.

        Args:
            drones: List of all drones in simulation.
            turn_number: Current turn number (1-indexed).

        Returns:
            SchedulingResult containing moves and status for this turn.
        """
        # Filter active drones (not delivered)
        active_drones = [d for d in drones if not d.is_delivered]

        # Track zone occupancy for this turn
        zone_occupancy: dict[str, int] = {}

        # Calculate zone capacities
        for zone_name, zone in self.graph.zones.items():
            zone_occupancy[zone_name] = 0

        # Count current occupancy
        for drone in active_drones:
            zone_occupancy[drone.current_zone] = (
                zone_occupancy.get(drone.current_zone, 0) + 1
            )

        # Compute candidate moves
        candidate_moves: dict[str, Optional[str]] = {}
        for drone in active_drones:
            if drone.is_delivered:
                continue

            # Handle restricted zone transit completion
            if drone.state == DroneState.IN_TRANSIT_RESTRICTED:
                next_zone = drone.next_zone
                if next_zone is None:
                    raise SchedulingError(
                        f"Drone {drone.drone_id} in transit but no next zone"
                    )
                candidate_moves[drone.drone_id] = next_zone
                continue

            # Get next zone
            next_zone = drone.next_zone
            if next_zone is None:
                # Reached destination
                if drone.current_zone == drone.destination_zone:
                    candidate_moves[drone.drone_id] = None
                    continue
                raise SchedulingError(
                    f"Drone {drone.drone_id} has no path to destination"
                )

            # Check if next zone is blocked
            next_zone_obj = self.graph.get_zone(next_zone)
            if next_zone_obj is None:
                raise SchedulingError(f"Zone not found: {next_zone}")

            if next_zone_obj.is_blocked:
                # Path is blocked, should have been avoided by pathfinder
                raise SchedulingError(
                    f"Drone {drone.drone_id} path includes blocked zone: "
                    f"{next_zone}"
                )

            candidate_moves[drone.drone_id] = next_zone

        # Validate and assign moves
        moves = self._validate_and_assign_moves(
            active_drones, candidate_moves, zone_occupancy, turn_number
        )

        # Execute moves
        completed = []
        waiting = []

        for drone in active_drones:
            if drone.is_delivered:
                continue

            move_to = moves.get(drone.drone_id)

            if move_to is None:
                # No move assigned (waiting or at destination)
                if drone.current_zone == drone.destination_zone:
                    drone.mark_delivered()
                    completed.append(drone.drone_id)
                else:
                    drone.set_waiting()
                    waiting.append(drone.drone_id)
            else:
                # Execute move
                self._execute_move(drone, move_to)

        return SchedulingResult(
            moves=moves,
            waiting_drones=waiting,
            completed_drones=completed,
            turn_number=turn_number,
            is_valid=True,
        )

    def _validate_and_assign_moves(
        self,
        drones: list[Drone],
        candidate_moves: dict[str, Optional[str]],
        zone_occupancy: dict[str, int],
        turn_number: int,
    ) -> dict[str, str]:
        """Validate candidate moves and resolve conflicts.

        Strategy:
        1. Prioritize drones already in transit (must complete)
        2. Prioritize drones closer to destination
        3. Resolve capacity conflicts by delaying some drones

        Args:
            drones: List of active drones.
            candidate_moves: Proposed moves (drone_id → zone).
            zone_occupancy: Current occupancy of each zone.
            turn_number: Current turn number.

        Returns:
            Dictionary of validated moves (drone_id → zone).
        """
        moves: dict[str, str] = {}

        # Separate drones by priority
        in_transit = []
        regular = []

        for drone in drones:
            if drone.is_delivered:
                continue
            if drone.state == DroneState.IN_TRANSIT_RESTRICTED:
                in_transit.append(drone)
            else:
                regular.append(drone)

        # Process in-transit drones first (must complete)
        for drone in in_transit:
            next_zone = drone.next_zone
            if next_zone is None:
                continue

            if candidate_moves.get(drone.drone_id) != next_zone:
                raise SchedulingError(
                    f"Drone {drone.drone_id} must reach {next_zone} "
                    f"(in restricted transit)"
                )

            # Ensure capacity
            next_zone_obj = self.graph.get_zone(next_zone)
            if next_zone_obj is None:
                raise SchedulingError(f"Zone not found: {next_zone}")

            current_occupancy = self._get_future_occupancy(
                next_zone, moves, zone_occupancy
            )

            if not next_zone_obj.has_capacity(current_occupancy):
                # Deadlock: cannot complete restricted transit
                raise SchedulingError(
                    f"Deadlock: Drone {drone.drone_id} cannot reach "
                    f"{next_zone} (capacity full)"
                )

            moves[drone.drone_id] = next_zone
            zone_occupancy[next_zone] = (
                zone_occupancy.get(next_zone, 0) + 1
            )

        # Process regular drones (greedy assignment)
        for drone in regular:
            next_zone = candidate_moves.get(drone.drone_id)

            if next_zone is None:
                # Drone is waiting or at destination
                continue

            next_zone_obj = self.graph.get_zone(next_zone)
            if next_zone_obj is None:
                continue

            # Check capacity
            current_occupancy = self._get_future_occupancy(
                next_zone, moves, zone_occupancy
            )

            # Check connection capacity
            conn = self.graph.get_connection(drone.current_zone, next_zone)
            if conn is not None:
                current_link_occupancy = self._get_connection_occupancy(
                    drone.current_zone, next_zone, moves, drones
                )
                if current_link_occupancy >= conn.max_link_capacity:
                    # Connection is saturated
                    continue

            if next_zone_obj.has_capacity(current_occupancy):
                # Assign move
                moves[drone.drone_id] = next_zone
                zone_occupancy[next_zone] = (
                    zone_occupancy.get(next_zone, 0) + 1
                )
            # else: drone waits (stays in current zone)

        return moves

    def _get_future_occupancy(
        self,
        zone_name: str,
        moves: dict[str, str],
        current_occupancy: dict[str, int],
    ) -> int:
        """Get the occupancy of a zone after all assigned moves.

        Args:
            zone_name: Name of the zone.
            moves: Dictionary of assigned moves.
            current_occupancy: Current occupancy before moves.

        Returns:
            Projected occupancy after all assigned moves.
        """
        occupancy = current_occupancy.get(zone_name, 0)

        # Count new drones entering this zone
        for dest in moves.values():
            if dest == zone_name:
                occupancy += 1

        return occupancy

    def _get_connection_occupancy(
        self,
        zone_a: str,
        zone_b: str,
        moves: dict[str, str],
        drones: list[Drone],
    ) -> int:
        """Get the number of drones using a connection this turn.

        Args:
            zone_a: First zone of the connection.
            zone_b: Second zone of the connection.
            moves: Dictionary of assigned moves.
            drones: List of all drones.

        Returns:
            Number of drones traversing this connection.
        """
        count = 0

        for drone_id, dest in moves.items():
            if dest == zone_b:
                # Find this drone
                for drone in drones:
                    if drone.drone_id == drone_id:
                        if drone.current_zone == zone_a:
                            count += 1
                        break

        return count

    def _execute_move(self, drone: Drone, destination: str) -> None:
        """Execute a single drone's movement.

        Handles both normal and restricted zone movements.

        Args:
            drone: Drone to move.
            destination: Name of destination zone.

        Raises:
            SchedulingError: If move is invalid.
        """
        destination_zone = self.graph.get_zone(destination)
        if destination_zone is None:
            raise SchedulingError(f"Zone not found: {destination}")

        # Check if restricted
        if destination_zone.zone_type == ZoneType.RESTRICTED:
            # Start restricted transit
            drone.start_restricted_transit(
                f"{drone.current_zone}-{destination}"
            )
        else:
            # Normal move
            drone.move_to(destination)

            # Check if at destination
            if drone.current_zone == drone.destination_zone:
                drone.mark_delivered()

    def __repr__(self) -> str:
        """Return readable representation."""
        return f"Scheduler(graph={self.graph}, pathfinder={self.pathfinder})"
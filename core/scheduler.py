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
    move_outputs: dict[str, str]
    waiting_drones: list[str]
    completed_drones: list[str]
    turn_number: int
    is_valid: bool
    zone_occupancy: dict[str, int]
    connection_usage: dict[str, int]

    def has_moves(self) -> bool:
        """Check if any drones moved in this turn."""
        return len(self.moves) > 0

    def __repr__(self) -> str:
        """Return readable representation."""
        return (
            f"SchedulingResult(turn={self.turn_number}, "
            f"moves={len(self.moves)}, "
            f"waiting={len(self.waiting_drones)}, "
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
        """Initialize scheduler with graph and pathfinder."""
        self.graph = graph
        self.pathfinder = pathfinder
        self.start_zone: Optional[str] = None
        self.end_zone: Optional[str] = None
        self._regular_rotation_offset: int = 0

    def schedule_all_drones(
        self,
        drones: list[Drone],
        start_zone: str,
        end_zone: str,
    ) -> list[SchedulingResult]:
        """Schedule all drones from start to end zone."""
        if not drones:
            raise SchedulingError("Cannot schedule empty drone list")

        self.start_zone = start_zone
        self.end_zone = end_zone

        initial_states = {
            drone.drone_id: (
                drone.current_zone,
                drone.destination_zone,
                drone.state,
                list(drone.path),
                drone.turns_until_arrival,
            )
            for drone in drones
        }

        candidate_paths = self.pathfinder.find_all_shortest_paths(
            start_zone,
            end_zone,
            max_paths=max(1, min(len(drones), 8)),
        )
        if not candidate_paths:
            raise SchedulingError(
                f"No path found from {start_zone} to {end_zone}"
            )

        path_attempts = [candidate_paths]
        if len(candidate_paths) > 1:
            path_attempts.append([candidate_paths[0]])

        last_error: SchedulingError | None = None
        for paths in path_attempts:
            self._reset_drones(drones, initial_states)
            self._assign_paths(drones, paths)
            try:
                return self._run_turn_loop(drones)
            except SchedulingError as e:
                last_error = e

        if last_error is not None:
            raise last_error
        raise SchedulingError("Scheduling failed unexpectedly")

    def _assign_paths(
        self,
        drones: list[Drone],
        paths: list[PathfindingResult],
    ) -> None:
        """Assign candidate paths to drones."""
        for drone in drones:
            try:
                result = paths[
                    (int(drone.drone_id[1:]) - 1) % len(paths)
                ]
                drone.set_path(result.path)
            except Exception as e:
                raise SchedulingError(
                    f"Failed to compute path for {drone.drone_id}: {e}"
                ) from e

    def _reset_drones(
        self,
        drones: list[Drone],
        initial_states: dict[
            str,
            tuple[str, str, DroneState, list[str], int],
        ],
    ) -> None:
        """Restore drones before a fallback scheduling attempt."""
        for drone in drones:
            state = initial_states[drone.drone_id]
            drone.current_zone = state[0]
            drone.destination_zone = state[1]
            drone.state = state[2]
            drone.path = list(state[3])
            drone.turns_until_arrival = state[4]

    def _run_turn_loop(self, drones: list[Drone]) -> list[SchedulingResult]:
        """Run the scheduling loop for the currently assigned paths."""
        results: list[SchedulingResult] = []
        turn = 0
        max_turns = 10000

        delivered_count = sum(1 for d in drones if d.is_delivered)
        turns_without_delivery_progress = 0
        max_turns_without_delivery_progress = max(50, len(drones) * 8)

        while (
            not all(drone.is_delivered for drone in drones)
            and turn < max_turns
        ):
            turn += 1
            scheduling_result = self.schedule_turn(drones, turn)
            results.append(scheduling_result)

            new_delivered_count = sum(1 for d in drones if d.is_delivered)
            if new_delivered_count > delivered_count:
                delivered_count = new_delivered_count
                turns_without_delivery_progress = 0
            else:
                turns_without_delivery_progress += 1

            if (
                turns_without_delivery_progress
                >= max_turns_without_delivery_progress
            ):
                undelivered = [
                    d.drone_id for d in drones if not d.is_delivered
                ]
                raise SchedulingError(
                    "Deadlock/starvation detected: "
                    f"no delivery progress for "
                    f"{turns_without_delivery_progress} turns. "
                    f"Delivered={delivered_count}/{len(drones)}. "
                    f"Undelivered drones: {', '.join(undelivered)}"
                )

        if turn >= max_turns and not all(
            drone.is_delivered for drone in drones
        ):
            raise SchedulingError(
                f"Simulation exceeded {max_turns} turns "
                f"(possible deadlock)"
            )

        return results

    def schedule_turn(
        self, drones: list[Drone], turn_number: int
    ) -> SchedulingResult:
        """Schedule movements for a single turn."""
        # Filter active drones (not delivered)
        active_drones = [d for d in drones if not d.is_delivered]

        # Track zone occupancy for this turn
        zone_occupancy: dict[str, int] = {}

        # Initialize occupancies
        for zone_name in self.graph.zones:
            zone_occupancy[zone_name] = 0

        # Count current occupancy
        for drone in active_drones:
            if drone.state == DroneState.IN_TRANSIT_RESTRICTED:
                continue
            zone_occupancy[drone.current_zone] = (
                zone_occupancy.get(drone.current_zone, 0) + 1
            )

        # Compute candidate moves
        candidate_moves: dict[str, Optional[str]] = {}
        for drone in active_drones:
            # Handle restricted zone transit completion
            if drone.state == DroneState.IN_TRANSIT_RESTRICTED:
                next_zone = drone.next_zone
                if next_zone is None:
                    raise SchedulingError(
                        f"Drone {drone.drone_id} in transit "
                        f"but no next zone"
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
                raise SchedulingError(
                    f"Drone {drone.drone_id} path includes blocked zone: "
                    f"{next_zone}"
                )

            candidate_moves[drone.drone_id] = next_zone

        # Validate and assign moves
        moves, connection_usage = self._validate_and_assign_moves(
            active_drones, candidate_moves, zone_occupancy, turn_number
        )
        move_outputs = self._format_move_outputs(active_drones, moves)

        # Execute moves
        completed = []
        waiting = []

        for drone in active_drones:
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
                if drone.is_delivered:
                    completed.append(drone.drone_id)

        return SchedulingResult(
            moves=moves,
            move_outputs=move_outputs,
            waiting_drones=waiting,
            completed_drones=completed,
            turn_number=turn_number,
            is_valid=True,
            zone_occupancy=dict(zone_occupancy),
            connection_usage=connection_usage,
        )

    def _validate_and_assign_moves(
        self,
        drones: list[Drone],
        candidate_moves: dict[str, Optional[str]],
        zone_occupancy: dict[str, int],
        turn_number: int,
    ) -> tuple[dict[str, str], dict[str, int]]:
        """Validate candidate moves and resolve conflicts."""
        _ = turn_number  # reserved for future debug/telemetry usage

        moves: dict[str, str] = {}
        connection_usage: dict[str, int] = {}
        restricted_arrivals: dict[str, int] = {}

        # Separate drones by priority
        in_transit: list[Drone] = []
        regular: list[Drone] = []

        for drone in drones:
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
                next_zone, zone_occupancy
            )

            if not next_zone_obj.has_capacity(current_occupancy):
                # Deadlock: cannot complete restricted transit
                raise SchedulingError(
                    f"Deadlock: Drone {drone.drone_id} cannot reach "
                    f"{next_zone} (capacity full)"
                )

            self._assign_move(
                drone,
                next_zone,
                moves,
                zone_occupancy,
                connection_usage,
            )

        # Process regular drones (greedy assignment with round-robin rotation)
        if regular:
            ordered_regular = sorted(
                regular,
                key=lambda drone: (
                    -self._path_progress(drone),
                    drone.drone_id,
                ),
            )
            self._regular_rotation_offset = (
                self._regular_rotation_offset + 1
            ) % len(regular)
        else:
            ordered_regular = regular

        for drone in ordered_regular:
            next_zone = candidate_moves.get(drone.drone_id)

            if next_zone is None:
                # Drone is waiting or at destination
                continue

            next_zone_obj = self.graph.get_zone(next_zone)
            if next_zone_obj is None:
                continue

            # Check capacity
            current_occupancy = self._get_future_occupancy(
                next_zone, zone_occupancy
            )

            if next_zone_obj.zone_type == ZoneType.RESTRICTED:
                current_occupancy += restricted_arrivals.get(next_zone, 0)

            # Check connection capacity
            conn = self.graph.get_connection(
                drone.current_zone, next_zone
            )
            if conn is not None:
                conn_key = self._connection_key(drone.current_zone, next_zone)
                current_link_occupancy = connection_usage.get(conn_key, 0)
                if current_link_occupancy >= conn.max_link_capacity:
                    # Connection is saturated
                    continue

            if next_zone_obj.has_capacity(current_occupancy):
                # Assign move
                self._assign_move(
                    drone,
                    next_zone,
                    moves,
                    zone_occupancy,
                    connection_usage,
                )
                if next_zone_obj.zone_type == ZoneType.RESTRICTED:
                    restricted_arrivals[next_zone] = (
                        restricted_arrivals.get(next_zone, 0) + 1
                    )
            # else: drone waits (stays in current zone)

        return moves, connection_usage

    def _get_future_occupancy(
        self,
        zone_name: str,
        current_occupancy: dict[str, int],
    ) -> int:
        """Get projected occupancy for a zone during assignment.

        current_occupancy is updated as moves are assigned: leaving drones
        decrement their source zone and arriving drones increment destination.
        """
        return current_occupancy.get(zone_name, 0)

    def _assign_move(
        self,
        drone: Drone,
        destination: str,
        moves: dict[str, str],
        zone_occupancy: dict[str, int],
        connection_usage: dict[str, int],
    ) -> None:
        """Assign a move and update projected capacities."""
        moves[drone.drone_id] = destination

        conn_key = self._connection_key(drone.current_zone, destination)
        connection_usage[conn_key] = connection_usage.get(conn_key, 0) + 1

        if drone.state != DroneState.IN_TRANSIT_RESTRICTED:
            zone_occupancy[drone.current_zone] = max(
                0,
                zone_occupancy.get(drone.current_zone, 0) - 1,
            )

        destination_zone = self.graph.get_zone(destination)
        if destination_zone is None:
            raise SchedulingError(f"Zone not found: {destination}")
        if (
            drone.state != DroneState.IN_TRANSIT_RESTRICTED
            and destination_zone.zone_type == ZoneType.RESTRICTED
        ):
            return

        zone_occupancy[destination] = (
            zone_occupancy.get(destination, 0) + 1
        )

    def _connection_key(self, zone_a: str, zone_b: str) -> str:
        """Return a stable bidirectional connection key."""
        return "-".join(sorted([zone_a, zone_b]))

    def _path_progress(self, drone: Drone) -> int:
        """Return the current index of the drone in its path."""
        try:
            return drone.path.index(drone.current_zone)
        except ValueError:
            return -1

    def _format_move_outputs(
        self,
        drones: list[Drone],
        moves: dict[str, str],
    ) -> dict[str, str]:
        """Format real movement output before drone states mutate."""
        output: dict[str, str] = {}
        drones_by_id = {drone.drone_id: drone for drone in drones}

        for drone_id, destination in moves.items():
            drone = drones_by_id[drone_id]
            destination_zone = self.graph.get_zone(destination)
            if destination_zone is None:
                raise SchedulingError(f"Zone not found: {destination}")
            if (
                drone.state != DroneState.IN_TRANSIT_RESTRICTED
                and destination_zone.zone_type == ZoneType.RESTRICTED
            ):
                output[drone_id] = (
                    f"{drone_id}-{drone.current_zone}-{destination}"
                )
            else:
                output[drone_id] = f"{drone_id}-{destination}"

        return output

    def _execute_move(
        self, drone: Drone, destination: str
    ) -> None:
        """Execute a single drone's movement."""
        destination_zone = self.graph.get_zone(destination)
        if destination_zone is None:
            raise SchedulingError(f"Zone not found: {destination}")

        # Case 1: drone is already in restricted transit -> complete arrival
        if drone.state == DroneState.IN_TRANSIT_RESTRICTED:
            try:
                drone.complete_restricted_transit(destination)
            except ValueError as e:
                raise SchedulingError(
                    f"Failed to complete restricted transit for "
                    f"{drone.drone_id}: {e}"
                ) from e

            if drone.current_zone == drone.destination_zone:
                drone.mark_delivered()
            return

        # Case 2: entering a restricted zone starts a 2-turn transit
        if destination_zone.zone_type == ZoneType.RESTRICTED:
            try:
                drone.start_restricted_transit(
                    f"{drone.current_zone}-{destination}"
                )
            except ValueError as e:
                raise SchedulingError(
                    f"Failed to start restricted transit for "
                    f"{drone.drone_id}: {e}"
                ) from e
            return

        # Case 3: normal move
        try:
            drone.move_to(destination)
        except ValueError as e:
            raise SchedulingError(
                f"Invalid move for {drone.drone_id} to {destination}: {e}"
            ) from e

        if drone.current_zone == drone.destination_zone:
            drone.mark_delivered()

    def __repr__(self) -> str:
        """Return readable representation."""
        return (
            f"Scheduler(graph={self.graph}, "
            f"pathfinder={self.pathfinder})\n"
        )

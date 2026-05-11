"""Drone model representing an individual autonomous agent."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional

from models.enums import DroneState


@dataclass
class Drone:
    """Represent a single drone in the simulation.

    A drone has a unique identifier, position, destination, and state.
    It follows a computed path through the network and respects movement
    costs and zone capacities during execution.

    Attributes:
        drone_id: Unique identifier for this drone (e.g., "D1", "D2").
        current_zone: Name of the zone where the drone currently is.
        destination_zone: Name of the target zone (end hub).
        state: Current state of the drone (idle, moving, etc.).
        path: Ordered list of zone names to traverse (including current).
        turns_until_arrival: For restricted zones, turns needed to arrive.
        metadata: Optional string key-value pairs for extensibility.
    """

    drone_id: str
    current_zone: str
    destination_zone: str
    state: DroneState = DroneState.IDLE
    path: list[str] = field(default_factory=list)
    turns_until_arrival: int = 0
    metadata: dict[str, str] = field(default_factory=dict)

    def __post_init__(self) -> None:
        """Validate drone data after initialization.

        Raises:
            ValueError: If drone_id is empty, zones are empty, or
                invalid state.
        """
        # Validate drone_id
        if not self.drone_id or not isinstance(self.drone_id, str):
            raise ValueError("drone_id must be a non-empty string")

        # Validate zone names
        if not self.current_zone or not isinstance(
            self.current_zone, str
        ):
            raise ValueError("current_zone must be a non-empty string")
        if not self.destination_zone or not isinstance(
            self.destination_zone, str
        ):
            raise ValueError(
                "destination_zone must be a non-empty string"
            )

        # Validate state
        if not isinstance(self.state, DroneState):
            raise ValueError(
                f"state must be a DroneState enum, got {type(self.state)}"
            )

        # Validate turns_until_arrival
        if not isinstance(self.turns_until_arrival, int):
            raise ValueError(
                f"turns_until_arrival must be an integer, "
                f"got {type(self.turns_until_arrival).__name__}"
            )
        if self.turns_until_arrival < 0:
            raise ValueError(
                f"turns_until_arrival must be non-negative, "
                f"got {self.turns_until_arrival}"
            )

        # Validate path is a list of strings
        if not isinstance(self.path, list):
            raise ValueError(
                f"path must be a list, got {type(self.path).__name__}"
            )
        for zone_name in self.path:
            if not isinstance(zone_name, str) or not zone_name:
                raise ValueError(
                    "path must contain non-empty strings"
                )

    @property
    def is_delivered(self) -> bool:
        """Check if the drone has reached its destination.

        Returns:
            True if drone is in the destination zone and marked
            delivered.
        """
        return (
            self.state == DroneState.DELIVERED
            and self.current_zone == self.destination_zone
        )

    @property
    def is_in_transit(self) -> bool:
        """Check if the drone is currently moving.

        Includes transit to restricted zones.

        Returns:
            True if drone is moving or in transit to a restricted zone.
        """
        return self.state in (
            DroneState.MOVING,
            DroneState.IN_TRANSIT_RESTRICTED,
        )

    @property
    def next_zone(self) -> Optional[str]:
        """Get the next zone in the planned path.

        Returns the zone immediately after the current position in the
        path, or None if no path is set or we're already at the end.

        Returns:
            Name of the next zone, or None if not available.
        """
        if not self.path or len(self.path) < 2:
            return None

        try:
            current_index = self.path.index(self.current_zone)
            if current_index + 1 < len(self.path):
                return self.path[current_index + 1]
        except (ValueError, IndexError):
            pass

        return None

    def set_path(self, new_path: list[str]) -> None:
        """Update the drone's planned path.

        The path should include the current zone as the first element.

        Args:
            new_path: Ordered list of zone names from current to
                destination.

        Raises:
            ValueError: If path is empty or contains empty zone names.
        """
        if not new_path or not isinstance(new_path, list):
            raise ValueError("new_path must be a non-empty list")

        for zone_name in new_path:
            if not isinstance(zone_name, str) or not zone_name:
                raise ValueError(
                    "path must contain non-empty strings"
                )

        if new_path[0] != self.current_zone:
            raise ValueError(
                f"First zone in path must be current zone "
                f"'{self.current_zone}', got '{new_path[0]}'"
            )

        self.path = new_path

    def move_to(self, next_zone: str) -> None:
        """Move the drone to an adjacent zone.

        This updates the drone's position and marks it as moving.
        Use this for normal 1-turn movements only.

        Args:
            next_zone: Name of the destination zone.

        Raises:
            ValueError: If next_zone is empty or not in planned path.
        """
        if not next_zone or not isinstance(next_zone, str):
            raise ValueError("next_zone must be a non-empty string")

        if next_zone != self.next_zone:
            raise ValueError(
                f"Cannot move to '{next_zone}': "
                f"next zone in path is '{self.next_zone}'"
            )

        self.current_zone = next_zone
        self.state = DroneState.MOVING

    def start_restricted_transit(self, connection_name: str) -> None:
        """Initiate a 2-turn transit to a restricted zone.

        The drone occupies the connection and must complete arrival
        next turn.

        Args:
            connection_name: Identifier of the connection being
                traversed.

        Raises:
            ValueError: If connection_name is empty.
        """
        if not connection_name or not isinstance(
            connection_name, str
        ):
            raise ValueError(
                "connection_name must be a non-empty string"
            )

        self.state = DroneState.IN_TRANSIT_RESTRICTED
        self.turns_until_arrival = 1  # Must arrive next turn

    def complete_restricted_transit(
        self, destination_zone: str
    ) -> None:
        """Complete a restricted zone transit by arriving.

        Args:
            destination_zone: Name of the restricted zone.

        Raises:
            ValueError: If not in transit or destination_zone is empty.
        """
        if self.state != DroneState.IN_TRANSIT_RESTRICTED:
            raise ValueError(
                f"Cannot complete transit: drone is in {self.state} state"
            )

        if not destination_zone or not isinstance(
            destination_zone, str
        ):
            raise ValueError(
                "destination_zone must be a non-empty string"
            )

        self.current_zone = destination_zone
        self.state = DroneState.MOVING
        self.turns_until_arrival = 0

    def mark_delivered(self) -> None:
        """Mark the drone as successfully delivered to the end zone.

        Raises:
            ValueError: If drone is not at the destination zone.
        """
        if self.current_zone != self.destination_zone:
            raise ValueError(
                f"Cannot mark as delivered: "
                f"drone is at '{self.current_zone}', "
                f"not at destination '{self.destination_zone}'"
            )

        self.state = DroneState.DELIVERED

    def set_waiting(self) -> None:
        """Mark the drone as waiting due to capacity constraints.

        The drone will not move on this turn, waiting for space to open
        up.
        """
        self.state = DroneState.WAITING_FOR_CAPACITY

    def __repr__(self) -> str:
        """Return a readable string representation of the drone."""
        return (
            f"Drone({self.drone_id} at {self.current_zone} "
            f"→ {self.destination_zone} [{self.state.value}])"
        )

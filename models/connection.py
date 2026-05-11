"""Connection model representing a bidirectional link between two zones."""

from dataclasses import dataclass, field


@dataclass(frozen=True)
class Connection:
    """Represents a bidirectional connection between two zones.

    A connection links two zones and defines the capacity for drone
    movement between them. Zone names cannot contain dashes or spaces,
    as dashes are used in the connection syntax and spaces would break
    parsing.

    Attributes:
        zone_a: Name of the first zone.
        zone_b: Name of the second zone.
        max_link_capacity: Maximum drones that can traverse this connection
            simultaneously. Defaults to 1 and must be positive.
        metadata: Optional dictionary of string key-value pairs for
            extensibility.
    """

    zone_a: str
    zone_b: str
    max_link_capacity: int = 1
    metadata: dict[str, str] = field(default_factory=dict)

    def __post_init__(self) -> None:
        """Validate connection parameters after initialization.

        Raises:
            ValueError: If zone names contain dashes or spaces, or if
                max_link_capacity is not positive.
        """
        # Validate zone_a
        if not isinstance(self.zone_a, str) or not self.zone_a:
            raise ValueError("zone_a must be a non-empty string")
        if "-" in self.zone_a or " " in self.zone_a:
            raise ValueError(
                f"Zone name '{self.zone_a}' cannot contain dashes "
                f"or spaces"
            )

        # Validate zone_b
        if not isinstance(self.zone_b, str) or not self.zone_b:
            raise ValueError("zone_b must be a non-empty string")
        if "-" in self.zone_b or " " in self.zone_b:
            raise ValueError(
                f"Zone name '{self.zone_b}' cannot contain dashes "
                f"or spaces"
            )

        # Validate zones are different
        if self.zone_a == self.zone_b:
            raise ValueError(
                "A connection cannot link a zone to itself"
            )

        # Validate capacity
        if not isinstance(self.max_link_capacity, int):
            raise ValueError(
                f"max_link_capacity must be an integer, "
                f"got {type(self.max_link_capacity).__name__}"
            )
        if self.max_link_capacity < 1:
            raise ValueError(
                f"max_link_capacity must be at least 1, "
                f"got {self.max_link_capacity}"
            )

    def connects(self, zone_a: str, zone_b: str) -> bool:
        """Check if this connection links the two given zones.

        The order of zone_a and zone_b does not matter since connections
        are bidirectional.

        Args:
            zone_a: First zone name.
            zone_b: Second zone name.

        Returns:
            True if this connection links both zones, False otherwise.
        """
        return (self.zone_a == zone_a and self.zone_b == zone_b) or (
            self.zone_a == zone_b and self.zone_b == zone_a
        )

    def involves(self, zone_name: str) -> bool:
        """Check if a zone is part of this connection.

        Args:
            zone_name: Name of the zone to check.

        Returns:
            True if the zone is one end of this connection,
            False otherwise.
        """
        return self.zone_a == zone_name or self.zone_b == zone_name

    def other_side(self, zone_name: str) -> str:
        """Get the other zone in this connection.

        Args:
            zone_name: Name of one end of the connection.

        Returns:
            Name of the other zone in this connection.

        Raises:
            ValueError: If the given zone_name is not part of this
                connection.
        """
        if self.zone_a == zone_name:
            return self.zone_b
        elif self.zone_b == zone_name:
            return self.zone_a
        else:
            raise ValueError(
                f"Zone '{zone_name}' is not part of this connection "
                f"between '{self.zone_a}' and '{self.zone_b}'"
            )

    def key(self) -> tuple[str, str]:
        """Get a normalized key for duplicate detection.

        Returns a tuple of zone names sorted alphabetically, ensuring that
        equivalent connections (e.g., a-b and b-a) produce the same key.

        Returns:
            Tuple of zone names in alphabetical order.
        """
        return tuple(sorted([self.zone_a, self.zone_b]))  # type: ignore

    def __repr__(self) -> str:
        """Return a readable string representation of the connection."""
        capacity_str = (
            f" [capacity={self.max_link_capacity}]"
            if self.max_link_capacity != 1
            else ""
        )
        return f"Connection({self.zone_a}-{self.zone_b}{capacity_str})"

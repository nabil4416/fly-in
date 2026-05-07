"""Zone model for the Fly-in drone simulation."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum


class ZoneType(str, Enum):
    """Supported zone types."""

    NORMAL = "normal"
    RESTRICTED = "restricted"
    PRIORITY = "priority"
    BLOCKED = "blocked"


class ZoneCategory(str, Enum):
    """Supported zone categories from the input file."""

    START_HUB = "start_hub"
    END_HUB = "end_hub"
    HUB = "hub"


@dataclass(frozen=True)
class Zone:
    """Represent a zone in the drone network graph."""

    name: str
    x: int
    y: int
    zone_type: ZoneType = ZoneType.NORMAL
    category: ZoneCategory = ZoneCategory.HUB
    max_drones: int = 1
    color: str | None = None
    metadata: dict[str, str] = field(default_factory=dict)

    def __post_init__(self) -> None:
        """Validate zone data after initialization."""
        if not self.name:
            raise ValueError("Zone name cannot be empty")
        if "-" in self.name or " " in self.name:
            raise ValueError(f"Invalid zone name: {self.name}")
        if self.max_drones < 1:
            raise ValueError("max_drones must be a positive integer")

    @property
    def is_start(self) -> bool:
        """Return True if this zone is the start hub."""
        return self.category == ZoneCategory.START_HUB

    @property
    def is_end(self) -> bool:
        """Return True if this zone is the end hub."""
        return self.category == ZoneCategory.END_HUB

    @property
    def is_special_hub(self) -> bool:
        """Return True if this zone is the start or end hub."""
        return self.is_start or self.is_end

    @property
    def is_blocked(self) -> bool:
        """Return True if this zone cannot be entered."""
        return self.zone_type == ZoneType.BLOCKED

    @property
    def movement_cost(self) -> int:
        """Return the number of turns required to enter this zone."""
        if self.zone_type in (ZoneType.NORMAL, ZoneType.PRIORITY):
            return 1
        if self.zone_type == ZoneType.RESTRICTED:
            return 2
        if self.zone_type == ZoneType.BLOCKED:
            return 0
        raise ValueError(f"Unsupported zone type: {self.zone_type}")

    def has_capacity(self, current_occupancy: int) -> bool:
        """Return True if another drone can occupy this zone."""
        if current_occupancy < 0:
            raise ValueError("current_occupancy cannot be negative")
        if self.is_start or self.is_end:
            return True
        return current_occupancy < self.max_drones

    def position(self) -> tuple[int, int]:
        """Return the zone coordinates."""
        return (self.x, self.y)
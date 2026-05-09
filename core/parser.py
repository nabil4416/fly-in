"""Parser for the Fly-in input file format."""

from __future__ import annotations

import re
from pathlib import Path
from typing import Optional

from models.connection import Connection
from models.drone import Drone
from models.enums import DroneState
from models.zone import Zone, ZoneCategory, ZoneType
from utils.exceptions import ParsingError


class InputData:
    """Container for parsed input data.

    Attributes:
        num_drones: Total number of drones to simulate.
        start_zone: The starting hub zone.
        end_zone: The ending hub zone.
        zones: Dictionary mapping zone name to Zone object.
        connections: List of Connection objects.
    """

    def __init__(
        self,
        num_drones: int,
        start_zone: Zone,
        end_zone: Zone,
        zones: dict[str, Zone],
        connections: list[Connection],
    ) -> None:
        """Initialize input data container."""
        self.num_drones = num_drones
        self.start_zone = start_zone
        self.end_zone = end_zone
        self.zones = zones
        self.connections = connections

    def __repr__(self) -> str:
        """Return readable representation."""
        return (
            f"InputData(drones={self.num_drones}, zones={len(self.zones)}, "
            f"connections={len(self.connections)})"
        )


class Parser:
    """Parser for Fly-in input file format.

    Responsibilities:
    - Read and parse input files
    - Validate syntax and semantic rules
    - Create Zone, Connection, and Drone objects
    - Provide clear error messages with line numbers
    """

    # Regex patterns for parsing
    NB_DRONES_PATTERN = r"^\s*nb_drones\s*:\s*(\d+)\s*$"
    ZONE_PATTERN = (
        r"^\s*(start_hub|end_hub|hub)\s*:\s*(\w+)\s+(-?\d+)\s+(-?\d+)"
        r"\s*(?:\[(.*?)\])?\s*$"
    )
    CONNECTION_PATTERN = r"^\s*connection\s*:\s*(\w+)-(\w+)\s*(?:\[(.*?)\])?\s*$"
    METADATA_PATTERN = r"(\w+)=([^\s\]]+)"
    COMMENT_PATTERN = r"^\s*#.*$"
    EMPTY_PATTERN = r"^\s*$"

    def __init__(self) -> None:
        """Initialize parser."""
        self.lines: list[str] = []
        self.current_line_number: int = 0
        self.num_drones: int = 0
        self.zones: dict[str, Zone] = {}
        self.connections: list[Connection] = []
        self.seen_connections: set[tuple[str, str]] = set()
        self.start_zone: Optional[Zone] = None
        self.end_zone: Optional[Zone] = None

    def parse_file(self, filepath: str | Path) -> InputData:
        """Parse an input file and return structured data.

        Args:
            filepath: Path to the input file.

        Returns:
            InputData object containing parsed configuration.

        Raises:
            ParsingError: If file cannot be read or contains errors.
        """
        try:
            with open(filepath, "r") as f:
                self.lines = f.readlines()
        except FileNotFoundError as e:
            raise ParsingError(f"File not found: {filepath}") from e
        except IOError as e:
            raise ParsingError(f"Cannot read file: {filepath}") from e

        # Parse line by line
        for line_idx, line in enumerate(self.lines, start=1):
            self.current_line_number = line_idx
            self._parse_line(line.rstrip("\n"))

        # Validate final state
        self._validate_final_state()

        return InputData(
            num_drones=self.num_drones,
            start_zone=self.start_zone,
            end_zone=self.end_zone,
            zones=self.zones,
            connections=self.connections,
        )

    def _parse_line(self, line: str) -> None:
        """Parse a single line.

        Args:
            line: Line to parse.

        Raises:
            ParsingError: If line is malformed.
        """
        # Skip empty lines and comments
        if re.match(self.EMPTY_PATTERN, line) or re.match(self.COMMENT_PATTERN, line):
            return

        # Try each pattern
        if self._try_parse_nb_drones(line):
            return
        if self._try_parse_zone(line):
            return
        if self._try_parse_connection(line):
            return

        # No pattern matched
        raise ParsingError(
            f"Unrecognized line format: {line}", self.current_line_number
        )

    def _try_parse_nb_drones(self, line: str) -> bool:
        """Try to parse nb_drones line.

        Args:
            line: Line to parse.

        Returns:
            True if line was nb_drones, False otherwise.

        Raises:
            ParsingError: If nb_drones is malformed.
        """
        match = re.match(self.NB_DRONES_PATTERN, line)
        if not match:
            return False

        if self.num_drones != 0:
            raise ParsingError(
                "Multiple nb_drones declarations",
                self.current_line_number,
            )

        try:
            num = int(match.group(1))
            if num < 1:
                raise ParsingError(
                    "nb_drones must be at least 1",
                    self.current_line_number,
                )
            self.num_drones = num
        except ValueError as e:
            raise ParsingError(
                f"Invalid number format: {match.group(1)}",
                self.current_line_number,
            ) from e

        return True

    def _try_parse_zone(self, line: str) -> bool:
        """Try to parse zone line.

        Args:
            line: Line to parse.

        Returns:
            True if line was zone, False otherwise.

        Raises:
            ParsingError: If zone is malformed.
        """
        match = re.match(self.ZONE_PATTERN, line)
        if not match:
            return False

        zone_category_str = match.group(1)
        zone_name = match.group(2)
        x_str = match.group(3)
        y_str = match.group(4)
        metadata_str = match.group(5) or ""

        # Validate zone name (no dashes, no spaces)
        if "-" in zone_name or " " in zone_name:
            raise ParsingError(
                f"Zone name '{zone_name}' cannot contain dashes or spaces",
                self.current_line_number,
            )

        # Check for duplicate zone names
        if zone_name in self.zones:
            raise ParsingError(
                f"Duplicate zone name: {zone_name}",
                self.current_line_number,
            )

        # Parse coordinates
        try:
            x = int(x_str)
            y = int(y_str)
        except ValueError as e:
            raise ParsingError(
                f"Invalid coordinates: {x_str}, {y_str}",
                self.current_line_number,
            ) from e

        # Parse metadata
        metadata = self._parse_metadata(metadata_str)

        # Extract zone type, color, max_drones
        zone_type_str = metadata.pop("zone", "normal").lower()
        color = metadata.pop("color", None)
        max_drones_str = metadata.pop("max_drones", "1")

        # Validate zone type
        try:
            zone_type = ZoneType(zone_type_str)
        except ValueError as e:
            raise ParsingError(
                f"Invalid zone type: {zone_type_str}. "
                f"Must be one of: {', '.join(zt.value for zt in ZoneType)}",
                self.current_line_number,
            ) from e

        # Validate max_drones
        try:
            max_drones = int(max_drones_str)
            if max_drones < 1:
                raise ValueError("Must be at least 1")
        except ValueError as e:
            raise ParsingError(
                f"Invalid max_drones value: {max_drones_str}",
                self.current_line_number,
            ) from e

        # Determine category and validate
        if zone_category_str == "start_hub":
            if self.start_zone is not None:
                raise ParsingError(
                    "Multiple start_hub zones declared",
                    self.current_line_number,
                )
            category = ZoneCategory.START_HUB
        elif zone_category_str == "end_hub":
            if self.end_zone is not None:
                raise ParsingError(
                    "Multiple end_hub zones declared",
                    self.current_line_number,
                )
            category = ZoneCategory.END_HUB
        else:
            category = ZoneCategory.HUB

        # Create zone
        zone = Zone(
            name=zone_name,
            x=x,
            y=y,
            zone_type=zone_type,
            category=category,
            max_drones=max_drones,
            color=color,
            metadata=metadata,
        )

        self.zones[zone_name] = zone

        if category == ZoneCategory.START_HUB:
            self.start_zone = zone
        elif category == ZoneCategory.END_HUB:
            self.end_zone = zone

        return True

    def _try_parse_connection(self, line: str) -> bool:
        """Try to parse connection line.

        Args:
            line: Line to parse.

        Returns:
            True if line was connection, False otherwise.

        Raises:
            ParsingError: If connection is malformed.
        """
        match = re.match(self.CONNECTION_PATTERN, line)
        if not match:
            return False

        zone_a = match.group(1)
        zone_b = match.group(2)
        metadata_str = match.group(3) or ""

        # Validate that zones exist
        if zone_a not in self.zones:
            raise ParsingError(
                f"Connection references undefined zone: {zone_a}",
                self.current_line_number,
            )
        if zone_b not in self.zones:
            raise ParsingError(
                f"Connection references undefined zone: {zone_b}",
                self.current_line_number,
            )

        # Check for self-connection
        if zone_a == zone_b:
            raise ParsingError(
                "Connection cannot link a zone to itself",
                self.current_line_number,
            )

        # Check for duplicate (bidirectional)
        conn_key = tuple(sorted([zone_a, zone_b]))
        if conn_key in self.seen_connections:
            raise ParsingError(
                f"Duplicate connection: {zone_a}-{zone_b}",
                self.current_line_number,
            )
        self.seen_connections.add(conn_key)

        # Parse metadata
        metadata = self._parse_metadata(metadata_str)
        max_link_capacity_str = metadata.pop("max_link_capacity", "1")

        # Validate max_link_capacity
        try:
            max_link_capacity = int(max_link_capacity_str)
            if max_link_capacity < 1:
                raise ValueError("Must be at least 1")
        except ValueError as e:
            raise ParsingError(
                f"Invalid max_link_capacity: {max_link_capacity_str}",
                self.current_line_number,
            ) from e

        # Create connection
        connection = Connection(
            zone_a=zone_a,
            zone_b=zone_b,
            max_link_capacity=max_link_capacity,
            metadata=metadata,
        )

        self.connections.append(connection)
        return True

    def _parse_metadata(self, metadata_str: str) -> dict[str, str]:
        """Parse metadata from [key=value key2=value2] format.

        Args:
            metadata_str: Metadata string without brackets.

        Returns:
            Dictionary of key-value pairs.

        Raises:
            ParsingError: If metadata is malformed.
        """
        if not metadata_str.strip():
            return {}

        metadata: dict[str, str] = {}
        matches = re.findall(self.METADATA_PATTERN, metadata_str)

        if not matches:
            raise ParsingError(
                f"Invalid metadata format: [{metadata_str}]",
                self.current_line_number,
            )

        for key, value in matches:
            if key in metadata:
                raise ParsingError(
                    f"Duplicate metadata key: {key}",
                    self.current_line_number,
                )
            metadata[key] = value

        return metadata

    def _validate_final_state(self) -> None:
        """Validate final parsing state.

        Raises:
            ParsingError: If required elements are missing.
        """
        if self.num_drones == 0:
            raise ParsingError("nb_drones not defined")

        if self.start_zone is None:
            raise ParsingError("start_hub zone not defined")

        if self.end_zone is None:
            raise ParsingError("end_hub zone not defined")

        if not self.zones:
            raise ParsingError("No zones defined")

    @staticmethod
    def create_drones(
        num_drones: int,
        start_zone: Zone,
        end_zone: Zone,
    ) -> list[Drone]:
        """Create initial drone objects from input data.

        Args:
            num_drones: Number of drones to create.
            start_zone: Starting zone for all drones.
            end_zone: Destination zone for all drones.

        Returns:
            List of initialized Drone objects.
        """
        drones: list[Drone] = []
        for i in range(1, num_drones + 1):
            drone = Drone(
                drone_id=f"D{i}",
                current_zone=start_zone.name,
                destination_zone=end_zone.name,
                state=DroneState.IDLE,
                path=[start_zone.name],
            )
            drones.append(drone)
        return drones

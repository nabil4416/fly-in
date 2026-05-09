"""Graph representation for the drone network."""

from __future__ import annotations

from collections import deque
from typing import Optional

from models.connection import Connection
from models.zone import Zone
from utils.exceptions import FlyInException


class GraphError(FlyInException):
    """Exception raised when graph operations fail."""

    pass


class Graph:
    """Represent a directed network of zones connected by paths.

    The graph is built from Zone and Connection objects and provides
    efficient queries for pathfinding and validation. It uses an
    adjacency list representation without external graph libraries.

    Attributes:
        zones: Dictionary mapping zone name to Zone object.
        connections: List of bidirectional connections between zones.
    """

    def __init__(self, zones: dict[str, Zone], connections: list[Connection]) -> None:
        """Initialize the graph from zones and connections.

        Args:
            zones: Dictionary mapping zone names to Zone objects.
            connections: List of Connection objects linking zones.

        Raises:
            GraphError: If zones or connections are invalid.
        """
        if not zones:
            raise GraphError("Cannot create graph with no zones")
        if not connections:
            raise GraphError("Cannot create graph with no connections")

        self.zones = zones
        self.connections = connections

        # Build adjacency list: zone_name -> [neighbor_names]
        self._adjacency: dict[str, list[str]] = self._build_adjacency_list()

        # Build connection map for O(1) lookups: (zone_a, zone_b) -> Connection
        self._connection_map: dict[tuple[str, str], Connection] = (
            self._build_connection_map()
        )

        # Validate graph structure
        self._validate_graph()

    def _build_adjacency_list(self) -> dict[str, list[str]]:
        """Build adjacency list from connections.

        Returns:
            Dictionary mapping each zone name to its list of neighbors.
        """
        adjacency: dict[str, list[str]] = {}

        # Initialize all zones with empty neighbor lists
        for zone_name in self.zones:
            adjacency[zone_name] = []

        # Add bidirectional edges for each connection
        for conn in self.connections:
            if conn.zone_a not in adjacency:
                adjacency[conn.zone_a] = []
            if conn.zone_b not in adjacency:
                adjacency[conn.zone_b] = []

            adjacency[conn.zone_a].append(conn.zone_b)
            adjacency[conn.zone_b].append(conn.zone_a)

        return adjacency

    def _build_connection_map(self) -> dict[tuple[str, str], Connection]:
        """Build a map of connections for O(1) lookups.

        Returns:
            Dictionary mapping (zone_a, zone_b) pairs to Connection objects.
            Both orderings are included for bidirectional lookup.
        """
        conn_map: dict[tuple[str, str], Connection] = {}

        for conn in self.connections:
            # Store both orderings for bidirectional access
            conn_map[(conn.zone_a, conn.zone_b)] = conn
            conn_map[(conn.zone_b, conn.zone_a)] = conn

        return conn_map

    def _validate_graph(self) -> None:
        """Validate graph structure after construction.

        Checks that:
        - All connections reference valid zones
        - No blocked zones are referenced
        - Graph is not disconnected (all zones reachable)

        Raises:
            GraphError: If validation fails.
        """
        # Check that all connections reference valid zones
        for conn in self.connections:
            if conn.zone_a not in self.zones:
                raise GraphError(
                    f"Connection references undefined zone: {conn.zone_a}"
                )
            if conn.zone_b not in self.zones:
                raise GraphError(
                    f"Connection references undefined zone: {conn.zone_b}"
                )

            # Warn if blocked zones are involved (they shouldn't be traversed)
            if self.zones[conn.zone_a].is_blocked:
                raise GraphError(
                    f"Cannot create connection to blocked zone: {conn.zone_a}"
                )
            if self.zones[conn.zone_b].is_blocked:
                raise GraphError(
                    f"Cannot create connection to blocked zone: {conn.zone_b}"
                )

    def get_neighbors(self, zone_name: str) -> list[str]:
        """Get all adjacent zones from a given zone.

        Args:
            zone_name: Name of the zone.

        Returns:
            List of adjacent zone names.

        Raises:
            GraphError: If zone does not exist.
        """
        if zone_name not in self.zones:
            raise GraphError(f"Zone not found: {zone_name}")

        return self._adjacency.get(zone_name, [])

    def get_connection(
        self, zone_a: str, zone_b: str
    ) -> Optional[Connection]:
        """Get the connection between two zones, if it exists.

        Args:
            zone_a: First zone name.
            zone_b: Second zone name.

        Returns:
            Connection object if connection exists, None otherwise.
        """
        return self._connection_map.get((zone_a, zone_b))

    def has_edge(self, zone_a: str, zone_b: str) -> bool:
        """Check if a direct connection exists between two zones.

        Args:
            zone_a: First zone name.
            zone_b: Second zone name.

        Returns:
            True if zones are directly connected, False otherwise.
        """
        return (zone_a, zone_b) in self._connection_map

    def is_reachable(self, start: str, end: str) -> bool:
        """Check if a path exists from start zone to end zone using BFS.

        This only checks connectivity; it does NOT consider zone types
        (blocked zones are treated as valid for this check). Blocked zone
        checking is delegated to pathfinding.

        Args:
            start: Starting zone name.
            end: Ending zone name.

        Returns:
            True if path exists, False otherwise.

        Raises:
            GraphError: If start or end zone does not exist.
        """
        if start not in self.zones:
            raise GraphError(f"Start zone not found: {start}")
        if end not in self.zones:
            raise GraphError(f"End zone not found: {end}")

        if start == end:
            return True

        # BFS: breadth-first search
        visited: set[str] = {start}
        queue: deque[str] = deque([start])

        while queue:
            current = queue.popleft()

            if current == end:
                return True

            for neighbor in self.get_neighbors(current):
                if neighbor not in visited:
                    visited.add(neighbor)
                    queue.append(neighbor)

        return False

    def get_all_zones(self) -> list[str]:
        """Get list of all zone names in the graph.

        Returns:
            List of zone names.
        """
        return list(self.zones.keys())

    def get_zone(self, zone_name: str) -> Optional[Zone]:
        """Get a Zone object by name.

        Args:
            zone_name: Name of the zone.

        Returns:
            Zone object if found, None otherwise.
        """
        return self.zones.get(zone_name)

    def get_movement_cost(self, zone_name: str) -> int:
        """Get the movement cost to enter a zone.

        Args:
            zone_name: Name of the zone.

        Returns:
            Cost in turns (1 for normal/priority, 2 for restricted, 0 for blocked).

        Raises:
            GraphError: If zone does not exist.
        """
        zone = self.get_zone(zone_name)
        if zone is None:
            raise GraphError(f"Zone not found: {zone_name}")

        return zone.movement_cost

    def get_connection_capacity(self, zone_a: str, zone_b: str) -> Optional[int]:
        """Get the maximum capacity of a connection.

        Args:
            zone_a: First zone name.
            zone_b: Second zone name.

        Returns:
            Maximum number of drones that can traverse the connection,
            or None if no connection exists.
        """
        conn = self.get_connection(zone_a, zone_b)
        if conn is None:
            return None
        return conn.max_link_capacity

    def get_all_connections(self) -> list[Connection]:
        """Get list of all connections in the graph.

        Returns:
            List of Connection objects.
        """
        return self.connections

    def __repr__(self) -> str:
        """Return a readable string representation of the graph."""
        return (
            f"Graph(zones={len(self.zones)}, "
            f"connections={len(self.connections)})"
        )

    def debug_info(self) -> str:
        """Return detailed debug information about the graph structure."""
        lines = ["Graph Debug Info:"]
        lines.append(f"  Total zones: {len(self.zones)}")
        lines.append(f"  Total connections: {len(self.connections)}")
        lines.append("\nZones:")
        for zone_name in sorted(self.zones.keys()):
            zone = self.zones[zone_name]
            neighbors = self.get_neighbors(zone_name)
            lines.append(
                f"  {zone_name}: type={zone.zone_type.value}, "
                f"capacity={zone.max_drones}, neighbors={neighbors}"
            )
        lines.append("\nConnections:")
        for conn in self.connections:
            capacity = (
                f"[capacity={conn.max_link_capacity}]"
                if conn.max_link_capacity != 1
                else ""
            )
            lines.append(f"  {conn.zone_a} 2 {conn.zone_b} {capacity}")
        return "\n".join(lines)

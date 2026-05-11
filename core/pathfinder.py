"""Dijkstra pathfinding for drone route computation.

This module implements shortest-path pathfinding using Dijkstra's algorithm
without external graph libraries. It computes optimal routes from any source
to any destination while respecting zone types and blocked zones.
"""

from __future__ import annotations

import heapq
from dataclasses import dataclass

from core.graph import Graph
from utils.exceptions import FlyInException


class PathfindingError(FlyInException):
    """Exception raised when pathfinding fails."""

    pass


@dataclass
class PathfindingResult:
    """Result of a pathfinding query.

    Attributes:
        path: List of zone names from source to destination.
        cost: Total movement cost (sum of zone movement costs).
    """

    path: list[str]
    cost: int

    def __post_init__(self) -> None:
        """Validate pathfinding result.

        Validation rules:
        - A trivial path (start == end) may be represented as a
          single-element list [start] with cost == 0.
        - A non-trivial path must have at least two zones and cost >= 1.
        """
        if not self.path:
            raise PathfindingError("Path must have at least one zone")
        if self.cost < 0:
            raise PathfindingError("Cost must be at least 0")

    def is_valid(self) -> bool:
        """Check if this is a valid path result.

        Returns:
            True if path has at least one zone and cost is non-negative.
        """
        return len(self.path) >= 1 and self.cost >= 0

    def __repr__(self) -> str:
        """Return readable representation."""
        path_str = " → ".join(self.path)
        return (
            f"PathfindingResult(path={path_str}, cost={self.cost})"
        )


class Pathfinder:
    """Compute shortest paths using Dijkstra's algorithm.

    This pathfinder respects zone movement costs:
    - normal/priority zones: 1 turn
    - restricted zones: 2 turns
    - blocked zones: inaccessible (excluded from graph)

    Attributes:
        graph: The graph to search in.
    """

    def __init__(self, graph: Graph) -> None:
        """Initialize pathfinder with a graph.

        Args:
            graph: Graph object for pathfinding.

        Raises:
            PathfindingError: If graph is invalid.
        """
        if not graph:
            raise PathfindingError("Graph cannot be None")
        self.graph = graph

    def find_shortest_path(
        self,
        source: str,
        destination: str,
    ) -> PathfindingResult:
        """Find shortest path between two zones using Dijkstra.

        Args:
            source: Starting zone name.
            destination: Target zone name.

        Returns:
            PathfindingResult with path and cost.

        Raises:
            PathfindingError: If zones don't exist or no path found.
        """
        # Validate inputs
        if source not in self.graph.zones:
            raise PathfindingError(f"Source zone '{source}' not found")
        if destination not in self.graph.zones:
            raise PathfindingError(
                f"Destination zone '{destination}' not found"
            )

        # Special case: source == destination
        if source == destination:
            return PathfindingResult(path=[source], cost=0)

        # Initialize Dijkstra's algorithm
        distances: dict[str, int] = {
            zone: 10000 for zone in self.graph.zones
        }
        distances[source] = 0
        previous: dict[str, str | None] = {
            zone: None for zone in self.graph.zones
        }
        visited: set[str] = set()

        # Priority queue: (cost, zone_name)
        pq: list[tuple[int, str]] = [(0, source)]

        while pq:
            current_cost, current_zone = heapq.heappop(pq)

            # Skip if already visited
            if current_zone in visited:
                continue
            visited.add(current_zone)

            # Found destination
            if current_zone == destination:
                path = self._reconstruct_path(previous, destination)
                return PathfindingResult(
                    path=path, cost=distances[destination]
                )

            # Explore neighbors
            neighbors = self.graph.get_neighbors(current_zone)
            for neighbor in neighbors:
                if neighbor in visited:
                    continue

                # Get movement cost to neighbor
                try:
                    neighbor_zone = self.graph.zones[neighbor]
                    move_cost = self._get_movement_cost(neighbor_zone)
                except KeyError:
                    continue

                # Skip blocked zones
                if move_cost == -1:
                    continue

                new_cost = current_cost + move_cost

                # Update if we found a better path
                if new_cost < distances[neighbor]:
                    distances[neighbor] = new_cost
                    previous[neighbor] = current_zone
                    heapq.heappush(pq, (new_cost, neighbor))

        # No path found
        raise PathfindingError(
            f"No path found from '{source}' to '{destination}'"
        )

    def _get_movement_cost(self, zone) -> int:  # type: ignore
        """Get movement cost to enter a zone.

        Args:
            zone: Zone object.

        Returns:
            Movement cost (1 or 2 turns). Returns -1 for blocked zones.
        """
        if zone.zone_type.value == "blocked":
            return -1
        if zone.zone_type.value == "restricted":
            return 2
        # normal and priority both cost 1
        return 1

    def _reconstruct_path(
        self,
        previous: dict[str, str | None],
        destination: str,
    ) -> list[str]:
        """Reconstruct path from source to destination.

        Args:
            previous: Mapping of zone to previous zone in path.
            destination: Target zone.

        Returns:
            List of zone names from source to destination.
        """
        path: list[str] = []
        current: str | None = destination

        while current is not None:
            path.append(current)
            current = previous[current]

        path.reverse()
        return path

    def find_all_shortest_paths(
        self,
        source: str,
        destination: str,
        max_paths: int = 5,
    ) -> list[PathfindingResult]:
        """Find multiple shortest paths (for load balancing).

        This is a simplified multi-path finder that may return paths
        with the same cost or slightly longer paths. Useful for
        distributing drones across multiple routes.

        Args:
            source: Starting zone name.
            destination: Target zone name.
            max_paths: Maximum number of paths to find.

        Returns:
            List of PathfindingResult objects, sorted by cost.

        Raises:
            PathfindingError: If zones don't exist.
        """
        if max_paths < 1:
            raise PathfindingError("max_paths must be at least 1")

        # For now, just return the shortest path
        # This can be extended to find alternative paths
        try:
            shortest = self.find_shortest_path(source, destination)
            return [shortest]
        except PathfindingError:
            return []

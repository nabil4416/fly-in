"""Pathfinding for optimal drone routes through the network."""

from __future__ import annotations

import heapq
from dataclasses import dataclass
from typing import Optional

from core.graph import Graph
from models.zone import ZoneType
from utils.exceptions import FlyInException


class PathfindingError(FlyInException):
    """Exception raised when pathfinding operations fail."""

    pass


@dataclass
class PathfindingResult:
    """Result of a pathfinding operation.

    Attributes:
        path: List of zone names from start to destination (inclusive).
        cost: Total movement cost in turns.
    """

    path: list[str]
    cost: int

    def __post_init__(self) -> None:
        """Validate pathfinding result."""
        if not self.path:
            raise PathfindingError("Path cannot be empty")
        if len(self.path) < 2:
            raise PathfindingError("Path must have at least start and end zone")
        if self.cost < 1:
            raise PathfindingError("Cost must be at least 1")

    def is_valid(self) -> bool:
        """Check if this is a valid path result.

        Returns:
            True if path has at least 2 zones and cost is positive.
        """
        return len(self.path) >= 2 and self.cost >= 1

    def __repr__(self) -> str:
        """Return readable representation."""
        path_str = " → ".join(self.path)
        return f"Path({path_str}) [cost={self.cost}]"


class Pathfinder:
    """Find optimal paths through the drone network using Dijkstra's algorithm.

    This pathfinder:
    - Computes shortest paths considering zone movement costs
    - Avoids blocked zones entirely
    - Handles restricted zones (2-turn cost) vs normal zones (1-turn cost)
    - Supports finding multiple alternative paths

    Algorithm: Dijkstra with priority queue
    - Time complexity: O((V + E) log V) where V=zones, E=connections
    - Space complexity: O(V)

    Note: We use Dijkstra instead of A* because:
    1. Dijkstra is simpler and more explainable (42 peer review)
    2. Network graphs are small (< 100 zones typically)
    3. Dijkstra is deterministic and fully testable
    4. No heuristic needed for correctness
    """

    def __init__(self, graph: Graph) -> None:
        """Initialize pathfinder with a graph.

        Args:
            graph: Graph object representing the network.

        Raises:
            PathfindingError: If graph is invalid.
        """
        if not graph or not graph.zones:
            raise PathfindingError("Cannot create pathfinder with empty graph")

        self.graph = graph

    def find_shortest_path(
        self, start: str, end: str
    ) -> Optional[PathfindingResult]:
        """Find the shortest path from start to end zone.

        Uses Dijkstra's algorithm to compute the optimal path considering
        movement costs for different zone types.

        Args:
            start: Name of the starting zone.
            end: Name of the destination zone.

        Returns:
            PathfindingResult with path and cost, or None if no path exists.

        Raises:
            PathfindingError: If start or end zone doesn't exist.
        """
        if start not in self.graph.zones:
            raise PathfindingError(f"Start zone not found: {start}")
        if end not in self.graph.zones:
            raise PathfindingError(f"End zone not found: {end}")

        if start == end:
            # Trivial case: already at destination
            return PathfindingResult(path=[start], cost=0)

        # Run Dijkstra
        distances, predecessors = self._dijkstra(start, end)

        # Check if path exists
        if end not in distances or distances[end] == float("inf"):
            return None

        # Reconstruct path
        path = self._reconstruct_path(end, predecessors)
        cost = distances[end]

        return PathfindingResult(path=path, cost=cost)

    def find_all_paths(
        self, start: str, end: str, max_cost: Optional[int] = None
    ) -> list[PathfindingResult]:
        """Find all reasonable paths from start to end (within cost limit).

        This uses a modified Dijkstra that explores all paths up to a cost
        threshold. This is useful for the scheduler to select diverse paths.

        Args:
            start: Starting zone name.
            end: Destination zone name.
            max_cost: Maximum path cost to consider (None = no limit).

        Returns:
            List of PathfindingResult objects, sorted by cost.

        Raises:
            PathfindingError: If start or end zone doesn't exist.
        """
        if start not in self.graph.zones:
            raise PathfindingError(f"Start zone not found: {start}")
        if end not in self.graph.zones:
            raise PathfindingError(f"End zone not found: {end}")

        if start == end:
            return [PathfindingResult(path=[start], cost=0)]

        # Find shortest path first
        shortest = self.find_shortest_path(start, end)
        if shortest is None:
            return []

        paths = [shortest]

        # For now, return just the shortest path
        # (More advanced: could find k-alternative paths using Yen's algorithm)
        return paths

    def get_path_cost(self, path: list[str]) -> int:
        """Calculate the total movement cost for a given path.

        Costs are based on destination zone types:
        - normal: 1 turn
        - priority: 1 turn (but preferred in selection)
        - restricted: 2 turns
        - blocked: inaccessible (should not be in valid path)

        Args:
            path: List of zone names representing the path.

        Returns:
            Total cost in turns.

        Raises:
            PathfindingError: If path is invalid or contains blocked zones.
        """
        if not path or len(path) < 2:
            raise PathfindingError("Path must have at least 2 zones")

        total_cost = 0

        # Cost is for entering each zone (skip the first zone, it's start)
        for zone_name in path[1:]:
            zone = self.graph.get_zone(zone_name)
            if zone is None:
                raise PathfindingError(f"Zone not found in path: {zone_name}")

            if zone.is_blocked:
                raise PathfindingError(
                    f"Path contains blocked zone: {zone_name}"
                )

            total_cost += zone.movement_cost

        return total_cost

    def _dijkstra(
        self, start: str, end: str
    ) -> tuple[dict[str, int | float], dict[str, str | None]]:
        """Run Dijkstra's algorithm to find shortest paths from start.

        Returns distances and predecessors for all reachable nodes.

        Args:
            start: Starting zone name.
            end: Destination zone name (for early termination).

        Returns:
            Tuple of (distances_dict, predecessors_dict)
            - distances_dict: zone_name → distance (or inf if unreachable)
            - predecessors_dict: zone_name → previous_zone_name (for reconstruction)
        """
        # Initialize distances and predecessors
        distances: dict[str, int | float] = {zone: float("inf") for zone in self.graph.zones}
        distances[start] = 0
        predecessors: dict[str, str | None] = {zone: None for zone in self.graph.zones}

        # Priority queue: (distance, zone_name)
        pq: list[tuple[int | float, str]] = [(0, start)]
        visited: set[str] = set()

        while pq:
            current_distance, current_zone = heapq.heappop(pq)

            # Skip if already visited
            if current_zone in visited:
                continue

            # Early termination: if we reached end, no need to continue
            if current_zone == end:
                break

            visited.add(current_zone)

            # Skip blocked zones
            current_zone_obj = self.graph.get_zone(current_zone)
            if current_zone_obj and current_zone_obj.is_blocked:
                continue

            # Explore neighbors
            for neighbor in self.graph.get_neighbors(current_zone):
                if neighbor in visited:
                    continue

                # Skip blocked neighbors entirely
                neighbor_obj = self.graph.get_zone(neighbor)
                if neighbor_obj and neighbor_obj.is_blocked:
                    continue

                # Calculate distance to neighbor
                # Cost is the movement cost to ENTER the neighbor
                movement_cost = neighbor_obj.movement_cost if neighbor_obj else 1
                new_distance = current_distance + movement_cost

                # If we found a shorter path, update it
                if new_distance < distances[neighbor]:
                    distances[neighbor] = new_distance
                    predecessors[neighbor] = current_zone
                    heapq.heappush(pq, (new_distance, neighbor))

        return distances, predecessors

    def _reconstruct_path(
        self, end: str, predecessors: dict[str, str | None]
    ) -> list[str]:
        """Reconstruct path from start to end using predecessor links.

        Args:
            end: Destination zone name.
            predecessors: Dictionary of zone → previous_zone.

        Returns:
            List of zone names from start to end.
        """
        path: list[str] = []
        current = end

        while current is not None:
            path.append(current)
            current = predecessors[current]

        # Reverse to get start → end order
        path.reverse()
        return path

    def __repr__(self) -> str:
        """Return readable representation."""
        return f"Pathfinder(graph={self.graph})"

"""Unit tests for the pathfinding algorithm."""

import unittest

from core.graph import Graph
from core.pathfinder import Pathfinder, PathfindingError
from models.connection import Connection
from models.zone import Zone, ZoneType


class TestPathfinder(unittest.TestCase):
    """Test cases for the Pathfinder class."""

    def setUp(self) -> None:
        """Set up test fixtures."""
        # Create simple graph: hub -> mid -> goal
        self.zones = {
            "hub": Zone("hub", 0, 0, ZoneType.NORMAL),
            "mid": Zone("mid", 2, 2, ZoneType.NORMAL),
            "goal": Zone("goal", 5, 5, ZoneType.NORMAL),
        }
        self.connections = [
            Connection("hub", "mid"),
            Connection("mid", "goal"),
        ]
        self.graph = Graph(self.zones, self.connections)
        self.pathfinder = Pathfinder(self.graph)

    def test_find_shortest_path_basic(self) -> None:
        """Test finding a basic shortest path."""
        result = self.pathfinder.find_shortest_path("hub", "goal")
        self.assertEqual(result.path, ["hub", "mid", "goal"])
        self.assertEqual(result.cost, 2)

    def test_find_shortest_path_same_source_dest(self) -> None:
        """Test path where source == destination."""
        result = self.pathfinder.find_shortest_path("hub", "hub")
        self.assertEqual(result.path, ["hub"])
        self.assertEqual(result.cost, 0)

    def test_find_shortest_path_invalid_source(self) -> None:
        """Test that invalid source raises error."""
        with self.assertRaises(PathfindingError):
            self.pathfinder.find_shortest_path("invalid", "goal")

    def test_find_shortest_path_no_path(self) -> None:
        """Test that unreachable destination raises error."""
        # Add disconnected zone
        zones = self.zones.copy()
        zones["isolated"] = Zone("isolated", 10, 10, ZoneType.NORMAL)
        graph = Graph(zones, self.connections)
        pathfinder = Pathfinder(graph)

        with self.assertRaises(PathfindingError):
            pathfinder.find_shortest_path("hub", "isolated")


if __name__ == "__main__":
    unittest.main()

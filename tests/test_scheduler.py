"""Unit tests for the scheduler."""

import unittest

from core.graph import Graph
from core.pathfinder import Pathfinder
from core.scheduler import Scheduler
from models.connection import Connection
from models.drone import Drone
from models.enums import DroneState
from models.zone import Zone


class TestScheduler(unittest.TestCase):
    """Test cases for the Scheduler class."""

    def setUp(self) -> None:
        """Set up test fixtures."""
        self.zones = {
            "hub": Zone("hub", 0, 0),
            "mid": Zone("mid", 2, 2),
            "goal": Zone("goal", 5, 5),
        }
        self.connections = [
            Connection("hub", "mid"),
            Connection("mid", "goal"),
        ]
        self.graph = Graph(self.zones, self.connections)
        self.pathfinder = Pathfinder(self.graph)
        self.scheduler = Scheduler(self.graph, self.pathfinder)

    def test_schedule_single_drone(self) -> None:
        """Test scheduling a single drone."""
        drone = Drone(
            drone_id="D1",
            current_zone="hub",
            destination_zone="goal",
            state=DroneState.IDLE,
            path=["hub"],
        )
        drones = [drone]

        results = self.scheduler.schedule_all_drones(drones, "hub", "goal")

        self.assertTrue(len(results) > 0)
        self.assertTrue(drones[0].is_delivered)


if __name__ == "__main__":
    unittest.main()

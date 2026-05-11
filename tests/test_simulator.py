"""Unit tests for the simulator."""

import unittest

from core.graph import Graph
from core.pathfinder import Pathfinder
from core.scheduler import Scheduler
from core.simulator import Simulator
from models.connection import Connection
from models.drone import Drone
from models.enums import DroneState
from models.zone import Zone


class TestSimulator(unittest.TestCase):
    """Test cases for the Simulator class."""

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

    def test_simulator_initialization(self) -> None:
        """Test simulator initialization."""
        drone = Drone(
            drone_id="D1",
            current_zone="hub",
            destination_zone="goal",
            state=DroneState.IDLE,
            path=["hub"],
        )
        drones = [drone]

        simulator = Simulator(
            self.graph, self.scheduler, drones, "hub", "goal"
        )

        # Simulator doesn't expose drones directly, check other attributes
        self.assertEqual(simulator.start_zone, "hub")
        self.assertEqual(simulator.end_zone, "goal")

    def test_simulator_run(self) -> None:
        """Test running a simulation."""
        drone = Drone(
            drone_id="D1",
            current_zone="hub",
            destination_zone="goal",
            state=DroneState.IDLE,
            path=["hub"],
        )
        drones = [drone]

        simulator = Simulator(
            self.graph, self.scheduler, drones, "hub", "goal"
        )

        state = simulator.run()
        self.assertTrue(state.is_completed)


if __name__ == "__main__":
    unittest.main()

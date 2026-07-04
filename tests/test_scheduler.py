"""Unit tests for the scheduler."""

import unittest

from core.graph import Graph
from core.pathfinder import Pathfinder
from core.scheduler import Scheduler
from models.connection import Connection
from models.drone import Drone
from models.enums import DroneState
from models.zone import Zone, ZoneCategory, ZoneType


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


def test_leaving_zone_frees_capacity_same_turn() -> None:
    """A drone leaving A frees A for another drone in the same turn."""
    zones = {
        "start": Zone("start", 0, 0, category=ZoneCategory.START_HUB),
        "a": Zone("a", 1, 0, max_drones=1),
        "b": Zone("b", 2, 0, max_drones=1),
        "goal": Zone("goal", 3, 0, category=ZoneCategory.END_HUB),
    }
    graph = Graph(
        zones,
        [
            Connection("start", "a"),
            Connection("a", "b"),
            Connection("b", "goal"),
        ],
    )
    scheduler = Scheduler(graph, Pathfinder(graph))
    drones = [
        Drone("D1", "a", "goal", path=["a", "b", "goal"]),
        Drone("D2", "start", "goal", path=["start", "a", "b", "goal"]),
    ]

    result = scheduler.schedule_turn(drones, 1)

    assert result.moves == {"D1": "b", "D2": "a"}
    assert result.zone_occupancy["a"] == 1
    assert result.zone_occupancy["b"] == 1


def test_connection_capacity_one_allows_one_drone() -> None:
    zones = {
        "start": Zone("start", 0, 0, category=ZoneCategory.START_HUB),
        "a": Zone("a", 1, 0, max_drones=3),
        "goal": Zone("goal", 2, 0, category=ZoneCategory.END_HUB),
    }
    graph = Graph(
        zones,
        [Connection("start", "a", max_link_capacity=1),
         Connection("a", "goal", max_link_capacity=3)],
    )
    scheduler = Scheduler(graph, Pathfinder(graph))
    drones = [
        Drone("D1", "start", "goal", path=["start", "a", "goal"]),
        Drone("D2", "start", "goal", path=["start", "a", "goal"]),
    ]

    result = scheduler.schedule_turn(drones, 1)

    assert len(result.moves) == 1
    assert result.connection_usage["a-start"] == 1


def test_connection_capacity_two_allows_two_drones() -> None:
    zones = {
        "start": Zone("start", 0, 0, category=ZoneCategory.START_HUB),
        "a": Zone("a", 1, 0, max_drones=3),
        "goal": Zone("goal", 2, 0, category=ZoneCategory.END_HUB),
    }
    graph = Graph(
        zones,
        [Connection("start", "a", max_link_capacity=2),
         Connection("a", "goal", max_link_capacity=3)],
    )
    scheduler = Scheduler(graph, Pathfinder(graph))
    drones = [
        Drone("D1", "start", "goal", path=["start", "a", "goal"]),
        Drone("D2", "start", "goal", path=["start", "a", "goal"]),
    ]

    result = scheduler.schedule_turn(drones, 1)

    assert len(result.moves) == 2
    assert result.connection_usage["a-start"] == 2


def test_restricted_zone_outputs_transit_then_arrival() -> None:
    from core.simulator import Simulator

    zones = {
        "start": Zone("start", 0, 0, category=ZoneCategory.START_HUB),
        "restricted": Zone(
            "restricted", 1, 0, zone_type=ZoneType.RESTRICTED
        ),
        "goal": Zone("goal", 2, 0, category=ZoneCategory.END_HUB),
    }
    graph = Graph(
        zones,
        [Connection("start", "restricted"),
         Connection("restricted", "goal")],
    )
    pathfinder = Pathfinder(graph)
    scheduler = Scheduler(graph, pathfinder)
    drones = [Drone("D1", "start", "goal")]

    simulator = Simulator(graph, scheduler, drones, "start", "goal")
    simulator.run()

    assert simulator.get_output().splitlines() == [
        "D1-start-restricted",
        "D1-restricted",
        "D1-goal",
    ]


if __name__ == "__main__":
    unittest.main()

"""Quick validation tests for Scheduler."""

from models.connection import Connection
from models.drone import Drone
from models.enums import DroneState
from models.zone import Zone, ZoneCategory, ZoneType
from core.graph import Graph
from core.pathfinder import Pathfinder
from core.scheduler import Scheduler


def test_scheduler_simple_path() -> None:
    """Test scheduler on a simple linear path."""
    zones = {
        "hub": Zone("hub", 0, 0, category=ZoneCategory.START_HUB),
        "roof1": Zone("roof1", 1, 1),
        "goal": Zone("goal", 2, 2, category=ZoneCategory.END_HUB),
    }
    connections = [
        Connection("hub", "roof1"),
        Connection("roof1", "goal"),
    ]
    graph = Graph(zones, connections)
    pathfinder = Pathfinder(graph)
    scheduler = Scheduler(graph, pathfinder)

    drones = [
        Drone("D1", "hub", "goal", state=DroneState.IDLE),
        Drone("D2", "hub", "goal", state=DroneState.IDLE),
    ]

    results = scheduler.schedule_all_drones(drones, "hub", "goal")

    assert len(results) > 0
    assert all(r.is_valid for r in results)
    assert all(d.is_delivered for d in drones)
    print("✅ test_scheduler_simple_path passed")


def test_scheduler_capacity_constraint() -> None:
    """Test scheduler respects zone capacity."""
    zones = {
        "hub": Zone("hub", 0, 0, category=ZoneCategory.START_HUB),
        "narrow": Zone("narrow", 1, 1, max_drones=1),
        "goal": Zone("goal", 2, 2, category=ZoneCategory.END_HUB),
    }
    connections = [
        Connection("hub", "narrow"),
        Connection("narrow", "goal"),
    ]
    graph = Graph(zones, connections)
    pathfinder = Pathfinder(graph)
    scheduler = Scheduler(graph, pathfinder)

    drones = [
        Drone("D1", "hub", "goal", state=DroneState.IDLE),
        Drone("D2", "hub", "goal", state=DroneState.IDLE),
    ]

    results = scheduler.schedule_all_drones(drones, "hub", "goal")

    # Both drones should complete, but staggered
    assert all(d.is_delivered for d in drones)
    assert len(results) > 2  # Takes more turns due to capacity
    print("✅ test_scheduler_capacity_constraint passed")


if __name__ == "__main__":
    test_scheduler_simple_path()
    test_scheduler_capacity_constraint()
    print("\n✅ All scheduler tests passed!")

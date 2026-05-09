"""Quick validation tests for Simulator."""

from models.connection import Connection
from models.drone import Drone
from models.enums import DroneState
from models.zone import Zone, ZoneCategory, ZoneType
from core.graph import Graph
from core.pathfinder import Pathfinder
from core.scheduler import Scheduler
from core.simulator import Simulator


def test_simulator_simple_path() -> None:
    """Test simulator on a simple linear path."""
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
    ]

    simulator = Simulator(graph, scheduler, drones, "hub", "goal")
    state = simulator.run()

    assert state.is_completed
    assert all(d.is_delivered for d in state.drones)
    assert state.metrics.total_turns > 0
    print("✅ test_simulator_simple_path passed")
    print(f"  Output:\n{simulator.get_output()}")


def test_simulator_multiple_drones() -> None:
    """Test simulator with multiple drones."""
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

    simulator = Simulator(graph, scheduler, drones, "hub", "goal")
    state = simulator.run()

    assert state.is_completed
    assert len(state.drones) == 2
    assert state.metrics.total_turns > 0
    print("✅ test_simulator_multiple_drones passed")
    print(f"  Turns: {state.metrics.total_turns}")
    print(f"  Avg drones/turn: {state.metrics.avg_drones_per_turn:.2f}")


def test_simulator_output_format() -> None:
    """Test that simulator produces correctly formatted output."""
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
    ]

    simulator = Simulator(graph, scheduler, drones, "hub", "goal")
    state = simulator.run()

    output = simulator.get_output()
    assert "Turn" in output
    assert "D1-" in output
    print("✅ test_simulator_output_format passed")


if __name__ == "__main__":
    test_simulator_simple_path()
    test_simulator_multiple_drones()
    test_simulator_output_format()
    print("\n✅ All simulator tests passed!")

"""Quick validation tests for Drone and DroneState."""

from models.drone import Drone
from models.enums import DroneState


def test_drone_creation() -> None:
    """Test basic drone creation."""
    drone = Drone(
        drone_id="D1",
        current_zone="hub",
        destination_zone="goal",
    )
    assert drone.drone_id == "D1"
    assert drone.state == DroneState.IDLE


def test_drone_next_zone() -> None:
    """Test next_zone calculation."""
    drone = Drone(
        drone_id="D1",
        current_zone="hub",
        destination_zone="goal",
        path=["hub", "roof1", "roof2", "goal"],
    )
    assert drone.next_zone == "roof1"


def test_drone_move_to() -> None:
    """Test moving drone to next zone."""
    drone = Drone(
        drone_id="D1",
        current_zone="hub",
        destination_zone="goal",
        path=["hub", "roof1", "roof2", "goal"],
    )
    drone.move_to("roof1")
    assert drone.current_zone == "roof1"
    assert drone.state == DroneState.MOVING


def test_drone_restricted_transit() -> None:
    """Test restricted zone transit flow."""
    drone = Drone(
        drone_id="D1",
        current_zone="hub",
        destination_zone="goal",
    )
    drone.start_restricted_transit("hub-restricted")
    assert drone.state == DroneState.IN_TRANSIT_RESTRICTED
    assert drone.turns_until_arrival == 1

    drone.complete_restricted_transit("restricted_zone")
    assert drone.current_zone == "restricted_zone"
    assert drone.state == DroneState.MOVING


def test_drone_delivered() -> None:
    """Test marking drone as delivered."""
    drone = Drone(
        drone_id="D1",
        current_zone="goal",
        destination_zone="goal",
    )
    drone.mark_delivered()
    assert drone.is_delivered
    assert drone.state == DroneState.DELIVERED


if __name__ == "__main__":
    test_drone_creation()
    test_drone_next_zone()
    test_drone_move_to()
    test_drone_restricted_transit()
    test_drone_delivered()
    print("✅ All drone tests passed!")

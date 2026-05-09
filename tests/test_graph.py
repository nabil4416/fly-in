"""Quick validation tests for Graph."""

from models.connection import Connection
from models.zone import Zone, ZoneCategory, ZoneType
from core.graph import Graph, GraphError


def test_graph_creation() -> None:
    """Test basic graph creation."""
    zones = {
        "hub": Zone("hub", 0, 0, category=ZoneCategory.START_HUB),
        "goal": Zone("goal", 10, 10, category=ZoneCategory.END_HUB),
        "roof1": Zone("roof1", 3, 4),
    }
    connections = [
        Connection("hub", "roof1"),
        Connection("roof1", "goal"),
    ]
    graph = Graph(zones, connections)

    assert len(graph.zones) == 3
    assert len(graph.connections) == 2
    print("✅ test_graph_creation passed")


def test_get_neighbors() -> None:
    """Test getting neighbors of a zone."""
    zones = {
        "hub": Zone("hub", 0, 0, category=ZoneCategory.START_HUB),
        "goal": Zone("goal", 10, 10, category=ZoneCategory.END_HUB),
        "roof1": Zone("roof1", 3, 4),
    }
    connections = [
        Connection("hub", "roof1"),
        Connection("roof1", "goal"),
    ]
    graph = Graph(zones, connections)

    neighbors = graph.get_neighbors("roof1")
    assert set(neighbors) == {"hub", "goal"}
    print("✅ test_get_neighbors passed")


def test_get_connection() -> None:
    """Test getting a connection between zones."""
    zones = {
        "hub": Zone("hub", 0, 0, category=ZoneCategory.START_HUB),
        "goal": Zone("goal", 10, 10, category=ZoneCategory.END_HUB),
        "roof1": Zone("roof1", 3, 4),
    }
    connections = [
        Connection("hub", "roof1", max_link_capacity=2),
        Connection("roof1", "goal"),
    ]
    graph = Graph(zones, connections)

    conn = graph.get_connection("hub", "roof1")
    assert conn is not None
    assert conn.max_link_capacity == 2

    # Test bidirectional
    conn_rev = graph.get_connection("roof1", "hub")
    assert conn_rev is not None
    assert conn_rev.max_link_capacity == 2
    print("✅ test_get_connection passed")


def test_is_reachable() -> None:
    """Test reachability check."""
    zones = {
        "hub": Zone("hub", 0, 0, category=ZoneCategory.START_HUB),
        "goal": Zone("goal", 10, 10, category=ZoneCategory.END_HUB),
        "roof1": Zone("roof1", 3, 4),
    }
    connections = [
        Connection("hub", "roof1"),
        Connection("roof1", "goal"),
    ]
    graph = Graph(zones, connections)

    assert graph.is_reachable("hub", "goal")
    assert not graph.is_reachable("goal", "hub")  # graph is not symmetric in meaning
    print("✅ test_is_reachable passed")


def test_movement_cost() -> None:
    """Test movement cost for different zone types."""
    zones = {
        "hub": Zone("hub", 0, 0, category=ZoneCategory.START_HUB),
        "goal": Zone("goal", 10, 10, category=ZoneCategory.END_HUB),
        "restricted": Zone(
            "restricted", 3, 4, zone_type=ZoneType.RESTRICTED
        ),
    }
    connections = [
        Connection("hub", "restricted"),
        Connection("restricted", "goal"),
    ]
    graph = Graph(zones, connections)

    assert graph.get_movement_cost("hub") == 1  # normal
    assert graph.get_movement_cost("restricted") == 2  # restricted
    print("✅ test_movement_cost passed")


if __name__ == "__main__":
    test_graph_creation()
    test_get_neighbors()
    test_get_connection()
    test_is_reachable()
    test_movement_cost()
    print("\n✅ All graph tests passed!")

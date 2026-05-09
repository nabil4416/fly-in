"""Quick validation tests for Pathfinder."""

from models.connection import Connection
from models.zone import Zone, ZoneCategory, ZoneType
from core.graph import Graph
from core.pathfinder import Pathfinder, PathfindingResult


def test_pathfinder_simple_linear() -> None:
    """Test pathfinding on a simple linear path."""
    zones = {
        "hub": Zone("hub", 0, 0, category=ZoneCategory.START_HUB),
        "roof1": Zone("roof1", 1, 1),
        "roof2": Zone("roof2", 2, 2),
        "goal": Zone("goal", 3, 3, category=ZoneCategory.END_HUB),
    }
    connections = [
        Connection("hub", "roof1"),
        Connection("roof1", "roof2"),
        Connection("roof2", "goal"),
    ]
    graph = Graph(zones, connections)
    pathfinder = Pathfinder(graph)

    result = pathfinder.find_shortest_path("hub", "goal")
    assert result is not None
    assert result.path == ["hub", "roof1", "roof2", "goal"]
    assert result.cost == 3  # 1+1+1 for entering each of the 3 destination zones
    print("✅ test_pathfinder_simple_linear passed")


def test_pathfinder_with_restricted() -> None:
    """Test pathfinding with restricted zone (cost 2)."""
    zones = {
        "hub": Zone("hub", 0, 0, category=ZoneCategory.START_HUB),
        "restricted": Zone(
            "restricted", 1, 1, zone_type=ZoneType.RESTRICTED
        ),
        "goal": Zone("goal", 2, 2, category=ZoneCategory.END_HUB),
    }
    connections = [
        Connection("hub", "restricted"),
        Connection("restricted", "goal"),
    ]
    graph = Graph(zones, connections)
    pathfinder = Pathfinder(graph)

    result = pathfinder.find_shortest_path("hub", "goal")
    assert result is not None
    # Cost = 2 (restricted) + 1 (goal)
    assert result.cost == 3
    print("✅ test_pathfinder_with_restricted passed")


def test_pathfinder_blocked_avoidance() -> None:
    """Test that pathfinder avoids blocked zones."""
    zones = {
        "hub": Zone("hub", 0, 0, category=ZoneCategory.START_HUB),
        "blocked": Zone("blocked", 1, 1, zone_type=ZoneType.BLOCKED),
        "detour": Zone("detour", 0, 1),
        "goal": Zone("goal", 1, 2, category=ZoneCategory.END_HUB),
    }
    connections = [
        Connection("hub", "blocked"),
        Connection("hub", "detour"),
        Connection("blocked", "goal"),
        Connection("detour", "goal"),
    ]
    graph = Graph(zones, connections)
    pathfinder = Pathfinder(graph)

    result = pathfinder.find_shortest_path("hub", "goal")
    assert result is not None
    # Should go through detour, not blocked
    assert "blocked" not in result.path
    assert "detour" in result.path
    print("✅ test_pathfinder_blocked_avoidance passed")


def test_pathfinder_multiple_paths() -> None:
    """Test that pathfinder finds alternative paths."""
    zones = {
        "hub": Zone("hub", 0, 0, category=ZoneCategory.START_HUB),
        "path1": Zone("path1", 1, 0),
        "path2": Zone("path2", 0, 1),
        "goal": Zone("goal", 1, 1, category=ZoneCategory.END_HUB),
    }
    connections = [
        Connection("hub", "path1"),
        Connection("hub", "path2"),
        Connection("path1", "goal"),
        Connection("path2", "goal"),
    ]
    graph = Graph(zones, connections)
    pathfinder = Pathfinder(graph)

    paths = pathfinder.find_all_paths("hub", "goal")
    assert len(paths) > 0
    # All paths should have same cost (both have 2 moves)
    assert all(p.cost == 2 for p in paths)
    print("✅ test_pathfinder_multiple_paths passed")


def test_pathfinder_trivial_start_equals_end() -> None:
    """Test trivial path where start and end are the same zone."""
    zones = {
        "hub": Zone("hub", 0, 0, category=ZoneCategory.START_HUB),
        "goal": Zone("goal", 1, 1, category=ZoneCategory.END_HUB),
    }
    connections = [Connection("hub", "goal")]
    graph = Graph(zones, connections)
    pathfinder = Pathfinder(graph)

    result = pathfinder.find_shortest_path("hub", "hub")
    assert result is not None
    assert isinstance(result, PathfindingResult)
    assert result.path == ["hub"]
    assert result.cost == 0

    all_paths = pathfinder.find_all_paths("hub", "hub")
    assert len(all_paths) == 1
    assert all_paths[0].path == ["hub"]
    assert all_paths[0].cost == 0
    print("✅ test_pathfinder_trivial_start_equals_end passed")


if __name__ == "__main__":
    test_pathfinder_simple_linear()
    test_pathfinder_with_restricted()
    test_pathfinder_blocked_avoidance()
    test_pathfinder_multiple_paths()
    test_pathfinder_trivial_start_equals_end()
    print("\n✅ All pathfinder tests passed!")

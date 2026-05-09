"""Quick validation tests for Parser."""

from pathlib import Path
import tempfile

from core.parser import Parser
from utils.exceptions import ParsingError


def test_parse_valid_file() -> None:
    """Test parsing a valid input file."""
    content = """nb_drones: 2
start_hub: hub 0 0 [color=green]
end_hub: goal 10 10 [color=yellow]
hub: roof1 3 4 [zone=restricted]
connection: hub-roof1
connection: roof1-goal
"""
    with tempfile.NamedTemporaryFile(mode="w", suffix=".txt", delete=False) as f:
        f.write(content)
        f.flush()

        parser = Parser()
        data = parser.parse_file(f.name)

        assert data.num_drones == 2
        assert data.start_zone.name == "hub"
        assert data.end_zone.name == "goal"
        assert len(data.zones) == 3
        assert len(data.connections) == 2

        Path(f.name).unlink()
    print("✅ test_parse_valid_file passed")


def test_parse_duplicate_zone() -> None:
    """Test that duplicate zones raise error."""
    content = """nb_drones: 2
start_hub: hub 0 0
hub: roof1 3 4
hub: roof1 5 6
"""
    with tempfile.NamedTemporaryFile(mode="w", suffix=".txt", delete=False) as f:
        f.write(content)
        f.flush()

        parser = Parser()
        try:
            parser.parse_file(f.name)
            assert False, "Should have raised ParsingError"
        except ParsingError as e:
            assert "Duplicate zone name" in str(e)

        Path(f.name).unlink()
    print("✅ test_parse_duplicate_zone passed")


def test_parse_invalid_zone_type() -> None:
    """Test that invalid zone type raises error."""
    content = """nb_drones: 1
start_hub: hub 0 0 [zone=invalid]
end_hub: goal 10 10
"""
    with tempfile.NamedTemporaryFile(mode="w", suffix=".txt", delete=False) as f:
        f.write(content)
        f.flush()

        parser = Parser()
        try:
            parser.parse_file(f.name)
            assert False, "Should have raised ParsingError"
        except ParsingError as e:
            assert "Invalid zone type" in str(e)

        Path(f.name).unlink()
    print("✅ test_parse_invalid_zone_type passed")


def test_parse_zone_with_dash_name() -> None:
    """Test that zone names with dashes raise error."""
    content = """nb_drones: 1
start_hub: hub 0 0
end_hub: goal 10 10
hub: roof-1 3 4
"""
    with tempfile.NamedTemporaryFile(mode="w", suffix=".txt", delete=False) as f:
        f.write(content)
        f.flush()

        parser = Parser()
        try:
            parser.parse_file(f.name)
            assert False, "Should have raised ParsingError"
        except ParsingError as e:
            assert "cannot contain dashes" in str(e)

        Path(f.name).unlink()
    print("✅ test_parse_zone_with_dash_name passed")


if __name__ == "__main__":
    test_parse_valid_file()
    test_parse_duplicate_zone()
    test_parse_invalid_zone_type()
    test_parse_zone_with_dash_name()
    print("\n✅ All parser tests passed!")

"""Unit tests for the input file parser."""

import unittest
import tempfile
from pathlib import Path

import pytest

from core.parser import Parser
from utils.exceptions import ParsingError


class TestParser(unittest.TestCase):
    """Test cases for the Parser class."""

    def setUp(self) -> None:
        """Set up test fixtures."""
        self.parser = Parser()

    def test_parse_valid_simple_input(self) -> None:
        """Test parsing a valid simple input file."""
        content = """nb_drones: 2
start_hub: hub 0 0
end_hub: goal 5 5
hub: mid 2 2
connection: hub-mid
connection: mid-goal
"""
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".txt", delete=False
        ) as f:
            f.write(content)
            f.flush()
            result = self.parser.parse_file(f.name)

        self.assertEqual(result.num_drones, 2)
        self.assertEqual(result.start_zone.name, "hub")
        self.assertEqual(result.end_zone.name, "goal")
        self.assertEqual(len(result.zones), 3)
        self.assertEqual(len(result.connections), 2)

    def test_parse_missing_nb_drones(self) -> None:
        """Test that parsing fails without nb_drones."""
        content = """start_hub: hub 0 0
end_hub: goal 5 5
connection: hub-goal
"""
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".txt", delete=False
        ) as f:
            f.write(content)
            f.flush()
            with self.assertRaises(ParsingError):
                self.parser.parse_file(f.name)

    def test_parse_invalid_zone_type(self) -> None:
        """Test that invalid zone types raise errors."""
        content = """nb_drones: 1
start_hub: hub 0 0
end_hub: goal 5 5 [zone=invalid]
connection: hub-goal
"""
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".txt", delete=False
        ) as f:
            f.write(content)
            f.flush()
            with self.assertRaises(ParsingError):
                self.parser.parse_file(f.name)


def _write_map(tmp_path: Path, content: str) -> Path:
    path = tmp_path / "map.txt"
    path.write_text(content)
    return path


def test_parser_can_be_reused_twice(tmp_path: Path) -> None:
    """Parsing a second file with the same instance must start clean."""
    first = _write_map(
        tmp_path,
        """nb_drones: 1
start_hub: start 0 0
end_hub: goal 1 0
connection: start-goal
""",
    )
    second = tmp_path / "second.txt"
    second.write_text(
        """nb_drones: 2
start_hub: a 0 0
end_hub: b 1 0
connection: a-b
"""
    )

    parser = Parser()
    assert parser.parse_file(first).num_drones == 1
    parsed = parser.parse_file(second)
    assert parsed.num_drones == 2
    assert set(parsed.zones) == {"a", "b"}


def test_parse_negative_nb_drones(tmp_path: Path) -> None:
    path = _write_map(
        tmp_path,
        """nb_drones: -1
start_hub: start 0 0
end_hub: goal 1 0
connection: start-goal
""",
    )
    with pytest.raises(ParsingError):
        Parser().parse_file(path)


def test_parse_zero_nb_drones(tmp_path: Path) -> None:
    path = _write_map(
        tmp_path,
        """nb_drones: 0
start_hub: start 0 0
end_hub: goal 1 0
connection: start-goal
""",
    )
    with pytest.raises(ParsingError):
        Parser().parse_file(path)


def test_parse_duplicate_zone(tmp_path: Path) -> None:
    path = _write_map(
        tmp_path,
        """nb_drones: 1
start_hub: start 0 0
hub: mid 1 0
hub: mid 2 0
end_hub: goal 3 0
connection: start-mid
connection: mid-goal
""",
    )
    with pytest.raises(ParsingError):
        Parser().parse_file(path)


def test_parse_connection_to_unknown_zone(tmp_path: Path) -> None:
    path = _write_map(
        tmp_path,
        """nb_drones: 1
start_hub: start 0 0
end_hub: goal 1 0
connection: start-missing
""",
    )
    with pytest.raises(ParsingError):
        Parser().parse_file(path)


def test_parse_reversed_duplicate_connection(tmp_path: Path) -> None:
    path = _write_map(
        tmp_path,
        """nb_drones: 1
start_hub: start 0 0
end_hub: goal 1 0
connection: start-goal
connection: goal-start
""",
    )
    with pytest.raises(ParsingError):
        Parser().parse_file(path)


def test_parse_invalid_metadata(tmp_path: Path) -> None:
    path = _write_map(
        tmp_path,
        """nb_drones: 1
start_hub: start 0 0
hub: mid 1 0 [zone=normal broken]
end_hub: goal 2 0
connection: start-mid
connection: mid-goal
""",
    )
    with pytest.raises(ParsingError):
        Parser().parse_file(path)


def test_parse_zero_capacity(tmp_path: Path) -> None:
    path = _write_map(
        tmp_path,
        """nb_drones: 1
start_hub: start 0 0
hub: mid 1 0 [max_drones=0]
end_hub: goal 2 0
connection: start-mid
connection: mid-goal
""",
    )
    with pytest.raises(ParsingError):
        Parser().parse_file(path)


def test_parse_missing_start(tmp_path: Path) -> None:
    path = _write_map(
        tmp_path,
        """nb_drones: 1
end_hub: goal 1 0
""",
    )
    with pytest.raises(ParsingError):
        Parser().parse_file(path)


def test_parse_missing_end(tmp_path: Path) -> None:
    path = _write_map(
        tmp_path,
        """nb_drones: 1
start_hub: start 0 0
""",
    )
    with pytest.raises(ParsingError):
        Parser().parse_file(path)


if __name__ == "__main__":
    unittest.main()

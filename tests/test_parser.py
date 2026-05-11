"""Unit tests for the input file parser."""

import unittest
from pathlib import Path
import tempfile

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


if __name__ == "__main__":
    unittest.main()

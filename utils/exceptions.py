"""Custom exceptions for the Fly-in project.

Provides a clear exception hierarchy for different error categories:
- Parsing errors (input file validation)
- Graph errors (connectivity, structure)
- Pathfinding errors (no route found)
- Scheduling errors (conflict resolution)
- Simulation errors (runtime issues)
"""


class FlyInException(Exception):
    """Base exception for all Fly-in errors."""

    pass


class ParsingError(FlyInException):
    """Exception raised when parsing input file fails."""

    def __init__(self, message: str, line_number: int | None = None) -> None:
        """Initialize parsing error with line context.

        Args:
            message: Error description.
            line_number: Line number where error occurred (1-indexed).
        """
        if line_number is not None:
            full_message = f"Parsing error at line {line_number}: {message}"
        else:
            full_message = f"Parsing error: {message}"
        super().__init__(full_message)
        self.line_number = line_number


class GraphError(FlyInException):
    """Exception raised when graph operations fail."""

    pass


class PathfindingError(FlyInException):
    """Exception raised when pathfinding fails."""

    pass


class SchedulingError(FlyInException):
    """Exception raised when scheduling conflicts occur."""

    pass


class SimulationError(FlyInException):
    """Exception raised during simulation execution."""

    pass

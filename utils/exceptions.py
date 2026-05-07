"""Custom exceptions for the Fly-in project."""


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
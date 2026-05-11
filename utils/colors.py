"""Terminal color utilities for colored output.

Provides ANSI color codes and helper functions for displaying
colored output in the terminal without external dependencies.
"""

# ANSI color codes
RESET = "\033[0m"
BOLD = "\033[1m"
DIM = "\033[2m"

# Foreground colors
BLACK = "\033[30m"
RED = "\033[31m"
GREEN = "\033[32m"
YELLOW = "\033[33m"
BLUE = "\033[34m"
MAGENTA = "\033[35m"
CYAN = "\033[36m"
WHITE = "\033[37m"

# Background colors
BG_RED = "\033[41m"
BG_GREEN = "\033[42m"
BG_YELLOW = "\033[43m"
BG_BLUE = "\033[44m"
BG_MAGENTA = "\033[45m"
BG_CYAN = "\033[46m"

# Color mapping for zone types
ZONE_TYPE_COLORS = {
    "normal": BLUE,
    "restricted": RED,
    "priority": GREEN,
    "blocked": MAGENTA,
}

# Color mapping for drone states
DRONE_STATE_COLORS = {
    "idle": YELLOW,
    "moving": CYAN,
    "waiting_for_capacity": YELLOW,
    "in_transit_restricted": RED,
    "delivered": GREEN,
}


def colorize(text: str, color: str) -> str:
    """Apply ANSI color to text.

    Args:
        text: Text to colorize.
        color: ANSI color code.

    Returns:
        Colored text with reset code.
    """
    return f"{color}{text}{RESET}"


def get_color_for_zone_type(zone_type: str) -> str:
    """Get ANSI color code for a zone type.

    Args:
        zone_type: Zone type name (normal, restricted, priority, blocked).

    Returns:
        ANSI color code, or empty string if not found.
    """
    return ZONE_TYPE_COLORS.get(zone_type, "")


def get_color_for_drone_state(state: str) -> str:
    """Get ANSI color code for a drone state.

    Args:
        state: Drone state name.

    Returns:
        ANSI color code, or empty string if not found.
    """
    return DRONE_STATE_COLORS.get(state, "")

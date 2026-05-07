"""Enumerations for the Fly-in drone simulation."""

from enum import Enum


class DroneState(str, Enum):
    """Enumeration of possible drone states during simulation.

    Attributes:
        IDLE: Drone is at the start zone waiting to begin.
        MOVING: Drone is moving between zones (normal 1-turn movement).
        WAITING_FOR_CAPACITY: Drone is waiting because destination is full.
        IN_TRANSIT_RESTRICTED: Drone is on a connection to a restricted zone.
        DELIVERED: Drone has reached the end zone.
    """

    IDLE = "idle"
    MOVING = "moving"
    WAITING_FOR_CAPACITY = "waiting_for_capacity"
    IN_TRANSIT_RESTRICTED = "in_transit_restricted"
    DELIVERED = "delivered"

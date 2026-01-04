"""Object type enumeration for circuit components."""

from enum import Enum


class ObjectType(str, Enum):
    """Types of circuit objects."""

    BATTERY = "Battery"
    LIION_CELL = "Li-Ion Cell"
    LED = "LED"
    WIRE = "Wire"
    NONE = "NONE"

"""Object type enumeration for circuit components."""

from enum import Enum

# These names for all component types are used to link the model, and view


class ObjectType(str, Enum):
    """Types of circuit objects."""

    BATTERY = "Battery"
    LIION_CELL = "Li-Ion Cell"
    LED = "LED"
    WIRE = "Wire"
    NONE = "NONE"

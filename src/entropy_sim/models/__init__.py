"""Circuit component models."""

from .base_connector import BaseConnector, ConnectorPoint
from .base_item import BaseItem
from .battery import Battery
from .circuit import Circuit
from .led import LED
from .liion_cell import LiIonCell
from .point import ConnectionPoint, Point
from .wire import Wire

# Backward compatibility alias
CircuitObject = BaseItem

__all__ = [
    "Battery",
    "Circuit",
    "BaseItem",
    "CircuitObject",
    "BaseConnector",
    "ConnectionPoint",
    "LED",
    "LiIonCell",
    "Point",
    "Wire",
    "ConnectorPoint",
]

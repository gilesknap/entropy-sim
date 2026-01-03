"""Lithium-ion cell component model."""

from typing import Literal

from pydantic import Field

from entropy_sim.object_type import ObjectType

from .circuit_base import CircuitBase
from .point import ConnectionPoint, Point


class LiIonCell(CircuitBase):
    """A cylindrical Lithium Ion battery cell with button positive terminal."""

    object_type: Literal[ObjectType.LIION_CELL] = ObjectType.LIION_CELL
    rotatable: bool = True
    has_connections: bool = True
    voltage: float = 3.7  # Volts (typical Li-Ion)
    size_x: float = 30.0  # Cell is 60 wide
    size_y: float = 10.0  # Cell is 20 tall
    positive: ConnectionPoint = Field(
        default_factory=lambda: ConnectionPoint(label="positive")
    )
    negative: ConnectionPoint = Field(
        default_factory=lambda: ConnectionPoint(label="negative")
    )

    @property
    def connection_points(self) -> list[ConnectionPoint]:
        """Get all connection points for this object."""
        return [self.positive, self.negative]

    def model_post_init(self, __context: object) -> None:
        """Update connection point positions relative to cell position."""
        self.update_connection_positions()

    def update_connection_positions(self) -> None:
        """Update connection points based on cell position and rotation."""
        import math

        # Cylindrical cell horizontal with button terminal at right (positive)
        # and flat terminal at left (negative)
        # Positive at (35, 0), Negative at (-33, 0)
        # Apply rotation around the center
        angle = math.radians(self.rotation)
        cos_a = math.cos(angle)
        sin_a = math.sin(angle)

        # Positive terminal at right (35, 0)
        pos_local_x = 35
        pos_local_y = 0
        pos_x = pos_local_x * cos_a - pos_local_y * sin_a
        pos_y = pos_local_x * sin_a + pos_local_y * cos_a
        self.positive.position = Point(
            x=self.position.x + pos_x, y=self.position.y + pos_y
        )

        # Negative terminal at left (-33, 0)
        neg_local_x = -33
        neg_local_y = 0
        neg_x = neg_local_x * cos_a - neg_local_y * sin_a
        neg_y = neg_local_x * sin_a + neg_local_y * cos_a
        self.negative.position = Point(
            x=self.position.x + neg_x, y=self.position.y + neg_y
        )

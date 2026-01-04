"""Battery component model."""

from typing import Literal

from pydantic import Field

from entropy_sim.object_type import ObjectType

from .base_item import BaseItem
from .point import ConnectionPoint, Point


class Battery(BaseItem):
    """A battery with positive and negative terminals."""

    object_type: Literal[ObjectType.BATTERY] = ObjectType.BATTERY
    rotatable: bool = True
    has_connections: bool = True
    voltage: float = 9.0  # Volts
    size_x: float = 40.0  # Battery is 80 wide
    size_y: float = 20.0  # Battery is 40 tall
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
        """Update connection point positions relative to battery position."""
        self.update_connection_positions()

    def update_connection_positions(self) -> None:
        """Update connection points based on battery position and rotation."""
        import math

        # 9V Battery has snap terminals protruding from the top
        # Connection points at the ends of the terminals
        # Positive terminal at left (-15, -35), Negative at right (15, -35)
        # Apply rotation around the center
        angle = math.radians(self.rotation)
        cos_a = math.cos(angle)
        sin_a = math.sin(angle)

        # Positive terminal at top-left (-15, -35)
        pos_local_x = -15
        pos_local_y = -35
        pos_x = pos_local_x * cos_a - pos_local_y * sin_a
        pos_y = pos_local_x * sin_a + pos_local_y * cos_a
        self.positive.position = Point(
            x=self.position.x + pos_x, y=self.position.y + pos_y
        )

        # Negative terminal at top-right (15, -35)
        neg_local_x = 15
        neg_local_y = -35
        neg_x = neg_local_x * cos_a - neg_local_y * sin_a
        neg_y = neg_local_x * sin_a + neg_local_y * cos_a
        self.negative.position = Point(
            x=self.position.x + neg_x, y=self.position.y + neg_y
        )

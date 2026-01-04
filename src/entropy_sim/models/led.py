"""LED component model."""

from typing import Literal

from pydantic import Field

from entropy_sim.object_type import ObjectType

from .base_item import BaseItem
from .point import ConnectionPoint, Point


class LED(BaseItem):
    """An LED with anode and cathode terminals."""

    object_type: Literal[ObjectType.LED] = ObjectType.LED
    is_rotatable: bool = True
    has_connections: bool = True
    color: str = "red"
    is_on: bool = False
    size_x: float = 15.0  # LED is 30 wide
    size_y: float = 30.0  # LED is 60 tall
    anode: ConnectionPoint = Field(
        default_factory=lambda: ConnectionPoint(label="positive")
    )
    cathode: ConnectionPoint = Field(
        default_factory=lambda: ConnectionPoint(label="negative")
    )

    @property
    def connection_points(self) -> list[ConnectionPoint]:
        """Get all connection points for this object."""
        return [self.anode, self.cathode]

    def model_post_init(self, __context: object) -> None:
        """Update connection point positions relative to LED position."""
        self.update_connection_positions()

    def update_connection_positions(self) -> None:
        """Update connection points based on LED position and rotation."""
        import math

        # LED has leads at bottom: anode at (-6, 30), cathode at (6, 30)
        # Apply rotation around the center
        angle = math.radians(self.rotation)
        cos_a = math.cos(angle)
        sin_a = math.sin(angle)

        # Anode lead at bottom-left (-6, 30)
        anode_local_x = -6
        anode_local_y = 30
        anode_x = anode_local_x * cos_a - anode_local_y * sin_a
        anode_y = anode_local_x * sin_a + anode_local_y * cos_a
        self.anode.position = Point(
            x=self.position.x + anode_x, y=self.position.y + anode_y
        )

        # Cathode lead at bottom-right (6, 30)
        cathode_local_x = 6
        cathode_local_y = 30
        cathode_x = cathode_local_x * cos_a - cathode_local_y * sin_a
        cathode_y = cathode_local_x * sin_a + cathode_local_y * cos_a
        self.cathode.position = Point(
            x=self.position.x + cathode_x, y=self.position.y + cathode_y
        )

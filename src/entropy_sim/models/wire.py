"""Wire component model."""

from typing import Literal
from uuid import UUID

from pydantic import BaseModel, Field

from entropy_sim.object_type import ObjectType

from .circuit_base import CircuitBase
from .point import ConnectionPoint


class WirePoint(BaseModel):
    """A point along a wire's path."""

    x: float
    y: float


class Wire(CircuitBase):
    """A wire connecting two connection points."""

    object_type: Literal[ObjectType.WIRE] = ObjectType.WIRE
    start: ConnectionPoint = Field(
        default_factory=lambda: ConnectionPoint(label="start")
    )
    end: ConnectionPoint = Field(default_factory=lambda: ConnectionPoint(label="end"))
    path: list[WirePoint] = Field(default_factory=list)
    # IDs of connection points this wire is connected to
    start_connected_to: UUID | None = None
    end_connected_to: UUID | None = None

    def get_bounds(self) -> tuple[float, float, float, float]:
        """Get bounding box including all path points."""
        all_x = [self.start.position.x, self.end.position.x] + [p.x for p in self.path]
        all_y = [self.start.position.y, self.end.position.y] + [p.y for p in self.path]
        return (min(all_x), min(all_y), max(all_x), max(all_y))

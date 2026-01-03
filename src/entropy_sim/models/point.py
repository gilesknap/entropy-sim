"""Point and connection point models."""

from typing import Literal
from uuid import UUID, uuid4

from pydantic import BaseModel, Field


class Point(BaseModel):
    """A 2D point on the canvas."""

    x: float = 0.0
    y: float = 0.0


class ConnectionPoint(BaseModel):
    """A connection point on a circuit object."""

    id: UUID = Field(default_factory=uuid4)
    position: Point = Field(default_factory=Point)
    label: Literal["positive", "negative", "start", "end"] = "positive"
    connected_to: UUID | None = None  # ID of connected wire endpoint

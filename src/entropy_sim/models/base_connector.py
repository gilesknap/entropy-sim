"""Wire component model."""

from uuid import UUID

from pydantic import BaseModel, Field

from .base_item import BaseItem
from .point import ConnectionPoint


class ConnectorPoint(BaseModel):
    """A point along a wire's path."""

    x: float
    y: float


class BaseConnector(BaseItem):
    """A connector for connecting two connection points."""

    is_connector: bool = True
    start: ConnectionPoint = Field(
        default_factory=lambda: ConnectionPoint(label="start")
    )
    end: ConnectionPoint = Field(default_factory=lambda: ConnectionPoint(label="end"))
    path: list[ConnectorPoint] = Field(default_factory=list)
    # IDs of connection points this wire is connected to
    start_connected_to: UUID | None = None
    end_connected_to: UUID | None = None

    def get_bounds(self) -> tuple[float, float, float, float]:
        """Get bounding box including all path points.

        Returns:
            Tuple of (min_x, min_y, max_x, max_y) coordinates.
        """
        all_x = [self.start.position.x, self.end.position.x] + [p.x for p in self.path]
        all_y = [self.start.position.y, self.end.position.y] + [p.y for p in self.path]
        return (min(all_x), min(all_y), max(all_x), max(all_y))

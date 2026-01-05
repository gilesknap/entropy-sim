"""Base class for all circuit objects."""

from uuid import UUID, uuid4

from pydantic import BaseModel, Field

from .point import ConnectionPoint, Point


class BaseItem(BaseModel):
    """Base class for all circuit objects."""

    id: UUID = Field(default_factory=uuid4)
    position: Point = Field(default_factory=Point)
    rotation: float = 0.0  # Rotation in degrees
    is_rotatable: bool = False  # Whether this object can be rotated
    has_connections: bool = False  # Whether this object has connection points
    is_connector: bool = False  # Whether this object is a connector (e.g., wire)
    size_x: float = 0.0  # Half-width (extends left and right from position)
    size_y: float = 0.0  # Half-height (extends up and down from position)

    @property
    def display_name(self) -> str:
        """Get the display name for this object type.

        Returns:
            The human-readable name of this object type.
        """
        # this would fail in the base class which does not have this Literal attribute
        return self.object_type.value  # type: ignore[attr-defined]

    @property
    def connection_points(self) -> list[ConnectionPoint]:
        """Get all connection points for this object.

        Returns:
            List of connection points on this object.

        Raises:
            NotImplementedError: Must be implemented by subclasses.
        """
        raise NotImplementedError

    def get_bounds(self) -> tuple[float, float, float, float]:
        """Get bounding box (min_x, min_y, max_x, max_y).

        Returns:
            Tuple of (min_x, min_y, max_x, max_y) coordinates.
        """
        return (
            self.position.x - self.size_x,
            self.position.y - self.size_y,
            self.position.x + self.size_x,
            self.position.y + self.size_y,
        )

    def contains_point(self, point: Point) -> bool:
        """Check if a point is within this object's bounds.

        Args:
            point: The point to check.

        Returns:
            True if the point is inside the object's bounding box.
        """
        min_x, min_y, max_x, max_y = self.get_bounds()
        return min_x <= point.x <= max_x and min_y <= point.y <= max_y

    def update_connection_positions(self) -> None:
        """Update connection points based on position and rotation.

        Raises:
            NotImplementedError: Must be implemented by subclasses.
        """
        raise NotImplementedError

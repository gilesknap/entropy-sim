"""Circuit model containing all components."""

from typing import Annotated
from uuid import UUID, uuid4

from pydantic import BaseModel, Discriminator, Field

from entropy_sim.object_type import ObjectType

from .battery import Battery
from .circuit_base import CircuitBase
from .led import LED
from .liion_cell import LiIonCell
from .point import ConnectionPoint, Point
from .wire import Wire

# Type alias for any component with discriminated union
Component = Annotated[
    Battery | LiIonCell | LED | Wire,
    Discriminator("object_type"),
]

# Mapping of ObjectType to component class
_COMPONENT_CLASSES: dict[ObjectType, type[Battery | LiIonCell | LED]] = {
    ObjectType.BATTERY: Battery,
    ObjectType.LIION_CELL: LiIonCell,
    ObjectType.LED: LED,
}


class Circuit(BaseModel):
    """A collection of circuit objects."""

    id: UUID = Field(default_factory=uuid4)
    name: str = "Untitled Circuit"
    components: list[Component] = Field(default_factory=list)
    wires: list[Wire] = Field(default_factory=list)

    @property
    def all_objects(self) -> list[CircuitBase]:
        """Get all circuit objects as a single list."""
        return [*self.components, *self.wires]

    def get_bounds(self) -> tuple[float, float, float, float]:
        """Get bounding box of all components (min_x, min_y, max_x, max_y)."""
        if not self.all_objects:
            return (0, 0, 0, 0)

        min_x = float("inf")
        min_y = float("inf")
        max_x = float("-inf")
        max_y = float("-inf")

        for obj in self.all_objects:
            obj_min_x, obj_min_y, obj_max_x, obj_max_y = obj.get_bounds()
            min_x = min(min_x, obj_min_x)
            min_y = min(min_y, obj_min_y)
            max_x = max(max_x, obj_max_x)
            max_y = max(max_y, obj_max_y)

        return (min_x, min_y, max_x, max_y)

    def add_object(
        self, object_type: ObjectType, position: Point | None = None, **kwargs
    ) -> CircuitBase:
        """Add a new component to the circuit based on object type.

        Args:
            object_type: The type of object to create
            position: Position for the object (default: Point(0, 0))
            **kwargs: Additional arguments for specific object types
            (e.g., color for LED)

        Returns:
            The created component object
        """
        obj_class = _COMPONENT_CLASSES.get(object_type)

        # there are components (circuit elements etc) and connectors (wires etc.)
        if obj_class is None:
            raise ValueError(f"Cannot add object of type {object_type}")

        obj = obj_class(position=position or Point(), **kwargs)
        obj.update_connection_positions()
        self.components.append(obj)
        return obj

    def add_wire(self) -> Wire:
        """Add a new wire to the circuit."""
        wire = Wire()
        self.wires.append(wire)
        return wire

    def get_all_connection_points(
        self,
    ) -> list[tuple[UUID, ConnectionPoint, Component]]:
        """Get all connection points in the circuit with their parent objects."""
        points: list[tuple[UUID, ConnectionPoint, Component]] = []
        for component in self.components:
            for conn_point in component.connection_points:
                points.append((component.id, conn_point, component))
        return points

    def find_nearest_connection_point(
        self, pos: Point, max_distance: float = 20.0
    ) -> tuple[UUID, ConnectionPoint, Component] | None:
        """Find the nearest connection point within max_distance."""
        nearest: tuple[UUID, ConnectionPoint, Component] | None = None
        min_dist = max_distance

        for obj_id, conn_point, obj in self.get_all_connection_points():
            dx = conn_point.position.x - pos.x
            dy = conn_point.position.y - pos.y
            dist = (dx * dx + dy * dy) ** 0.5
            if dist < min_dist:
                min_dist = dist
                nearest = (obj_id, conn_point, obj)

        return nearest

    def remove_component(self, component_id: UUID) -> bool:
        """Remove a component by ID."""
        for i, component in enumerate(self.components):
            if component.id == component_id:
                self.components.pop(i)
                return True
        for i, wire in enumerate(self.wires):
            if wire.id == component_id:
                self.wires.pop(i)
                return True
        return False

"""Pydantic models for circuit simulation objects."""

from enum import Enum
from typing import Annotated, Literal
from uuid import UUID, uuid4

from pydantic import BaseModel, Discriminator, Field


class ObjectType(str, Enum):
    """Types of circuit objects."""

    BATTERY = "battery"
    LIION_CELL = "liion_cell"
    LED = "led"
    WIRE = "wire"

    @property
    def display_name(self) -> str:
        """Get the human-readable display name for this object type."""
        return {
            ObjectType.BATTERY: "Battery",
            ObjectType.LIION_CELL: "Li-Ion Cell",
            ObjectType.LED: "LED",
            ObjectType.WIRE: "Wire",
        }[self]


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


class CircuitObject(BaseModel):
    """Base class for all circuit objects."""

    id: UUID = Field(default_factory=uuid4)
    position: Point = Field(default_factory=Point)
    rotation: float = 0.0  # Rotation in degrees
    rotatable: bool = False  # Whether this object can be rotated
    has_connections: bool = False  # Whether this object has connection points
    size_x: float = 0.0  # Half-width (extends left and right from position)
    size_y: float = 0.0  # Half-height (extends up and down from position)

    @property
    def display_name(self) -> str:
        """Get the display name for this object type."""
        return self.object_type.display_name  # type: ignore[attr-defined]

    @property
    def connection_points(self) -> list[ConnectionPoint]:
        """Get all connection points for this object."""
        raise NotImplementedError

    def get_bounds(self) -> tuple[float, float, float, float]:
        """Get bounding box (min_x, min_y, max_x, max_y)."""
        return (
            self.position.x - self.size_x,
            self.position.y - self.size_y,
            self.position.x + self.size_x,
            self.position.y + self.size_y,
        )

    def contains_point(self, point: Point) -> bool:
        """Check if a point is within this object's bounds."""
        min_x, min_y, max_x, max_y = self.get_bounds()
        return min_x <= point.x <= max_x and min_y <= point.y <= max_y

    def update_connection_positions(self) -> None:
        """Update connection points based on position and rotation. Override
        in subclasses."""
        raise NotImplementedError


class Battery(CircuitObject):
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


class LiIonCell(CircuitObject):
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


class LED(CircuitObject):
    """An LED with anode and cathode terminals."""

    object_type: Literal[ObjectType.LED] = ObjectType.LED
    rotatable: bool = True
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


class WirePoint(BaseModel):
    """A point along a wire's path."""

    x: float
    y: float


class Wire(CircuitObject):
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


# Type alias for any component with discriminated union
Component = Annotated[
    Battery | LiIonCell | LED | Wire,
    Discriminator("object_type"),
]


class Circuit(BaseModel):
    """A collection of circuit objects."""

    id: UUID = Field(default_factory=uuid4)
    name: str = "Untitled Circuit"
    components: list[
        Annotated[Battery | LiIonCell | LED, Discriminator("object_type")]
    ] = Field(default_factory=list)
    wires: list[Wire] = Field(default_factory=list)

    @property
    def all_objects(self) -> list[CircuitObject]:
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

    def add_battery(self, position: Point | None = None) -> Battery:
        """Add a new battery to the circuit."""
        battery = Battery(position=position or Point())
        battery.update_connection_positions()
        self.components.append(battery)
        return battery

    def add_liion_cell(self, position: Point | None = None) -> LiIonCell:
        """Add a new Li-Ion cell to the circuit."""
        cell = LiIonCell(position=position or Point())
        cell.update_connection_positions()
        self.components.append(cell)
        return cell

    def add_led(self, position: Point | None = None, color: str = "red") -> LED:
        """Add a new LED to the circuit."""
        led = LED(position=position or Point(), color=color)
        led.update_connection_positions()
        self.components.append(led)
        return led

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

"""Pydantic models for circuit simulation objects."""

from enum import Enum
from typing import Literal
from uuid import UUID, uuid4

from pydantic import BaseModel, Field


class ObjectType(str, Enum):
    """Types of circuit objects."""

    BATTERY = "battery"
    LED = "led"
    WIRE = "wire"


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
    size_x: float = 0.0  # Half-width (extends left and right from position)
    size_y: float = 0.0  # Half-height (extends up and down from position)

    def get_bounds(self) -> tuple[float, float, float, float]:
        """Get bounding box (min_x, min_y, max_x, max_y)."""
        return (
            self.position.x - self.size_x,
            self.position.y - self.size_y,
            self.position.x + self.size_x,
            self.position.y + self.size_y,
        )


class Battery(CircuitObject):
    """A battery with positive and negative terminals."""

    object_type: Literal[ObjectType.BATTERY] = ObjectType.BATTERY
    voltage: float = 9.0  # Volts
    size_x: float = 40.0  # Battery is 80 wide
    size_y: float = 20.0  # Battery is 40 tall
    positive: ConnectionPoint = Field(
        default_factory=lambda: ConnectionPoint(label="positive")
    )
    negative: ConnectionPoint = Field(
        default_factory=lambda: ConnectionPoint(label="negative")
    )

    def model_post_init(self, __context: object) -> None:
        """Update connection point positions relative to battery position."""
        self.update_connection_positions()

    def update_connection_positions(self) -> None:
        """Update connection points based on battery position and rotation."""
        import math

        # Battery is horizontal, positive on right, negative on left
        # Apply rotation around the center
        angle = math.radians(self.rotation)
        cos_a = math.cos(angle)
        sin_a = math.sin(angle)

        # Right side (positive terminal) at +40 offset
        pos_x = 40 * cos_a
        pos_y = 40 * sin_a
        self.positive.position = Point(
            x=self.position.x + pos_x, y=self.position.y + pos_y
        )

        # Left side (negative terminal) at -40 offset
        neg_x = -40 * cos_a
        neg_y = -40 * sin_a
        self.negative.position = Point(
            x=self.position.x + neg_x, y=self.position.y + neg_y
        )


class LED(CircuitObject):
    """An LED with anode and cathode terminals."""

    object_type: Literal[ObjectType.LED] = ObjectType.LED
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

    def model_post_init(self, __context: object) -> None:
        """Update connection point positions relative to LED position."""
        self.update_connection_positions()

    def update_connection_positions(self) -> None:
        """Update connection points based on LED position and rotation."""
        import math

        # LED is vertical, anode on top, cathode on bottom
        # Apply rotation around the center
        angle = math.radians(self.rotation)
        cos_a = math.cos(angle)
        sin_a = math.sin(angle)

        # Top (anode) at -30 offset in y
        anode_x = -30 * sin_a
        anode_y = -30 * cos_a
        self.anode.position = Point(
            x=self.position.x + anode_x, y=self.position.y + anode_y
        )

        # Bottom (cathode) at +30 offset in y
        cathode_x = 30 * sin_a
        cathode_y = 30 * cos_a
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


# Type alias for any component
Component = Battery | LED | Wire


class Circuit(BaseModel):
    """A collection of circuit objects."""

    id: UUID = Field(default_factory=uuid4)
    name: str = "Untitled Circuit"
    batteries: list[Battery] = Field(default_factory=list)
    leds: list[LED] = Field(default_factory=list)
    wires: list[Wire] = Field(default_factory=list)

    @property
    def all_objects(self) -> list[CircuitObject]:
        """Get all circuit objects as a single list."""
        return [*self.batteries, *self.leds, *self.wires]

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
        self.batteries.append(battery)
        return battery

    def add_led(self, position: Point | None = None, color: str = "red") -> LED:
        """Add a new LED to the circuit."""
        led = LED(position=position or Point(), color=color)
        led.update_connection_positions()
        self.leds.append(led)
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
        for battery in self.batteries:
            points.append((battery.id, battery.positive, battery))
            points.append((battery.id, battery.negative, battery))
        for led in self.leds:
            points.append((led.id, led.anode, led))
            points.append((led.id, led.cathode, led))
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
        for i, battery in enumerate(self.batteries):
            if battery.id == component_id:
                self.batteries.pop(i)
                return True
        for i, led in enumerate(self.leds):
            if led.id == component_id:
                self.leds.pop(i)
                return True
        for i, wire in enumerate(self.wires):
            if wire.id == component_id:
                self.wires.pop(i)
                return True
        return False

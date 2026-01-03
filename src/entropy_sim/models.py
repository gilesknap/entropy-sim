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


class Battery(CircuitObject):
    """A battery with positive and negative terminals."""

    object_type: Literal[ObjectType.BATTERY] = ObjectType.BATTERY
    voltage: float = 9.0  # Volts
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
        """Update connection points based on battery position."""
        # Battery is horizontal, positive on right, negative on left
        self.positive.position = Point(x=self.position.x + 40, y=self.position.y)
        self.negative.position = Point(x=self.position.x - 40, y=self.position.y)


class LED(CircuitObject):
    """An LED with anode and cathode terminals."""

    object_type: Literal[ObjectType.LED] = ObjectType.LED
    color: str = "red"
    is_on: bool = False
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
        """Update connection points based on LED position."""
        # LED is vertical, anode on top, cathode on bottom
        self.anode.position = Point(x=self.position.x, y=self.position.y - 30)
        self.cathode.position = Point(x=self.position.x, y=self.position.y + 30)


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


# Type alias for any component
Component = Battery | LED | Wire


class Circuit(BaseModel):
    """A collection of circuit objects."""

    id: UUID = Field(default_factory=uuid4)
    name: str = "Untitled Circuit"
    batteries: list[Battery] = Field(default_factory=list)
    leds: list[LED] = Field(default_factory=list)
    wires: list[Wire] = Field(default_factory=list)

    def get_bounds(self) -> tuple[float, float, float, float]:
        """Get bounding box of all components (min_x, min_y, max_x, max_y)."""
        if not self.batteries and not self.leds and not self.wires:
            return (0, 0, 0, 0)

        min_x = float("inf")
        min_y = float("inf")
        max_x = float("-inf")
        max_y = float("-inf")

        for battery in self.batteries:
            # Battery dimensions: 80x40 centered on position
            min_x = min(min_x, battery.position.x - 40)
            max_x = max(max_x, battery.position.x + 40)
            min_y = min(min_y, battery.position.y - 20)
            max_y = max(max_y, battery.position.y + 20)

        for led in self.leds:
            # LED dimensions: 30x60 centered on position
            min_x = min(min_x, led.position.x - 15)
            max_x = max(max_x, led.position.x + 15)
            min_y = min(min_y, led.position.y - 30)
            max_y = max(max_y, led.position.y + 30)

        for wire in self.wires:
            for point in wire.path:
                min_x = min(min_x, point.x)
                max_x = max(max_x, point.x)
                min_y = min(min_y, point.y)
                max_y = max(max_y, point.y)
            # Also check start/end positions
            min_x = min(min_x, wire.start.position.x, wire.end.position.x)
            max_x = max(max_x, wire.start.position.x, wire.end.position.x)
            min_y = min(min_y, wire.start.position.y, wire.end.position.y)
            max_y = max(max_y, wire.start.position.y, wire.end.position.y)

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

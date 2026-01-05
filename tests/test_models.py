"""Unit tests for circuit component models."""

from uuid import UUID

import pytest

from entropy_sim.models import (
    LED,
    Battery,
    Circuit,
    LiIonCell,
    Point,
    Wire,
)
from entropy_sim.object_type import ObjectType


class TestPoint:
    """Tests for the Point model."""

    def test_default_values(self) -> None:
        """Test Point creates with default coordinates."""
        point = Point()
        assert point.x == 0.0
        assert point.y == 0.0

    def test_custom_values(self) -> None:
        """Test Point creates with custom coordinates."""
        point = Point(x=10.5, y=20.3)
        assert point.x == 10.5
        assert point.y == 20.3

    def test_negative_values(self) -> None:
        """Test Point handles negative coordinates."""
        point = Point(x=-5.0, y=-10.0)
        assert point.x == -5.0
        assert point.y == -10.0


class TestBattery:
    """Tests for the Battery model."""

    def test_default_values(self) -> None:
        """Test Battery creates with default values."""
        battery = Battery()
        assert battery.voltage == 9.0
        assert battery.is_rotatable is True
        assert battery.has_connections is True
        assert battery.object_type == ObjectType.BATTERY

    def test_position(self) -> None:
        """Test Battery position setting."""
        battery = Battery(position=Point(x=100, y=200))
        assert battery.position.x == 100
        assert battery.position.y == 200

    def test_connection_points(self) -> None:
        """Test Battery has positive and negative connection points."""
        battery = Battery(position=Point(x=100, y=100))
        conn_points = battery.connection_points
        assert len(conn_points) == 2
        labels = [cp.label for cp in conn_points]
        assert "positive" in labels
        assert "negative" in labels

    def test_connection_points_update_on_position_change(self) -> None:
        """Test connection points update when position changes."""
        battery = Battery(position=Point(x=0, y=0))
        initial_pos_x = battery.positive.position.x
        initial_neg_x = battery.negative.position.x

        battery.position = Point(x=100, y=100)
        battery.update_connection_positions()

        assert battery.positive.position.x == initial_pos_x + 100
        assert battery.negative.position.x == initial_neg_x + 100

    def test_rotation(self) -> None:
        """Test Battery rotation updates connection points."""
        battery = Battery(position=Point(x=0, y=0), rotation=0)
        pos_before = (battery.positive.position.x, battery.positive.position.y)

        battery.rotation = 90
        battery.update_connection_positions()
        pos_after = (battery.positive.position.x, battery.positive.position.y)

        # Position should change after rotation
        assert pos_before != pos_after

    def test_contains_point_inside(self) -> None:
        """Test contains_point returns True for point inside bounds."""
        battery = Battery(position=Point(x=100, y=100))
        assert battery.contains_point(Point(x=100, y=100)) is True
        assert battery.contains_point(Point(x=90, y=90)) is True

    def test_contains_point_outside(self) -> None:
        """Test contains_point returns False for point outside bounds."""
        battery = Battery(position=Point(x=100, y=100))
        assert battery.contains_point(Point(x=0, y=0)) is False
        assert battery.contains_point(Point(x=200, y=200)) is False

    def test_get_bounds(self) -> None:
        """Test get_bounds returns correct bounding box."""
        battery = Battery(position=Point(x=100, y=100))
        min_x, min_y, max_x, max_y = battery.get_bounds()

        assert min_x == 100 - battery.size_x
        assert max_x == 100 + battery.size_x
        assert min_y == 100 - battery.size_y
        assert max_y == 100 + battery.size_y

    def test_display_name(self) -> None:
        """Test display_name returns correct value."""
        battery = Battery()
        assert battery.display_name == "Battery"

    def test_unique_id(self) -> None:
        """Test each Battery gets a unique ID."""
        battery1 = Battery()
        battery2 = Battery()
        assert battery1.id != battery2.id
        assert isinstance(battery1.id, UUID)


class TestLiIonCell:
    """Tests for the LiIonCell model."""

    def test_default_values(self) -> None:
        """Test LiIonCell creates with default values."""
        cell = LiIonCell()
        assert cell.voltage == 3.7
        assert cell.is_rotatable is True
        assert cell.has_connections is True
        assert cell.object_type == ObjectType.LIION_CELL

    def test_connection_points(self) -> None:
        """Test LiIonCell has positive and negative connection points."""
        cell = LiIonCell(position=Point(x=100, y=100))
        conn_points = cell.connection_points
        assert len(conn_points) == 2
        labels = [cp.label for cp in conn_points]
        assert "positive" in labels
        assert "negative" in labels

    def test_horizontal_terminal_positions(self) -> None:
        """Test terminals are positioned horizontally (left/right)."""
        cell = LiIonCell(position=Point(x=0, y=0), rotation=0)
        # Positive at right, negative at left
        assert cell.positive.position.x > 0
        assert cell.negative.position.x < 0
        # Both should be at y=0 (horizontal orientation)
        assert abs(cell.positive.position.y) < 1
        assert abs(cell.negative.position.y) < 1


class TestLED:
    """Tests for the LED model."""

    def test_default_values(self) -> None:
        """Test LED creates with default values."""
        led = LED()
        assert led.color == "red"
        assert led.is_on is False
        assert led.is_rotatable is True
        assert led.has_connections is True
        assert led.object_type == ObjectType.LED

    def test_custom_color(self) -> None:
        """Test LED with custom color."""
        led = LED(color="green")
        assert led.color == "green"

    def test_connection_points(self) -> None:
        """Test LED has anode and cathode connection points."""
        led = LED(position=Point(x=100, y=100))
        conn_points = led.connection_points
        assert len(conn_points) == 2
        # LED uses "positive" (anode) and "negative" (cathode) labels
        labels = [cp.label for cp in conn_points]
        assert "positive" in labels
        assert "negative" in labels

    def test_vertical_lead_positions(self) -> None:
        """Test LED leads are positioned at bottom (vertical orientation)."""
        led = LED(position=Point(x=0, y=0), rotation=0)
        # Both leads should be below center (positive y)
        assert led.anode.position.y > 0
        assert led.cathode.position.y > 0

    def test_is_on_state(self) -> None:
        """Test LED on/off state."""
        led = LED(is_on=False)
        assert led.is_on is False

        led.is_on = True
        assert led.is_on is True


class TestWire:
    """Tests for the Wire model."""

    def test_default_values(self) -> None:
        """Test Wire creates with default values."""
        wire = Wire()
        assert wire.object_type == ObjectType.WIRE
        assert wire.is_connector is True
        assert wire.start_connected_to is None
        assert wire.end_connected_to is None
        assert wire.path == []

    def test_has_start_and_end(self) -> None:
        """Test Wire has start and end connection points."""
        wire = Wire()
        assert wire.start is not None
        assert wire.end is not None
        assert wire.start.label == "start"
        assert wire.end.label == "end"

    def test_path_manipulation(self) -> None:
        """Test Wire path can be modified."""
        from entropy_sim.models.base_connector import ConnectorPoint

        wire = Wire()
        wire.path = [
            ConnectorPoint(x=0, y=0),
            ConnectorPoint(x=100, y=0),
            ConnectorPoint(x=100, y=100),
        ]
        assert len(wire.path) == 3
        assert wire.path[0].x == 0
        assert wire.path[1].x == 100
        assert wire.path[2].y == 100

    def test_get_bounds(self) -> None:
        """Test Wire get_bounds includes all path points."""
        from entropy_sim.models.base_connector import ConnectorPoint

        wire = Wire()
        wire.start.position = Point(x=0, y=0)
        wire.end.position = Point(x=100, y=100)
        wire.path = [
            ConnectorPoint(x=0, y=0),
            ConnectorPoint(x=50, y=50),
            ConnectorPoint(x=100, y=100),
        ]

        min_x, min_y, max_x, max_y = wire.get_bounds()
        assert min_x == 0
        assert min_y == 0
        assert max_x == 100
        assert max_y == 100


class TestCircuit:
    """Tests for the Circuit model."""

    def test_default_values(self) -> None:
        """Test Circuit creates with default values."""
        circuit = Circuit()
        assert circuit.name == "Untitled Circuit"
        assert circuit.components == []
        assert circuit.wires == []
        assert isinstance(circuit.id, UUID)

    def test_add_battery(self) -> None:
        """Test adding a battery to circuit."""
        circuit = Circuit()
        battery = circuit.add_object(ObjectType.BATTERY, Point(x=100, y=100))

        assert len(circuit.components) == 1
        assert isinstance(battery, Battery)
        assert battery.position.x == 100
        assert battery.position.y == 100

    def test_add_led(self) -> None:
        """Test adding an LED to circuit."""
        circuit = Circuit()
        led = circuit.add_object(ObjectType.LED, Point(x=200, y=200), color="blue")

        assert len(circuit.components) == 1
        assert isinstance(led, LED)
        assert led.color == "blue"

    def test_add_liion_cell(self) -> None:
        """Test adding a Li-Ion cell to circuit."""
        circuit = Circuit()
        cell = circuit.add_object(ObjectType.LIION_CELL, Point(x=150, y=150))

        assert len(circuit.components) == 1
        assert isinstance(cell, LiIonCell)

    def test_add_wire(self) -> None:
        """Test adding a wire to circuit."""
        circuit = Circuit()
        wire = circuit.add_wire()

        assert len(circuit.wires) == 1
        assert isinstance(wire, Wire)

    def test_add_invalid_object_type(self) -> None:
        """Test adding invalid object type raises error."""
        circuit = Circuit()
        with pytest.raises(ValueError, match="Cannot add object"):
            circuit.add_object(ObjectType.WIRE, Point(x=0, y=0))

    def test_all_objects(self) -> None:
        """Test all_objects returns components and wires."""
        circuit = Circuit()
        circuit.add_object(ObjectType.BATTERY, Point(x=100, y=100))
        circuit.add_object(ObjectType.LED, Point(x=200, y=200))
        circuit.add_wire()

        all_objs = circuit.all_objects
        assert len(all_objs) == 3

    def test_get_bounds_empty(self) -> None:
        """Test get_bounds on empty circuit."""
        circuit = Circuit()
        bounds = circuit.get_bounds()
        assert bounds == (0, 0, 0, 0)

    def test_get_bounds_with_components(self) -> None:
        """Test get_bounds with components."""
        circuit = Circuit()
        circuit.add_object(ObjectType.BATTERY, Point(x=100, y=100))
        circuit.add_object(ObjectType.LED, Point(x=300, y=300))

        min_x, min_y, max_x, max_y = circuit.get_bounds()
        assert min_x < 100
        assert min_y < 100
        assert max_x > 300
        assert max_y > 300

    def test_get_all_connection_points(self) -> None:
        """Test getting all connection points."""
        circuit = Circuit()
        circuit.add_object(ObjectType.BATTERY, Point(x=100, y=100))
        circuit.add_object(ObjectType.LED, Point(x=200, y=200))

        conn_points = circuit.get_all_connection_points()
        # Battery has 2, LED has 2
        assert len(conn_points) == 4

    def test_find_nearest_connection_point(self) -> None:
        """Test finding nearest connection point."""
        circuit = Circuit()
        battery = circuit.add_object(ObjectType.BATTERY, Point(x=100, y=100))

        # Search near the positive terminal
        pos_terminal = battery.positive.position  # type: ignore[union-attr]
        result = circuit.find_nearest_connection_point(
            Point(x=pos_terminal.x + 5, y=pos_terminal.y + 5), max_distance=20.0
        )

        assert result is not None
        _, conn_point, _ = result
        assert conn_point.label == "positive"

    def test_find_nearest_connection_point_none(self) -> None:
        """Test finding nearest connection point when none nearby."""
        circuit = Circuit()
        circuit.add_object(ObjectType.BATTERY, Point(x=100, y=100))

        result = circuit.find_nearest_connection_point(
            Point(x=500, y=500), max_distance=20.0
        )
        assert result is None

    def test_remove_component(self) -> None:
        """Test removing a component."""
        circuit = Circuit()
        battery = circuit.add_object(ObjectType.BATTERY, Point(x=100, y=100))

        assert len(circuit.components) == 1
        result = circuit.remove_component(battery.id)
        assert result is True
        assert len(circuit.components) == 0

    def test_remove_wire(self) -> None:
        """Test removing a wire."""
        circuit = Circuit()
        wire = circuit.add_wire()

        assert len(circuit.wires) == 1
        result = circuit.remove_component(wire.id)
        assert result is True
        assert len(circuit.wires) == 0

    def test_remove_nonexistent_component(self) -> None:
        """Test removing non-existent component returns False."""
        from uuid import uuid4

        circuit = Circuit()
        result = circuit.remove_component(uuid4())
        assert result is False

    def test_json_serialization(self) -> None:
        """Test circuit can be serialized to JSON and back."""
        circuit = Circuit()
        circuit.add_object(ObjectType.BATTERY, Point(x=100, y=100))
        circuit.add_object(ObjectType.LED, Point(x=200, y=200), color="green")
        circuit.add_wire()

        json_data = circuit.model_dump_json()
        loaded = Circuit.model_validate_json(json_data)

        assert loaded.name == circuit.name
        assert len(loaded.components) == 2
        assert len(loaded.wires) == 1


class TestConnectionPointRotation:
    """Tests for connection point rotation calculations."""

    def test_battery_90_degree_rotation(self) -> None:
        """Test battery terminals rotate correctly at 90 degrees."""
        battery = Battery(position=Point(x=0, y=0), rotation=0)
        pos_0 = (battery.positive.position.x, battery.positive.position.y)

        battery.rotation = 90
        battery.update_connection_positions()
        pos_90 = (battery.positive.position.x, battery.positive.position.y)

        # After 90 degree rotation, x and y should swap (approximately)
        assert abs(pos_90[0] - pos_0[1]) < 1 or abs(pos_90[0] + pos_0[1]) < 1

    def test_led_180_degree_rotation(self) -> None:
        """Test LED leads rotate correctly at 180 degrees."""
        led = LED(position=Point(x=0, y=0), rotation=0)
        anode_0 = led.anode.position.y

        led.rotation = 180
        led.update_connection_positions()
        anode_180 = led.anode.position.y

        # After 180 degree rotation, y should be negated
        assert abs(anode_180 + anode_0) < 1

    def test_full_rotation_returns_to_start(self) -> None:
        """Test 360 degree rotation returns to original position."""
        battery = Battery(position=Point(x=100, y=100), rotation=0)
        pos_orig = (battery.positive.position.x, battery.positive.position.y)

        battery.rotation = 360
        battery.update_connection_positions()
        pos_360 = (battery.positive.position.x, battery.positive.position.y)

        assert abs(pos_360[0] - pos_orig[0]) < 0.01
        assert abs(pos_360[1] - pos_orig[1]) < 0.01

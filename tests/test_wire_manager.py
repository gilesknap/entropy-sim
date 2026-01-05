"""Unit tests for WireManager."""

from uuid import uuid4

from entropy_sim.models import Circuit, Point, Wire
from entropy_sim.models.base_connector import ConnectorPoint
from entropy_sim.object_type import ObjectType
from entropy_sim.wire_manager import WireManager


class TestWireManagerInit:
    """Tests for WireManager initialization."""

    def test_initial_state(self) -> None:
        """Test WireManager initializes with correct default state."""
        circuit = Circuit()

        def on_change() -> None:
            pass

        wm = WireManager(circuit, on_change)

        assert wm.circuit is circuit
        assert wm.dragging_wire is None
        assert wm.dragging_wire_corner is None

    def test_constants(self) -> None:
        """Test WireManager constants are set."""
        assert WireManager.SNAP_DISTANCE == 20.0
        assert WireManager.WIRE_CORNER_HIT_RADIUS == 12.0


class TestWireManagerProperties:
    """Tests for WireManager properties."""

    def test_circuit_property(self) -> None:
        """Test circuit property getter and setter."""
        circuit1 = Circuit()
        circuit2 = Circuit()
        wm = WireManager(circuit1, lambda: None)

        assert wm.circuit is circuit1

        wm.circuit = circuit2
        assert wm.circuit is circuit2

    def test_is_drawing_property(self) -> None:
        """Test is_drawing property."""
        circuit = Circuit()
        wm = WireManager(circuit, lambda: None)

        assert wm.is_drawing is False

        wm.start_wire(Point(x=100, y=100))
        assert wm.is_drawing is True

    def test_is_dragging_corner_property(self) -> None:
        """Test is_dragging_corner property."""
        circuit = Circuit()
        wm = WireManager(circuit, lambda: None)

        assert wm.is_dragging_corner is False

        wm.dragging_wire_corner = (uuid4(), 1)
        assert wm.is_dragging_corner is True


class TestWireDrawing:
    """Tests for wire drawing operations."""

    def test_start_wire_creates_wire(self) -> None:
        """Test starting a wire creates a new wire in circuit."""
        circuit = Circuit()
        wm = WireManager(circuit, lambda: None)

        wm.start_wire(Point(x=100, y=100))

        assert len(circuit.wires) == 1
        assert wm.dragging_wire is circuit.wires[0]

    def test_start_wire_sets_start_position(self) -> None:
        """Test starting a wire sets correct start position."""
        circuit = Circuit()
        wm = WireManager(circuit, lambda: None)

        wm.start_wire(Point(x=100, y=100))

        assert wm.dragging_wire is not None
        assert wm.dragging_wire.path[0].x == 100
        assert wm.dragging_wire.path[0].y == 100

    def test_start_wire_snaps_to_connection_point(self) -> None:
        """Test wire start snaps to nearby connection point."""
        circuit = Circuit()
        battery = circuit.add_object(ObjectType.BATTERY, Point(x=100, y=100))
        pos_terminal = battery.positive.position  # type: ignore[union-attr]

        wm = WireManager(circuit, lambda: None)
        # Start wire near the positive terminal
        wm.start_wire(Point(x=pos_terminal.x + 5, y=pos_terminal.y + 5))

        assert wm.dragging_wire is not None
        assert wm.dragging_wire.start_connected_to is not None

    def test_add_corner_to_wire(self) -> None:
        """Test adding a corner point to wire."""
        circuit = Circuit()
        wm = WireManager(circuit, lambda: None)
        wm.start_wire(Point(x=100, y=100))

        # Click again to add a corner
        wm.start_wire(Point(x=200, y=100))

        assert wm.dragging_wire is not None
        assert len(wm.dragging_wire.path) == 2

    def test_wire_corners_are_orthogonal(self) -> None:
        """Test wire corners maintain orthogonal alignment."""
        circuit = Circuit()
        wm = WireManager(circuit, lambda: None)
        wm.start_wire(Point(x=100, y=100))

        # Try to add diagonal point - should snap to orthogonal
        wm.start_wire(Point(x=200, y=150))

        assert wm.dragging_wire is not None
        path = wm.dragging_wire.path
        assert len(path) == 2
        # Should snap to either horizontal or vertical
        assert path[0].x == path[1].x or path[0].y == path[1].y

    def test_finish_wire_at_connection(self) -> None:
        """Test finishing wire at a connection point."""
        circuit = Circuit()
        battery = circuit.add_object(ObjectType.BATTERY, Point(x=100, y=100))
        led = circuit.add_object(ObjectType.LED, Point(x=300, y=100))

        wm = WireManager(circuit, lambda: None)

        # Start at battery terminal
        pos_terminal = battery.positive.position  # type: ignore[union-attr]
        wm.start_wire(Point(x=pos_terminal.x, y=pos_terminal.y))

        # Finish at LED terminal
        anode = led.anode.position  # type: ignore[union-attr]
        result = wm.start_wire(Point(x=anode.x, y=anode.y))

        assert result is True  # Wire completed
        assert wm.dragging_wire is None
        assert len(circuit.wires) == 1
        assert circuit.wires[0].end_connected_to is not None

    def test_update_wire_preview(self) -> None:
        """Test updating wire preview position."""
        circuit = Circuit()
        wm = WireManager(circuit, lambda: None)
        wm.start_wire(Point(x=100, y=100))

        wm.update_wire_preview(Point(x=200, y=100))

        assert wm.dragging_wire is not None
        # End should be updated (snapped to orthogonal)
        end = wm.dragging_wire.end.position
        assert end.x == 200 or end.y == 100

    def test_update_wire_preview_snaps_to_connection(self) -> None:
        """Test wire preview snaps to nearby connection point."""
        circuit = Circuit()
        battery = circuit.add_object(ObjectType.BATTERY, Point(x=300, y=100))

        wm = WireManager(circuit, lambda: None)
        wm.start_wire(Point(x=100, y=100))

        # Move near battery terminal
        pos_terminal = battery.positive.position  # type: ignore[union-attr]
        wm.update_wire_preview(Point(x=pos_terminal.x + 5, y=pos_terminal.y + 5))

        assert wm.dragging_wire is not None
        # Should snap to terminal position
        end = wm.dragging_wire.end.position
        assert abs(end.x - pos_terminal.x) < 1
        assert abs(end.y - pos_terminal.y) < 1

    def test_cancel_wire(self) -> None:
        """Test canceling wire removes it from circuit."""
        circuit = Circuit()
        wm = WireManager(circuit, lambda: None)
        wm.start_wire(Point(x=100, y=100))

        assert len(circuit.wires) == 1

        wm.cancel_wire()

        assert len(circuit.wires) == 0
        assert wm.dragging_wire is None


class TestWireCornerDragging:
    """Tests for wire corner dragging operations."""

    def test_check_corner_hit_returns_false_for_empty_circuit(self) -> None:
        """Test corner hit returns False when no wires exist."""
        circuit = Circuit()
        wm = WireManager(circuit, lambda: None)

        result = wm.check_corner_hit(Point(x=100, y=100))

        assert result is False

    def test_check_corner_hit_returns_false_for_endpoints(self) -> None:
        """Test corner hit returns False for wire endpoints."""
        circuit = Circuit()
        wire = circuit.add_wire()
        wire.path = [
            ConnectorPoint(x=0, y=0),
            ConnectorPoint(x=50, y=0),
            ConnectorPoint(x=50, y=50),
            ConnectorPoint(x=100, y=50),
        ]

        wm = WireManager(circuit, lambda: None)

        # First and last points should not be draggable
        assert wm.check_corner_hit(Point(x=0, y=0)) is False
        assert wm.check_corner_hit(Point(x=100, y=50)) is False

    def test_check_corner_hit_returns_true_for_middle_points(self) -> None:
        """Test corner hit returns True for middle points."""
        circuit = Circuit()
        wire = circuit.add_wire()
        wire.path = [
            ConnectorPoint(x=0, y=0),
            ConnectorPoint(x=50, y=0),
            ConnectorPoint(x=50, y=50),
            ConnectorPoint(x=100, y=50),
        ]

        wm = WireManager(circuit, lambda: None)

        # Middle points should be draggable
        result = wm.check_corner_hit(Point(x=50, y=0))
        assert result is True
        assert wm.dragging_wire_corner is not None
        assert wm.dragging_wire_corner[0] == wire.id
        assert wm.dragging_wire_corner[1] == 1

    def test_update_corner_position(self) -> None:
        """Test updating corner position."""
        circuit = Circuit()
        wire = circuit.add_wire()
        wire.path = [
            ConnectorPoint(x=0, y=0),
            ConnectorPoint(x=50, y=0),
            ConnectorPoint(x=50, y=50),
            ConnectorPoint(x=100, y=50),
        ]

        wm = WireManager(circuit, lambda: None)
        wm.check_corner_hit(Point(x=50, y=0))

        wm.update_corner_position(Point(x=75, y=0))

        # Corner should have moved (maintaining orthogonality)
        assert wire.path[1].x != 50 or wire.path[1].y != 0

    def test_finish_corner_drag(self) -> None:
        """Test finishing corner drag."""
        circuit = Circuit()
        wire = circuit.add_wire()
        wire.path = [
            ConnectorPoint(x=0, y=0),
            ConnectorPoint(x=50, y=0),
            ConnectorPoint(x=50, y=50),
        ]

        wm = WireManager(circuit, lambda: None)
        wm.check_corner_hit(Point(x=50, y=0))

        assert wm.dragging_wire_corner is not None

        wm.finish_corner_drag()

        assert wm.dragging_wire_corner is None


class TestOrthogonalSnapping:
    """Tests for orthogonal snapping behavior."""

    def test_snap_to_horizontal(self) -> None:
        """Test snapping to horizontal when dx > dy."""
        circuit = Circuit()
        wm = WireManager(circuit, lambda: None)

        result = wm._snap_to_orthogonal(Point(x=100, y=10), Point(x=0, y=0))

        assert result.y == 0  # Snapped to horizontal
        assert result.x == 100

    def test_snap_to_vertical(self) -> None:
        """Test snapping to vertical when dy > dx."""
        circuit = Circuit()
        wm = WireManager(circuit, lambda: None)

        result = wm._snap_to_orthogonal(Point(x=10, y=100), Point(x=0, y=0))

        assert result.x == 0  # Snapped to vertical
        assert result.y == 100


class TestSegmentHelpers:
    """Tests for segment helper methods."""

    def test_get_first_segment_horizontal(self) -> None:
        """Test determining first segment orientation."""
        circuit = Circuit()
        wm = WireManager(circuit, lambda: None)

        wire = Wire()
        wire.path = [
            ConnectorPoint(x=0, y=0),
            ConnectorPoint(x=100, y=0),  # Horizontal first segment
        ]

        assert wm._get_first_segment_horizontal(wire) is True

        wire.path = [
            ConnectorPoint(x=0, y=0),
            ConnectorPoint(x=0, y=100),  # Vertical first segment
        ]

        assert wm._get_first_segment_horizontal(wire) is False

    def test_is_segment_horizontal(self) -> None:
        """Test checking if segment at index is horizontal."""
        circuit = Circuit()
        wm = WireManager(circuit, lambda: None)

        wire = Wire()
        wire.path = [
            ConnectorPoint(x=0, y=0),
            ConnectorPoint(x=100, y=0),  # Horizontal
            ConnectorPoint(x=100, y=100),  # Vertical
            ConnectorPoint(x=200, y=100),  # Horizontal
        ]

        assert wm._is_segment_horizontal(wire, 0) is True
        assert wm._is_segment_horizontal(wire, 1) is False
        assert wm._is_segment_horizontal(wire, 2) is True


class TestConnectedWireUpdates:
    """Tests for updating connected wires when components move."""

    def test_update_connected_wires_start(self) -> None:
        """Test updating wire when start connection moves."""
        circuit = Circuit()
        battery = circuit.add_object(ObjectType.BATTERY, Point(x=100, y=100))
        wire = circuit.add_wire()
        wire.start_connected_to = battery.positive.id  # type: ignore[union-attr]
        wire.start.position = Point(
            x=battery.positive.position.x,  # type: ignore[union-attr]
            y=battery.positive.position.y,  # type: ignore[union-attr]
        )
        wire.path = [
            ConnectorPoint(
                x=battery.positive.position.x,
                y=battery.positive.position.y,  # type: ignore[union-attr]
            ),
            ConnectorPoint(x=200, y=battery.positive.position.y),  # type: ignore[union-attr]
        ]

        wm = WireManager(circuit, lambda: None)

        # Move battery
        battery.position = Point(x=150, y=150)
        battery.update_connection_positions()
        wm.update_connected_wires(battery)

        # Wire start should have moved with the terminal
        new_pos = battery.positive.position  # type: ignore[union-attr]
        assert wire.start.position.x == new_pos.x
        assert wire.start.position.y == new_pos.y

    def test_update_connected_wires_end(self) -> None:
        """Test updating wire when end connection moves."""
        circuit = Circuit()
        led = circuit.add_object(ObjectType.LED, Point(x=200, y=200))
        wire = circuit.add_wire()
        wire.end_connected_to = led.anode.id  # type: ignore[union-attr]
        wire.end.position = Point(
            x=led.anode.position.x,
            y=led.anode.position.y,  # type: ignore[union-attr]
        )
        wire.path = [
            ConnectorPoint(x=100, y=led.anode.position.y),  # type: ignore[union-attr]
            ConnectorPoint(x=led.anode.position.x, y=led.anode.position.y),  # type: ignore[union-attr]
        ]

        wm = WireManager(circuit, lambda: None)

        # Move LED
        led.position = Point(x=250, y=250)
        led.update_connection_positions()
        wm.update_connected_wires(led)

        # Wire end should have moved with the terminal
        new_pos = led.anode.position  # type: ignore[union-attr]
        assert wire.end.position.x == new_pos.x
        assert wire.end.position.y == new_pos.y


class TestChangeNotification:
    """Tests for change notification during wire operations."""

    def test_start_wire_notifies_change(self) -> None:
        """Test starting wire triggers change notification."""
        circuit = Circuit()
        notified = []
        wm = WireManager(circuit, lambda: notified.append(True))

        wm.start_wire(Point(x=100, y=100))

        assert len(notified) == 1

    def test_update_preview_notifies_change(self) -> None:
        """Test updating preview triggers change notification."""
        circuit = Circuit()
        notified = []
        wm = WireManager(circuit, lambda: notified.append(True))
        wm.start_wire(Point(x=100, y=100))
        notified.clear()

        wm.update_wire_preview(Point(x=200, y=100))

        assert len(notified) == 1

    def test_cancel_wire_notifies_change(self) -> None:
        """Test canceling wire triggers change notification."""
        circuit = Circuit()
        notified = []
        wm = WireManager(circuit, lambda: notified.append(True))
        wm.start_wire(Point(x=100, y=100))
        notified.clear()

        wm.cancel_wire()

        assert len(notified) == 1

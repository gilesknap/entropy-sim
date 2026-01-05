"""Unit tests for CircuitViewModel."""

from unittest.mock import MagicMock, patch

from entropy_sim.models import Circuit, Point
from entropy_sim.object_type import ObjectType
from entropy_sim.viewmodel import CircuitViewModel


class TestCircuitViewModelInit:
    """Tests for CircuitViewModel initialization."""

    def test_initial_state(self) -> None:
        """Test ViewModel initializes with correct default state."""
        vm = CircuitViewModel()

        assert isinstance(vm.circuit, Circuit)
        assert vm.selected_palette_item is None
        assert vm.dragging_component is None
        assert vm.drag_offset.x == 0
        assert vm.drag_offset.y == 0
        assert vm.undo_stack == []
        assert vm.redo_stack == []
        assert vm.max_history == 50

    def test_wire_manager_created(self) -> None:
        """Test WireManager is created and linked to circuit."""
        vm = CircuitViewModel()
        assert vm._wire_manager is not None
        assert vm._wire_manager.circuit is vm.circuit


class TestChangeNotification:
    """Tests for change notification system."""

    def test_add_change_listener(self) -> None:
        """Test adding a change listener."""
        vm = CircuitViewModel()
        callback = MagicMock()

        vm.add_change_listener(callback)

        assert callback in vm._on_change_callbacks

    def test_change_listener_called_on_component_place(self) -> None:
        """Test change listener is called when component is placed."""
        vm = CircuitViewModel()
        callback = MagicMock()
        vm.add_change_listener(callback)

        vm.selected_palette_item = ObjectType.BATTERY
        with patch("entropy_sim.viewmodel.ui"):
            vm.place_component(Point(x=100, y=100))

        callback.assert_called()

    def test_multiple_listeners(self) -> None:
        """Test multiple change listeners are all called."""
        vm = CircuitViewModel()
        callback1 = MagicMock()
        callback2 = MagicMock()
        vm.add_change_listener(callback1)
        vm.add_change_listener(callback2)

        vm._notify_change()

        callback1.assert_called_once()
        callback2.assert_called_once()


class TestPaletteSelection:
    """Tests for palette item selection."""

    def test_select_palette_item(self) -> None:
        """Test selecting a palette item."""
        vm = CircuitViewModel()

        with patch("entropy_sim.viewmodel.ui"):
            vm.select_palette_item(ObjectType.LED)

        assert vm.selected_palette_item == ObjectType.LED

    def test_clear_selection(self) -> None:
        """Test clearing palette selection."""
        vm = CircuitViewModel()
        vm.selected_palette_item = ObjectType.BATTERY

        vm.clear_selection()

        assert vm.selected_palette_item is None


class TestComponentPlacement:
    """Tests for component placement."""

    def test_place_battery(self) -> None:
        """Test placing a battery."""
        vm = CircuitViewModel()
        vm.selected_palette_item = ObjectType.BATTERY

        with patch("entropy_sim.viewmodel.ui"):
            vm.place_component(Point(x=100, y=100))

        assert len(vm.circuit.components) == 1
        assert vm.circuit.components[0].position.x == 100
        assert vm.circuit.components[0].position.y == 100
        assert vm.selected_palette_item is None

    def test_place_led(self) -> None:
        """Test placing an LED."""
        vm = CircuitViewModel()
        vm.selected_palette_item = ObjectType.LED

        with patch("entropy_sim.viewmodel.ui"):
            vm.place_component(Point(x=200, y=200))

        assert len(vm.circuit.components) == 1
        assert vm.selected_palette_item is None

    def test_place_without_selection_does_nothing(self) -> None:
        """Test placing without selection does nothing."""
        vm = CircuitViewModel()
        vm.selected_palette_item = None

        vm.place_component(Point(x=100, y=100))

        assert len(vm.circuit.components) == 0

    def test_place_saves_state_for_undo(self) -> None:
        """Test placing a component saves state for undo."""
        vm = CircuitViewModel()
        vm.selected_palette_item = ObjectType.BATTERY

        with patch("entropy_sim.viewmodel.ui"):
            vm.place_component(Point(x=100, y=100))

        assert len(vm.undo_stack) == 1


class TestComponentDragging:
    """Tests for component dragging."""

    def test_check_component_drag_starts_drag(self) -> None:
        """Test drag starts when clicking on component."""
        vm = CircuitViewModel()
        vm.selected_palette_item = ObjectType.BATTERY
        with patch("entropy_sim.viewmodel.ui"):
            vm.place_component(Point(x=100, y=100))

        # Clear undo stack from placement
        vm.undo_stack.clear()

        result = vm.check_component_drag(Point(x=100, y=100))

        assert result is True
        assert vm.dragging_component is not None
        assert len(vm.undo_stack) == 1  # State saved for undo

    def test_check_component_drag_no_component(self) -> None:
        """Test drag returns False when no component at position."""
        vm = CircuitViewModel()

        result = vm.check_component_drag(Point(x=100, y=100))

        assert result is False
        assert vm.dragging_component is None

    def test_update_component_position(self) -> None:
        """Test updating component position during drag."""
        vm = CircuitViewModel()
        vm.selected_palette_item = ObjectType.BATTERY
        with patch("entropy_sim.viewmodel.ui"):
            vm.place_component(Point(x=100, y=100))

        vm.check_component_drag(Point(x=100, y=100))
        vm.update_component_position(Point(x=150, y=150))

        # Component should have moved (accounting for drag offset)
        component = vm.circuit.components[0]
        assert component.position.x != 100 or component.position.y != 100

    def test_finish_drag(self) -> None:
        """Test finishing a drag."""
        vm = CircuitViewModel()
        vm.selected_palette_item = ObjectType.BATTERY
        with patch("entropy_sim.viewmodel.ui"):
            vm.place_component(Point(x=100, y=100))

        vm.check_component_drag(Point(x=100, y=100))
        assert vm.dragging_component is not None

        vm.finish_drag()
        assert vm.dragging_component is None

    def test_clear_drag_state(self) -> None:
        """Test clearing all drag state."""
        vm = CircuitViewModel()
        vm.dragging_component = vm.circuit.id  # Just use any UUID

        vm.clear_drag_state()

        assert vm.dragging_component is None


class TestObjectDetection:
    """Tests for object detection at position."""

    def test_get_object_at_component(self) -> None:
        """Test detecting component at position."""
        vm = CircuitViewModel()
        vm.selected_palette_item = ObjectType.BATTERY
        with patch("entropy_sim.viewmodel.ui"):
            vm.place_component(Point(x=100, y=100))

        result = vm.get_object_at(Point(x=100, y=100))

        assert result is not None
        obj_type, obj_id, obj = result
        assert obj_type == "Battery"

    def test_get_object_at_empty(self) -> None:
        """Test detecting nothing at empty position."""
        vm = CircuitViewModel()

        result = vm.get_object_at(Point(x=100, y=100))

        assert result is None

    def test_get_object_at_wire(self) -> None:
        """Test detecting wire at position."""
        vm = CircuitViewModel()
        wire = vm.circuit.add_wire()
        from entropy_sim.models.base_connector import ConnectorPoint

        wire.path = [
            ConnectorPoint(x=0, y=0),
            ConnectorPoint(x=100, y=0),
        ]
        wire.start.position = Point(x=0, y=0)
        wire.end.position = Point(x=100, y=0)

        result = vm.get_object_at(Point(x=50, y=0))

        assert result is not None
        obj_type, _, _ = result
        assert obj_type == "wire"


class TestDeleteOperations:
    """Tests for delete operations."""

    def test_delete_component(self) -> None:
        """Test deleting a component."""
        vm = CircuitViewModel()
        vm.selected_palette_item = ObjectType.BATTERY
        with patch("entropy_sim.viewmodel.ui"):
            vm.place_component(Point(x=100, y=100))

        component_id = vm.circuit.components[0].id
        vm.undo_stack.clear()

        with patch("entropy_sim.viewmodel.ui"):
            vm.delete_object("Battery", component_id)

        assert len(vm.circuit.components) == 0
        assert len(vm.undo_stack) == 1  # State saved for undo

    def test_delete_wire(self) -> None:
        """Test deleting a wire."""
        vm = CircuitViewModel()
        wire = vm.circuit.add_wire()
        wire_id = wire.id

        with patch("entropy_sim.viewmodel.ui"):
            vm.delete_object("wire", wire_id)

        assert len(vm.circuit.wires) == 0

    def test_delete_component_removes_connected_wires(self) -> None:
        """Test deleting component also removes connected wires."""
        vm = CircuitViewModel()
        vm.selected_palette_item = ObjectType.BATTERY
        with patch("entropy_sim.viewmodel.ui"):
            vm.place_component(Point(x=100, y=100))

        battery = vm.circuit.components[0]
        wire = vm.circuit.add_wire()
        wire.start_connected_to = battery.positive.id  # type: ignore[union-attr]

        with patch("entropy_sim.viewmodel.ui"):
            vm.delete_object("Battery", battery.id)

        assert len(vm.circuit.components) == 0
        assert len(vm.circuit.wires) == 0


class TestRotationOperations:
    """Tests for rotation operations."""

    def test_rotate_component(self) -> None:
        """Test rotating a component."""
        vm = CircuitViewModel()
        vm.selected_palette_item = ObjectType.BATTERY
        with patch("entropy_sim.viewmodel.ui"):
            vm.place_component(Point(x=100, y=100))

        component = vm.circuit.components[0]
        initial_rotation = component.rotation
        vm.undo_stack.clear()

        with patch("entropy_sim.viewmodel.ui"):
            vm.rotate_object("Battery", component.id, 90)

        assert component.rotation == (initial_rotation + 90) % 360
        assert len(vm.undo_stack) == 1

    def test_rotate_updates_connection_points(self) -> None:
        """Test rotation updates connection point positions."""
        vm = CircuitViewModel()
        vm.selected_palette_item = ObjectType.BATTERY
        with patch("entropy_sim.viewmodel.ui"):
            vm.place_component(Point(x=100, y=100))

        battery = vm.circuit.components[0]
        pos_before = (battery.positive.position.x, battery.positive.position.y)  # type: ignore[union-attr]

        with patch("entropy_sim.viewmodel.ui"):
            vm.rotate_object("Battery", battery.id, 90)

        pos_after = (battery.positive.position.x, battery.positive.position.y)  # type: ignore[union-attr]
        assert pos_before != pos_after


class TestCircuitOperations:
    """Tests for circuit-level operations."""

    def test_clear_circuit(self) -> None:
        """Test clearing the circuit."""
        vm = CircuitViewModel()
        vm.selected_palette_item = ObjectType.BATTERY
        with patch("entropy_sim.viewmodel.ui"):
            vm.place_component(Point(x=100, y=100))
        vm.circuit.add_wire()

        with patch("entropy_sim.viewmodel.ui"):
            vm.clear_circuit()

        assert len(vm.circuit.components) == 0
        assert len(vm.circuit.wires) == 0

    def test_save_circuit(self) -> None:
        """Test saving circuit returns JSON."""
        vm = CircuitViewModel()
        vm.selected_palette_item = ObjectType.BATTERY
        with patch("entropy_sim.viewmodel.ui"):
            vm.place_component(Point(x=100, y=100))
            json_data = vm.save_circuit()

        assert isinstance(json_data, str)
        assert "Battery" in json_data or "BATTERY" in json_data

    def test_load_circuit(self) -> None:
        """Test loading circuit from JSON."""
        vm = CircuitViewModel()
        vm.selected_palette_item = ObjectType.BATTERY
        with patch("entropy_sim.viewmodel.ui"):
            vm.place_component(Point(x=100, y=100))
            json_data = vm.save_circuit()

        vm2 = CircuitViewModel()
        with patch("entropy_sim.viewmodel.ui"):
            vm2.load_circuit(json_data)

        assert len(vm2.circuit.components) == 1


class TestUndoRedo:
    """Tests for undo/redo functionality."""

    def test_undo_restores_previous_state(self) -> None:
        """Test undo restores previous circuit state."""
        vm = CircuitViewModel()
        vm.selected_palette_item = ObjectType.BATTERY
        with patch("entropy_sim.viewmodel.ui"):
            vm.place_component(Point(x=100, y=100))

        assert len(vm.circuit.components) == 1

        with patch("entropy_sim.viewmodel.ui"):
            result = vm.undo()

        assert result is True
        assert len(vm.circuit.components) == 0

    def test_undo_empty_stack(self) -> None:
        """Test undo with empty stack returns False."""
        vm = CircuitViewModel()

        with patch("entropy_sim.viewmodel.ui"):
            result = vm.undo()

        assert result is False

    def test_redo_restores_undone_state(self) -> None:
        """Test redo restores undone state."""
        vm = CircuitViewModel()
        vm.selected_palette_item = ObjectType.BATTERY
        with patch("entropy_sim.viewmodel.ui"):
            vm.place_component(Point(x=100, y=100))
            vm.undo()

        assert len(vm.circuit.components) == 0

        with patch("entropy_sim.viewmodel.ui"):
            result = vm.redo()

        assert result is True
        assert len(vm.circuit.components) == 1

    def test_redo_empty_stack(self) -> None:
        """Test redo with empty stack returns False."""
        vm = CircuitViewModel()

        with patch("entropy_sim.viewmodel.ui"):
            result = vm.redo()

        assert result is False

    def test_can_undo_property(self) -> None:
        """Test can_undo property."""
        vm = CircuitViewModel()
        assert vm.can_undo is False

        vm.selected_palette_item = ObjectType.BATTERY
        with patch("entropy_sim.viewmodel.ui"):
            vm.place_component(Point(x=100, y=100))

        assert vm.can_undo is True

    def test_can_redo_property(self) -> None:
        """Test can_redo property."""
        vm = CircuitViewModel()
        assert vm.can_redo is False

        vm.selected_palette_item = ObjectType.BATTERY
        with patch("entropy_sim.viewmodel.ui"):
            vm.place_component(Point(x=100, y=100))
            vm.undo()

        assert vm.can_redo is True

    def test_undo_clears_redo_stack(self) -> None:
        """Test new action clears redo stack."""
        vm = CircuitViewModel()
        vm.selected_palette_item = ObjectType.BATTERY
        with patch("entropy_sim.viewmodel.ui"):
            vm.place_component(Point(x=100, y=100))
            vm.undo()

        assert vm.can_redo is True

        vm.selected_palette_item = ObjectType.LED
        with patch("entropy_sim.viewmodel.ui"):
            vm.place_component(Point(x=200, y=200))

        assert vm.can_redo is False

    def test_max_history_limit(self) -> None:
        """Test undo stack respects max_history limit."""
        vm = CircuitViewModel()
        vm.max_history = 5

        # Add more states than limit
        for i in range(10):
            vm.selected_palette_item = ObjectType.BATTERY
            with patch("entropy_sim.viewmodel.ui"):
                vm.place_component(Point(x=i * 50, y=100))

        assert len(vm.undo_stack) == 5


class TestWireOperations:
    """Tests for wire-related operations via ViewModel."""

    def test_start_wire(self) -> None:
        """Test starting a wire."""
        vm = CircuitViewModel()
        vm.selected_palette_item = ObjectType.WIRE

        vm.start_wire(Point(x=100, y=100))

        assert vm.dragging_wire is not None
        assert len(vm.undo_stack) == 1

    def test_update_wire_end(self) -> None:
        """Test updating wire preview position."""
        vm = CircuitViewModel()
        vm.selected_palette_item = ObjectType.WIRE
        vm.start_wire(Point(x=100, y=100))

        vm.update_wire_end(Point(x=200, y=100))

        assert vm.dragging_wire is not None
        # Wire end should be updated (snapped to orthogonal)
        end = vm.dragging_wire.end.position
        assert end.x != 100 or end.y != 100

    def test_cancel_wire(self) -> None:
        """Test canceling wire drawing."""
        vm = CircuitViewModel()
        vm.selected_palette_item = ObjectType.WIRE
        vm.start_wire(Point(x=100, y=100))

        assert vm.dragging_wire is not None

        vm.cancel_wire()

        assert vm.dragging_wire is None
        assert vm.selected_palette_item is None

    def test_dragging_wire_property(self) -> None:
        """Test dragging_wire property delegates to wire_manager."""
        vm = CircuitViewModel()

        assert vm.dragging_wire is None

        vm.selected_palette_item = ObjectType.WIRE
        vm.start_wire(Point(x=100, y=100))

        assert vm.dragging_wire is not None

    def test_dragging_wire_corner_property(self) -> None:
        """Test dragging_wire_corner property delegates to wire_manager."""
        vm = CircuitViewModel()

        assert vm.dragging_wire_corner is None

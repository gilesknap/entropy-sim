"""ViewModel for the circuit canvas - manages state and business logic."""

from collections.abc import Callable
from uuid import UUID

from nicegui import ui

from .models import LED, Battery, Circuit, Point, Wire
from .pathfinding import find_wire_path


class CircuitViewModel:
    """ViewModel managing circuit state and operations."""

    # Component dimensions for hit testing
    BATTERY_WIDTH = 80
    BATTERY_HEIGHT = 40
    LED_WIDTH = 30
    LED_HEIGHT = 60
    SNAP_DISTANCE = 20.0

    def __init__(self) -> None:
        """Initialize the view model."""
        self.circuit = Circuit()

        # Interaction state
        self.selected_palette_item: str | None = None
        self.dragging_component: UUID | None = None
        self.dragging_wire: Wire | None = None
        self.wire_start_point: Point | None = None
        self.drag_offset = Point(x=0, y=0)

        # Undo/redo history
        self.undo_stack: list[str] = []  # JSON snapshots of circuit state
        self.redo_stack: list[str] = []
        self.max_history = 50

        # Callbacks for view updates
        self._on_change_callbacks: list[Callable[[], None]] = []

    def add_change_listener(self, callback: Callable[[], None]) -> None:
        """Register a callback to be called when circuit state changes."""
        self._on_change_callbacks.append(callback)

    def _notify_change(self) -> None:
        """Notify all listeners that the circuit state has changed."""
        for callback in self._on_change_callbacks:
            callback()

    # === Palette Selection ===

    def select_palette_item(self, item: str) -> None:
        """Select an item from the palette."""
        self.selected_palette_item = item
        ui.notify(f"Selected: {item}. Click on canvas to place.")

    def clear_selection(self) -> None:
        """Clear the current palette selection."""
        self.selected_palette_item = None

    # === Component Placement ===

    def place_component(self, pos: Point) -> None:
        """Place the selected component at the given position."""
        if not self.selected_palette_item:
            return

        self._save_state()

        if self.selected_palette_item == "battery":
            self.circuit.add_battery(pos)
            ui.notify("Battery placed!")
        elif self.selected_palette_item == "led":
            self.circuit.add_led(pos)
            ui.notify("LED placed!")

        self.selected_palette_item = None
        self._notify_change()

    # === Wire Operations ===

    def start_wire(self, pos: Point) -> None:
        """Start drawing a new wire."""
        self._save_state()

        nearest = self.circuit.find_nearest_connection_point(pos, self.SNAP_DISTANCE)
        wire = self.circuit.add_wire()
        self.dragging_wire = wire

        if nearest:
            _obj_id, conn_point, _ = nearest
            wire.start.position = Point(
                x=conn_point.position.x, y=conn_point.position.y
            )
            wire.start_connected_to = conn_point.id
            self.wire_start_point = conn_point.position
        else:
            wire.start.position = pos
            self.wire_start_point = pos

        wire.end.position = pos
        wire.path = find_wire_path(wire.start.position, wire.end.position)
        self._notify_change()

    def update_wire_end(self, pos: Point) -> None:
        """Update the end position of a wire being drawn."""
        if not self.dragging_wire or not self.wire_start_point:
            return

        nearest = self.circuit.find_nearest_connection_point(pos, self.SNAP_DISTANCE)

        if nearest:
            _, conn_point, _ = nearest
            end_pos = Point(x=conn_point.position.x, y=conn_point.position.y)
        else:
            end_pos = pos

        self.dragging_wire.end.position = end_pos
        self.dragging_wire.path = find_wire_path(self.wire_start_point, end_pos)
        self._notify_change()

    def finish_wire(self, pos: Point) -> None:
        """Finish wire placement."""
        if not self.dragging_wire:
            return

        nearest = self.circuit.find_nearest_connection_point(pos, self.SNAP_DISTANCE)

        if nearest:
            _obj_id, conn_point, _ = nearest
            self.dragging_wire.end.position = Point(
                x=conn_point.position.x, y=conn_point.position.y
            )
            self.dragging_wire.end_connected_to = conn_point.id
            conn_point.connected_to = self.dragging_wire.id

        if self.wire_start_point:
            self.dragging_wire.path = find_wire_path(
                self.wire_start_point, self.dragging_wire.end.position
            )

        self.dragging_wire = None
        self.wire_start_point = None
        self.selected_palette_item = None
        self._notify_change()

    # === Component Dragging ===

    def check_component_drag(self, pos: Point) -> bool:
        """Check if a component should be dragged. Returns True if drag started."""
        # Check batteries
        for battery in self.circuit.batteries:
            if self._point_in_rect(
                pos, battery.position, self.BATTERY_WIDTH, self.BATTERY_HEIGHT
            ):
                self._save_state()
                self.dragging_component = battery.id
                self.drag_offset = Point(
                    x=pos.x - battery.position.x, y=pos.y - battery.position.y
                )
                return True

        # Check LEDs
        for led in self.circuit.leds:
            if self._point_in_rect(pos, led.position, self.LED_WIDTH, self.LED_HEIGHT):
                self._save_state()
                self.dragging_component = led.id
                self.drag_offset = Point(
                    x=pos.x - led.position.x, y=pos.y - led.position.y
                )
                return True

        return False

    def update_component_position(self, pos: Point) -> None:
        """Update a component's position during drag."""
        if not self.dragging_component:
            return

        new_pos = Point(x=pos.x - self.drag_offset.x, y=pos.y - self.drag_offset.y)

        for battery in self.circuit.batteries:
            if battery.id == self.dragging_component:
                battery.position = new_pos
                battery.update_connection_positions()
                self._update_connected_wires(battery)
                self._notify_change()
                return

        for led in self.circuit.leds:
            if led.id == self.dragging_component:
                led.position = new_pos
                led.update_connection_positions()
                self._update_connected_wires(led)
                self._notify_change()
                return

    def finish_drag(self) -> None:
        """Finish dragging a component."""
        self.dragging_component = None

    def _update_connected_wires(self, component: Battery | LED) -> None:
        """Update wires connected to a component."""
        conn_points = []
        if isinstance(component, Battery):
            conn_points = [component.positive, component.negative]
        elif isinstance(component, LED):
            conn_points = [component.anode, component.cathode]

        for conn_point in conn_points:
            for wire in self.circuit.wires:
                if wire.start_connected_to == conn_point.id:
                    wire.start.position = Point(
                        x=conn_point.position.x, y=conn_point.position.y
                    )
                    wire.path = find_wire_path(wire.start.position, wire.end.position)
                elif wire.end_connected_to == conn_point.id:
                    wire.end.position = Point(
                        x=conn_point.position.x, y=conn_point.position.y
                    )
                    wire.path = find_wire_path(wire.start.position, wire.end.position)

    def _point_in_rect(
        self, point: Point, center: Point, width: float, height: float
    ) -> bool:
        """Check if a point is inside a rectangle centered at center."""
        half_w = width / 2
        half_h = height / 2
        return (
            center.x - half_w <= point.x <= center.x + half_w
            and center.y - half_h <= point.y <= center.y + half_h
        )

    # === Circuit Operations ===

    def clear_circuit(self) -> None:
        """Clear all components from the circuit."""
        self._save_state()
        self.circuit = Circuit()
        self._notify_change()
        ui.notify("Circuit cleared!")

    def save_circuit(self) -> str:
        """Save the circuit and return JSON data."""
        json_data = self.circuit.model_dump_json(indent=2)
        ui.notify(
            f"Circuit saved! ({len(self.circuit.batteries)} batteries, "
            f"{len(self.circuit.leds)} LEDs, {len(self.circuit.wires)} wires)"
        )
        return json_data

    def load_circuit(self, json_data: str) -> None:
        """Load a circuit from JSON data."""
        self._save_state()
        self.circuit = Circuit.model_validate_json(json_data)
        self._notify_change()
        ui.notify("Circuit loaded!")

    # === Undo/Redo ===

    def _save_state(self) -> None:
        """Save the current circuit state to the undo stack."""
        state = self.circuit.model_dump_json()
        self.undo_stack.append(state)
        if len(self.undo_stack) > self.max_history:
            self.undo_stack.pop(0)
        self.redo_stack.clear()

    def undo(self) -> bool:
        """Undo the last action. Returns True if successful."""
        if not self.undo_stack:
            ui.notify("Nothing to undo", type="warning")
            return False

        current_state = self.circuit.model_dump_json()
        self.redo_stack.append(current_state)

        previous_state = self.undo_stack.pop()
        self.circuit = Circuit.model_validate_json(previous_state)
        self._notify_change()
        ui.notify("Undone", type="info")
        return True

    def redo(self) -> bool:
        """Redo the last undone action. Returns True if successful."""
        if not self.redo_stack:
            ui.notify("Nothing to redo", type="warning")
            return False

        current_state = self.circuit.model_dump_json()
        self.undo_stack.append(current_state)

        next_state = self.redo_stack.pop()
        self.circuit = Circuit.model_validate_json(next_state)
        self._notify_change()
        ui.notify("Redone", type="info")
        return True

    @property
    def can_undo(self) -> bool:
        """Check if undo is available."""
        return len(self.undo_stack) > 0

    @property
    def can_redo(self) -> bool:
        """Check if redo is available."""
        return len(self.redo_stack) > 0

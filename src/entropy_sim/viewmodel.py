"""ViewModel for the circuit canvas - manages state and business logic."""

from collections.abc import Callable
from uuid import UUID

from nicegui import ui

from .models import Circuit, Point, Wire, WirePoint
from .wire_manager import WireManager


class CircuitViewModel:
    """ViewModel managing circuit state and operations."""

    # Component dimensions for hit testing
    BATTERY_WIDTH = 80
    BATTERY_HEIGHT = 40
    LED_WIDTH = 30
    LED_HEIGHT = 60

    def __init__(self) -> None:
        """Initialize the view model."""
        self.circuit = Circuit()

        # Callbacks for view updates
        self._on_change_callbacks: list[Callable[[], None]] = []

        # Wire manager handles all wire operations
        self._wire_manager = WireManager(self.circuit, self._notify_change)

        # Interaction state
        self.selected_palette_item: str | None = None
        self.dragging_component: UUID | None = None
        self.drag_offset = Point(x=0, y=0)

        # Undo/redo history
        self.undo_stack: list[str] = []
        self.redo_stack: list[str] = []
        self.max_history = 50

    # === Properties delegated to WireManager ===

    @property
    def dragging_wire(self) -> Wire | None:
        """Get the wire currently being drawn."""
        return self._wire_manager.dragging_wire

    @property
    def dragging_wire_corner(self) -> tuple[UUID, int] | None:
        """Get the wire corner currently being dragged."""
        return self._wire_manager.dragging_wire_corner

    # === Change Notification ===

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

    # === Wire Operations (delegated to WireManager) ===

    def start_wire(self, pos: Point) -> None:
        """Start drawing a new wire or add a segment."""
        if not self._wire_manager.is_drawing:
            self._save_state()
        wire_completed = self._wire_manager.start_wire(pos)
        if wire_completed:
            self.selected_palette_item = None

    def update_wire_end(self, pos: Point) -> None:
        """Update the preview end position of a wire being drawn."""
        self._wire_manager.update_wire_preview(pos)

    def cancel_wire(self) -> None:
        """Cancel wire drawing (called on Esc)."""
        self._wire_manager.cancel_wire()
        self.selected_palette_item = None

    def finish_wire(self, pos: Point) -> None:
        """Legacy method - now handled by start_wire click logic."""
        pass

    # === Component Dragging ===

    def check_component_drag(self, pos: Point) -> bool:
        """Check if a component should be dragged. Returns True if drag started."""
        # First check wire corners (they should be on top visually)
        if self._wire_manager.check_corner_hit(pos):
            self._save_state()
            return True

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
        # Handle wire corner dragging
        if self._wire_manager.is_dragging_corner:
            self._wire_manager.update_corner_position(pos)
            return

        if not self.dragging_component:
            return

        new_pos = Point(x=pos.x - self.drag_offset.x, y=pos.y - self.drag_offset.y)

        for battery in self.circuit.batteries:
            if battery.id == self.dragging_component:
                battery.position = new_pos
                battery.update_connection_positions()
                self._wire_manager.update_connected_wires(battery)
                self._notify_change()
                return

        for led in self.circuit.leds:
            if led.id == self.dragging_component:
                led.position = new_pos
                led.update_connection_positions()
                self._wire_manager.update_connected_wires(led)
                self._notify_change()
                return

    def finish_drag(self) -> None:
        """Finish dragging a component or wire corner."""
        self.dragging_component = None
        self._wire_manager.finish_corner_drag()

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

    # === Object Detection ===

    def get_object_at(self, pos: Point) -> tuple[str, UUID] | None:
        """Get the object at a position. Returns (type, id) or None."""
        # Check wire corners first
        for wire in self.circuit.wires:
            for i, point in enumerate(wire.path):
                if i == 0 or i == len(wire.path) - 1:
                    continue
                dist = ((pos.x - point.x) ** 2 + (pos.y - point.y) ** 2) ** 0.5
                if dist <= self._wire_manager.WIRE_CORNER_HIT_RADIUS:
                    return ("wire", wire.id)

        # Check batteries
        for battery in self.circuit.batteries:
            if self._point_in_rect(
                pos, battery.position, self.BATTERY_WIDTH, self.BATTERY_HEIGHT
            ):
                return ("battery", battery.id)

        # Check LEDs
        for led in self.circuit.leds:
            if self._point_in_rect(pos, led.position, self.LED_WIDTH, self.LED_HEIGHT):
                return ("led", led.id)

        # Check wire segments
        for wire in self.circuit.wires:
            if self._point_near_wire(pos, wire):
                return ("wire", wire.id)

        return None

    def _point_near_wire(self, pos: Point, wire: Wire, threshold: float = 10) -> bool:
        """Check if point is near any segment of a wire."""
        for i in range(len(wire.path) - 1):
            p1 = wire.path[i]
            p2 = wire.path[i + 1]
            dist = self._point_to_segment_distance(pos, p1, p2)
            if dist <= threshold:
                return True
        return False

    def _point_to_segment_distance(
        self, pos: Point, p1: WirePoint, p2: WirePoint
    ) -> float:
        """Calculate distance from point to line segment."""
        # Vector from p1 to p2
        dx = p2.x - p1.x
        dy = p2.y - p1.y
        seg_len_sq = dx * dx + dy * dy

        if seg_len_sq == 0:
            # p1 and p2 are the same point
            return ((pos.x - p1.x) ** 2 + (pos.y - p1.y) ** 2) ** 0.5

        # Project pos onto the line, clamped to segment
        t = max(0, min(1, ((pos.x - p1.x) * dx + (pos.y - p1.y) * dy) / seg_len_sq))
        proj_x = p1.x + t * dx
        proj_y = p1.y + t * dy

        return ((pos.x - proj_x) ** 2 + (pos.y - proj_y) ** 2) ** 0.5

    # === Delete Operations ===

    def delete_object(self, obj_type: str, obj_id: UUID) -> None:
        """Delete an object by type and ID."""
        self._save_state()

        if obj_type == "battery":
            self._delete_battery(obj_id)
        elif obj_type == "led":
            self._delete_led(obj_id)
        elif obj_type == "wire":
            self._delete_wire(obj_id)

        self._notify_change()

    def _delete_battery(self, battery_id: UUID) -> None:
        """Delete a battery and its connected wires."""
        battery = next((b for b in self.circuit.batteries if b.id == battery_id), None)
        if not battery:
            return

        # Delete connected wires
        conn_ids = {battery.positive.id, battery.negative.id}
        self.circuit.wires = [
            w
            for w in self.circuit.wires
            if w.start_connected_to not in conn_ids
            and w.end_connected_to not in conn_ids
        ]

        # Delete the battery
        self.circuit.batteries = [
            b for b in self.circuit.batteries if b.id != battery_id
        ]
        ui.notify("Battery deleted")

    def _delete_led(self, led_id: UUID) -> None:
        """Delete an LED and its connected wires."""
        led = next((item for item in self.circuit.leds if item.id == led_id), None)
        if not led:
            return

        # Delete connected wires
        conn_ids = {led.anode.id, led.cathode.id}
        self.circuit.wires = [
            w
            for w in self.circuit.wires
            if w.start_connected_to not in conn_ids
            and w.end_connected_to not in conn_ids
        ]

        # Delete the LED
        self.circuit.leds = [item for item in self.circuit.leds if item.id != led_id]
        ui.notify("LED deleted")

    def _delete_wire(self, wire_id: UUID) -> None:
        """Delete a wire."""
        self.circuit.wires = [w for w in self.circuit.wires if w.id != wire_id]
        ui.notify("Wire deleted")

    # === Rotation Operations ===

    def rotate_object(self, obj_type: str, obj_id: UUID, degrees: float) -> None:
        """Rotate an object by the specified degrees."""
        self._save_state()

        if obj_type == "battery":
            self._rotate_battery(obj_id, degrees)
        elif obj_type == "led":
            self._rotate_led(obj_id, degrees)

        self._notify_change()

    def _rotate_battery(self, battery_id: UUID, degrees: float) -> None:
        """Rotate a battery and update its connected wires."""
        battery = next((b for b in self.circuit.batteries if b.id == battery_id), None)
        if not battery:
            return

        battery.rotation = (battery.rotation + degrees) % 360
        battery.update_connection_positions()

        # Update connected wires
        self._wire_manager.update_connected_wires(battery)

        ui.notify(f"Battery rotated {degrees}°")

    def _rotate_led(self, led_id: UUID, degrees: float) -> None:
        """Rotate an LED and update its connected wires."""
        led = next((item for item in self.circuit.leds if item.id == led_id), None)
        if not led:
            return

        led.rotation = (led.rotation + degrees) % 360
        led.update_connection_positions()

        # Update connected wires
        self._wire_manager.update_connected_wires(led)

        ui.notify(f"LED rotated {degrees}°")

    # === Circuit Operations ===

    def clear_circuit(self) -> None:
        """Clear all components from the circuit."""
        self._save_state()
        self.circuit = Circuit()
        self._wire_manager.circuit = self.circuit
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
        self._wire_manager.circuit = self.circuit
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
        self._wire_manager.circuit = self.circuit
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
        self._wire_manager.circuit = self.circuit
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

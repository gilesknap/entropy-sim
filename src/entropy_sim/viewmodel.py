"""ViewModel for the circuit canvas - manages state and business logic."""

from collections.abc import Callable
from uuid import UUID

from nicegui import ui

from .models import LED, Battery, Circuit, ConnectionPoint, Point, Wire, WirePoint


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
        self.drag_offset = Point(x=0, y=0)

        # Wire corner dragging state
        self.dragging_wire_corner: tuple[UUID, int] | None = (
            None  # (wire_id, corner_index)
        )

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

    def _snap_to_orthogonal(self, pos: Point, reference: Point) -> Point:
        """Snap position to be orthogonal (horizontal or vertical) from reference."""
        dx = abs(pos.x - reference.x)
        dy = abs(pos.y - reference.y)

        # Snap to the axis with larger displacement
        if dx > dy:
            # Horizontal - keep x, snap y to reference
            return Point(x=pos.x, y=reference.y)
        else:
            # Vertical - keep y, snap x to reference
            return Point(x=reference.x, y=pos.y)

    def start_wire(self, pos: Point) -> None:
        """Start drawing a new wire or add a segment."""
        nearest = self.circuit.find_nearest_connection_point(pos, self.SNAP_DISTANCE)

        # If already drawing a wire, this click adds a corner or finishes
        if self.dragging_wire:
            if nearest:
                # Clicked on a connection point - finish the wire
                self._finish_wire_at_connection(nearest)
            else:
                # Add a corner point and continue drawing
                self._add_wire_corner(pos)
            return

        # Starting a new wire
        self._save_state()
        wire = self.circuit.add_wire()
        self.dragging_wire = wire

        if nearest:
            _obj_id, conn_point, _ = nearest
            start_pos = Point(x=conn_point.position.x, y=conn_point.position.y)
            wire.start.position = start_pos
            wire.start_connected_to = conn_point.id
            wire.path = [WirePoint(x=start_pos.x, y=start_pos.y)]
        else:
            wire.start.position = pos
            wire.path = [WirePoint(x=pos.x, y=pos.y)]

        wire.end.position = pos
        self._notify_change()

    def _add_wire_corner(self, pos: Point) -> None:
        """Add a corner point to the wire being drawn."""
        if not self.dragging_wire or not self.dragging_wire.path:
            return

        # Snap to orthogonal from last point
        last_point = self.dragging_wire.path[-1]
        snapped_pos = self._snap_to_orthogonal(
            pos, Point(x=last_point.x, y=last_point.y)
        )

        # Add the corner point to the path
        self.dragging_wire.path.append(WirePoint(x=snapped_pos.x, y=snapped_pos.y))
        self._notify_change()

    def _finish_wire_at_connection(
        self, nearest: tuple[UUID, "ConnectionPoint", "Battery | LED"]
    ) -> None:
        """Finish wire at a connection point."""
        if not self.dragging_wire or not self.dragging_wire.path:
            return

        _obj_id, conn_point, _ = nearest
        end_pos = Point(x=conn_point.position.x, y=conn_point.position.y)

        self.dragging_wire.end.position = end_pos
        self.dragging_wire.end_connected_to = conn_point.id
        conn_point.connected_to = self.dragging_wire.id

        # Get last point in current path
        last_point = self.dragging_wire.path[-1]

        # Check if we need an intermediate corner to maintain orthogonality
        dx = abs(end_pos.x - last_point.x)
        dy = abs(end_pos.y - last_point.y)

        # If not already aligned horizontally or vertically, add a corner
        if dx > 1 and dy > 1:
            # Add an L-shaped corner - first go horizontal, then vertical
            corner = WirePoint(x=end_pos.x, y=last_point.y)
            self.dragging_wire.path.append(corner)

        # Add final point to path
        self.dragging_wire.path.append(WirePoint(x=end_pos.x, y=end_pos.y))

        self.dragging_wire = None
        self.selected_palette_item = None
        self._notify_change()

    def update_wire_end(self, pos: Point) -> None:
        """Update the preview end position of a wire being drawn."""
        if not self.dragging_wire or not self.dragging_wire.path:
            return

        nearest = self.circuit.find_nearest_connection_point(pos, self.SNAP_DISTANCE)

        if nearest:
            _, conn_point, _ = nearest
            end_pos = Point(x=conn_point.position.x, y=conn_point.position.y)
        else:
            # Snap to orthogonal from last path point
            last_point = self.dragging_wire.path[-1]
            end_pos = self._snap_to_orthogonal(
                pos, Point(x=last_point.x, y=last_point.y)
            )

        self.dragging_wire.end.position = end_pos
        self._notify_change()

    def cancel_wire(self) -> None:
        """Cancel wire drawing (called on Esc)."""
        if self.dragging_wire:
            # Remove the incomplete wire
            self.circuit.wires.remove(self.dragging_wire)
            self.dragging_wire = None
            self.selected_palette_item = None
            self._notify_change()

    def finish_wire(self, pos: Point) -> None:
        """Legacy method - now handled by start_wire click logic."""
        # This is now a no-op since wire finishing is handled by clicking
        # on connection points in start_wire
        pass

    # === Component Dragging ===

    WIRE_CORNER_HIT_RADIUS = 12.0  # Radius for clicking on wire corners

    def check_component_drag(self, pos: Point) -> bool:
        """Check if a component should be dragged. Returns True if drag started."""
        # First check wire corners (they should be on top visually)
        for wire in self.circuit.wires:
            # Check intermediate points (not start/end which are connection points)
            for i, point in enumerate(wire.path):
                # Skip first and last points (they're connected to components)
                if i == 0 or i == len(wire.path) - 1:
                    continue
                dist = ((pos.x - point.x) ** 2 + (pos.y - point.y) ** 2) ** 0.5
                if dist <= self.WIRE_CORNER_HIT_RADIUS:
                    self._save_state()
                    self.dragging_wire_corner = (wire.id, i)
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
        if self.dragging_wire_corner:
            wire_id, corner_idx = self.dragging_wire_corner
            for wire in self.circuit.wires:
                if wire.id == wire_id:
                    if 0 < corner_idx < len(wire.path):
                        # Get adjacent points
                        prev_point = wire.path[corner_idx - 1]
                        next_point = (
                            wire.path[corner_idx + 1]
                            if corner_idx + 1 < len(wire.path)
                            else None
                        )

                        # Determine which axis to constrain based on previous segment
                        # The segment before this corner determines the first constraint
                        prev_is_horizontal = (
                            abs(prev_point.y - wire.path[corner_idx].y) < 1
                        )

                        if prev_is_horizontal:
                            # Horizontal segment: corner moves vertically
                            # Keep x from previous, use new y
                            wire.path[corner_idx].x = prev_point.x
                            wire.path[corner_idx].y = pos.y
                        else:
                            # Vertical segment: corner moves horizontally
                            # Keep y from previous, use new x
                            wire.path[corner_idx].x = pos.x
                            wire.path[corner_idx].y = prev_point.y

                        # Update next segment to maintain orthogonality
                        if next_point:
                            if prev_is_horizontal:
                                # Corner moved vertically, next is horizontal
                                next_point.y = wire.path[corner_idx].y
                            else:
                                # Corner moved horizontally, next is vertical
                                next_point.x = wire.path[corner_idx].x

                        self._notify_change()
                    return
            return

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
        """Finish dragging a component or wire corner."""
        self.dragging_component = None
        self.dragging_wire_corner = None

    def _update_connected_wires(self, component: Battery | LED) -> None:
        """Update wires connected to a component, maintaining orthogonal segments."""
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
                    # Update first point in path to match new position
                    if wire.path:
                        wire.path[0].x = conn_point.position.x
                        wire.path[0].y = conn_point.position.y

                        # Adjust second point to maintain orthogonality
                        if len(wire.path) > 1:
                            second_point = wire.path[1]

                            # Orientation from third point (if exists)
                            if len(wire.path) > 2:
                                third_point = wire.path[2]
                                # Check if segment 2->3 is horizontal or vertical
                                segment_23_is_horizontal = abs(
                                    third_point.x - second_point.x
                                ) > abs(third_point.y - second_point.y)

                                if segment_23_is_horizontal:
                                    # 2->3 horizontal, so 1->2 vertical
                                    second_point.x = wire.path[0].x
                                else:
                                    # 2->3 vertical, so 1->2 horizontal
                                    second_point.y = wire.path[0].y
                            else:
                                # Only 2 points - use larger displacement
                                dx = abs(second_point.x - wire.path[0].x)
                                dy = abs(second_point.y - wire.path[0].y)

                                if dx > dy:
                                    # Make horizontal
                                    second_point.y = wire.path[0].y
                                else:
                                    # Make vertical
                                    second_point.x = wire.path[0].x

                elif wire.end_connected_to == conn_point.id:
                    wire.end.position = Point(
                        x=conn_point.position.x, y=conn_point.position.y
                    )
                    # Update last point in path to match new position
                    if wire.path:
                        wire.path[-1].x = conn_point.position.x
                        wire.path[-1].y = conn_point.position.y

                        # Adjust second-to-last point to maintain orthogonality
                        if len(wire.path) > 1:
                            second_last_point = wire.path[-2]

                            # Orientation from third-to-last point
                            if len(wire.path) > 2:
                                third_last_point = wire.path[-3]
                                # Check if segment (n-3)->(n-2) is horizontal
                                # or vertical
                                segment_is_horizontal = abs(
                                    second_last_point.x - third_last_point.x
                                ) > abs(second_last_point.y - third_last_point.y)

                                if segment_is_horizontal:
                                    # (n-3)->(n-2) horizontal, so vertical
                                    second_last_point.x = wire.path[-1].x
                                else:
                                    # (n-3)->(n-2) vertical, so horizontal
                                    second_last_point.y = wire.path[-1].y
                            else:
                                # Only 2 points - use larger displacement
                                dx = abs(wire.path[-1].x - second_last_point.x)
                                dy = abs(wire.path[-1].y - second_last_point.y)

                                if dx > dy:
                                    # Make horizontal
                                    second_last_point.y = wire.path[-1].y
                                else:
                                    # Make vertical
                                    second_last_point.x = wire.path[-1].x

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

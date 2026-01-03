"""NiceGUI-based canvas for circuit visualization and interaction."""

import base64
from uuid import UUID

from nicegui import ui
from nicegui.events import KeyEventArguments, MouseEventArguments

from .models import LED, Battery, Circuit, Point, Wire
from .pathfinding import find_wire_path


class CircuitCanvas:
    """Interactive canvas for building and viewing circuits."""

    CANVAS_WIDTH = 1000
    CANVAS_HEIGHT = 700
    PALETTE_WIDTH = 150
    SNAP_DISTANCE = 20.0

    # Component dimensions
    BATTERY_WIDTH = 80
    BATTERY_HEIGHT = 40
    LED_WIDTH = 30
    LED_HEIGHT = 60

    def __init__(self) -> None:
        """Initialize the circuit canvas."""
        self.circuit = Circuit()
        self.interactive_image: ui.interactive_image | None = None
        self.selected_palette_item: str | None = None
        self.dragging_component: UUID | None = None
        self.dragging_wire: Wire | None = None
        self.wire_start_point: Point | None = None
        self.drag_offset = Point(x=0, y=0)
        self.selection_label: ui.label | None = None
        # Undo/redo history
        self.undo_stack: list[str] = []  # JSON snapshots of circuit state
        self.redo_stack: list[str] = []
        self.max_history = 50

    def render(self) -> None:
        """Render the complete circuit canvas UI."""
        with ui.column().classes("w-full items-center"):
            ui.label("Entropy Simulation - Circuit Builder").classes(
                "text-2xl font-bold mb-4"
            )

            with ui.row().classes("gap-4"):
                self._render_canvas()
                self._render_palette()

            self._render_controls()

    def _render_palette(self) -> None:
        """Render the component palette."""
        with ui.card().classes("p-4").style(f"width: {self.PALETTE_WIDTH}px"):
            ui.label("Components").classes("text-lg font-bold mb-2")

            # Battery palette item
            with ui.card().classes(
                "p-2 mb-2 cursor-pointer hover:bg-gray-100"
            ) as battery_card:
                ui.html(self._get_battery_svg(0, 0, mini=True), sanitize=False).classes(
                    "w-full"
                )
                ui.label("Battery").classes("text-center text-sm")
            battery_card.on("click", lambda: self._on_palette_click("battery"))

            # LED palette item
            with ui.card().classes(
                "p-2 mb-2 cursor-pointer hover:bg-gray-100"
            ) as led_card:
                ui.html(self._get_led_svg(0, 0, mini=True), sanitize=False).classes(
                    "w-full"
                )
                ui.label("LED").classes("text-center text-sm")
            led_card.on("click", lambda: self._on_palette_click("led"))

            # Wire palette item
            with ui.card().classes(
                "p-2 mb-2 cursor-pointer hover:bg-gray-100"
            ) as wire_card:
                ui.html(self._get_wire_palette_svg(), sanitize=False).classes("w-full")
                ui.label("Wire").classes("text-center text-sm")
            wire_card.on("click", lambda: self._on_palette_click("wire"))

            ui.separator().classes("my-2")
            ui.label("Selected:").classes("text-sm")
            self.selection_label = ui.label("None").classes("text-sm font-bold")

            # Undo/Redo buttons
            ui.separator().classes("my-2")
            ui.label("History").classes("text-sm font-bold")
            with ui.row().classes("gap-1 w-full justify-center"):
                ui.button(icon="undo", on_click=self._undo).props("flat dense").tooltip(
                    "Undo (Ctrl+Z)"
                )
                ui.button(icon="redo", on_click=self._redo).props("flat dense").tooltip(
                    "Redo (Ctrl+Shift+Z)"
                )

        # Add keyboard shortcuts
        ui.keyboard(on_key=self._handle_keyboard)

    def _render_canvas(self) -> None:
        """Render the main SVG canvas."""
        # Create SVG as a data URI for use with interactive_image
        svg_data = self._generate_svg()
        svg_b64 = base64.b64encode(svg_data.encode()).decode()
        data_uri = f"data:image/svg+xml;base64,{svg_b64}"

        self.interactive_image = ui.interactive_image(
            data_uri,
            on_mouse=self._on_mouse_event,
            events=["mousedown", "mouseup", "mousemove"],
            cross=False,
        ).classes("border border-gray-300")
        self.interactive_image.style(
            f"width: {self.CANVAS_WIDTH}px; height: {self.CANVAS_HEIGHT}px;"
        )

    def _render_controls(self) -> None:
        """Render control buttons."""
        with ui.row().classes("mt-4 gap-2"):
            ui.button("Clear All", on_click=self._clear_circuit).props("color=negative")
            ui.button("Save Circuit", on_click=self._save_circuit).props(
                "color=primary"
            )
            ui.button("Load Circuit", on_click=self._load_circuit).props(
                "color=secondary"
            )

    def _generate_svg(self) -> str:
        """Generate the complete SVG for the circuit."""
        svg_content = f"""
        <svg width="{self.CANVAS_WIDTH}" height="{self.CANVAS_HEIGHT}"
             xmlns="http://www.w3.org/2000/svg"
             style="background-color: #f8f9fa;">
            <!-- Grid pattern -->
            <defs>
                <pattern id="grid" width="20" height="20" patternUnits="userSpaceOnUse">
                    <path d="M 20 0 L 0 0 0 20" fill="none" stroke="#e0e0e0" stroke-width="0.5"/>
                </pattern>
            </defs>
            <rect width="100%" height="100%" fill="url(#grid)"/>

            <!-- Wires (render first so components appear on top) -->
            {self._render_wires_svg()}

            <!-- Batteries -->
            {self._render_batteries_svg()}

            <!-- LEDs -->
            {self._render_leds_svg()}

            <!-- Connection points (render last for visibility) -->
            {self._render_connection_points_svg()}
        </svg>
        """
        return svg_content

    def _render_batteries_svg(self) -> str:
        """Generate SVG for all batteries."""
        svg = ""
        for battery in self.circuit.batteries:
            svg += self._get_battery_svg(battery.position.x, battery.position.y)
        return svg

    def _render_leds_svg(self) -> str:
        """Generate SVG for all LEDs."""
        svg = ""
        for led in self.circuit.leds:
            svg += self._get_led_svg(
                led.position.x, led.position.y, led.color, led.is_on
            )
        return svg

    def _render_wires_svg(self) -> str:
        """Generate SVG for all wires."""
        svg = ""
        for wire in self.circuit.wires:
            if wire.path:
                path_d = f"M {wire.path[0].x} {wire.path[0].y}"
                for point in wire.path[1:]:
                    path_d += f" L {point.x} {point.y}"
                svg += f"""
                <path d="{path_d}" fill="none" stroke="#333" stroke-width="3"
                      stroke-linecap="round" stroke-linejoin="round"/>
                """
        return svg

    def _render_connection_points_svg(self) -> str:
        """Generate SVG for connection points."""
        svg = ""
        for _obj_id, conn_point, obj in self.circuit.get_all_connection_points():
            color = "#22c55e" if conn_point.connected_to else "#3b82f6"
            # Determine if this is positive or negative terminal
            if conn_point.label == "positive":
                color = "#ef4444" if not conn_point.connected_to else "#22c55e"
            elif conn_point.label == "negative":
                color = "#1e40af" if not conn_point.connected_to else "#22c55e"

            svg += f"""
            <circle cx="{conn_point.position.x}" cy="{conn_point.position.y}"
                    r="6" fill="{color}" stroke="#fff" stroke-width="2"/>
            """
        return svg

    def _get_battery_svg(self, x: float, y: float, mini: bool = False) -> str:
        """Generate SVG for a battery."""
        if mini:
            return """
            <svg width="80" height="40" viewBox="-40 -20 80 40">
                <rect x="-35" y="-15" width="70" height="30" rx="3" fill="#fbbf24" stroke="#92400e" stroke-width="2"/>
                <rect x="35" y="-8" width="5" height="16" fill="#92400e"/>
                <text x="0" y="5" text-anchor="middle" font-size="12" fill="#92400e">+  -</text>
            </svg>
            """
        return f"""
        <g transform="translate({x}, {y})">
            <rect x="-35" y="-15" width="70" height="30" rx="3" fill="#fbbf24" stroke="#92400e" stroke-width="2"/>
            <rect x="35" y="-8" width="5" height="16" fill="#92400e"/>
            <text x="-20" y="5" text-anchor="middle" font-size="14" font-weight="bold" fill="#92400e">+</text>
            <text x="20" y="5" text-anchor="middle" font-size="14" font-weight="bold" fill="#92400e">-</text>
        </g>
        """

    def _get_led_svg(
        self,
        x: float,
        y: float,
        color: str = "red",
        is_on: bool = False,
        mini: bool = False,
    ) -> str:
        """Generate SVG for an LED."""
        led_color = self._get_led_color(color, is_on)
        glow = 'filter="url(#glow)"' if is_on else ""

        if mini:
            return f"""
            <svg width="30" height="60" viewBox="-15 -30 30 60">
                <polygon points="0,-20 12,10 -12,10" fill="{led_color}" stroke="#333" stroke-width="2"/>
                <line x1="-12" y1="10" x2="12" y2="10" stroke="#333" stroke-width="3"/>
                <line x1="0" y1="10" x2="0" y2="25" stroke="#333" stroke-width="2"/>
            </svg>
            """
        return f"""
        <g transform="translate({x}, {y})">
            <defs>
                <filter id="glow" x="-50%" y="-50%" width="200%" height="200%">
                    <feGaussianBlur stdDeviation="4" result="coloredBlur"/>
                    <feMerge>
                        <feMergeNode in="coloredBlur"/>
                        <feMergeNode in="SourceGraphic"/>
                    </feMerge>
                </filter>
            </defs>
            <polygon points="0,-20 15,15 -15,15" fill="{led_color}" stroke="#333" stroke-width="2" {glow}/>
            <line x1="-15" y1="15" x2="15" y2="15" stroke="#333" stroke-width="3"/>
            <line x1="0" y1="-20" x2="0" y2="-30" stroke="#333" stroke-width="2"/>
            <line x1="0" y1="15" x2="0" y2="30" stroke="#333" stroke-width="2"/>
        </g>
        """

    def _get_wire_palette_svg(self) -> str:
        """Generate SVG for wire palette item."""
        return """
        <svg width="80" height="40" viewBox="0 0 80 40">
            <line x1="10" y1="20" x2="70" y2="20" stroke="#333" stroke-width="3" stroke-linecap="round"/>
            <circle cx="10" cy="20" r="5" fill="#3b82f6"/>
            <circle cx="70" cy="20" r="5" fill="#3b82f6"/>
        </svg>
        """

    def _get_led_color(self, color: str, is_on: bool) -> str:
        """Get the fill color for an LED."""
        colors = {
            "red": ("#ff6b6b", "#cc0000"),
            "green": ("#6bff6b", "#00cc00"),
            "blue": ("#6b6bff", "#0000cc"),
            "yellow": ("#ffff6b", "#cccc00"),
        }
        on_color, off_color = colors.get(color, colors["red"])
        return on_color if is_on else off_color

    def _on_palette_click(self, item: str) -> None:
        """Handle palette item selection."""
        self.selected_palette_item = item
        self.selection_label.set_text(item.capitalize())
        ui.notify(f"Selected: {item}. Click on canvas to place.")

    def _on_mouse_event(self, e: MouseEventArguments) -> None:
        """Handle all mouse events on canvas."""
        pos = Point(x=e.image_x, y=e.image_y)
        event_type = e.type

        if event_type == "mousedown":
            if self.selected_palette_item == "wire":
                self._start_wire(pos)
            elif self.selected_palette_item:
                self._place_component(pos)
            else:
                self._check_component_drag(pos)
        elif event_type == "mousemove":
            if self.dragging_wire:
                self._update_wire_end(pos)
            elif self.dragging_component:
                self._update_component_position(pos)
        elif event_type == "mouseup":
            if self.dragging_wire:
                self._finish_wire(pos)
            elif self.dragging_component:
                self.dragging_component = None
            self._update_canvas()

    def _place_component(self, pos: Point) -> None:
        """Place a new component on the canvas."""
        self._save_state()
        if self.selected_palette_item == "battery":
            self.circuit.add_battery(pos)
            ui.notify("Battery placed!")
        elif self.selected_palette_item == "led":
            self.circuit.add_led(pos)
            ui.notify("LED placed!")

        self.selected_palette_item = None
        self.selection_label.set_text("None")
        self._update_canvas()

    def _start_wire(self, pos: Point) -> None:
        """Start drawing a new wire."""
        self._save_state()
        # Check if starting near a connection point
        nearest = self.circuit.find_nearest_connection_point(pos, self.SNAP_DISTANCE)

        wire = self.circuit.add_wire()
        self.dragging_wire = wire

        if nearest:
            obj_id, conn_point, _ = nearest
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
        self._update_canvas()

    def _update_wire_end(self, pos: Point) -> None:
        """Update the end position of a wire being drawn."""
        if not self.dragging_wire or not self.wire_start_point:
            return

        # Check for snap to connection point
        nearest = self.circuit.find_nearest_connection_point(pos, self.SNAP_DISTANCE)

        if nearest:
            _, conn_point, _ = nearest
            end_pos = Point(x=conn_point.position.x, y=conn_point.position.y)
        else:
            end_pos = pos

        self.dragging_wire.end.position = end_pos
        self.dragging_wire.path = find_wire_path(self.wire_start_point, end_pos)
        self._update_canvas()

    def _finish_wire(self, pos: Point) -> None:
        """Finish wire placement."""
        if not self.dragging_wire:
            return

        # Check if ending near a connection point
        nearest = self.circuit.find_nearest_connection_point(pos, self.SNAP_DISTANCE)

        if nearest:
            obj_id, conn_point, _ = nearest
            self.dragging_wire.end.position = Point(
                x=conn_point.position.x, y=conn_point.position.y
            )
            self.dragging_wire.end_connected_to = conn_point.id

            # Update the connection point to mark it as connected
            conn_point.connected_to = self.dragging_wire.id

        # Recalculate final path
        if self.wire_start_point:
            self.dragging_wire.path = find_wire_path(
                self.wire_start_point, self.dragging_wire.end.position
            )

        self.dragging_wire = None
        self.wire_start_point = None
        self.selected_palette_item = None
        self.selection_label.set_text("None")

    def _check_component_drag(self, pos: Point) -> None:
        """Check if a component should be dragged."""
        # Check batteries
        for battery in self.circuit.batteries:
            if self._point_in_rect(
                pos, battery.position, self.BATTERY_WIDTH, self.BATTERY_HEIGHT
            ):
                self._save_state()  # Save before drag starts
                self.dragging_component = battery.id
                self.drag_offset = Point(
                    x=pos.x - battery.position.x, y=pos.y - battery.position.y
                )
                return

        # Check LEDs
        for led in self.circuit.leds:
            if self._point_in_rect(pos, led.position, self.LED_WIDTH, self.LED_HEIGHT):
                self._save_state()  # Save before drag starts
                self.dragging_component = led.id
                self.drag_offset = Point(
                    x=pos.x - led.position.x, y=pos.y - led.position.y
                )
                return

    def _update_component_position(self, pos: Point) -> None:
        """Update a component's position during drag."""
        if not self.dragging_component:
            return

        new_pos = Point(x=pos.x - self.drag_offset.x, y=pos.y - self.drag_offset.y)

        # Find and update the component
        for battery in self.circuit.batteries:
            if battery.id == self.dragging_component:
                battery.position = new_pos
                battery._update_connection_positions()
                self._update_connected_wires(battery)
                self._update_canvas()
                return

        for led in self.circuit.leds:
            if led.id == self.dragging_component:
                led.position = new_pos
                led._update_connection_positions()
                self._update_connected_wires(led)
                self._update_canvas()
                return

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

    def _update_canvas(self) -> None:
        """Update the canvas SVG."""
        if self.interactive_image:
            svg_data = self._generate_svg()
            svg_b64 = base64.b64encode(svg_data.encode()).decode()
            data_uri = f"data:image/svg+xml;base64,{svg_b64}"
            self.interactive_image.set_source(data_uri)

    def _clear_circuit(self) -> None:
        """Clear all components from the circuit."""
        self._save_state()
        self.circuit = Circuit()
        self._update_canvas()
        ui.notify("Circuit cleared!")

    def _save_circuit(self) -> None:
        """Save the circuit (placeholder)."""
        # Export as JSON
        json_data = self.circuit.model_dump_json(indent=2)
        ui.notify(
            f"Circuit saved! ({len(self.circuit.batteries)} batteries, "
            f"{len(self.circuit.leds)} LEDs, {len(self.circuit.wires)} wires)"
        )
        print(json_data)  # For now, just print to console

    def _load_circuit(self) -> None:
        """Load a circuit (placeholder)."""
        ui.notify("Load functionality coming soon!")

    def _save_state(self) -> None:
        """Save the current circuit state to the undo stack."""
        state = self.circuit.model_dump_json()
        self.undo_stack.append(state)
        # Limit history size
        if len(self.undo_stack) > self.max_history:
            self.undo_stack.pop(0)
        # Clear redo stack when new action is performed
        self.redo_stack.clear()

    def _undo(self) -> None:
        """Undo the last action."""
        if not self.undo_stack:
            ui.notify("Nothing to undo", type="warning")
            return

        # Save current state to redo stack
        current_state = self.circuit.model_dump_json()
        self.redo_stack.append(current_state)

        # Restore previous state
        previous_state = self.undo_stack.pop()
        self.circuit = Circuit.model_validate_json(previous_state)
        self._update_canvas()
        ui.notify("Undone", type="info")

    def _redo(self) -> None:
        """Redo the last undone action."""
        if not self.redo_stack:
            ui.notify("Nothing to redo", type="warning")
            return

        # Save current state to undo stack
        current_state = self.circuit.model_dump_json()
        self.undo_stack.append(current_state)

        # Restore next state
        next_state = self.redo_stack.pop()
        self.circuit = Circuit.model_validate_json(next_state)
        self._update_canvas()
        ui.notify("Redone", type="info")

    def _handle_keyboard(self, e: KeyEventArguments) -> None:
        """Handle keyboard shortcuts."""
        if e.action.keydown:
            if e.key == "z" and e.modifiers.ctrl and e.modifiers.shift:
                self._redo()
            elif e.key == "z" and e.modifiers.ctrl:
                self._undo()


@ui.page("/")
def index() -> None:
    """Main page for the circuit builder."""
    ui.dark_mode(False)
    canvas = CircuitCanvas()
    canvas.render()


def run() -> None:
    """Run the circuit simulation application."""
    ui.run(title="Entropy Simulation", port=8080, reload=False)

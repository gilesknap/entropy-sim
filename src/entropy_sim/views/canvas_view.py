"""Main canvas view that composes all circuit UI components."""

import base64

from nicegui import ui
from nicegui.events import MouseEventArguments

from ..models import Point
from ..viewmodel import CircuitViewModel
from .controls import ControlsView
from .palette import PaletteView
from .svg_renderer import SVGRenderer


class CircuitCanvasView:
    """Main view composing the circuit canvas, palette, and controls."""

    CANVAS_WIDTH = 1000
    CANVAS_HEIGHT = 700
    PALETTE_WIDTH = 150

    def __init__(self) -> None:
        """Initialize the canvas view."""
        self.viewmodel = CircuitViewModel()
        self.renderer = SVGRenderer(self.CANVAS_WIDTH, self.CANVAS_HEIGHT)
        self.palette = PaletteView(self.viewmodel, self.renderer, self.PALETTE_WIDTH)
        self.controls = ControlsView(self.viewmodel)

        self.interactive_image: ui.interactive_image | None = None

        # Register for viewmodel changes
        self.viewmodel.add_change_listener(self._on_circuit_change)

    def render(self) -> None:
        """Render the complete circuit canvas UI."""
        with ui.column().classes("w-full items-center"):
            ui.label("Entropy Simulation - Circuit Builder").classes(
                "text-2xl font-bold mb-4"
            )

            with ui.row().classes("gap-4"):
                self._render_canvas()
                self.palette.render()

            self.controls.render()

    def _render_canvas(self) -> None:
        """Render the main SVG canvas."""
        svg_data = self.renderer.render_circuit(self.viewmodel.circuit)
        svg_b64 = base64.b64encode(svg_data.encode()).decode()
        data_uri = f"data:image/svg+xml;base64,{svg_b64}"

        self.interactive_image = (
            ui.interactive_image(
                data_uri,
                on_mouse=self._on_mouse_event,
                events=["mousedown", "mouseup", "mousemove"],
                cross=False,
            )
            .classes("border border-gray-300")
            .style(f"width: {self.CANVAS_WIDTH}px; height: {self.CANVAS_HEIGHT}px;")
        )

    def _on_mouse_event(self, e: MouseEventArguments) -> None:
        """Handle mouse events on canvas."""
        pos = Point(x=e.image_x, y=e.image_y)
        event_type = e.type

        if event_type == "mousedown":
            self._handle_mouse_down(pos)
        elif event_type == "mousemove":
            self._handle_mouse_move(pos)
        elif event_type == "mouseup":
            self._handle_mouse_up(pos)

    def _handle_mouse_down(self, pos: Point) -> None:
        """Handle mouse down event."""
        if self.viewmodel.selected_palette_item == "wire":
            self.viewmodel.start_wire(pos)
        elif self.viewmodel.selected_palette_item:
            self.viewmodel.place_component(pos)
            self.palette.update_selection_label("None")
        else:
            self.viewmodel.check_component_drag(pos)

    def _handle_mouse_move(self, pos: Point) -> None:
        """Handle mouse move event."""
        if self.viewmodel.dragging_wire:
            self.viewmodel.update_wire_end(pos)
        elif self.viewmodel.dragging_component:
            self.viewmodel.update_component_position(pos)

    def _handle_mouse_up(self, pos: Point) -> None:
        """Handle mouse up event."""
        if self.viewmodel.dragging_wire:
            self.viewmodel.finish_wire(pos)
            self.palette.update_selection_label("None")
        elif self.viewmodel.dragging_component:
            self.viewmodel.finish_drag()

    def _on_circuit_change(self) -> None:
        """Handle circuit state change from viewmodel."""
        self._update_canvas()

    def _update_canvas(self) -> None:
        """Update the canvas SVG."""
        if self.interactive_image:
            svg_data = self.renderer.render_circuit(self.viewmodel.circuit)
            svg_b64 = base64.b64encode(svg_data.encode()).decode()
            data_uri = f"data:image/svg+xml;base64,{svg_b64}"
            self.interactive_image.set_source(data_uri)

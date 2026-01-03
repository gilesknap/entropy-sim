"""Main canvas view that composes all circuit UI components."""

import base64
from uuid import UUID

from nicegui import ui
from nicegui.events import MouseEventArguments

from ..models import Point
from ..viewmodel import CircuitViewModel
from .controls import ControlsView
from .palette import PaletteView
from .svg_renderer import SVGRenderer


class CircuitCanvasView:
    """Main view composing the circuit canvas, palette, and controls."""

    PALETTE_WIDTH = 150

    def __init__(self) -> None:
        """Initialize the canvas view."""
        self.viewmodel = CircuitViewModel()
        self.renderer = SVGRenderer()
        self.palette = PaletteView(self.viewmodel, self.renderer, self.PALETTE_WIDTH)
        self.controls = ControlsView(self.viewmodel)

        self.interactive_image: ui.interactive_image | None = None
        self.canvas_container: ui.element | None = None

        # Register for viewmodel changes
        self.viewmodel.add_change_listener(self._on_circuit_change)

    def render(self) -> None:
        """Render the complete circuit canvas UI."""
        with (
            ui.column()
            .classes("w-full p-4")
            .style(
                "height: 100vh; max-height: 100vh; overflow: hidden; "
                "box-sizing: border-box;"
            )
        ):
            ui.label("Entropy Simulation - Circuit Builder").classes(
                "text-2xl font-bold mb-4 flex-shrink-0"
            )

            with (
                ui.row()
                .classes("gap-4 flex-1 w-full")
                .style("min-height: 0; overflow: hidden;")
            ):
                self._render_canvas()
                self.palette.render()

            self.controls.render()

    def _render_canvas(self) -> None:
        """Render the main SVG canvas."""
        svg_data = self.renderer.render_circuit(self.viewmodel.circuit)
        svg_b64 = base64.b64encode(svg_data.encode()).decode()
        data_uri = f"data:image/svg+xml;base64,{svg_b64}"

        # Canvas uses fixed pixel dimensions from renderer
        canvas_w = self.renderer.width
        canvas_h = self.renderer.height

        with (
            ui.element("div")
            .classes("flex-1")
            .style(
                "min-width: 0; min-height: 0; overflow: auto; "
                "width: 100%; height: 100%;"
            )
        ) as container:
            self.canvas_container = container
            self.interactive_image = (
                ui.interactive_image(
                    data_uri,
                    on_mouse=self._on_mouse_event,
                    events=["mousedown", "mouseup", "mousemove"],
                    cross=False,
                )
                .classes("border border-gray-300")
                .style(f"width: {canvas_w}px; height: {canvas_h}px;")
            )

        # Context menu state
        self._context_menu_target: tuple[str, UUID] | None = None
        self._context_menu_type_name: str = ""

        # Create context menu attached to interactive image
        if self.interactive_image:
            with self.interactive_image:
                with ui.context_menu() as self.context_menu:
                    self.rotate_cw_item = ui.menu_item(
                        "Rotate 90° CW",
                        on_click=lambda: self._rotate_context_target(90),
                    )
                    self.rotate_ccw_item = ui.menu_item(
                        "Rotate 90° CCW",
                        on_click=lambda: self._rotate_context_target(-90),
                    )
                    ui.separator()
                    self.delete_menu_item = ui.menu_item(
                        "Delete", on_click=self._delete_context_target
                    )

            # Handle right-click to capture what object was clicked
            self.interactive_image.on(
                "contextmenu",
                self._on_right_click,
                ["offsetX", "offsetY"],
            )

    def _on_right_click(self, e: object) -> None:
        """Handle right-click on canvas to determine target object."""
        # Event can be dict or have args attribute depending on NiceGUI version
        if hasattr(e, "args"):
            args: dict[str, float] = e.args  # type: ignore[union-attr]
        else:
            args = e  # type: ignore[assignment]
        x = args.get("offsetX", 0)
        y = args.get("offsetY", 0)
        pos = Point(x=x, y=y)

        obj = self.viewmodel.get_object_at(pos)
        if obj:
            obj_type, obj_id = obj
            self._context_menu_target = (obj_type, obj_id)
            self._context_menu_type_name = obj_type.capitalize()
            # Show/hide rotation options based on object type
            is_rotatable = obj_type in ("battery", "led")
            self.rotate_cw_item.set_visibility(is_rotatable)
            self.rotate_ccw_item.set_visibility(is_rotatable)
        else:
            self._context_menu_target = None
            self._context_menu_type_name = ""
            self.rotate_cw_item.set_visibility(False)
            self.rotate_ccw_item.set_visibility(False)

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

    def _rotate_context_target(self, degrees: float) -> None:
        """Rotate the object that was right-clicked."""
        if self._context_menu_target:
            obj_type, obj_id = self._context_menu_target
            self.viewmodel.rotate_object(obj_type, obj_id, degrees)
            # Clear any drag state that might have been set
            self.viewmodel.clear_drag_state()

    def _delete_context_target(self) -> None:
        """Delete the object targeted by context menu."""
        if self._context_menu_target:
            obj_type, obj_id = self._context_menu_target
            self.viewmodel.delete_object(obj_type, obj_id)
            self._context_menu_target = None
        self.context_menu.close()

    def _handle_mouse_down(self, pos: Point) -> None:
        """Handle mouse down event."""
        if (
            self.viewmodel.selected_palette_item == "wire"
            or self.viewmodel.dragging_wire
        ):
            # Wire drawing uses clicks to add points
            self.viewmodel.start_wire(pos)
            # Don't clear selection while drawing wire
            if not self.viewmodel.dragging_wire:
                self.palette.update_selection_label("None")
        elif self.viewmodel.selected_palette_item:
            self.viewmodel.place_component(pos)
            self.palette.update_selection_label("None")
        else:
            self.viewmodel.check_component_drag(pos)

    def _handle_mouse_move(self, pos: Point) -> None:
        """Handle mouse move event."""
        if self.viewmodel.dragging_wire:
            self.viewmodel.update_wire_end(pos)
        elif self.viewmodel.dragging_component or self.viewmodel.dragging_wire_corner:
            self.viewmodel.update_component_position(pos)

    def _handle_mouse_up(self, pos: Point) -> None:
        """Handle mouse up event."""
        # Wire drawing is now click-based, so mouseup only handles component drag
        if self.viewmodel.dragging_component or self.viewmodel.dragging_wire_corner:
            self.viewmodel.finish_drag()

    def _on_circuit_change(self) -> None:
        """Handle circuit state change from viewmodel."""
        self._update_canvas()

    def _update_canvas(self) -> None:
        """Update the canvas SVG and resize if needed."""
        if self.interactive_image:
            svg_data = self.renderer.render_circuit(self.viewmodel.circuit)
            svg_b64 = base64.b64encode(svg_data.encode()).decode()
            data_uri = f"data:image/svg+xml;base64,{svg_b64}"
            self.interactive_image.set_source(data_uri)

            # Update canvas size to match SVG dimensions
            canvas_w = self.renderer.width
            canvas_h = self.renderer.height
            self.interactive_image.style(f"width: {canvas_w}px; height: {canvas_h}px;")

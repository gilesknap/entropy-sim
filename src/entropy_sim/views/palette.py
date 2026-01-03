"""Palette view component for selecting circuit components."""

from nicegui import ui
from nicegui.events import KeyEventArguments

from ..viewmodel import CircuitViewModel
from .svg_renderer import SVGRenderer


class PaletteView:
    """Component palette for selecting items to place on canvas."""

    def __init__(
        self, viewmodel: CircuitViewModel, renderer: SVGRenderer, width: int = 150
    ) -> None:
        """Initialize the palette view."""
        self.viewmodel = viewmodel
        self.renderer = renderer
        self.width = width
        self.selection_label: ui.label | None = None

    def render(self) -> None:
        """Render the palette UI."""
        with (
            ui.card()
            .classes("p-4")
            .style(
                f"width: {self.width}px; flex: 0 0 {self.width}px; "
                "display: flex; flex-direction: column; height: 100%;"
            )
        ):
            ui.label("Components").classes("text-lg font-bold mb-2")

            self._render_battery_item()
            self._render_liion_cell_item()
            self._render_led_item()
            self._render_wire_item()

            ui.separator().classes("my-2")
            ui.label("Selected:").classes("text-sm")
            self.selection_label = ui.label("None").classes("text-sm font-bold")

            self._render_history_controls()

        # Add keyboard shortcuts
        ui.keyboard(on_key=self._handle_keyboard)

    def _render_battery_item(self) -> None:
        """Render battery palette item."""
        with ui.card().classes("p-2 mb-2 cursor-pointer hover:bg-gray-100") as card:
            ui.html(
                self.renderer.get_battery_svg(0, 0, mini=True), sanitize=False
            ).classes("w-full")
            ui.label("9V Battery").classes("text-center text-sm")
        card.on("click", lambda: self._on_item_click("battery"))

    def _render_liion_cell_item(self) -> None:
        """Render Li-Ion cell palette item."""
        with ui.card().classes("p-2 mb-2 cursor-pointer hover:bg-gray-100") as card:
            ui.html(
                self.renderer.get_liion_cell_svg(0, 0, mini=True), sanitize=False
            ).classes("w-full")
            ui.label("Li-Ion Cell").classes("text-center text-sm")
        card.on("click", lambda: self._on_item_click("liion_cell"))

    def _render_led_item(self) -> None:
        """Render LED palette item."""
        with ui.card().classes("p-2 mb-2 cursor-pointer hover:bg-gray-100") as card:
            ui.html(self.renderer.get_led_svg(0, 0, mini=True), sanitize=False).classes(
                "w-full"
            )
            ui.label("LED").classes("text-center text-sm")
        card.on("click", lambda: self._on_item_click("led"))

    def _render_wire_item(self) -> None:
        """Render wire palette item."""
        with ui.card().classes("p-2 mb-2 cursor-pointer hover:bg-gray-100") as card:
            ui.html(self.renderer.get_wire_palette_svg(), sanitize=False).classes(
                "w-full"
            )
            ui.label("Wire").classes("text-center text-sm")
        card.on("click", lambda: self._on_item_click("wire"))

    def _render_history_controls(self) -> None:
        """Render undo/redo buttons."""
        ui.separator().classes("my-2")
        ui.label("History").classes("text-sm font-bold")
        with ui.row().classes("gap-1 w-full justify-center"):
            ui.button(icon="undo", on_click=self._on_undo).props("flat dense").tooltip(
                "Undo (Ctrl+Z)"
            )
            ui.button(icon="redo", on_click=self._on_redo).props("flat dense").tooltip(
                "Redo (Ctrl+Shift+Z)"
            )

    def _on_item_click(self, item: str) -> None:
        """Handle palette item click."""
        self.viewmodel.select_palette_item(item)
        if self.selection_label:
            self.selection_label.set_text(item.capitalize())

    def _on_undo(self) -> None:
        """Handle undo button click."""
        self.viewmodel.undo()

    def _on_redo(self) -> None:
        """Handle redo button click."""
        self.viewmodel.redo()

    def _handle_keyboard(self, e: KeyEventArguments) -> None:
        """Handle keyboard shortcuts."""
        if e.action.keydown:
            if e.key == "z" and e.modifiers.ctrl and e.modifiers.shift:
                self.viewmodel.redo()
            elif e.key == "z" and e.modifiers.ctrl:
                self.viewmodel.undo()
            elif e.key == "Escape":
                self.viewmodel.cancel_wire()
                if self.selection_label:
                    self.selection_label.set_text("None")

    def update_selection_label(self, text: str) -> None:
        """Update the selection label text."""
        if self.selection_label:
            self.selection_label.set_text(text)

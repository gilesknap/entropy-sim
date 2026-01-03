"""Control buttons view component."""

from nicegui import ui

from ..viewmodel import CircuitViewModel


class ControlsView:
    """Control buttons for circuit operations."""

    def __init__(self, viewmodel: CircuitViewModel) -> None:
        """Initialize the controls view."""
        self.viewmodel = viewmodel

    def render(self) -> None:
        """Render the control buttons."""
        with ui.row().classes("mt-4 pb-2 gap-2 flex-shrink-0"):
            ui.button("Clear All", on_click=self._on_clear).props("color=negative")
            ui.button("Save Circuit", on_click=self._on_save).props("color=primary")
            ui.button("Load Circuit", on_click=self._on_load).props("color=secondary")

    def _on_clear(self) -> None:
        """Handle clear button click."""
        self.viewmodel.clear_circuit()

    def _on_save(self) -> None:
        """Handle save button click."""
        json_data = self.viewmodel.save_circuit()
        # For now, just print to console
        print(json_data)

    def _on_load(self) -> None:
        """Handle load button click."""
        ui.notify("Load functionality coming soon!")

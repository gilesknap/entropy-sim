"""Control buttons view component."""

import logging

from nicegui import ui

from ..viewmodel import CircuitViewModel

logger = logging.getLogger(__name__)


class ControlsView:
    """Control buttons for circuit operations.

    Provides UI controls for clearing, saving, and loading circuits.
    """

    def __init__(self, viewmodel: CircuitViewModel) -> None:
        """Initialize the controls view.

        Args:
            viewmodel: The circuit view model to control.
        """
        self.viewmodel = viewmodel

    def render(self) -> None:
        """Render the control buttons in a horizontal row."""
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
        # Log the circuit data for debugging (production would save to file)
        logger.info("Circuit saved: %d characters", len(json_data))

    def _on_load(self) -> None:
        """Handle load button click."""
        ui.notify("Load functionality coming soon!")

"""Main entry point for the circuit simulation application."""

from nicegui import ui

from .canvas_view import CircuitCanvasView


@ui.page("/")
def index() -> None:
    """Main page for the circuit builder."""
    ui.dark_mode(False)
    canvas = CircuitCanvasView()
    canvas.render()


def run() -> None:
    """Run the circuit simulation application."""
    ui.run(title="Entropy Simulation", port=8080, reload=False)

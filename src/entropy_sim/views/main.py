"""Main entry point for the circuit simulation application."""

from nicegui import ui

from .canvas_view import CircuitCanvasView


@ui.page("/")
def index() -> None:
    """Main page for the circuit builder."""
    ui.dark_mode(False)
    # Remove default margins and ensure no overflow on body
    ui.add_head_html("""
        <style>
            html, body {
                margin: 0;
                padding: 0;
                overflow: hidden;
                height: 100%;
            }
            .nicegui-content {
                height: 100%;
            }
        </style>
    """)
    canvas = CircuitCanvasView()
    canvas.render()


def run() -> None:
    """Run the circuit simulation application."""
    ui.run(title="Entropy Simulation", port=8080, reload=False)

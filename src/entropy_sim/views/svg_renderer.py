"""SVG rendering for circuit components."""

from importlib.resources import files

from ..models import Circuit


class SVGRenderer:
    """Renders circuit components as SVG."""

    # Padding around content to ensure objects aren't clipped
    CONTENT_PADDING = 100
    # Default canvas size when empty
    DEFAULT_WIDTH = 2000
    DEFAULT_HEIGHT = 1500

    def __init__(self) -> None:
        """Initialize the renderer."""
        # Track canvas dimensions (coordinate system)
        self.width = self.DEFAULT_WIDTH
        self.height = self.DEFAULT_HEIGHT
        # Load component SVG templates
        self._load_component_templates()

    def _load_component_templates(self) -> None:
        """Load SVG component templates from asset files."""
        import entropy_sim.assets.components as components_pkg

        self.battery_template = (
            files(components_pkg).joinpath("battery.svg").read_text()
        )
        self.battery_mini_template = (
            files(components_pkg).joinpath("battery_mini.svg").read_text()
        )
        self.led_template = files(components_pkg).joinpath("led.svg").read_text()
        self.led_mini_template = (
            files(components_pkg).joinpath("led_mini.svg").read_text()
        )

    def calculate_canvas_size(self, circuit: Circuit) -> tuple[int, int]:
        """Calculate canvas size based on content and defaults."""
        min_x, min_y, max_x, max_y = circuit.get_bounds()

        # Start with default size
        width = self.DEFAULT_WIDTH
        height = self.DEFAULT_HEIGHT

        # Expand if content extends beyond defaults
        if max_x != float("-inf"):
            width = max(width, int(max_x + self.CONTENT_PADDING))
            height = max(height, int(max_y + self.CONTENT_PADDING))

        return (width, height)

    def render_circuit(self, circuit: Circuit) -> str:
        """Generate the complete SVG for the circuit."""
        self.width, self.height = self.calculate_canvas_size(circuit)

        # SVG uses fixed dimensions for coordinate system
        return f"""
        <svg width="{self.width}" height="{self.height}"
             xmlns="http://www.w3.org/2000/svg"
             style="background-color: #f8f9fa;">
            <!-- Grid pattern -->
            <defs>
                <pattern id="grid" width="20" height="20"
                         patternUnits="userSpaceOnUse">
                    <path d="M 20 0 L 0 0 0 20" fill="none"
                          stroke="#e0e0e0" stroke-width="0.5"/>
                </pattern>
            </defs>
            <rect width="100%" height="100%" fill="url(#grid)"/>

            <!-- Wires (render first so components appear on top) -->
            {self._render_wires(circuit)}

            <!-- Batteries -->
            {self._render_batteries(circuit)}

            <!-- LEDs -->
            {self._render_leds(circuit)}

            <!-- Connection points (render last for visibility) -->
            {self._render_connection_points(circuit)}
        </svg>
        """

    def _render_batteries(self, circuit: Circuit) -> str:
        """Generate SVG for all batteries."""
        svg = ""
        for battery in circuit.batteries:
            svg += self.get_battery_svg(
                battery.position.x, battery.position.y, battery.rotation
            )
        return svg

    def _render_leds(self, circuit: Circuit) -> str:
        """Generate SVG for all LEDs."""
        svg = ""
        for led in circuit.leds:
            svg += self.get_led_svg(
                led.position.x, led.position.y, led.color, led.is_on, led.rotation
            )
        return svg

    def _render_wires(self, circuit: Circuit) -> str:
        """Generate SVG for all wires."""
        svg = ""
        for wire in circuit.wires:
            if wire.path:
                # Draw the committed path segments
                path_d = f"M {wire.path[0].x} {wire.path[0].y}"
                for point in wire.path[1:]:
                    path_d += f" L {point.x} {point.y}"
                svg += f"""
                <path d="{path_d}" fill="none" stroke="#333" stroke-width="3"
                      stroke-linecap="round" stroke-linejoin="round"/>
                """

                # Draw preview line from last path point to end position (while drawing)
                last_point = wire.path[-1]
                if (
                    abs(last_point.x - wire.end.position.x) > 1
                    or abs(last_point.y - wire.end.position.y) > 1
                ):
                    svg += f"""
                    <line x1="{last_point.x}" y1="{last_point.y}"
                          x2="{wire.end.position.x}" y2="{wire.end.position.y}"
                          stroke="#333" stroke-width="3" stroke-dasharray="5,5"
                          stroke-linecap="round"/>
                    """

                # Render draggable corner handles (skip first and last points)
                for i, point in enumerate(wire.path):
                    if i == 0 or i == len(wire.path) - 1:
                        continue
                    svg += f"""
                    <circle cx="{point.x}" cy="{point.y}" r="6"
                            fill="#6366f1" stroke="#fff" stroke-width="2"
                            style="cursor: move;"/>
                    """
        return svg

    def _render_connection_points(self, circuit: Circuit) -> str:
        """Generate SVG for connection points."""
        svg = ""
        for _obj_id, conn_point, _obj in circuit.get_all_connection_points():
            color = "#22c55e" if conn_point.connected_to else "#3b82f6"
            if conn_point.label == "positive":
                color = "#ef4444" if not conn_point.connected_to else "#22c55e"
            elif conn_point.label == "negative":
                color = "#1e40af" if not conn_point.connected_to else "#22c55e"

            svg += f"""
            <circle cx="{conn_point.position.x}" cy="{conn_point.position.y}"
                    r="6" fill="{color}" stroke="#fff" stroke-width="2"/>
            """
        return svg

    def get_battery_svg(
        self, x: float, y: float, rotation: float = 0.0, mini: bool = False
    ) -> str:
        """Generate SVG for a battery (Fritzing-style 9V battery)."""
        if mini:
            return self.battery_mini_template
        return f"""
        <g transform="translate({x}, {y}) rotate({rotation})">
            {self.battery_template}
        </g>
        """

    def get_led_svg(
        self,
        x: float,
        y: float,
        color: str = "red",
        is_on: bool = False,
        rotation: float = 0.0,
        mini: bool = False,
    ) -> str:
        """Generate SVG for an LED (Fritzing-style realistic LED)."""
        led_color = self._get_led_color(color, is_on)
        led_body_color = led_color if is_on else self._get_led_off_body(color)
        glow = 'filter="url(#ledGlow)"' if is_on else ""

        if mini:
            return self.led_mini_template.format(body_color=led_body_color)

        # Load template and substitute color placeholders
        svg_content = self.led_template.format(
            led_color=led_color, body_color=led_body_color, glow=glow
        )

        return f"""
        <g transform="translate({x}, {y}) rotate({rotation})">
            {svg_content}
        </g>
        """

    def get_wire_palette_svg(self) -> str:
        """Generate SVG for wire palette item."""
        return """
        <svg width="80" height="40" viewBox="0 0 80 40">
            <line x1="10" y1="20" x2="70" y2="20" stroke="#333"
                  stroke-width="3" stroke-linecap="round"/>
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

    def _get_led_off_body(self, color: str) -> str:
        """Get the body/dome color for an LED when off (more translucent)."""
        body_colors = {
            "red": "#ff9999",
            "green": "#99ff99",
            "blue": "#9999ff",
            "yellow": "#ffff99",
        }
        return body_colors.get(color, body_colors["red"])

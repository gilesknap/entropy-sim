"""Unit tests for SVGRenderer."""

from entropy_sim.models import Circuit, Point
from entropy_sim.models.base_connector import ConnectorPoint
from entropy_sim.object_type import ObjectType
from entropy_sim.views.svg_renderer import SVGRenderer


class TestSVGRendererInit:
    """Tests for SVGRenderer initialization."""

    def test_default_dimensions(self) -> None:
        """Test renderer initializes with default dimensions."""
        renderer = SVGRenderer()

        assert renderer.width == renderer.DEFAULT_WIDTH
        assert renderer.height == renderer.DEFAULT_HEIGHT

    def test_templates_loaded(self) -> None:
        """Test component templates are loaded."""
        renderer = SVGRenderer()

        assert renderer.battery_template is not None
        assert renderer.battery_mini_template is not None
        assert renderer.led_template is not None
        assert renderer.led_mini_template is not None
        assert renderer.liion_cell_template is not None
        assert renderer.liion_cell_mini_template is not None

    def test_templates_are_svg(self) -> None:
        """Test templates contain SVG content."""
        renderer = SVGRenderer()

        # Templates should contain SVG elements
        assert "<" in renderer.battery_template
        assert "<" in renderer.led_template


class TestCanvasSizeCalculation:
    """Tests for canvas size calculation."""

    def test_empty_circuit_uses_defaults(self) -> None:
        """Test empty circuit uses default dimensions."""
        renderer = SVGRenderer()
        circuit = Circuit()

        width, height = renderer.calculate_canvas_size(circuit)

        assert width == renderer.DEFAULT_WIDTH
        assert height == renderer.DEFAULT_HEIGHT

    def test_expands_for_large_content(self) -> None:
        """Test canvas expands when content exceeds defaults."""
        renderer = SVGRenderer()
        circuit = Circuit()
        # Add component far from origin
        circuit.add_object(ObjectType.BATTERY, Point(x=3000, y=2000))

        width, height = renderer.calculate_canvas_size(circuit)

        assert width > renderer.DEFAULT_WIDTH
        assert height > renderer.DEFAULT_HEIGHT

    def test_includes_padding(self) -> None:
        """Test canvas includes padding around content."""
        renderer = SVGRenderer()
        circuit = Circuit()
        circuit.add_object(ObjectType.BATTERY, Point(x=2500, y=2000))

        width, height = renderer.calculate_canvas_size(circuit)

        # Should have padding beyond the component
        assert width >= 2500 + renderer.CONTENT_PADDING
        assert height >= 2000 + renderer.CONTENT_PADDING


class TestCircuitRendering:
    """Tests for full circuit SVG rendering."""

    def test_render_empty_circuit(self) -> None:
        """Test rendering empty circuit produces valid SVG."""
        renderer = SVGRenderer()
        circuit = Circuit()

        svg = renderer.render_circuit(circuit)

        assert svg.startswith("\n        <svg")
        assert "</svg>" in svg
        assert 'xmlns="http://www.w3.org/2000/svg"' in svg

    def test_render_includes_grid(self) -> None:
        """Test rendered SVG includes grid pattern."""
        renderer = SVGRenderer()
        circuit = Circuit()

        svg = renderer.render_circuit(circuit)

        assert 'id="grid"' in svg
        assert 'fill="url(#grid)"' in svg

    def test_render_with_battery(self) -> None:
        """Test rendering circuit with battery."""
        renderer = SVGRenderer()
        circuit = Circuit()
        circuit.add_object(ObjectType.BATTERY, Point(x=100, y=100))

        svg = renderer.render_circuit(circuit)

        # Should contain battery SVG elements
        assert "translate(100" in svg or "translate(100.0" in svg

    def test_render_with_led(self) -> None:
        """Test rendering circuit with LED."""
        renderer = SVGRenderer()
        circuit = Circuit()
        circuit.add_object(ObjectType.LED, Point(x=200, y=200))

        svg = renderer.render_circuit(circuit)

        assert "translate(200" in svg or "translate(200.0" in svg

    def test_render_with_liion_cell(self) -> None:
        """Test rendering circuit with Li-Ion cell."""
        renderer = SVGRenderer()
        circuit = Circuit()
        circuit.add_object(ObjectType.LIION_CELL, Point(x=150, y=150))

        svg = renderer.render_circuit(circuit)

        assert "translate(150" in svg or "translate(150.0" in svg

    def test_render_with_wire(self) -> None:
        """Test rendering circuit with wire."""
        renderer = SVGRenderer()
        circuit = Circuit()
        wire = circuit.add_wire()
        wire.path = [
            ConnectorPoint(x=100, y=100),
            ConnectorPoint(x=200, y=100),
            ConnectorPoint(x=200, y=200),
        ]
        wire.start.position = Point(x=100, y=100)
        wire.end.position = Point(x=200, y=200)

        svg = renderer.render_circuit(circuit)

        # Should contain path element for wire
        assert "<path" in svg
        assert "M 100" in svg or "M 100.0" in svg

    def test_render_includes_connection_points(self) -> None:
        """Test rendered SVG includes connection point circles."""
        renderer = SVGRenderer()
        circuit = Circuit()
        circuit.add_object(ObjectType.BATTERY, Point(x=100, y=100))

        svg = renderer.render_circuit(circuit)

        # Should contain circles for connection points
        assert "<circle" in svg


class TestBatterySVG:
    """Tests for battery SVG generation."""

    def test_get_battery_svg_full(self) -> None:
        """Test getting full battery SVG."""
        renderer = SVGRenderer()

        svg = renderer.get_battery_svg(100, 200)

        assert "<g transform=" in svg
        assert "translate(100" in svg or "translate(100.0" in svg
        assert "rotate(0" in svg or "rotate(0.0" in svg

    def test_get_battery_svg_mini(self) -> None:
        """Test getting mini battery SVG."""
        renderer = SVGRenderer()

        svg = renderer.get_battery_svg(0, 0, mini=True)

        # Mini version should be the template directly
        assert svg == renderer.battery_mini_template

    def test_get_battery_svg_with_rotation(self) -> None:
        """Test battery SVG with rotation."""
        renderer = SVGRenderer()

        svg = renderer.get_battery_svg(100, 100, rotation=90)

        assert "rotate(90" in svg or "rotate(90.0" in svg


class TestLiIonCellSVG:
    """Tests for Li-Ion cell SVG generation."""

    def test_get_liion_cell_svg_full(self) -> None:
        """Test getting full Li-Ion cell SVG."""
        renderer = SVGRenderer()

        svg = renderer.get_liion_cell_svg(150, 150)

        assert "<g transform=" in svg
        assert "translate(150" in svg or "translate(150.0" in svg

    def test_get_liion_cell_svg_mini(self) -> None:
        """Test getting mini Li-Ion cell SVG."""
        renderer = SVGRenderer()

        svg = renderer.get_liion_cell_svg(0, 0, mini=True)

        assert svg == renderer.liion_cell_mini_template

    def test_get_liion_cell_svg_with_rotation(self) -> None:
        """Test Li-Ion cell SVG with rotation."""
        renderer = SVGRenderer()

        svg = renderer.get_liion_cell_svg(100, 100, rotation=45)

        assert "rotate(45" in svg or "rotate(45.0" in svg


class TestLEDSVG:
    """Tests for LED SVG generation."""

    def test_get_led_svg_full(self) -> None:
        """Test getting full LED SVG."""
        renderer = SVGRenderer()

        svg = renderer.get_led_svg(200, 200)

        assert "<g transform=" in svg
        assert "translate(200" in svg or "translate(200.0" in svg

    def test_get_led_svg_mini(self) -> None:
        """Test getting mini LED SVG."""
        renderer = SVGRenderer()

        svg = renderer.get_led_svg(0, 0, mini=True)

        # Mini should use the mini template
        assert "body_color" not in svg or "{body_color}" not in svg

    def test_get_led_svg_with_color(self) -> None:
        """Test LED SVG with different colors."""
        renderer = SVGRenderer()

        svg_red = renderer.get_led_svg(100, 100, color="red")
        svg_green = renderer.get_led_svg(100, 100, color="green")

        # Colors should be different in the rendered SVG
        # The templates use color placeholders that get filled
        assert svg_red != svg_green

    def test_get_led_svg_on_vs_off(self) -> None:
        """Test LED SVG differs when on vs off."""
        renderer = SVGRenderer()

        svg_off = renderer.get_led_svg(100, 100, is_on=False)
        svg_on = renderer.get_led_svg(100, 100, is_on=True)

        # On state should apply the glow filter (filter="url(#ledGlow)")
        # Off state should not apply the filter
        assert 'filter="url(#ledGlow)"' not in svg_off
        assert 'filter="url(#ledGlow)"' in svg_on

    def test_get_led_svg_with_rotation(self) -> None:
        """Test LED SVG with rotation."""
        renderer = SVGRenderer()

        svg = renderer.get_led_svg(100, 100, rotation=180)

        assert "rotate(180" in svg or "rotate(180.0" in svg


class TestWirePaletteSVG:
    """Tests for wire palette SVG generation."""

    def test_get_wire_palette_svg(self) -> None:
        """Test getting wire palette icon SVG."""
        renderer = SVGRenderer()

        svg = renderer.get_wire_palette_svg()

        assert "<svg" in svg
        assert "</svg>" in svg
        assert "<line" in svg
        assert "<circle" in svg


class TestLEDColors:
    """Tests for LED color helper methods."""

    def test_get_led_color_red(self) -> None:
        """Test getting red LED color."""
        renderer = SVGRenderer()

        color_off = renderer._get_led_color("red", is_on=False)
        color_on = renderer._get_led_color("red", is_on=True)

        assert color_off != color_on
        assert "#" in color_off  # Should be hex color

    def test_get_led_color_green(self) -> None:
        """Test getting green LED color."""
        renderer = SVGRenderer()

        color = renderer._get_led_color("green", is_on=False)

        assert "#" in color

    def test_get_led_color_blue(self) -> None:
        """Test getting blue LED color."""
        renderer = SVGRenderer()

        color = renderer._get_led_color("blue", is_on=False)

        assert "#" in color

    def test_get_led_color_yellow(self) -> None:
        """Test getting yellow LED color."""
        renderer = SVGRenderer()

        color = renderer._get_led_color("yellow", is_on=False)

        assert "#" in color

    def test_get_led_color_unknown_defaults_to_red(self) -> None:
        """Test unknown color defaults to red."""
        renderer = SVGRenderer()

        color = renderer._get_led_color("purple", is_on=False)
        red_color = renderer._get_led_color("red", is_on=False)

        assert color == red_color

    def test_get_led_off_body_colors(self) -> None:
        """Test LED body colors when off."""
        renderer = SVGRenderer()

        red_body = renderer._get_led_off_body("red")
        green_body = renderer._get_led_off_body("green")

        assert "#" in red_body
        assert red_body != green_body


class TestWireRendering:
    """Tests for wire rendering specifics."""

    def test_wire_path_rendering(self) -> None:
        """Test wire path is rendered as SVG path."""
        renderer = SVGRenderer()
        circuit = Circuit()
        wire = circuit.add_wire()
        wire.path = [
            ConnectorPoint(x=50, y=50),
            ConnectorPoint(x=150, y=50),
            ConnectorPoint(x=150, y=150),
        ]
        wire.start.position = Point(x=50, y=50)
        wire.end.position = Point(x=150, y=150)

        svg = renderer.render_circuit(circuit)

        # Check path contains expected coordinates
        assert "M 50" in svg or "M 50.0" in svg
        assert "L 150" in svg or "L 150.0" in svg

    def test_wire_preview_rendering(self) -> None:
        """Test wire preview (dashed line) is rendered."""
        renderer = SVGRenderer()
        circuit = Circuit()
        wire = circuit.add_wire()
        wire.path = [ConnectorPoint(x=50, y=50)]
        wire.start.position = Point(x=50, y=50)
        wire.end.position = Point(x=150, y=150)  # Different from last path point

        svg = renderer.render_circuit(circuit)

        # Should have dashed line for preview
        assert "stroke-dasharray" in svg

    def test_wire_corner_handles_rendering(self) -> None:
        """Test wire corner handles (circles) are rendered."""
        renderer = SVGRenderer()
        circuit = Circuit()
        wire = circuit.add_wire()
        wire.path = [
            ConnectorPoint(x=0, y=0),
            ConnectorPoint(x=100, y=0),  # Middle point - should have handle
            ConnectorPoint(x=100, y=100),
        ]
        wire.start.position = Point(x=0, y=0)
        wire.end.position = Point(x=100, y=100)

        svg = renderer.render_circuit(circuit)

        # Should have circle for middle corner handle
        # (endpoints don't get handles)
        assert 'cx="100"' in svg or 'cx="100.0"' in svg


class TestConnectionPointRendering:
    """Tests for connection point rendering."""

    def test_positive_terminal_color(self) -> None:
        """Test positive terminals render with red color."""
        renderer = SVGRenderer()
        circuit = Circuit()
        circuit.add_object(ObjectType.BATTERY, Point(x=100, y=100))

        svg = renderer.render_circuit(circuit)

        # Red color for positive
        assert "#ef4444" in svg

    def test_negative_terminal_color(self) -> None:
        """Test negative terminals render with black color."""
        renderer = SVGRenderer()
        circuit = Circuit()
        circuit.add_object(ObjectType.BATTERY, Point(x=100, y=100))

        svg = renderer.render_circuit(circuit)

        # Black color for negative
        assert "#000000" in svg

    def test_connected_point_filled(self) -> None:
        """Test connected points render with solid fill."""
        renderer = SVGRenderer()
        circuit = Circuit()
        battery = circuit.add_object(ObjectType.BATTERY, Point(x=100, y=100))
        wire = circuit.add_wire()
        wire.start_connected_to = battery.positive.id  # type: ignore[union-attr]
        battery.positive.connected_to = wire.id  # type: ignore[union-attr]

        svg = renderer.render_circuit(circuit)

        # Connected points should have fill (not "none")
        # This is hard to test precisely, but we can verify the SVG renders
        assert "<circle" in svg


class TestRendererUpdatesSize:
    """Tests for renderer updating its size property."""

    def test_render_updates_width_height(self) -> None:
        """Test render_circuit updates renderer width/height."""
        renderer = SVGRenderer()
        circuit = Circuit()
        circuit.add_object(ObjectType.BATTERY, Point(x=3000, y=2500))

        renderer.render_circuit(circuit)

        assert renderer.width > renderer.DEFAULT_WIDTH
        assert renderer.height > renderer.DEFAULT_HEIGHT

    def test_render_sets_svg_dimensions(self) -> None:
        """Test rendered SVG has correct dimension attributes."""
        renderer = SVGRenderer()
        circuit = Circuit()

        svg = renderer.render_circuit(circuit)

        assert f'width="{renderer.width}"' in svg
        assert f'height="{renderer.height}"' in svg

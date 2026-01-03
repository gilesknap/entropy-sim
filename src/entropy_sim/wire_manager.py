"""Wire management module - handles orthogonal wire drawing and manipulation."""

from collections.abc import Callable
from uuid import UUID

from .models import LED, Battery, Circuit, ConnectionPoint, Point, Wire, WirePoint


class WireManager:
    """Manages wire drawing, corner dragging, and orthogonal constraints."""

    SNAP_DISTANCE = 20.0
    WIRE_CORNER_HIT_RADIUS = 12.0

    def __init__(self, circuit: Circuit, on_change: Callable[[], None]) -> None:
        """Initialize the wire manager.

        Args:
            circuit: The circuit model to manage wires for
            on_change: Callback to notify when wire state changes
        """
        self._circuit = circuit
        self._on_change = on_change

        # Wire drawing state
        self.dragging_wire: Wire | None = None

        # Wire corner dragging state: (wire_id, corner_index)
        self.dragging_wire_corner: tuple[UUID, int] | None = None

    @property
    def circuit(self) -> Circuit:
        """Get the current circuit."""
        return self._circuit

    @circuit.setter
    def circuit(self, value: Circuit) -> None:
        """Set the circuit (e.g., after undo/redo)."""
        self._circuit = value

    @property
    def is_drawing(self) -> bool:
        """Check if currently drawing a wire."""
        return self.dragging_wire is not None

    @property
    def is_dragging_corner(self) -> bool:
        """Check if currently dragging a wire corner."""
        return self.dragging_wire_corner is not None

    # === Wire Drawing ===

    def _snap_to_orthogonal(self, pos: Point, reference: Point) -> Point:
        """Snap position to be orthogonal (horizontal or vertical) from reference."""
        dx = abs(pos.x - reference.x)
        dy = abs(pos.y - reference.y)

        if dx > dy:
            return Point(x=pos.x, y=reference.y)
        else:
            return Point(x=reference.x, y=pos.y)

    def start_wire(self, pos: Point) -> bool:
        """Start drawing a new wire or add a segment.

        Returns True if this started/modified wire drawing.
        """
        nearest = self._circuit.find_nearest_connection_point(pos, self.SNAP_DISTANCE)

        # If already drawing a wire, this click adds a corner or finishes
        if self.dragging_wire:
            if nearest:
                self._finish_wire_at_connection(nearest)
            else:
                self._add_wire_corner(pos)
            return True

        # Starting a new wire
        wire = self._circuit.add_wire()
        self.dragging_wire = wire

        if nearest:
            _obj_id, conn_point, _ = nearest
            start_pos = Point(x=conn_point.position.x, y=conn_point.position.y)
            wire.start.position = start_pos
            wire.start_connected_to = conn_point.id
            wire.path = [WirePoint(x=start_pos.x, y=start_pos.y)]
        else:
            wire.start.position = pos
            wire.path = [WirePoint(x=pos.x, y=pos.y)]

        wire.end.position = pos
        self._on_change()
        return True

    def _add_wire_corner(self, pos: Point) -> None:
        """Add a corner point to the wire being drawn."""
        if not self.dragging_wire or not self.dragging_wire.path:
            return

        last_point = self.dragging_wire.path[-1]
        snapped_pos = self._snap_to_orthogonal(
            pos, Point(x=last_point.x, y=last_point.y)
        )

        self.dragging_wire.path.append(WirePoint(x=snapped_pos.x, y=snapped_pos.y))
        self._on_change()

    def _finish_wire_at_connection(
        self, nearest: tuple[UUID, ConnectionPoint, Battery | LED]
    ) -> None:
        """Finish wire at a connection point."""
        if not self.dragging_wire or not self.dragging_wire.path:
            return

        _obj_id, conn_point, _ = nearest
        end_pos = Point(x=conn_point.position.x, y=conn_point.position.y)

        self.dragging_wire.end.position = end_pos
        self.dragging_wire.end_connected_to = conn_point.id
        conn_point.connected_to = self.dragging_wire.id

        last_point = self.dragging_wire.path[-1]

        # Check if we need to adjust for orthogonality
        dx = abs(end_pos.x - last_point.x)
        dy = abs(end_pos.y - last_point.y)

        if dx > 1 and dy > 1:
            # Not aligned - need to adjust to maintain orthogonality
            # Determine what orientation the last segment should be based on
            # the alternating pattern
            if len(self.dragging_wire.path) >= 2:
                prev_point = self.dragging_wire.path[-2]
                # Check if segment prev->last is horizontal or vertical
                prev_seg_horizontal = abs(last_point.y - prev_point.y) < 1

                if prev_seg_horizontal:
                    # Previous segment is horizontal (same y)
                    # So last->endpoint should be vertical (same x)
                    # Adjust last_point.x to match endpoint.x
                    last_point.x = end_pos.x
                else:
                    # Previous segment is vertical (same x)
                    # So last->endpoint should be horizontal (same y)
                    # Adjust last_point.y to match endpoint.y
                    last_point.y = end_pos.y
            else:
                # Only one point - choose based on smaller displacement
                if dx < dy:
                    last_point.y = end_pos.y
                else:
                    last_point.x = end_pos.x

        self.dragging_wire.path.append(WirePoint(x=end_pos.x, y=end_pos.y))

        self.dragging_wire = None
        self._on_change()

    def update_wire_preview(self, pos: Point) -> None:
        """Update the preview end position of a wire being drawn."""
        if not self.dragging_wire or not self.dragging_wire.path:
            return

        nearest = self._circuit.find_nearest_connection_point(pos, self.SNAP_DISTANCE)

        if nearest:
            _, conn_point, _ = nearest
            end_pos = Point(x=conn_point.position.x, y=conn_point.position.y)
        else:
            last_point = self.dragging_wire.path[-1]
            end_pos = self._snap_to_orthogonal(
                pos, Point(x=last_point.x, y=last_point.y)
            )

        self.dragging_wire.end.position = end_pos
        self._on_change()

    def cancel_wire(self) -> None:
        """Cancel wire drawing (called on Esc)."""
        if self.dragging_wire:
            self._circuit.wires.remove(self.dragging_wire)
            self.dragging_wire = None
            self._on_change()

    # === Wire Corner Dragging ===

    def check_corner_hit(self, pos: Point) -> bool:
        """Check if position hits a draggable wire corner.

        Returns True and starts dragging if a corner was hit.
        """
        for wire in self._circuit.wires:
            for i, point in enumerate(wire.path):
                # Skip first and last points (connected to components)
                if i == 0 or i == len(wire.path) - 1:
                    continue
                dist = ((pos.x - point.x) ** 2 + (pos.y - point.y) ** 2) ** 0.5
                if dist <= self.WIRE_CORNER_HIT_RADIUS:
                    self.dragging_wire_corner = (wire.id, i)
                    return True
        return False

    def update_corner_position(self, pos: Point) -> None:
        """Update position of a wire corner being dragged."""
        if not self.dragging_wire_corner:
            return

        wire_id, corner_idx = self.dragging_wire_corner
        for wire in self._circuit.wires:
            if wire.id == wire_id:
                self._drag_corner(wire, corner_idx, pos)
                self._on_change()
                return

    def _drag_corner(self, wire: Wire, corner_idx: int, pos: Point) -> None:
        """Handle dragging a specific wire corner with orthogonal constraints."""
        if not (0 < corner_idx < len(wire.path) - 1):
            return

        is_near_start = corner_idx == 1
        is_near_end = corner_idx == len(wire.path) - 2
        prev_point = wire.path[corner_idx - 1]
        next_point = wire.path[corner_idx + 1]

        if is_near_start and is_near_end:
            # Only 3 points - L-shape between fixed endpoints
            dx = abs(pos.x - prev_point.x)
            dy = abs(pos.y - prev_point.y)
            if dx < dy:
                wire.path[corner_idx].x = prev_point.x
                wire.path[corner_idx].y = next_point.y
            else:
                wire.path[corner_idx].y = prev_point.y
                wire.path[corner_idx].x = next_point.x
        elif is_near_end:
            # Near end: propagate changes backward
            prev_seg_horiz = self._is_segment_horizontal(wire, corner_idx - 1)
            next_seg_horiz = not prev_seg_horiz

            if next_seg_horiz:
                wire.path[corner_idx].y = next_point.y
                wire.path[corner_idx].x = pos.x
            else:
                wire.path[corner_idx].x = next_point.x
                wire.path[corner_idx].y = pos.y

            # Propagate backward from corner to start
            for i in range(corner_idx - 1, 0, -1):
                seg_horiz = self._is_segment_horizontal(wire, i)
                if seg_horiz:
                    wire.path[i].y = wire.path[i + 1].y
                else:
                    wire.path[i].x = wire.path[i + 1].x
        else:
            # Near start or middle: propagate forward
            prev_seg_horiz = self._is_segment_horizontal(wire, corner_idx - 1)

            if prev_seg_horiz:
                wire.path[corner_idx].y = prev_point.y
                wire.path[corner_idx].x = pos.x
            else:
                wire.path[corner_idx].x = prev_point.x
                wire.path[corner_idx].y = pos.y

            # Propagate forward from corner to end
            for i in range(corner_idx + 1, len(wire.path) - 1):
                seg_horiz = self._is_segment_horizontal(wire, i - 1)
                if seg_horiz:
                    wire.path[i].y = wire.path[i - 1].y
                else:
                    wire.path[i].x = wire.path[i - 1].x

    def finish_corner_drag(self) -> None:
        """Finish dragging a wire corner."""
        self.dragging_wire_corner = None

    # === Orthogonal Segment Helpers ===

    def _get_first_segment_horizontal(self, wire: Wire) -> bool:
        """Determine if the first segment of a wire is horizontal."""
        if len(wire.path) < 2:
            return True
        p0, p1 = wire.path[0], wire.path[1]
        return abs(p1.x - p0.x) >= abs(p1.y - p0.y)

    def _is_segment_horizontal(self, wire: Wire, seg_idx: int) -> bool:
        """Check if segment at given index should be horizontal."""
        first_horiz = self._get_first_segment_horizontal(wire)
        return (seg_idx % 2 == 0) == first_horiz

    # === Component Connection Updates ===

    def update_connected_wires(self, component: Battery | LED) -> None:
        """Update wires connected to a component, maintaining orthogonal segments."""
        conn_points: list[ConnectionPoint] = []
        if isinstance(component, Battery):
            conn_points = [component.positive, component.negative]
        elif isinstance(component, LED):
            conn_points = [component.anode, component.cathode]

        for conn_point in conn_points:
            for wire in self._circuit.wires:
                if wire.start_connected_to == conn_point.id:
                    self._update_wire_start(wire, conn_point)
                elif wire.end_connected_to == conn_point.id:
                    self._update_wire_end(wire, conn_point)

    def _update_wire_start(self, wire: Wire, conn_point: ConnectionPoint) -> None:
        """Update wire when its start connection point moves."""
        wire.start.position = Point(x=conn_point.position.x, y=conn_point.position.y)
        if not wire.path:
            return

        wire.path[0].x = conn_point.position.x
        wire.path[0].y = conn_point.position.y

        if len(wire.path) > 1:
            second_point = wire.path[1]

            if len(wire.path) > 2:
                third_point = wire.path[2]
                segment_23_is_horizontal = abs(third_point.x - second_point.x) > abs(
                    third_point.y - second_point.y
                )

                if segment_23_is_horizontal:
                    second_point.x = wire.path[0].x
                else:
                    second_point.y = wire.path[0].y
            else:
                dx = abs(second_point.x - wire.path[0].x)
                dy = abs(second_point.y - wire.path[0].y)

                if dx > dy:
                    second_point.y = wire.path[0].y
                else:
                    second_point.x = wire.path[0].x

    def _update_wire_end(self, wire: Wire, conn_point: ConnectionPoint) -> None:
        """Update wire when its end connection point moves."""
        wire.end.position = Point(x=conn_point.position.x, y=conn_point.position.y)
        if not wire.path:
            return

        wire.path[-1].x = conn_point.position.x
        wire.path[-1].y = conn_point.position.y

        if len(wire.path) > 1:
            second_last_point = wire.path[-2]

            if len(wire.path) > 2:
                third_last_point = wire.path[-3]
                segment_is_horizontal = abs(
                    second_last_point.x - third_last_point.x
                ) > abs(second_last_point.y - third_last_point.y)

                if segment_is_horizontal:
                    second_last_point.x = wire.path[-1].x
                else:
                    second_last_point.y = wire.path[-1].y
            else:
                dx = abs(wire.path[-1].x - second_last_point.x)
                dy = abs(wire.path[-1].y - second_last_point.y)

                if dx > dy:
                    second_last_point.y = wire.path[-1].y
                else:
                    second_last_point.x = wire.path[-1].x

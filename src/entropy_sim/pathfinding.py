"""Wire path finding for aesthetic circuit routing."""

import heapq
from dataclasses import dataclass, field
from typing import TYPE_CHECKING

from .models import Point, WirePoint

if TYPE_CHECKING:
    from .models import Circuit


@dataclass(order=True)
class _Node:
    """Node for A* pathfinding."""

    f_cost: float
    g_cost: float = field(compare=False)
    x: float = field(compare=False)
    y: float = field(compare=False)
    parent: "_Node | None" = field(compare=False, default=None)


# Grid resolution for pathfinding
GRID_SIZE = 20
# Padding around obstacles
OBSTACLE_PADDING = 10
# Cost for turning (encourages straighter paths)
TURN_COST = 50
# Cost for being near existing wires (discourages overlap)
WIRE_PROXIMITY_COST = 100


def find_wire_path(
    start: Point,
    end: Point,
    circuit: "Circuit | None" = None,
    current_wire_id: str | None = None,
) -> list[WirePoint]:
    """
    Calculate an aesthetically pleasing wire path between two points.

    Uses A* pathfinding with obstacle avoidance for components and
    penalty costs for paths near existing wires.

    Args:
        start: Starting point of the wire
        end: Ending point of the wire
        circuit: Circuit containing obstacles (batteries, LEDs, wires)
        current_wire_id: ID of current wire being drawn (to exclude from obstacles)

    Returns:
        List of WirePoint forming the path
    """
    # Collect obstacles from circuit
    obstacles: list[tuple[float, float, float, float]] = []
    wire_segments: list[tuple[float, float, float, float]] = []

    if circuit:
        # Add batteries and LEDs as obstacles
        for battery in circuit.batteries:
            bounds = battery.get_bounds()
            # Add padding around obstacles
            obstacles.append(
                (
                    bounds[0] - OBSTACLE_PADDING,
                    bounds[1] - OBSTACLE_PADDING,
                    bounds[2] + OBSTACLE_PADDING,
                    bounds[3] + OBSTACLE_PADDING,
                )
            )

        for led in circuit.leds:
            bounds = led.get_bounds()
            obstacles.append(
                (
                    bounds[0] - OBSTACLE_PADDING,
                    bounds[1] - OBSTACLE_PADDING,
                    bounds[2] + OBSTACLE_PADDING,
                    bounds[3] + OBSTACLE_PADDING,
                )
            )

        # Collect existing wire segments (for proximity penalty)
        for wire in circuit.wires:
            if current_wire_id and str(wire.id) == current_wire_id:
                continue
            if len(wire.path) >= 2:
                for i in range(len(wire.path) - 1):
                    wire_segments.append(
                        (
                            wire.path[i].x,
                            wire.path[i].y,
                            wire.path[i + 1].x,
                            wire.path[i + 1].y,
                        )
                    )

    # Check if direct path is possible (no obstacles)
    if not obstacles or not _path_blocked(start, end, obstacles):
        return _simple_orthogonal_path(start, end)

    # Use A* for complex routing
    path = _astar_path(start, end, obstacles, wire_segments)

    if path:
        return _simplify_path(path)

    # Fallback to simple path if A* fails
    return _simple_orthogonal_path(start, end)


def _simple_orthogonal_path(start: Point, end: Point) -> list[WirePoint]:
    """Create a simple L-shaped or Z-shaped orthogonal path."""
    path: list[WirePoint] = [WirePoint(x=start.x, y=start.y)]

    dx = end.x - start.x
    dy = end.y - start.y

    if abs(dx) < 10 or abs(dy) < 10:
        # Nearly aligned, direct connection
        pass
    else:
        # Z-shape through midpoint
        mid_x = start.x + dx / 2
        path.append(WirePoint(x=mid_x, y=start.y))
        path.append(WirePoint(x=mid_x, y=end.y))

    path.append(WirePoint(x=end.x, y=end.y))
    return path


def _path_blocked(
    start: Point, end: Point, obstacles: list[tuple[float, float, float, float]]
) -> bool:
    """Check if a simple L-path would be blocked by obstacles."""
    # Check L-shape: vertical then horizontal
    mid1 = (start.x, end.y)
    if _line_hits_obstacles(
        (start.x, start.y), mid1, obstacles
    ) or _line_hits_obstacles(mid1, (end.x, end.y), obstacles):
        # Try other L-shape: horizontal then vertical
        mid2 = (end.x, start.y)
        if _line_hits_obstacles(
            (start.x, start.y), mid2, obstacles
        ) or _line_hits_obstacles(mid2, (end.x, end.y), obstacles):
            return True
    return False


def _line_hits_obstacles(
    p1: tuple[float, float],
    p2: tuple[float, float],
    obstacles: list[tuple[float, float, float, float]],
) -> bool:
    """Check if a line segment intersects any obstacle."""
    for obs in obstacles:
        if _line_intersects_rect(p1, p2, obs):
            return True
    return False


def _line_intersects_rect(
    p1: tuple[float, float],
    p2: tuple[float, float],
    rect: tuple[float, float, float, float],
) -> bool:
    """Check if line segment intersects rectangle (min_x, min_y, max_x, max_y)."""
    min_x, min_y, max_x, max_y = rect

    # Line bounding box
    line_min_x = min(p1[0], p2[0])
    line_max_x = max(p1[0], p2[0])
    line_min_y = min(p1[1], p2[1])
    line_max_y = max(p1[1], p2[1])

    # Quick rejection
    if line_max_x < min_x or line_min_x > max_x:
        return False
    if line_max_y < min_y or line_min_y > max_y:
        return False

    # For orthogonal lines, bounding box overlap means intersection
    return True


def _point_in_obstacle(
    x: float, y: float, obstacles: list[tuple[float, float, float, float]]
) -> bool:
    """Check if a point is inside any obstacle."""
    for min_x, min_y, max_x, max_y in obstacles:
        if min_x <= x <= max_x and min_y <= y <= max_y:
            return True
    return False


def _distance_to_wire_segments(
    x: float, y: float, wire_segments: list[tuple[float, float, float, float]]
) -> float:
    """Calculate minimum distance from point to any existing wire segment."""
    if not wire_segments:
        return float("inf")

    min_dist = float("inf")
    for x1, y1, x2, y2 in wire_segments:
        dist = _point_to_segment_distance(x, y, x1, y1, x2, y2)
        min_dist = min(min_dist, dist)
    return min_dist


def _point_to_segment_distance(
    px: float, py: float, x1: float, y1: float, x2: float, y2: float
) -> float:
    """Calculate distance from point to line segment."""
    dx = x2 - x1
    dy = y2 - y1

    if dx == 0 and dy == 0:
        return ((px - x1) ** 2 + (py - y1) ** 2) ** 0.5

    t = max(0, min(1, ((px - x1) * dx + (py - y1) * dy) / (dx * dx + dy * dy)))
    proj_x = x1 + t * dx
    proj_y = y1 + t * dy

    return ((px - proj_x) ** 2 + (py - proj_y) ** 2) ** 0.5


def _astar_path(
    start: Point,
    end: Point,
    obstacles: list[tuple[float, float, float, float]],
    wire_segments: list[tuple[float, float, float, float]],
) -> list[WirePoint] | None:
    """A* pathfinding with orthogonal movement."""
    # Snap to grid
    start_x = round(start.x / GRID_SIZE) * GRID_SIZE
    start_y = round(start.y / GRID_SIZE) * GRID_SIZE
    end_x = round(end.x / GRID_SIZE) * GRID_SIZE
    end_y = round(end.y / GRID_SIZE) * GRID_SIZE

    # Directions: right, down, left, up
    directions = [(GRID_SIZE, 0), (0, GRID_SIZE), (-GRID_SIZE, 0), (0, -GRID_SIZE)]

    def heuristic(x: float, y: float) -> float:
        return abs(x - end_x) + abs(y - end_y)

    start_node = _Node(
        f_cost=heuristic(start_x, start_y), g_cost=0, x=start_x, y=start_y
    )

    open_set: list[_Node] = [start_node]
    visited: set[tuple[float, float]] = set()
    node_map: dict[tuple[float, float], _Node] = {(start_x, start_y): start_node}

    iterations = 0
    max_iterations = 5000  # Prevent infinite loops

    while open_set and iterations < max_iterations:
        iterations += 1
        current = heapq.heappop(open_set)

        if (current.x, current.y) in visited:
            continue

        visited.add((current.x, current.y))

        # Check if we reached the goal
        if abs(current.x - end_x) < GRID_SIZE and abs(current.y - end_y) < GRID_SIZE:
            # Reconstruct path
            path: list[WirePoint] = []
            node: _Node | None = current
            while node:
                path.append(WirePoint(x=node.x, y=node.y))
                node = node.parent
            path.reverse()

            # Add exact start and end points
            path[0] = WirePoint(x=start.x, y=start.y)
            path.append(WirePoint(x=end.x, y=end.y))
            return path

        # Get direction from parent (for turn cost)
        parent_dir: tuple[float, float] | None = None
        if current.parent:
            parent_dir = (
                current.x - current.parent.x,
                current.y - current.parent.y,
            )

        # Explore neighbors
        for dx, dy in directions:
            nx, ny = current.x + dx, current.y + dy

            if (nx, ny) in visited:
                continue

            # Check if blocked by obstacle
            if _point_in_obstacle(nx, ny, obstacles):
                continue

            # Check if line to neighbor crosses obstacle
            if _line_hits_obstacles((current.x, current.y), (nx, ny), obstacles):
                continue

            # Calculate cost
            move_cost = float(GRID_SIZE)

            # Add turn cost if changing direction
            if parent_dir and (dx, dy) != parent_dir:
                move_cost += TURN_COST

            # Add wire proximity cost
            wire_dist = _distance_to_wire_segments(nx, ny, wire_segments)
            if wire_dist < GRID_SIZE * 2:
                move_cost += WIRE_PROXIMITY_COST * (1 - wire_dist / (GRID_SIZE * 2))

            g_cost = current.g_cost + move_cost
            f_cost = g_cost + heuristic(nx, ny)

            # Check if we found a better path to this node
            if (nx, ny) in node_map:
                if g_cost >= node_map[(nx, ny)].g_cost:
                    continue

            new_node = _Node(f_cost=f_cost, g_cost=g_cost, x=nx, y=ny, parent=current)
            node_map[(nx, ny)] = new_node
            heapq.heappush(open_set, new_node)

    return None


def _simplify_path(path: list[WirePoint]) -> list[WirePoint]:
    """Remove redundant points from path (collinear points)."""
    if len(path) < 3:
        return path

    simplified: list[WirePoint] = [path[0]]

    for i in range(1, len(path) - 1):
        prev = simplified[-1]
        curr = path[i]
        next_pt = path[i + 1]

        # Check if points are collinear (same x or same y)
        same_x = abs(prev.x - curr.x) < 0.1 and abs(curr.x - next_pt.x) < 0.1
        same_y = abs(prev.y - curr.y) < 0.1 and abs(curr.y - next_pt.y) < 0.1

        if not same_x and not same_y:
            simplified.append(curr)

    simplified.append(path[-1])
    return simplified


def smooth_path(path: list[WirePoint], corner_radius: float = 5.0) -> list[WirePoint]:
    """
    Add smoothing to corners in the path.

    This can be used to create rounded corners for a more
    polished appearance.

    Args:
        path: Original path with sharp corners
        corner_radius: Radius for corner smoothing

    Returns:
        Path with additional points for smooth corners
    """
    if len(path) < 3:
        return path

    smoothed: list[WirePoint] = [path[0]]

    for i in range(1, len(path) - 1):
        prev_pt = path[i - 1]
        curr_pt = path[i]
        next_pt = path[i + 1]

        # Calculate vectors
        v1_x = curr_pt.x - prev_pt.x
        v1_y = curr_pt.y - prev_pt.y
        v2_x = next_pt.x - curr_pt.x
        v2_y = next_pt.y - curr_pt.y

        # Normalize and find points for smooth corner
        len1 = (v1_x * v1_x + v1_y * v1_y) ** 0.5
        len2 = (v2_x * v2_x + v2_y * v2_y) ** 0.5

        if len1 > 0 and len2 > 0:
            # Point before corner
            offset1 = min(corner_radius, len1 / 2)
            smoothed.append(
                WirePoint(
                    x=curr_pt.x - (v1_x / len1) * offset1,
                    y=curr_pt.y - (v1_y / len1) * offset1,
                )
            )

            # Point after corner
            offset2 = min(corner_radius, len2 / 2)
            smoothed.append(
                WirePoint(
                    x=curr_pt.x + (v2_x / len2) * offset2,
                    y=curr_pt.y + (v2_y / len2) * offset2,
                )
            )
        else:
            smoothed.append(curr_pt)

    smoothed.append(path[-1])
    return smoothed

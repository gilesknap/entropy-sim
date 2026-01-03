"""Wire path finding for aesthetic circuit routing."""

from .models import Point, WirePoint


def find_wire_path(
    start: Point,
    end: Point,
    obstacles: list[tuple[float, float, float, float]] | None = None,
) -> list[WirePoint]:
    """
    Calculate an aesthetically pleasing wire path between two points.

    Uses an orthogonal routing algorithm that creates paths with
    only horizontal and vertical segments, typical of circuit diagrams.

    Args:
        start: Starting point of the wire
        end: Ending point of the wire
        obstacles: List of rectangles (x, y, width, height) to avoid

    Returns:
        List of WirePoint forming the path
    """
    obstacles = obstacles or []

    # Simple orthogonal routing - creates an L-shaped or Z-shaped path
    path: list[WirePoint] = []

    # Start point
    path.append(WirePoint(x=start.x, y=start.y))

    dx = end.x - start.x
    dy = end.y - start.y

    # Determine the best routing strategy
    if abs(dx) < 10 and abs(dy) < 10:
        # Points are very close, direct connection
        pass
    elif abs(dx) < 10:
        # Nearly vertical alignment - direct vertical line
        pass
    elif abs(dy) < 10:
        # Nearly horizontal alignment - direct horizontal line
        pass
    else:
        # Need to route around - use Z-shaped routing
        # Determine if we should go horizontal first or vertical first
        # based on which creates a more balanced path

        mid_x = start.x + dx / 2
        mid_y = start.y + dy / 2

        # Check if a simple L-shape works (no obstacles)
        if not _path_intersects_obstacles(
            [(start.x, start.y), (start.x, end.y), (end.x, end.y)], obstacles
        ):
            # Vertical then horizontal (L-shape)
            path.append(WirePoint(x=start.x, y=end.y))
        elif not _path_intersects_obstacles(
            [(start.x, start.y), (end.x, start.y), (end.x, end.y)], obstacles
        ):
            # Horizontal then vertical (L-shape)
            path.append(WirePoint(x=end.x, y=start.y))
        else:
            # Z-shape routing through midpoint
            # Go horizontal to midpoint, then vertical, then horizontal to end
            path.append(WirePoint(x=mid_x, y=start.y))
            path.append(WirePoint(x=mid_x, y=end.y))

    # End point
    path.append(WirePoint(x=end.x, y=end.y))

    return path


def _path_intersects_obstacles(
    points: list[tuple[float, float]],
    obstacles: list[tuple[float, float, float, float]],
) -> bool:
    """Check if a path intersects any obstacles."""
    for i in range(len(points) - 1):
        p1 = points[i]
        p2 = points[i + 1]
        for obs in obstacles:
            if _line_intersects_rect(p1, p2, obs):
                return True
    return False


def _line_intersects_rect(
    p1: tuple[float, float],
    p2: tuple[float, float],
    rect: tuple[float, float, float, float],
) -> bool:
    """Check if a line segment intersects a rectangle."""
    x, y, w, h = rect
    # Simple bounding box check for orthogonal lines
    min_x = min(p1[0], p2[0])
    max_x = max(p1[0], p2[0])
    min_y = min(p1[1], p2[1])
    max_y = max(p1[1], p2[1])

    # Check if line bounding box intersects rectangle
    if max_x < x or min_x > x + w:
        return False
    if max_y < y or min_y > y + h:
        return False

    return True


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

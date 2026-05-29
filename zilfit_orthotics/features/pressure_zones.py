"""Geometric zone partitioning for plantar surface analysis.

Splits the foot into heel, midfoot, forefoot, and toe zones based on
y-axis fraction along the foot length. All labels are geometric only:
zone, region, segment. No reflexology or therapy terminology.
"""

import math
from typing import Dict, List, Tuple

from ..config import ZONE_BOUNDARIES
from ..coordinate_system import FootFrame


def partition_soles_by_geometry(
    point_cloud: list,
    frame: FootFrame,
) -> Dict[str, List[Tuple]]:
    """Split plantar surface points into geometric zones.

    Zones are defined by y-axis fraction of the total foot length:
        heel:    0.00 – 0.25
        midfoot: 0.25 – 0.55
        forefoot:0.55 – 0.85
        toes:    0.85 – 1.00

    Only points near the plantar surface (z < 5 mm in local frame) are included.

    Returns dict mapping zone name to list of global-coordinate points.
    """
    # Transform all points and compute foot-length y range
    local_pts = [(frame.transform_point(pt), pt) for pt in point_cloud]

    if not local_pts:
        return {zone: [] for zone in ZONE_BOUNDARIES}

    y_vals = [lp[0][1] for lp in local_pts]
    y_min, y_max = min(y_vals), max(y_vals)
    y_span = y_max - y_min
    if y_span < 1e-6:
        return {zone: [] for zone in ZONE_BOUNDARIES}

    zones = {zone: [] for zone in ZONE_BOUNDARIES}

    for (lx, ly, lz), global_pt in local_pts:
        if lz > 5.0:  # Not plantar surface
            continue
        fraction = (ly - y_min) / y_span
        for zone_name, (low, high) in ZONE_BOUNDARIES.items():
            if low <= fraction < high or (fraction == 1.0 and high == 1.0):
                zones[zone_name].append(global_pt)
                break

    return zones


def zone_centroids(zones: Dict[str, List[Tuple]]) -> Dict[str, Tuple]:
    """Compute geometric centroid for each zone.

    Returns dict mapping zone name to (cx, cy, cz) centroid tuple.
    Empty zones return (0, 0, 0).
    """
    centroids = {}
    for zone_name, points in zones.items():
        if not points:
            centroids[zone_name] = (0.0, 0.0, 0.0)
            continue

        n = len(points)
        cx = sum(p[0] for p in points) / n
        cy = sum(p[1] for p in points) / n
        cz = sum(p[2] for p in points) / n
        centroids[zone_name] = (round(cx, 2), round(cy, 2), round(cz, 2))

    return centroids


def zone_surface_area(points: List[Tuple]) -> float:
    """Approximate surface area of a point set using convex hull (2D projection).

    Projects points onto the XY plane and computes the convex hull area.
    Returns area in mm².
    """
    if len(points) < 3:
        return 0.0

    # Project to 2D
    pts_2d = [(p[0], p[1]) for p in points]
    hull = _convex_hull(pts_2d)

    if len(hull) < 3:
        return 0.0

    # Shoelace formula
    area = 0.0
    n = len(hull)
    for i in range(n):
        x1, y1 = hull[i]
        x2, y2 = hull[(i + 1) % n]
        area += x1 * y2 - x2 * y1

    return round(abs(area) / 2.0, 2)


def _convex_hull(points: List[Tuple[float, float]]) -> List[Tuple[float, float]]:
    """Monotone chain convex hull algorithm."""
    pts = sorted(set(points))
    if len(pts) <= 1:
        return pts

    def cross(o, a, b):
        return (a[0] - o[0]) * (b[1] - o[1]) - (a[1] - o[1]) * (b[0] - o[0])

    lower = []
    for p in pts:
        while len(lower) >= 2 and cross(lower[-2], lower[-1], p) <= 0:
            lower.pop()
        lower.append(p)

    upper = []
    for p in reversed(pts):
        while len(upper) >= 2 and cross(upper[-2], upper[-1], p) <= 0:
            upper.pop()
        upper.append(p)

    return lower[:-1] + upper[:-1]

"""Pure geometric arch characterization.

All outputs are numeric geometric measurements.
No clinical labels (pes planus, pes cavus, flat foot, high arch) are used.
"""

import math
from typing import List, Tuple

from ..config import ARCH_MIDFOOT_LOWER_Y, ARCH_MIDFOOT_UPPER_Y, ARCH_CONTACT_Z_THRESHOLD_MM
from ..coordinate_system import FootFrame


def arch_height_geometric(landmarks: dict, frame: FootFrame) -> float:
    """Geometric vertical distance from navicular landmark to plantar reference plane.

    The plantar reference plane is defined by the three lowest-contact landmarks:
    heel_center, met1_head, met5_head (approximating the ground plane).

    Returns height in mm.
    """
    if "navicular" not in landmarks:
        raise ValueError("Navicular landmark required for geometric arch height.")

    navicular = landmarks["navicular"]
    # Plantar plane: defined by heel_center, met1_head, met5_head
    heel = landmarks["heel_center"]
    met1 = landmarks["met1_head"]
    met5 = landmarks["met5_head"]

    # Plane normal via cross product of (met1-heel) × (met5-heel)
    v1 = (met1[0] - heel[0], met1[1] - heel[1], met1[2] - heel[2])
    v2 = (met5[0] - heel[0], met5[1] - heel[1], met5[2] - heel[2])
    normal = (
        v1[1] * v2[2] - v1[2] * v2[1],
        v1[2] * v2[0] - v1[0] * v2[2],
        v1[0] * v2[1] - v1[1] * v2[0],
    )
    norm_len = math.sqrt(normal[0]**2 + normal[1]**2 + normal[2]**2)
    if norm_len < 1e-9:
        return 0.0

    n = (normal[0] / norm_len, normal[1] / norm_len, normal[2] / norm_len)

    # Distance from navicular to plane
    d = abs(
        (navicular[0] - heel[0]) * n[0] +
        (navicular[1] - heel[1]) * n[1] +
        (navicular[2] - heel[2]) * n[2]
    )
    return round(d, 2)


def arch_contour_curvature(point_cloud: list, frame: FootFrame) -> list:
    """Compute curvature values along the medial longitudinal arch profile.

    Extracts points in the midfoot y-range near the medial edge (x > 0),
    sorts by y, and computes local curvature at each sampled point.

    Returns list of curvature values (1/radius in mm⁻¹).
    """
    local_points = []
    for pt in point_cloud:
        lp = frame.transform_point(pt)
        x, y, z = lp
        if ARCH_MIDFOOT_LOWER_Y <= y <= ARCH_MIDFOOT_UPPER_Y and x > 0:
            local_points.append((y, z))  # Profile: y vs z

    if len(local_points) < 5:
        return []

    local_points.sort(key=lambda p: p[0])

    # Sample uniformly along y
    curvatures = []
    step = max(1, len(local_points) // 20)
    for i in range(2, len(local_points) - 2, step):
        y0, z0 = local_points[i - 2]
        y1, z1 = local_points[i - 1]
        y2, z2 = local_points[i]
        y3, z3 = local_points[i + 1]
        y4, z4 = local_points[i + 2]
        curvature = _five_point_curvature(y0, z0, y1, z1, y2, z2, y3, z3, y4, z4)
        curvatures.append(round(curvature, 6))

    return curvatures


def arch_contact_ratio(point_cloud: list, frame: FootFrame) -> float:
    """Fraction of midfoot points within a z-threshold of the plantar plane.

    Points in the midfoot y-range whose z-coordinate is below the threshold
    are considered in contact with the ground plane.

    Returns ratio 0.0–1.0.
    """
    in_contact = 0
    total = 0

    for pt in point_cloud:
        lp = frame.transform_point(pt)
        x, y, z = lp
        if ARCH_MIDFOOT_LOWER_Y <= y <= ARCH_MIDFOOT_UPPER_Y:
            total += 1
            if z <= ARCH_CONTACT_Z_THRESHOLD_MM:
                in_contact += 1

    if total == 0:
        return 0.0

    return round(in_contact / total, 4)


def _five_point_curvature(y0, z0, y1, z1, y2, z2, y3, z3, y4, z4) -> float:
    """Estimate curvature at (y2, z2) using 5-point finite difference.

    Curvature = |z''| / (1 + z'²)^(3/2)
    where z' and z'' are computed via central differences.
    """
    h = y2 - y1
    if abs(h) < 1e-9:
        return 0.0

    zp = (z3 - z1) / (2 * h)
    zpp = (z3 - 2 * z2 + z1) / (h * h)

    denom = (1 + zp * zp) ** 1.5
    if denom < 1e-9:
        return 0.0

    return abs(zpp) / denom

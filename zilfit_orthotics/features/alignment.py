"""Geometric axis relationships without diagnosis.

All outputs are numeric offsets, deviations, and ratios.
No pronation, supination, or gait abnormality labels are used.
"""

import math
from typing import List, Tuple, Dict

from ..config import ARCH_MIDFOOT_LOWER_Y, ARCH_MIDFOOT_UPPER_Y
from ..coordinate_system import FootFrame


def heel_toe_alignment_offset(landmarks: dict, frame: FootFrame) -> float:
    """Geometric angular offset (degrees) between heel-to-toe axis and foot frame midline.

    This is purely geometric. It measures how the heel-to-toe vector deviates
    from the anteroposterior axis of the foot coordinate frame.
    """
    hta = frame.heel_to_toe_axis(landmarks)
    dot = hta[0] * frame.y_axis[0] + hta[1] * frame.y_axis[1] + hta[2] * frame.y_axis[2]
    dot = max(-1.0, min(1.0, dot))
    return round(math.degrees(math.acos(dot)), 2)


def midline_curvature_profile(point_cloud: list, frame: FootFrame) -> list:
    """Lateral (x) deviation of dorsal midline points along the foot's y-axis.

    Extracts the highest-z point in narrow x-bands near the midline at each y-slice,
    recording the x-offset from true midline. Returns list of x-offsets in mm.

    A purely geometric measurement. Does not indicate any clinical condition.
    """
    # Find midline x-range: x values of met1 and met5 transformed
    met1_local = frame.transform_point(point_cloud[0]) if point_cloud else None
    # Instead, compute from the point cloud directly

    local_points = [(frame.transform_point(pt), pt) for pt in point_cloud]
    local_points.sort(key=lambda t: t[0][1])  # Sort by y

    offsets = []
    window_size = max(1, len(local_points) // 30)

    for i in range(0, len(local_points) - window_size, window_size):
        window = local_points[i : i + window_size]
        y_center = sum(p[0][1] for p in window) / len(window)
        if not (ARCH_MIDFOOT_LOWER_Y <= y_center <= ARCH_MIDFOOT_UPPER_Y):
            continue

        # Find the highest-z point in the window (dorsal surface)
        highest = max(window, key=lambda p: p[0][2])
        x, y, z = highest[0]
        offsets.append(round(x, 2))

    return offsets


def left_right_symmetry_ratio(
    left_landmarks: dict,
    right_landmarks: dict,
) -> Dict[str, float]:
    """Geometric ratio of key dimensions between left and right feet.

    Ratio = left_value / right_value.
    1.0 = symmetric. Deviation from 1.0 = geometric asymmetry.

    Measured dimensions: foot length, foot width, arch height.

    No clinical interpretation is assigned to asymmetry values.
    """
    from .foot_dimensions import foot_length_geometric, foot_width_geometric
    from .arch_geometry import arch_height_geometric

    ratios = {}

    try:
        ll = foot_length_geometric(left_landmarks)
        rl = foot_length_geometric(right_landmarks)
        ratios["length_ratio"] = round(ll / rl, 4) if rl > 0 else None
    except Exception:
        ratios["length_ratio"] = None

    try:
        lw = foot_width_geometric(left_landmarks)
        rw = foot_width_geometric(right_landmarks)
        ratios["width_ratio"] = round(lw / rw, 4) if rw > 0 else None
    except Exception:
        ratios["width_ratio"] = None

    try:
        lf = FootFrame.from_landmarks(left_landmarks)
        rf = FootFrame.from_landmarks(right_landmarks)
        la = arch_height_geometric(left_landmarks, lf)
        ra = arch_height_geometric(right_landmarks, rf)
        ratios["arch_height_ratio"] = round(la / ra, 4) if ra > 0 else None
    except Exception:
        ratios["arch_height_ratio"] = None

    return ratios

"""Pure geometric foot measurements.

All outputs are numeric values in mm.
No clinical labels (bunion, hallux valgus, splay foot) are used.
"""

import math
from typing import Dict, Tuple


def _distance(a: tuple, b: tuple) -> float:
    """Euclidean distance in 3D."""
    return math.sqrt((a[0] - b[0])**2 + (a[1] - b[1])**2 + (a[2] - b[2])**2)


def foot_length_geometric(landmarks: Dict[str, Tuple]) -> float:
    """Geometric foot length: heel_center to hallux_tip distance in mm.

    Falls back to heel_center → met1_head if hallux_tip is missing.
    """
    heel = landmarks.get("heel_center")
    toe = landmarks.get("hallux_tip") or landmarks.get("met1_head")

    if not heel:
        raise ValueError("heel_center landmark required for foot length.")
    if not toe:
        raise ValueError("hallux_tip or met1_head landmark required for foot length.")

    return round(_distance(heel, toe), 2)


def foot_width_geometric(landmarks: Dict[str, Tuple]) -> float:
    """Geometric foot width: distance between met1_head and met5_head in mm."""
    met1 = landmarks.get("met1_head")
    met5 = landmarks.get("met5_head")

    if not met1 or not met5:
        raise ValueError("met1_head and met5_head landmarks required for foot width.")

    return round(_distance(met1, met5), 2)


def forefoot_width_geometric(landmarks: Dict[str, Tuple]) -> float:
    """Geometric forefoot width: same as foot width, at metatarsal heads.

    Provided as a distinct measurement for compatibility with zone-based analysis.
    """
    return foot_width_geometric(landmarks)


def heel_width_geometric(landmarks: Dict[str, Tuple]) -> float:
    """Geometric heel width: distance between calcaneus_lateral and calcaneus_medial.

    Falls back to lateral_malleolus–medial_malleolus if calcaneus landmarks missing.
    Returns None if neither pair is available.
    """
    cl = landmarks.get("calcaneus_lateral")
    cm = landmarks.get("calcaneus_medial")

    if cl and cm:
        return round(_distance(cl, cm), 2)

    lm = landmarks.get("lateral_malleolus")
    mm = landmarks.get("medial_malleolus")

    if lm and mm:
        return round(_distance(lm, mm), 2)

    return None

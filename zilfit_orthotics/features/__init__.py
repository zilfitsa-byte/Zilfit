"""Feature extraction: geometric properties of the foot from landmarks and point cloud."""

from typing import Optional

from .arch_geometry import arch_height_geometric, arch_contour_curvature, arch_contact_ratio
from .foot_dimensions import (
    foot_length_geometric,
    foot_width_geometric,
    forefoot_width_geometric,
    heel_width_geometric,
)
from .alignment import (
    heel_toe_alignment_offset,
    midline_curvature_profile,
    left_right_symmetry_ratio,
)
from .pressure_zones import partition_soles_by_geometry, zone_centroids, zone_surface_area
from ..coordinate_system import FootFrame


def compute_all_features(
    landmarks: dict,
    point_cloud: Optional[list] = None,
    frame: Optional[FootFrame] = None,
) -> dict:
    """Compute all geometric features for a foot.

    Args:
        landmarks: Dict of landmark_label → (x, y, z).
        point_cloud: Optional list of (x, y, z) point cloud vertices.
        frame: Optional pre-built FootFrame. Created from landmarks if omitted.

    Returns:
        Dictionary of geometric measurements keyed by feature name.
    """
    if frame is None:
        frame = FootFrame.from_landmarks(landmarks)

    result = {}

    # Dimensions
    result["foot_length_mm"] = foot_length_geometric(landmarks)
    result["foot_width_mm"] = foot_width_geometric(landmarks)
    result["forefoot_width_mm"] = forefoot_width_geometric(landmarks)
    result["heel_width_mm"] = heel_width_geometric(landmarks)

    # Arch
    result["arch_height_geometric_mm"] = arch_height_geometric(landmarks, frame)

    # Alignment
    result["alignment_offset_deg"] = heel_toe_alignment_offset(landmarks, frame)

    # Point cloud features (if provided)
    if point_cloud:
        result["arch_curvature"] = arch_contour_curvature(point_cloud, frame)
        result["arch_contact_ratio"] = arch_contact_ratio(point_cloud, frame)
        result["midline_curvature"] = midline_curvature_profile(point_cloud, frame)
        zones = partition_soles_by_geometry(point_cloud, frame)
        result["zone_centroids"] = zone_centroids(zones)
        result["zone_surface_areas_mm2"] = {
            zone: zone_surface_area(pts) for zone, pts in zones.items()
        }

    return result

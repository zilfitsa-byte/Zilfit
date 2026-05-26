"""Entry point for zilfit_orthotics geometric analysis pipeline.

Usage:
    python -m zilfit_orthotics.run landmarks.json [point_cloud.stl]

Or programmatically:
    from zilfit_orthotics.run import process
    result = process("landmarks.json", "scan.stl")
"""

import json
import sys
from typing import Optional

from .intake import load_landmarks, load_point_cloud
from .coordinate_system import FootFrame
from .features import compute_all_features


def process(
    landmarks_path: str,
    point_cloud_path: Optional[str] = None,
) -> dict:
    """Run the full geometric analysis pipeline.

    Args:
        landmarks_path: Path to landmarks JSON file.
        point_cloud_path: Optional path to STL/PLY point cloud.

    Returns:
        Dictionary of all geometric measurements.
    """
    landmarks = load_landmarks(landmarks_path)
    frame = FootFrame.from_landmarks(landmarks)

    point_cloud = None
    if point_cloud_path:
        point_cloud = load_point_cloud(point_cloud_path)

    features = compute_all_features(landmarks, point_cloud, frame)

    return {
        "landmarks_loaded": len(landmarks),
        "point_cloud_vertices": len(point_cloud) if point_cloud else 0,
        "frame_origin": frame.origin,
        "features": features,
    }


def _format_output(result: dict) -> str:
    """Format results as readable text."""
    lines = []
    lines.append("=" * 50)
    lines.append("ZILFIT Orthotics — Geometric Analysis Report")
    lines.append("=" * 50)
    lines.append(f"Landmarks loaded: {result['landmarks_loaded']}")
    lines.append(f"Point cloud vertices: {result['point_cloud_vertices']}")
    lines.append(f"Frame origin (heel_center): {result['frame_origin']}")
    lines.append("-" * 50)

    feats = result.get("features", {})
    for key, value in feats.items():
        if value is not None:
            lines.append(f"  {key}: {value}")

    lines.append("=" * 50)
    return "\n".join(lines)


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python -m zilfit_orthotics.run <landmarks.json> [point_cloud.stl]")
        sys.exit(1)

    lm_path = sys.argv[1]
    pc_path = sys.argv[2] if len(sys.argv) > 2 else None

    try:
        result = process(lm_path, pc_path)
        print(_format_output(result))
    except (ValueError, FileNotFoundError) as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)

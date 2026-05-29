"""Landmark and point cloud intake with geometric-only validation.

No orientation flipping is performed. Input coordinates are preserved exactly.
All error messages use geometric terminology only.
"""

import json
import os
from typing import Optional, Union, List, Tuple

from .config import COORDINATE_BOUNDS, MINIMUM_LANDMARKS, REFERENCE_LANDMARK_LABELS


def load_landmarks(path: str) -> dict:
    """Load landmark coordinates from a JSON file.

    Expected JSON format: {"landmark_name": [x, y, z], ...}

    Args:
        path: Absolute or relative path to a landmarks JSON file.

    Returns:
        Dictionary mapping landmark label strings to (x, y, z) tuples.

    Raises:
        FileNotFoundError: Path does not exist.
        ValueError: File contents invalid or insufficient landmarks.
    """
    if not os.path.isfile(path):
        raise FileNotFoundError(f"Landmark file not found: {path}")

    with open(path, "r") as f:
        try:
            data = json.load(f)
        except json.JSONDecodeError as e:
            raise ValueError(f"Landmark file is not valid JSON: {e}")

    if not isinstance(data, dict):
        raise ValueError("Landmark file must contain a JSON object mapping names to coordinates.")

    landmarks = {}
    for label, coords in data.items():
        if not isinstance(coords, (list, tuple)) or len(coords) != 3:
            raise ValueError(f"Landmark '{label}' must be a list of 3 numeric values [x, y, z].")
        try:
            x, y, z = float(coords[0]), float(coords[1]), float(coords[2])
        except (TypeError, ValueError):
            raise ValueError(f"Landmark '{label}' coordinates must be numeric.")
        landmarks[label] = (x, y, z)

    validate_landmarks(landmarks)
    return landmarks


def validate_landmarks(landmarks: dict) -> bool:
    """Validate landmarks against geometric bounds.

    Checks:
        - At least MINIMUM_LANDMARKS present.
        - All coordinates within COORDINATE_BOUNDS.
        - Required reference labels are present.

    Args:
        landmarks: Dict of label → (x, y, z).

    Returns:
        True if valid.

    Raises:
        ValueError: Any geometric validation failure.
    """
    if len(landmarks) < MINIMUM_LANDMARKS:
        raise ValueError(
            f"Insufficient landmarks: {len(landmarks)} provided, "
            f"need at least {MINIMUM_LANDMARKS}."
        )

    required = {"heel_center", "met1_head", "met5_head", "hallux_tip"}
    missing = required - set(landmarks.keys())
    if missing:
        raise ValueError(
            f"Missing required geometric landmarks: {', '.join(sorted(missing))}."
        )

    bx = COORDINATE_BOUNDS["x"]
    by = COORDINATE_BOUNDS["y"]
    bz = COORDINATE_BOUNDS["z"]

    for label, (x, y, z) in landmarks.items():
        if not (bx[0] <= x <= bx[1]):
            raise ValueError(
                f"Landmark '{label}' x={x:.1f} mm outside geometric bounds "
                f"[{bx[0]:.0f}, {bx[1]:.0f}] mm."
            )
        if not (by[0] <= y <= by[1]):
            raise ValueError(
                f"Landmark '{label}' y={y:.1f} mm outside geometric bounds "
                f"[{by[0]:.0f}, {by[1]:.0f}] mm."
            )
        if not (bz[0] <= z <= bz[1]):
            raise ValueError(
                f"Landmark '{label}' z={z:.1f} mm outside geometric bounds "
                f"[{bz[0]:.0f}, {bz[1]:.0f}] mm."
            )

    return True


def load_point_cloud(path: str) -> list:
    """Load a point cloud from an STL (ASCII) or PLY (ASCII) file.

    Supports only ASCII-format STL and PLY files.
    Returns list of (x, y, z) tuples.

    Args:
        path: Path to an ASCII STL or PLY file.

    Returns:
        List of (x, y, z) point tuples.

    Raises:
        FileNotFoundError: Path does not exist.
        ValueError: Unsupported format or invalid geometry.
    """
    if not os.path.isfile(path):
        raise FileNotFoundError(f"Point cloud file not found: {path}")

    ext = os.path.splitext(path)[1].lower()

    if ext == ".stl":
        points = _read_ascii_stl(path)
    elif ext == ".ply":
        points = _read_ascii_ply(path)
    else:
        raise ValueError(f"Unsupported point cloud format: {ext}. Supported: .stl, .ply")

    if not points:
        raise ValueError("Point cloud contains no vertices.")

    _validate_point_cloud_bounds(points)
    return points


def _read_ascii_stl(path: str) -> list:
    """Read vertices from an ASCII STL file."""
    points = []
    with open(path, "r") as f:
        lines = f.readlines()

    i = 0
    while i < len(lines):
        stripped = lines[i].strip()
        if stripped.startswith("vertex "):
            parts = stripped.split()
            if len(parts) >= 4:
                try:
                    x, y, z = float(parts[1]), float(parts[2]), float(parts[3])
                    points.append((x, y, z))
                except ValueError:
                    pass
        i += 1

    return points


def _read_ascii_ply(path: str) -> list:
    """Read vertices from an ASCII PLY file."""
    points = []
    in_header = True
    vertex_count = 0
    vertex_read = 0
    has_z = False

    with open(path, "r") as f:
        for line in f:
            stripped = line.strip()
            if in_header:
                if stripped.startswith("element vertex "):
                    try:
                        vertex_count = int(stripped.split()[-1])
                    except ValueError:
                        raise ValueError("PLY header: could not parse vertex count.")
                elif stripped.startswith("property ") and "z" in stripped.split()[-1]:
                    has_z = True
                elif stripped == "end_header":
                    in_header = False
                continue

            # Body
            if vertex_read >= vertex_count:
                break

            parts = stripped.split()
            if len(parts) >= 3:
                try:
                    x, y, z_val = float(parts[0]), float(parts[1]), float(parts[2]) if len(parts) >= 3 and has_z else 0.0
                    points.append((x, y, z_val))
                    vertex_read += 1
                except ValueError:
                    pass

    return points


def _validate_point_cloud_bounds(points: list) -> None:
    """Verify all points fall within COORDINATE_BOUNDS."""
    bx = COORDINATE_BOUNDS["x"]
    by = COORDINATE_BOUNDS["y"]
    bz = COORDINATE_BOUNDS["z"]

    out_of_bounds = 0
    for x, y, z in points:
        if not (bx[0] <= x <= bx[1]) or not (by[0] <= y <= by[1]) or not (bz[0] <= z <= bz[1]):
            out_of_bounds += 1

    if out_of_bounds > len(points) * 0.5:
        raise ValueError(
            f"More than 50% of point cloud vertices ({out_of_bounds}/{len(points)}) "
            "fall outside geometric coordinate bounds. Check input coordinate frame."
        )

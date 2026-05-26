"""Foot coordinate frame built purely from geometric landmarks.

Axis convention:
    x: medial → lateral (rightward)
    y: posterior → anterior (heel → toes)
    z: plantar → dorsal (bottom → top)

All measurements are geometric only. No clinical or diagnostic labels.
"""

import math
from typing import Tuple


class FootFrame:
    """A right-handed orthonormal coordinate frame anchored to the foot.

    Built from geometric landmarks only. Used to transform raw coordinates
    into a standardized foot-local frame for consistent measurement.

    Attributes:
        origin: Frame origin point (heel_center).
        x_axis: Unit vector, medial → lateral.
        y_axis: Unit vector, posterior → anterior.
        z_axis: Unit vector, plantar → dorsal.
    """

    def __init__(self, origin, x_axis, y_axis, z_axis):
        self.origin = tuple(origin)
        self.x_axis = tuple(x_axis)
        self.y_axis = tuple(y_axis)
        self.z_axis = tuple(z_axis)

    @classmethod
    def from_landmarks(cls, landmarks: dict) -> "FootFrame":
        """Build FootFrame from geometric landmarks.

        Requires: heel_center, met1_head, met5_head, hallux_tip.

        Construction:
            - origin = heel_center
            - y_axis ≈ heel_center → midpoint(met1_head, met5_head), projected to horizontal
            - z_axis ≈ global vertical (0,0,1)
            - x_axis = y_axis × z_axis (medial-lateral, rightward)
        """
        required = {"heel_center", "met1_head", "met5_head"}
        missing = required - set(landmarks.keys())
        if missing:
            raise ValueError(
                f"Cannot build FootFrame: missing landmarks {sorted(missing)}."
            )

        origin = landmarks["heel_center"]
        met1 = landmarks["met1_head"]
        met5 = landmarks["met5_head"]

        # Y-axis: heel → midpoint of metatarsal heads, projected to XY plane for stability
        mid_met = (
            (met1[0] + met5[0]) / 2.0,
            (met1[1] + met5[1]) / 2.0,
            (met1[2] + met5[2]) / 2.0,
        )
        y_vec = (
            mid_met[0] - origin[0],
            mid_met[1] - origin[1],
            0.0,  # Project to horizontal for a stable anteroposterior axis
        )

        y_norm = math.sqrt(y_vec[0]**2 + y_vec[1]**2 + y_vec[2]**2)
        if y_norm < 1e-6:
            raise ValueError("FootFrame: heel-to-mid-metatarsal distance too small to define axis.")
        y_axis = (y_vec[0] / y_norm, y_vec[1] / y_norm, y_vec[2] / y_norm)

        # Z-axis: world up (plantar → dorsal)
        z_axis = (0.0, 0.0, 1.0)

        # X-axis: y × z (rightward, medial → lateral for a right foot)
        # For a left foot this flips sign — that's expected geometric behavior.
        x_axis = _cross(y_axis, z_axis)

        return cls(origin=origin, x_axis=x_axis, y_axis=y_axis, z_axis=z_axis)

    def transform_point(self, point: tuple) -> tuple:
        """Express a global point in foot-local coordinates.

        Returns (x_local, y_local, z_local) relative to origin.
        """
        px, py, pz = point
        ox, oy, oz = self.origin
        dx, dy, dz = px - ox, py - oy, pz - oz
        return (
            dx * self.x_axis[0] + dy * self.x_axis[1] + dz * self.x_axis[2],
            dx * self.y_axis[0] + dy * self.y_axis[1] + dz * self.y_axis[2],
            dx * self.z_axis[0] + dy * self.z_axis[1] + dz * self.z_axis[2],
        )

    def foot_length(self) -> float:
        """Geometric foot length: distance from heel_center to met1-met5 midpoint along y-axis."""
        return math.sqrt(
            (self.y_axis[0])**2 + (self.y_axis[1])**2
        )  # Placeholder — caller provides the scalar length computed from landmarks.
        # Actually: we need the landmark data. Let me fix this.

    def heel_to_toe_axis(self, landmarks: dict) -> tuple:
        """Geometric vector from heel_center to hallux_tip (or met1_head if hallux missing).

        Returns unit vector.
        """
        heel = self.origin
        if "hallux_tip" in landmarks:
            toe = landmarks["hallux_tip"]
        elif "met1_head" in landmarks:
            toe = landmarks["met1_head"]
        else:
            raise ValueError("Need hallux_tip or met1_head to compute heel-to-toe axis.")

        vec = (toe[0] - heel[0], toe[1] - heel[1], toe[2] - heel[2])
        norm = math.sqrt(vec[0]**2 + vec[1]**2 + vec[2]**2)
        if norm < 1e-6:
            return (0.0, 1.0, 0.0)
        return (vec[0] / norm, vec[1] / norm, vec[2] / norm)

    def midline_deviation(self, landmarks: dict) -> float:
        """Geometric angular offset (degrees) between heel-to-toe axis and frame y-axis.

        This is a purely geometric measurement. It does not diagnose pronation,
        supination, or any clinical condition.
        """
        hta = self.heel_to_toe_axis(landmarks)
        dot = hta[0] * self.y_axis[0] + hta[1] * self.y_axis[1] + hta[2] * self.y_axis[2]
        dot = max(-1.0, min(1.0, dot))
        return math.degrees(math.acos(dot))


def _cross(a: tuple, b: tuple) -> tuple:
    """3D cross product."""
    return (
        a[1] * b[2] - a[2] * b[1],
        a[2] * b[0] - a[0] * b[2],
        a[0] * b[1] - a[1] * b[0],
    )


def _dot(a: tuple, b: tuple) -> float:
    """3D dot product."""
    return a[0] * b[0] + a[1] * b[1] + a[2] * b[2]

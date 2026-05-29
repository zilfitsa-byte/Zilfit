"""
ZILFIT STL Generator Runtime — From GeometryPlan to Mesh Configuration

Consumes output from zilfit_geometry_runtime.py and produces:
  - implicit gyroid field parameters
  - voxel grid settings
  - mesh generation configuration
  - export metadata
  - STL readiness score (0.0 → 1.0)

Pure Python. No Blender. No GUI. No binary STL in this phase.
Only mathematical field definitions and mesh config.

No Telegram. No agents. No governance.
"""

from __future__ import annotations

import json
import math
import uuid
from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------
_PROJECT_ROOT = Path(__file__).resolve().parent.parent
_SCHEMAS_DIR = _PROJECT_ROOT / "schemas"
_STL_SCHEMA_PATH = _SCHEMAS_DIR / "stl_generation.schema.json"

# ---------------------------------------------------------------------------
# Hard engineering constraints (must match geometry_runtime)
# ---------------------------------------------------------------------------
MIN_WALL_THICKNESS_MM = 0.6
DENSITY_MIN = 0.15
DENSITY_MAX = 0.45
GYROID_CELL_SIZE_MIN_MM = 5.0
GYROID_CELL_SIZE_MAX_MM = 7.0

# ---------------------------------------------------------------------------
# Gyroid implicit surface equation constants
# ---------------------------------------------------------------------------
# sin(x/a)·cos(y/b) + sin(y/b)·cos(z/c) + sin(z/c)·cos(x/a) = t
# where a, b, c are cell dimensions, t is threshold (density-dependent)

GYROID_PERIODS = 3  # standard gyroid: 3 sinusoidal terms
GYROID_DEFAULT_THRESHOLD_MIN = -0.8  # t_min for density_max (solid)
GYROID_DEFAULT_THRESHOLD_MAX = 0.8   # t_max for density_min (porous)

# ---------------------------------------------------------------------------
# Insole bounding box defaults (mm)
# ---------------------------------------------------------------------------
DEFAULT_INSOLE_LENGTH_MM = 260.0
DEFAULT_INSOLE_WIDTH_MM = 95.0
DEFAULT_INSOLE_THICKNESS_MM = 6.0

# Voxel resolution (mm per voxel)
VOXEL_RESOLUTION_FINE = 0.1
VOXEL_RESOLUTION_COARSE = 0.5
VOXEL_RESOLUTION_DEFAULT = 0.25

# ---------------------------------------------------------------------------
# Exceptions
# ---------------------------------------------------------------------------
class STLGenerationError(Exception):
    """Raised when STL generation cannot proceed."""


class InvalidGeometryPlanError(Exception):
    """Raised when the input GeometryPlan is invalid for STL generation."""


class ConstraintViolationError(Exception):
    """Raised when hard engineering constraints are violated."""


# ---------------------------------------------------------------------------
# Data classes
# ---------------------------------------------------------------------------
@dataclass
class GyroidFieldParams:
    """Parameters for the implicit gyroid scalar field.

    The field function is:
        F(x,y,z) = Σ sin(π·x/a)·cos(π·y/b) − t

    where t is zone-specific and derived from density.
    """
    # Cell dimensions per zone
    cell_size_x_mm: float
    cell_size_y_mm: float
    cell_size_z_mm: float

    # Threshold value — controls solid vs void ratio
    # Lower t = more solid (higher density)
    # Higher t = more void (lower density)
    threshold: float

    # Field function coefficients
    coefficient_x: float  # π / cell_size_x
    coefficient_y: float  # π / cell_size_y
    coefficient_z: float  # π / cell_size_z

    # Zone identity
    zone_name: str

    # Edition that produced this field
    edition: str
    is_hybrid: bool = False
    secondary_edition: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class VoxelGridSettings:
    """Voxelization grid for marching cubes extraction."""
    grid_size_x: int
    grid_size_y: int
    grid_size_z: int
    resolution_mm: float
    bounding_box: Dict[str, float]  # {x_min, x_max, y_min, y_max, z_min, z_max}
    total_voxels: int
    memory_estimate_bytes: int  # 4 bytes per float field value

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class ZoneMeshConfig:
    """Mesh generation configuration for a single foot zone."""
    zone_name: str
    field_params: GyroidFieldParams
    density_target: float          # 0.15 – 0.45
    wall_thickness_mm: float       # >= 0.6
    cell_size_mm: float            # 5.0 – 7.0
    mesh_resolution_mm: float
    stimulation_type: str
    structural_role: str
    # Isosurface extraction settings
    iso_value: float               # iso-surface threshold
    gradient_steps: int            # numerical gradient approximation steps
    smooth_iterations: int         # Laplacian smoothing passes

    def to_dict(self) -> Dict[str, Any]:
        d = asdict(self)
        d["field_params"] = self.field_params.to_dict()
        return d


@dataclass
class ExportMetadata:
    """Export metadata for downstream STL/OBJ consumers."""
    plan_id: str
    source_session_id: str
    edition: str
    is_hybrid: bool
    secondary_edition: Optional[str]
    blend_ratio: Tuple[float, float]
    timestamp: str
    total_zones: int
    total_voxels: int
    estimated_triangles: int
    estimated_filesize_mb: float
    format_hint: str  # "stl_ascii", "stl_binary", "obj", "3mf"
    units: str  # "mm"
    coordinate_system: str  # "right-handed Y-up"

    def to_dict(self) -> Dict[str, Any]:
        d = asdict(self)
        d["blend_ratio"] = list(self.blend_ratio)
        return d


@dataclass
class STLReadinessReport:
    """Readiness scoring: 0.0 (not ready) → 1.0 (fully ready)."""
    score: float
    is_ready: bool
    checks: List[Dict[str, Any]] = field(default_factory=list)
    blockers: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class STLGenerationConfig:
    """Complete STL generation configuration output."""
    config_id: str
    timestamp: str
    source_plan_id: str
    edition: str
    is_hybrid: bool
    readiness: STLReadinessReport
    gyroid_fields: List[GyroidFieldParams]
    voxel_grid: VoxelGridSettings
    zone_meshes: List[ZoneMeshConfig]
    export_metadata: ExportMetadata
    # Constraint enforcement record
    constraints_enforced: Dict[str, Any] = field(default_factory=dict)
    zone_transition_config: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "config_id": self.config_id,
            "timestamp": self.timestamp,
            "source_plan_id": self.source_plan_id,
            "edition": self.edition,
            "is_hybrid": self.is_hybrid,
            "readiness": self.readiness.to_dict(),
            "gyroid_fields": [f.to_dict() for f in self.gyroid_fields],
            "voxel_grid": self.voxel_grid.to_dict(),
            "zone_meshes": [m.to_dict() for m in self.zone_meshes],
            "export_metadata": self.export_metadata.to_dict(),
            "constraints_enforced": self.constraints_enforced,
            "zone_transition_config": self.zone_transition_config,
        }

    def to_json(self, indent: int = 2) -> str:
        return json.dumps(self.to_dict(), indent=indent, ensure_ascii=False)


# ---------------------------------------------------------------------------
# STL Readiness Scorer
# ---------------------------------------------------------------------------
class STLReadinessScorer:
    """Scores a GeometryPlan for STL generation readiness."""

    def score(self, geometry_plan: Any) -> STLReadinessReport:
        """Score from 0.0 to 1.0 based on multiple checks."""
        checks = []
        blockers = []
        warnings = []
        passed = 0
        total = 0

        def _check(name: str, ok: bool, detail: str = "", is_blocker: bool = True):
            nonlocal passed, total
            total += 1
            entry = {"name": name, "passed": ok, "detail": detail}
            checks.append(entry)
            if ok:
                passed += 1
            elif is_blocker:
                blockers.append(name)
            else:
                warnings.append(name)

        plan = geometry_plan

        # 1. ready_for_stl flag
        _check("ready_for_stl_flag",
               getattr(plan, "ready_for_stl", False),
               "Plan must have ready_for_stl=True")

        # 2. manufacturability passed
        mfg = getattr(plan, "manufacturability", None)
        _check("manufacturability_passed",
               mfg is not None and mfg.passed,
               "Manufacturability checks must pass")

        # 3. Wall thickness >= 0.6
        min_wall = min(z.wall_thickness_mm for z in plan.zones) if plan.zones else 0
        _check("wall_thickness_min",
               min_wall >= MIN_WALL_THICKNESS_MM,
               f"Min wall = {min_wall}mm, required >= {MIN_WALL_THICKNESS_MM}mm")

        # 4. Density range
        densities = [z.density_pct / 100.0 for z in plan.zones]
        d_min = min(densities) if densities else 0
        d_max = max(densities) if densities else 1
        _check("density_range",
               DENSITY_MIN <= d_min and d_max <= DENSITY_MAX,
               f"Density range [{d_min:.3f}, {d_max:.3f}], "
               f"required [{DENSITY_MIN}, {DENSITY_MAX}]")

        # 5. Cell size range
        cells = [z.gyroid_cell_size_mm for z in plan.zones]
        c_min = min(cells) if cells else 0
        c_max = max(cells) if cells else 0
        _check("cell_size_range",
               GYROID_CELL_SIZE_MIN_MM <= c_min and c_max <= GYROID_CELL_SIZE_MAX_MM,
               f"Cell sizes [{c_min}, {c_max}], "
               f"required [{GYROID_CELL_SIZE_MIN_MM}, {GYROID_CELL_SIZE_MAX_MM}]")

        # 6. All 7 zones present
        zone_names = {z.zone_name for z in plan.zones}
        expected_zones = {"heel", "midfoot", "forefoot", "toe",
                          "arch", "medial_edge", "lateral_edge"}
        _check("all_zones_present",
               expected_zones.issubset(zone_names),
               f"Found {len(zone_names)} zones, expected 7")

        # 7. Valid edition
        valid_editions = {"CALM", "VITAL", "FOCUS", "BALANCE", "FEMME"}
        _check("valid_edition",
               plan.edition in valid_editions,
               f"Edition '{plan.edition}' not in {valid_editions}")

        # 8. Hybrid consistency (warning only if not hybrid)
        if plan.is_hybrid:
            _check("hybrid_has_secondary",
                   plan.secondary_edition is not None,
                   "HYBRID requires secondary_edition")
            _check("hybrid_blend_valid",
                   sum(plan.blend_ratio) >= 0.99,
                   f"Blend ratio {plan.blend_ratio} must sum to ~1.0")

        score = passed / total if total > 0 else 0.0
        score = round(min(1.0, max(0.0, score)), 4)

        return STLReadinessReport(
            score=score,
            is_ready=(score == 1.0 and len(blockers) == 0),
            checks=checks,
            blockers=blockers,
            warnings=warnings,
        )


# ---------------------------------------------------------------------------
# Core: Gyroid field generation
# ---------------------------------------------------------------------------
def _density_to_threshold(density: float) -> float:
    """Map density [0.15, 0.45] to gyroid threshold t [-0.8, 0.8].

    Lower density → higher threshold (more void).
    Higher density → lower threshold (more solid).

    Linear mapping:
        density=0.45 (max solid) → t = -0.8
        density=0.15 (min solid) → t = +0.8
    """
    d = max(DENSITY_MIN, min(DENSITY_MAX, density))
    t_min = GYROID_DEFAULT_THRESHOLD_MIN
    t_max = GYROID_DEFAULT_THRESHOLD_MAX
    # Linear interpolation: high density → low threshold
    t = t_min + (t_max - t_min) * (1.0 - (d - DENSITY_MIN) / (DENSITY_MAX - DENSITY_MIN))
    return round(t, 6)


def generate_gyroid_field(
    zone_name: str,
    cell_size_mm: float,
    density: float,
    edition: str,
    is_hybrid: bool = False,
    secondary_edition: Optional[str] = None,
) -> GyroidFieldParams:
    """Generate implicit gyroid field parameters for a single zone.

    The gyroid implicit surface is defined as:
        F(x,y,z) = sin(πx/a)·cos(πy/b) + sin(πy/b)·cos(πz/c) + sin(πz/c)·cos(πx/a) = t

    Args:
        zone_name: Foot zone identifier (e.g. 'heel', 'arch').
        cell_size_mm: Unit cell size in mm (5.0–7.0).
        density: Target density fraction (0.15–0.45).
        edition: Edition name.
        is_hybrid: Whether this is a hybrid edition.
        secondary_edition: Secondary edition if hybrid.

    Returns:
        GyroidFieldParams with cell dimensions, threshold, and coefficients.
    """
    # Clamp inputs
    cell = max(GYROID_CELL_SIZE_MIN_MM, min(GYROID_CELL_SIZE_MAX_MM, cell_size_mm))
    d = max(DENSITY_MIN, min(DENSITY_MAX, density))

    # Coefficients: π / cell_size (same for all axes in isotropic gyroid)
    coeff = math.pi / cell

    # Threshold from density
    threshold = _density_to_threshold(d)

    return GyroidFieldParams(
        cell_size_x_mm=round(cell, 4),
        cell_size_y_mm=round(cell, 4),
        cell_size_z_mm=round(cell, 4),
        threshold=threshold,
        coefficient_x=round(coeff, 6),
        coefficient_y=round(coeff, 6),
        coefficient_z=round(coeff, 6),
        zone_name=zone_name,
        edition=edition,
        is_hybrid=is_hybrid,
        secondary_edition=secondary_edition,
    )


def generate_density_gradient(
    plan: Any,
    resolution_mm: float = VOXEL_RESOLUTION_DEFAULT,
    interpolation: str = "linear",
) -> Dict[str, Any]:
    """Generate density gradient configuration for zone transitions.

    Computes inter-zone density deltas and suggests interpolation strategy
    for smooth transitions between adjacent foot zones.

    For HYBRID editions, also computes cross-edition blend gradients.

    Args:
        plan: GeometryPlan from zilfit_geometry_runtime.
        resolution_mm: Voxel resolution for gradient sampling.
        interpolation: "linear", "cubic", or "spline".

    Returns:
        Dict mapping zone pairs to gradient configuration.
    """
    zones = plan.zones
    gradients: Dict[str, Any] = {}

    # Known adjacency map for foot zones
    adjacency = {
        "heel": ["midfoot", "medial_edge", "lateral_edge"],
        "midfoot": ["heel", "forefoot", "arch", "medial_edge", "lateral_edge"],
        "forefoot": ["midfoot", "toe", "medial_edge", "lateral_edge"],
        "toe": ["forefoot"],
        "arch": ["midfoot", "medial_edge", "lateral_edge"],
        "medial_edge": ["heel", "midfoot", "forefoot", "arch"],
        "lateral_edge": ["heel", "midfoot", "forefoot", "arch"],
    }

    for zone in zones:
        zone_density = zone.density_pct / 100.0
        neighbor_gradients = []

        for neighbor_name in adjacency.get(zone.zone_name, []):
            # Find neighbor zone
            neighbor = next(
                (z for z in zones if z.zone_name == neighbor_name), None
            )
            if neighbor is None:
                continue

            neighbor_density = neighbor.density_pct / 100.0
            delta = abs(zone_density - neighbor_density)

            neighbor_gradients.append({
                "from_zone": zone.zone_name,
                "to_zone": neighbor_name,
                "density_from": round(zone_density, 4),
                "density_to": round(neighbor_density, 4),
                "delta": round(delta, 4),
                "interpolation": interpolation,
                "transition_width_mm": round(
                    max(GYROID_CELL_SIZE_MIN_MM, delta * 20.0), 2
                ),
                "requires_smoothing": delta > 0.10,
            })

        gradients[zone.zone_name] = {
            "zone_density": round(zone_density, 4),
            "cell_size_mm": zone.gyroid_cell_size_mm,
            "neighbor_count": len(neighbor_gradients),
            "max_neighbor_delta": round(
                max((g["delta"] for g in neighbor_gradients), default=0), 4
            ),
            "neighbors": neighbor_gradients,
        }

    return {
        "resolution_mm": resolution_mm,
        "interpolation_method": interpolation,
        "is_hybrid": getattr(plan, "is_hybrid", False),
        "gradient_by_zone": gradients,
    }


def build_mesh_config(
    plan: Any,
    resolution_mm: float = VOXEL_RESOLUTION_DEFAULT,
    insole_length_mm: float = DEFAULT_INSOLE_LENGTH_MM,
    insole_width_mm: float = DEFAULT_INSOLE_WIDTH_MM,
    insole_thickness_mm: float = DEFAULT_INSOLE_THICKNESS_MM,
) -> STLGenerationConfig:
    """Build complete STL generation configuration from a GeometryPlan.

    This is the main entry point. It:
    1. Validates the GeometryPlan
    2. Computes readiness score
    3. Generates gyroid field params for each zone
    4. Computes voxel grid
    5. Generates density gradient configuration
    6. Assembles export metadata

    Args:
        plan: GeometryPlan from zilfit_geometry_runtime.
        resolution_mm: Voxel resolution (0.1 = fine, 0.25 = default, 0.5 = coarse).
        insole_length_mm: Foot length in mm.
        insole_width_mm: Foot width in mm.
        insole_thickness_mm: Insole thickness in mm.

    Returns:
        STLGenerationConfig complete configuration.
    """
    # --- Readiness ---
    scorer = STLReadinessScorer()
    readiness = scorer.score(plan)

    # --- Gyroid fields per zone ---
    gyroid_fields: List[GyroidFieldParams] = []
    zone_meshes: List[ZoneMeshConfig] = []

    for zone in plan.zones:
        zone_density = zone.density_pct / 100.0

        field_params = generate_gyroid_field(
            zone_name=zone.zone_name,
            cell_size_mm=zone.gyroid_cell_size_mm,
            density=zone_density,
            edition=plan.edition,
            is_hybrid=plan.is_hybrid,
            secondary_edition=plan.secondary_edition,
        )
        gyroid_fields.append(field_params)

        # Isosurface extraction settings per zone
        iso_surface = field_params.threshold
        grad_steps = 2 if zone_density > 0.30 else 1
        smooth_passes = 1 if zone_density < 0.25 else 2

        mesh_cfg = ZoneMeshConfig(
            zone_name=zone.zone_name,
            field_params=field_params,
            density_target=round(zone_density, 4),
            wall_thickness_mm=zone.wall_thickness_mm,
            cell_size_mm=zone.gyroid_cell_size_mm,
            mesh_resolution_mm=resolution_mm,
            stimulation_type=zone.stimulation_type,
            structural_role=zone.structural_role,
            iso_value=iso_surface,
            gradient_steps=grad_steps,
            smooth_iterations=smooth_passes,
        )
        zone_meshes.append(mesh_cfg)

    # --- Voxel grid ---
    grid_x = max(2, int(math.ceil(insole_length_mm / resolution_mm)))
    grid_y = max(2, int(math.ceil(insole_width_mm / resolution_mm)))
    grid_z = max(2, int(math.ceil(insole_thickness_mm / resolution_mm)))
    total_voxels = grid_x * grid_y * grid_z
    memory_bytes = total_voxels * 4  # float32

    # Bounding box: center origin, Y up
    voxel_grid = VoxelGridSettings(
        grid_size_x=grid_x,
        grid_size_y=grid_y,
        grid_size_z=grid_z,
        resolution_mm=resolution_mm,
        bounding_box={
            "x_min": -insole_length_mm / 2.0,
            "x_max": insole_length_mm / 2.0,
            "y_min": -insole_width_mm / 2.0,
            "y_max": insole_width_mm / 2.0,
            "z_min": 0.0,
            "z_max": insole_thickness_mm,
        },
        total_voxels=total_voxels,
        memory_estimate_bytes=memory_bytes,
    )

    # --- Density gradients ---
    gradient_cfg = generate_density_gradient(plan, resolution_mm)

    # --- Zone transition config ---
    zone_transitions = {}
    adj_pairs = set()
    for zname, zdata in gradient_cfg["gradient_by_zone"].items():
        for nb in zdata["neighbors"]:
            pair_key = tuple(sorted([nb["from_zone"], nb["to_zone"]]))
            if pair_key not in adj_pairs:
                adj_pairs.add(pair_key)
                zone_transitions["_".join(pair_key)] = {
                    "density_delta": nb["delta"],
                    "transition_width_mm": nb["transition_width_mm"],
                    "requires_smoothing": nb["requires_smoothing"],
                    "interpolation": nb["interpolation"],
                }

    # --- Export metadata ---
    # Rough triangle estimate: ~2 triangles per voxel on surface
    surface_ratio = 0.12  # typical for gyroid lattice
    est_triangles = int(total_voxels * surface_ratio)
    est_filesize_mb = round(est_triangles * 50 / (1024 * 1024), 2)

    export_meta = ExportMetadata(
        plan_id=plan.plan_id,
        source_session_id=plan.source_session_id,
        edition=plan.edition,
        is_hybrid=plan.is_hybrid,
        secondary_edition=plan.secondary_edition,
        blend_ratio=tuple(plan.blend_ratio) if hasattr(plan, "blend_ratio") else (1.0, 0.0),
        timestamp=datetime.now(timezone.utc).isoformat(),
        total_zones=len(plan.zones),
        total_voxels=total_voxels,
        estimated_triangles=est_triangles,
        estimated_filesize_mb=est_filesize_mb,
        format_hint="stl_binary",
        units="mm",
        coordinate_system="right-handed Y-up",
    )

    # --- Constraint enforcement record ---
    constraints_enforced = {
        "wall_thickness_mm": {
            "minimum": MIN_WALL_THICKNESS_MM,
            "enforced": True,
            "actual_min": min(z.wall_thickness_mm for z in plan.zones),
        },
        "density_range": {
            "minimum": DENSITY_MIN,
            "maximum": DENSITY_MAX,
            "enforced": True,
            "actual_range": [
                round(min(z.density_pct / 100 for z in plan.zones), 4),
                round(max(z.density_pct / 100 for z in plan.zones), 4),
            ],
        },
        "cell_size_range": {
            "minimum": GYROID_CELL_SIZE_MIN_MM,
            "maximum": GYROID_CELL_SIZE_MAX_MM,
            "enforced": True,
            "actual_range": [
                round(min(z.gyroid_cell_size_mm for z in plan.zones), 4),
                round(max(z.gyroid_cell_size_mm for z in plan.zones), 4),
            ],
        },
    }

    return STLGenerationConfig(
        config_id=str(uuid.uuid4()),
        timestamp=datetime.now(timezone.utc).isoformat(),
        source_plan_id=plan.plan_id,
        edition=plan.edition,
        is_hybrid=plan.is_hybrid,
        readiness=readiness,
        gyroid_fields=gyroid_fields,
        voxel_grid=voxel_grid,
        zone_meshes=zone_meshes,
        export_metadata=export_meta,
        constraints_enforced=constraints_enforced,
        zone_transition_config=zone_transitions,
    )


# ---------------------------------------------------------------------------
# Schema access
# ---------------------------------------------------------------------------
def _load_schema() -> Dict[str, Any]:
    """Load the STL generation JSON schema."""
    if _STL_SCHEMA_PATH.exists():
        with open(_STL_SCHEMA_PATH, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}


def validate_config_against_schema(config: STLGenerationConfig) -> List[str]:
    """Validate config dict against stl_generation.schema.json."""
    errors: List[str] = []
    schema = _load_schema()
    if not schema:
        return errors

    cfg_dict = config.to_dict()
    required = schema.get("required", [])
    props = schema.get("properties", {})

    for field_name in required:
        if field_name not in cfg_dict:
            errors.append(f"Missing required field: {field_name}")

    # Validate readiness score range
    readiness = cfg_dict.get("readiness", {})
    score = readiness.get("score", -1)
    if score < 0 or score > 1:
        errors.append(f"readiness.score={score} out of range [0,1]")

    # Validate gyroid fields have required structure
    fields = cfg_dict.get("gyroid_fields", [])
    for i, f in enumerate(fields):
        for req in ["cell_size_x_mm", "cell_size_y_mm", "cell_size_z_mm",
                    "threshold", "coefficient_x", "coefficient_y",
                    "coefficient_z", "zone_name"]:
            if req not in f:
                errors.append(f"gyroid_fields[{i}] missing {req}")

    # Validate voxel grid
    vg = cfg_dict.get("voxel_grid", {})
    vg_required = ["grid_size_x", "grid_size_y", "grid_size_z",
                   "resolution_mm", "bounding_box", "total_voxels"]
    for req in vg_required:
        if req not in vg:
            errors.append(f"voxel_grid missing {req}")

    # Validate zone meshes
    meshes = cfg_dict.get("zone_meshes", [])
    for i, m in enumerate(meshes):
        m_required = ["zone_name", "density_target", "wall_thickness_mm",
                      "cell_size_mm", "iso_value"]
        for req in m_required:
            if req not in m:
                errors.append(f"zone_meshes[{i}] missing {req}")

        # Enforce wall thickness
        wt = m.get("wall_thickness_mm", 0)
        if wt < MIN_WALL_THICKNESS_MM:
            errors.append(
                f"zone_meshes[{i}].wall_thickness_mm={wt} < {MIN_WALL_THICKNESS_MM}"
            )

        # Enforce density range
        dt = m.get("density_target", 0)
        if dt < DENSITY_MIN or dt > DENSITY_MAX:
            errors.append(
                f"zone_meshes[{i}].density_target={dt} out of range [{DENSITY_MIN}, {DENSITY_MAX}]"
            )

        # Enforce cell size
        cs = m.get("cell_size_mm", 0)
        if cs < GYROID_CELL_SIZE_MIN_MM or cs > GYROID_CELL_SIZE_MAX_MM:
            errors.append(
                f"zone_meshes[{i}].cell_size_mm={cs} out of range [{GYROID_CELL_SIZE_MIN_MM}, {GYROID_CELL_SIZE_MAX_MM}]"
            )

    return errors


# ---------------------------------------------------------------------------
# Utility: evaluate gyroid field at a point (for testing / verification)
# ---------------------------------------------------------------------------
def evaluate_gyroid_at(
    x: float, y: float, z: float,
    field: GyroidFieldParams,
) -> float:
    """Evaluate the implicit gyroid field F(x,y,z) at a point.

    F(x,y,z) = sin(ax·x)·cos(ay·y) + sin(ay·y)·cos(az·z) + sin(az·z)·cos(ax·x) - t

    Returns:
        Field value. Negative = inside solid, positive = in void.
        Zero-crossing = surface boundary.
    """
    ax, ay, az = field.coefficient_x, field.coefficient_y, field.coefficient_z
    t = field.threshold

    f_val = (
        math.sin(ax * x) * math.cos(ay * y)
        + math.sin(ay * y) * math.cos(az * z)
        + math.sin(az * z) * math.cos(ax * x)
        - t
    )
    return f_val

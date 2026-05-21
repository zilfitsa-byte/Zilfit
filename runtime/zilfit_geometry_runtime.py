"""
ZILFIT Geometry Runtime — From Scientific Decision to Manufacturing Geometry

Consumes output from zilfit_scientific_layer.py and produces a clean JSON
geometry plan ready for STL generation.

No Telegram. No agents. No governance. Pure runtime.
No STL output — only geometric specifications.
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
_GEOMETRY_RUNTIME_SCHEMA = _SCHEMAS_DIR / "geometry_runtime.schema.json"

# ---------------------------------------------------------------------------
# Hard engineering constraints (shared with scientific_layer)
# ---------------------------------------------------------------------------
MIN_WALL_THICKNESS_MM = 0.6
MAX_WALL_THICKNESS_MM = 2.0  # TPU printability upper bound

DENSITY_MIN = 0.15  # 15% — below this: structurally unsound
DENSITY_MAX = 0.45  # 45% — above this: too rigid / heat trapping

GYROID_CELL_SIZE_BASE_MM = 6.0
GYROID_CELL_SIZE_MIN_MM = 5.0
GYROID_CELL_SIZE_MAX_MM = 7.0

# ---------------------------------------------------------------------------
# Pressure limits per edition (absolute safety caps)
# ---------------------------------------------------------------------------
EDITION_MAX_PRESSURE_KPA: Dict[str, float] = {
    "CALM": 45.0,
    "VITAL": 65.0,
    "FOCUS": 60.0,
    "BALANCE": 55.0,
    "FEMME": 42.0,
    "NONE": 0.0,
}

# ---------------------------------------------------------------------------
# Foot zones
# ---------------------------------------------------------------------------
FOOT_ZONES = ["heel", "midfoot", "forefoot", "toe", "arch", "medial_edge", "lateral_edge"]

# ---------------------------------------------------------------------------
# Exceptions
# ---------------------------------------------------------------------------
class GeometryValidationError(Exception):
    """Raised when geometry plan fails validation checks."""

class InvalidEditionError(Exception):
    """Raised when an unknown edition is requested."""

class BlockedEditionError(Exception):
    """Raised when the edition is NONE (safety-blocked)."""

# ---------------------------------------------------------------------------
# Data classes
# ---------------------------------------------------------------------------
@dataclass
class ZoneSpec:
    """Geometric specification for a single foot zone."""
    zone_name: str
    density_pct: float
    pressure_limit_kpa: float
    gyroid_cell_size_mm: float
    wall_thickness_mm: float
    stimulation_type: str  # "static", "graded", "zoned_firm", etc.
    structural_role: str   # "shock_absorption", "support", "proprioceptive"

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

@dataclass
class PressureLimits:
    """Safe pressure envelope for the entire insole."""
    heel_max_kpa: float
    midfoot_max_kpa: float
    forefoot_max_kpa: float
    toe_max_kpa: float
    arch_max_kpa: float
    global_max_kpa: float
    global_abs_limit_kpa: float = 80.0  # absolute safety hard cap

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

@dataclass
class GyroidParameters:
    """Parameters for gyroid lattice generation."""
    cell_size_mm: float
    wall_thickness_mm: float
    min_density: float
    max_density: float
    unit_cell_type: str = "gyroid"
    lattice_orientation: str = "aligned"
    gradation_method: str = "linear"  # "linear", "cubic", "spline"
    resolution_mm: float = 0.1  # mesh resolution for manifold gen

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

@dataclass
class ManufacturabilityCheck:
    """Manufacturability analysis results."""
    passed: bool
    checks: List[Dict[str, Any]] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    violations: List[str] = field(default_factory=list)

    def add_check(self, name: str, passed: bool, detail: str = ""):
        self.checks.append({
            "name": name,
            "passed": passed,
            "detail": detail,
        })
        if not passed:
            self.violations.append(name)

    def add_warning(self, message: str):
        self.warnings.append(message)

    @property
    def is_valid(self) -> bool:
        return self.passed and len(self.violations) == 0

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

@dataclass
class SafetyConstraints:
    """Safety constraints applied to this geometry."""
    wall_thickness_enforced: bool
    wall_thickness_mm: float
    density_range_enforced: bool
    density_min: float
    density_max: float
    pressure_cap_enforced: bool
    pressure_cap_kpa: float
    absolute_pressure_limit_kpa: float = 80.0
    temperature_adjustment_applied: bool = False
    pregnancy_restriction_applied: bool = False

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

@dataclass
class GeometryPlan:
    """
    Complete geometry plan ready for STL generation.

    This is the output of ZilfitGeometryRuntime.generate().
    """
    plan_id: str
    timestamp: str
    source_session_id: str
    edition: str
    is_hybrid: bool
    secondary_edition: Optional[str]
    blend_ratio: Tuple[float, float]
    zones: List[ZoneSpec]
    density_by_zone: Dict[str, float]
    pressure_limits: PressureLimits
    gyroid_parameters: GyroidParameters
    manufacturability: ManufacturabilityCheck
    safety_constraints: SafetyConstraints
    manufacturing_notes: str = ""
    warnings: List[str] = field(default_factory=list)
    ready_for_stl: bool = False

    def to_dict(self) -> Dict[str, Any]:
        return {
            "plan_id": self.plan_id,
            "timestamp": self.timestamp,
            "source_session_id": self.source_session_id,
            "edition": self.edition,
            "is_hybrid": self.is_hybrid,
            "secondary_edition": self.secondary_edition,
            "blend_ratio": list(self.blend_ratio),
            "zones": [z.to_dict() for z in self.zones],
            "density_by_zone": self.density_by_zone,
            "pressure_limits": self.pressure_limits.to_dict(),
            "gyroid_parameters": self.gyroid_parameters.to_dict(),
            "manufacturability": self.manufacturability.to_dict(),
            "safety_constraints": self.safety_constraints.to_dict(),
            "manufacturing_notes": self.manufacturing_notes,
            "warnings": self.warnings,
            "ready_for_stl": self.ready_for_stl,
        }

    def to_json(self, indent: int = 2) -> str:
        return json.dumps(self.to_dict(), indent=indent, ensure_ascii=False)

# ---------------------------------------------------------------------------
# Zone definitions per edition
# ---------------------------------------------------------------------------
# Each zone maps: (structural_role, stimulation_modifier)
# Stimulation modifier scales local pressure feeling
ZONE_PROFILES: Dict[str, Dict[str, Any]] = {
    "heel": {
        "structural_role": "shock_absorption",
        "stimulation_base": "static",
    },
    "midfoot": {
        "structural_role": "support",
        "stimulation_base": "static",
    },
    "forefoot": {
        "structural_role": "proprioceptive",
        "stimulation_base": "static",
    },
    "toe": {
        "structural_role": "proprioceptive",
        "stimulation_base": "static",
    },
    "arch": {
        "structural_role": "support",
        "stimulation_base": "graded",
    },
    "medial_edge": {
        "structural_role": "stability",
        "stimulation_base": "static",
    },
    "lateral_edge": {
        "structural_role": "stability",
        "stimulation_base": "static",
    },
}

# Stimulation pattern → zone stimulation type mapping
STIMULATION_PATTERNS: Dict[str, Dict[str, str]] = {
    "static_soft": {
        "heel": "static", "midfoot": "static", "forefoot": "static",
        "toe": "static", "arch": "graded", "medial_edge": "static", "lateral_edge": "static",
    },
    "static_firm": {
        "heel": "static", "midfoot": "static", "forefoot": "static",
        "toe": "static", "arch": "graded", "medial_edge": "static", "lateral_edge": "static",
    },
    "zoned_firm_toe": {
        "heel": "static", "midfoot": "static", "forefoot": "static",
        "toe": "zoned_firm", "arch": "graded", "medial_edge": "static", "lateral_edge": "static",
    },
    "graduated_even": {
        "heel": "graded", "midfoot": "graded", "forefoot": "graded",
        "toe": "graded", "arch": "graded", "medial_edge": "graded", "lateral_edge": "graded",
    },
    "static_ultra_soft": {
        "heel": "static", "midfoot": "static", "forefoot": "static",
        "toe": "static", "arch": "graded", "medial_edge": "static", "lateral_edge": "static",
    },
}

# ---------------------------------------------------------------------------
# Geometry Validator
# ---------------------------------------------------------------------------
class GeometryValidator:
    """Validates geometry constraints before plan generation."""

    def validate_wall_thickness(self, thickness: float) -> Tuple[bool, str]:
        if thickness < MIN_WALL_THICKNESS_MM:
            return False, (
                f"Wall thickness {thickness}mm below minimum {MIN_WALL_THICKNESS_MM}mm"
            )
        if thickness > MAX_WALL_THICKNESS_MM:
            return False, (
                f"Wall thickness {thickness}mm above printability limit {MAX_WALL_THICKNESS_MM}mm"
            )
        return True, "OK"

    def validate_pressure(self, pressure: float, edition: str, zone: str = "") -> Tuple[bool, str]:
        if pressure < 0:
            return False, f"Negative pressure {pressure} kPa"

        # Absolute safety cap — checked first
        if pressure > 80.0:
            return False, (
                f"Pressure {pressure} kPa exceeds absolute safety cap 80.0 kPa"
            )

        edition_cap = EDITION_MAX_PRESSURE_KPA.get(edition, 0)
        if edition_cap > 0 and pressure > edition_cap:
            return False, (
                f"Pressure {pressure} kPa exceeds {edition} cap of {edition_cap} kPa"
            )

        return True, "OK"

    def validate_density(self, density: float) -> Tuple[bool, str]:
        """Density must be in [0.15, 0.45] range."""
        if density < DENSITY_MIN:
            return False, (
                f"Density {density:.3f} below minimum {DENSITY_MIN:.2f} — structurally unsound"
            )
        if density > DENSITY_MAX:
            return False, (
                f"Density {density:.3f} above maximum {DENSITY_MAX:.2f} — too rigid / heat trapping"
            )
        return True, "OK"

    def validate_cell_size(self, cell_size: float) -> Tuple[bool, str]:
        if cell_size < GYROID_CELL_SIZE_MIN_MM:
            return False, (
                f"Cell size {cell_size}mm below minimum {GYROID_CELL_SIZE_MIN_MM}mm"
            )
        if cell_size > GYROID_CELL_SIZE_MAX_MM:
            return False, (
                f"Cell size {cell_size}mm above maximum {GYROID_CELL_SIZE_MAX_MM}mm"
            )
        return True, "OK"

# ---------------------------------------------------------------------------
# Geometry Runtime
# ---------------------------------------------------------------------------
class ZilfitGeometryRuntime:
    """
    Converts ScientificDecision output into a GeometryPlan.

    Usage:
        runtime = ZilfitGeometryRuntime()

        # From a ScientificDecision object:
        plan = runtime.from_decision(scientific_decision_obj)

        # Or from a dict (JSON from API):
        plan = runtime.from_dict(scientific_decision_dict)
    """

    def __init__(self):
        self.validator = GeometryValidator()
        self._schema = self._load_schema()

    def _load_schema(self) -> Dict[str, Any]:
        if _GEOMETRY_RUNTIME_SCHEMA.exists():
            with open(_GEOMETRY_RUNTIME_SCHEMA, "r", encoding="utf-8") as f:
                return json.load(f)
        return {}

    # ------------------------------------------------------------------
    # Entry points
    # ------------------------------------------------------------------
    def from_decision(self, decision) -> GeometryPlan:
        """Accepts a ScientificDecision dataclass from zilfit_scientific_layer."""
        return self._build_plan(
            edition=decision.selection.primary_edition,
            secondary_edition=decision.selection.secondary_edition,
            is_hybrid=decision.selection.is_hybrid,
            blend_ratio=decision.selection.blend_ratio,
            engineering=decision.engineering,
            session_id=decision.session_id,
            gate_density_factor=decision.gate.density_reduction_factor,
            gate_action=decision.gate.action,
            pregnancy_restricted=decision.gate.action == "RESTRICT",
        )

    def from_dict(self, decision_dict: Dict[str, Any]) -> GeometryPlan:
        """Accepts a dict (JSON-decoded) matching ScientificDecision.to_dict()."""
        selection = decision_dict.get("selection", {})
        engineering = decision_dict.get("engineering", {})
        gate = decision_dict.get("gate", {})

        return self._build_plan(
            edition=selection.get("primary_edition", "NONE"),
            secondary_edition=selection.get("secondary_edition"),
            is_hybrid=selection.get("is_hybrid", False),
            blend_ratio=tuple(selection.get("blend_ratio", [1.0, 0.0])),
            engineering=engineering,
            session_id=decision_dict.get("session_id", ""),
            gate_density_factor=gate.get("density_reduction_factor", 1.0),
            gate_action=gate.get("action", "PASS"),
            pregnancy_restricted=gate.get("action") == "RESTRICT",
        )

    # ------------------------------------------------------------------
    # Core build logic
    # ------------------------------------------------------------------
    def _build_plan(
        self,
        edition: str,
        secondary_edition: Optional[str],
        is_hybrid: bool,
        blend_ratio: Tuple[float, float],
        engineering: Any,  # dict or EngineeringDirective
        session_id: str,
        gate_density_factor: float,
        gate_action: str,
        pregnancy_restricted: bool,
    ) -> GeometryPlan:
        """Internal: build the full geometry plan."""

        # Check blocked edition
        if edition == "NONE":
            raise BlockedEditionError(
                "Cannot generate geometry for blocked edition (Safety Gate STOP)"
            )

        # Extract properties (works with dict or dataclass)
        props = self._get_props(engineering)

        # Build base densities from engineering directive
        base_densities = {
            "heel": props.get("heel_density_pct", 20) / 100.0,
            "midfoot": props.get("midfoot_density_pct", 20) / 100.0,
            "forefoot": props.get("forefoot_density_pct", 20) / 100.0,
            "toe": props.get("toe_density_pct", 20) / 100.0,
            "arch": props.get("midfoot_density_pct", 20) / 100.0 * 0.9,
            "medial_edge": props.get("midfoot_density_pct", 20) / 100.0 * 0.95,
            "lateral_edge": props.get("midfoot_density_pct", 20) / 100.0 * 0.95,
        }

        # HYBRED: blend with secondary edition specs
        if is_hybrid and secondary_edition and 0.0 < blend_ratio[1] < 1.0:
            blend_primary = blend_ratio[0]
            blend_secondary = blend_ratio[1]
            specs = self._get_edition_specs(secondary_edition)
            secondary_densities = {
                "heel": specs.get("heel_density", 20) / 100.0,
                "midfoot": specs.get("midfoot_density", 20) / 100.0,
                "forefoot": specs.get("forefoot_density", 20) / 100.0,
                "toe": specs.get("toe_density", 20) / 100.0,
                "arch": specs.get("midfoot_density", 20) / 100.0 * 0.9,
                "medial_edge": specs.get("midfoot_density", 20) / 100.0 * 0.95,
                "lateral_edge": specs.get("midfoot_density", 20) / 100.0 * 0.95,
            }
            for zone in base_densities:
                base_densities[zone] = (
                    base_densities[zone] * blend_primary
                    + secondary_densities[zone] * blend_secondary
                )

        # Apply density reduction factor from safety gate
        if gate_density_factor < 1.0:
            for zone in base_densities:
                base_densities[zone] *= gate_density_factor

        # Clamp densities to [0.15, 0.45]
        for zone in base_densities:
            base_densities[zone] = max(DENSITY_MIN, min(DENSITY_MAX, base_densities[zone]))

        # Stimulation pattern
        stim_pattern = props.get("stimulation_pattern", "static")
        zone_stims = STIMULATION_PATTERNS.get(stim_pattern, STIMULATION_PATTERNS["static_soft"])

        # Build zones
        zones: List[ZoneSpec] = []
        density_by_zone: Dict[str, float] = {}

        for zone_name in FOOT_ZONES:
            density = base_densities[zone_name]
            profile = ZONE_PROFILES[zone_name]

            # Pressure limit: proportional to density ratio within this edition
            edition_max = props.get("max_pressure_kpa", 45.0)
            zone_pressure = edition_max * (density / max(base_densities.values()))
            zone_pressure = min(zone_pressure, edition_max)

            cell_size = props.get("gyroid_cell_size_mm", GYROID_CELL_SIZE_BASE_MM)
            wall_thickness = MIN_WALL_THICKNESS_MM

            stim_type = zone_stims.get(zone_name, "static")

            zone_spec = ZoneSpec(
                zone_name=zone_name,
                density_pct=round(density * 100, 1),
                pressure_limit_kpa=round(zone_pressure, 1),
                gyroid_cell_size_mm=round(cell_size, 1),
                wall_thickness_mm=wall_thickness,
                stimulation_type=stim_type,
                structural_role=profile["structural_role"],
            )
            zones.append(zone_spec)
            density_by_zone[zone_name] = round(density, 4)

        # Pressure limits
        edition_cap = props.get("max_pressure_kpa", 45.0)
        pressure_limits = PressureLimits(
            heel_max_kpa=round(edition_cap * 0.7, 1),
            midfoot_max_kpa=round(edition_cap * 0.8, 1),
            forefoot_max_kpa=round(edition_cap * 0.9, 1),
            toe_max_kpa=round(edition_cap * 0.85, 1),
            arch_max_kpa=round(edition_cap * 0.75, 1),
            global_max_kpa=edition_cap,
        )

        # Gyroid parameters
        cell_size = props.get("gyroid_cell_size_mm", GYROID_CELL_SIZE_BASE_MM)
        cell_size = max(GYROID_CELL_SIZE_MIN_MM, min(GYROID_CELL_SIZE_MAX_MM, cell_size))
        gyroid_params = GyroidParameters(
            cell_size_mm=round(cell_size, 1),
            wall_thickness_mm=MIN_WALL_THICKNESS_MM,
            min_density=DENSITY_MIN,
            max_density=DENSITY_MAX,
        )

        # Manufacturability checks
        mfg = ManufacturabilityCheck(passed=True)
        self._run_manufacturability_checks(mfg, zones, edition, edition_cap)

        # Safety constraints
        safety = SafetyConstraints(
            wall_thickness_enforced=True,
            wall_thickness_mm=MIN_WALL_THICKNESS_MM,
            density_range_enforced=True,
            density_min=DENSITY_MIN,
            density_max=DENSITY_MAX,
            pressure_cap_enforced=True,
            pressure_cap_kpa=edition_cap,
            temperature_adjustment_applied=gate_density_factor < 1.0,
            pregnancy_restriction_applied=pregnancy_restricted,
        )

        # Warnings
        warnings = list(mfg.warnings)

        plan = GeometryPlan(
            plan_id=str(uuid.uuid4()),
            timestamp=datetime.now(timezone.utc).isoformat(),
            source_session_id=session_id,
            edition=edition,
            is_hybrid=is_hybrid,
            secondary_edition=secondary_edition,
            blend_ratio=blend_ratio,
            zones=zones,
            density_by_zone=density_by_zone,
            pressure_limits=pressure_limits,
            gyroid_parameters=gyroid_params,
            manufacturability=mfg,
            safety_constraints=safety,
            manufacturing_notes=props.get("manufacturing_notes", ""),
            warnings=warnings,
            ready_for_stl=mfg.is_valid,
        )

        # Validate the plan itself
        self._validate_plan(plan)

        return plan

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------
    def _get_props(self, engineering: Any) -> Dict[str, Any]:
        """Extract properties from dict or EngineeringDirective."""
        if isinstance(engineering, dict):
            return engineering
        if hasattr(engineering, "to_dict"):
            return engineering.to_dict()
        if hasattr(engineering, "__dict__"):
            return engineering.__dict__
        raise ValueError(f"Cannot extract properties from type {type(engineering)}")

    def _get_edition_specs(self, edition: str) -> Dict[str, Any]:
        """Return edition specs from the known set."""
        return _EDITION_SPECS.get(edition, {})

    # Import specs lazily so we don't create circular deps
    def _run_manufacturability_checks(
        self,
        mfg: ManufacturabilityCheck,
        zones: List[ZoneSpec],
        edition: str,
        edition_cap: float,
    ):
        """Run all manufacturability validation checks."""
        v = GeometryValidator()

        # 1. Wall thickness check
        ok, msg = v.validate_wall_thickness(MIN_WALL_THICKNESS_MM)
        mfg.add_check("wall_thickness", ok, msg)

        # 2. Density range check for each zone
        for zone in zones:
            density = zone.density_pct / 100.0
            ok, msg = v.validate_density(density)
            mfg.add_check(f"density_{zone.zone_name}", ok,
                          f"{zone.zone_name}: {density:.3f} — {msg}")

        # 3. Pressure limit per zone
        for zone in zones:
            ok, msg = v.validate_pressure(zone.pressure_limit_kpa, edition)
            mfg.add_check(f"pressure_{zone.zone_name}", ok,
                          f"{zone.zone_name}: {zone.pressure_limit_kpa} kPa — {msg}")

        # 4. Cell size bounds
        max_cell = max(z.gyroid_cell_size_mm for z in zones)
        min_cell = min(z.gyroid_cell_size_mm for z in zones)
        ok1, msg1 = v.validate_cell_size(max_cell)
        ok2, msg2 = v.validate_cell_size(min_cell)
        mfg.add_check("cell_size_range", ok1 and ok2, f"min={min_cell}, max={max_cell}")

        # 5. Edition pressure cap
        ok, msg = v.validate_pressure(edition_cap, edition)
        mfg.add_check("edition_pressure_cap", ok, f"cap={edition_cap} kPa")

        # 6. Check all zones have positive values
        zero_issues = [z.zone_name for z in zones if z.density_pct <= 0]
        if zero_issues:
            mfg.add_check(
                "positive_densities", False,
                f"Zero density in: {', '.join(zero_issues)}"
            )
        else:
            mfg.add_check("positive_densities", True)

        # 7. Density gradient smoothness (warning only)
        dens_vals = [z.density_pct for z in zones]
        max_delta = max(dens_vals) - min(dens_vals)
        if max_delta > 25:
            mfg.add_warning(
                f"Large density gradient {max_delta:.1f}% — may require smoother transitions"
            )

        # 8. Set overall passed
        mfg.passed = len(mfg.violations) == 0

    def _validate_plan(self, plan: GeometryPlan):
        """Post-build validation — ensures plan integrity."""
        if not plan.manufacturability.is_valid:
            violations = plan.manufacturability.violations
            raise GeometryValidationError(
                f"Geometry plan has {len(violations)} violation(s): {', '.join(violations)}"
            )

        # Ensure all zones have valid density
        for zone in plan.zones:
            d = zone.density_pct / 100.0
            if d < DENSITY_MIN or d > DENSITY_MAX:
                raise GeometryValidationError(
                    f"Zone '{zone.zone_name}' density {d:.3f} out of range "
                    f"[{DENSITY_MIN}, {DENSITY_MAX}]"
                )

            if zone.wall_thickness_mm < MIN_WALL_THICKNESS_MM:
                raise GeometryValidationError(
                    f"Zone '{zone.zone_name}' wall thickness "
                    f"{zone.wall_thickness_mm}mm < {MIN_WALL_THICKNESS_MM}mm"
                )

        # Verify pressure limits don't exceed edition cap
        edition_cap = plan.safety_constraints.pressure_cap_kpa
        for zone in plan.zones:
            if zone.pressure_limit_kpa > edition_cap:
                raise GeometryValidationError(
                    f"Zone '{zone.zone_name}' pressure {zone.pressure_limit_kpa} kPa "
                    f"exceeds edition cap {edition_cap} kPa"
                )

        # Hybrid consistency
        if plan.is_hybrid:
            if plan.secondary_edition is None:
                raise GeometryValidationError(
                    "HYBRID mode requires secondary_edition"
                )
            if plan.blend_ratio[0] + plan.blend_ratio[1] < 0.99:
                raise GeometryValidationError(
                    "HYBRID blend_ratio must sum to ~1.0"
                )

    # ------------------------------------------------------------------
    # Schema access
    # ------------------------------------------------------------------
    @property
    def schema(self) -> Dict[str, Any]:
        return self._schema

    def validate_plan_against_schema(self, plan: GeometryPlan) -> List[str]:
        """Validate plan dict against geometry_runtime.schema.json."""
        errors: List[str] = []
        schema = self._load_schema()
        if not schema:
            return errors

        plan_dict = plan.to_dict()
        required = schema.get("required", [])
        props = schema.get("properties", {})

        for field_name in required:
            if field_name not in plan_dict:
                errors.append(f"Missing required field: {field_name}")

        # Check density values
        density_map = plan_dict.get("density_by_zone", {})
        density_props = props.get("density_by_zone", {}).get("patternProperties", {})
        if density_props:
            d_props = density_props.get("^.*$", {})
            d_min = d_props.get("minimum", DENSITY_MIN)
            d_max = d_props.get("maximum", DENSITY_MAX)
            for zone, val in density_map.items():
                if val < d_min or val > d_max:
                    errors.append(
                        f"density_by_zone.{zone}={val} out of range [{d_min}, {d_max}]"
                    )

        # Check safety constraints
        safety = plan_dict.get("safety_constraints", {})
        if safety.get("wall_thickness_mm", 0) < MIN_WALL_THICKNESS_MM:
            errors.append("wall_thickness_mm below minimum")

        return errors

    # ------------------------------------------------------------------
    # Batch / utility
    # ------------------------------------------------------------------
    def generate(
        self,
        scientific_decision,
    ) -> GeometryPlan:
        """Alias for from_decision — the main public API."""
        return self.from_decision(scientific_decision)


# ============================================================================
# Edition specs (mirrors scientific_layer for standalone use)
# ============================================================================
_EDITION_SPECS: Dict[str, Dict[str, Any]] = {
    "CALM": {
        "heel_density": 22, "midfoot_density": 20, "forefoot_density": 25,
        "toe_density": 22, "max_pressure_kpa": 45,
        "gyroid_cell_size_mm": 6.5,
        "stimulation_pattern": "static_soft",
        "comfort_risk_level": "Low",
        "manufacturing_notes": "SLS TPU 95A، مسامية عالية، تشطيب ناعم",
    },
    "VITAL": {
        "heel_density": 35, "midfoot_density": 32, "forefoot_density": 35,
        "toe_density": 30, "max_pressure_kpa": 65,
        "gyroid_cell_size_mm": 5.5,
        "stimulation_pattern": "static_firm",
        "comfort_risk_level": "Medium",
        "manufacturing_notes": "SLS TPU 95A، ضغط جانبي مقاوم",
    },
    "FOCUS": {
        "heel_density": 28, "midfoot_density": 25, "forefoot_density": 38,
        "toe_density": 42, "max_pressure_kpa": 60,
        "gyroid_cell_size_mm": 5.0,
        "stimulation_pattern": "zoned_firm_toe",
        "comfort_risk_level": "Medium",
        "manufacturing_notes": "MJF للدقة في منطقة الأصابع",
    },
    "BALANCE": {
        "heel_density": 30, "midfoot_density": 28, "forefoot_density": 30,
        "toe_density": 28, "max_pressure_kpa": 55,
        "gyroid_cell_size_mm": 6.0,
        "stimulation_pattern": "graduated_even",
        "comfort_risk_level": "Low-Medium",
        "manufacturing_notes": "SLS مع تحقق التدرج",
    },
    "FEMME": {
        "heel_density": 18, "midfoot_density": 17, "forefoot_density": 20,
        "toe_density": 18, "max_pressure_kpa": 42,
        "gyroid_cell_size_mm": 7.0,
        "stimulation_pattern": "static_ultra_soft",
        "comfort_risk_level": "Very Low",
        "manufacturing_notes": "SLS TPU 95A أليّن grade",
    },
}

"""Geometric constants and material-agnostic parameters for zilfit_orthotics."""

DEFAULT_UNIT = "mm"

# Coordinate bounds for raw intake validation (in mm)
# Origin at heel center. X: medial-lateral, Y: anterior-posterior, Z: dorsal-plantar
COORDINATE_BOUNDS = {
    "x": (-150.0, 150.0),   # mediolateral span
    "y": (-50.0, 350.0),    # anteroposterior span
    "z": (-80.0, 120.0),    # dorsoplantar span
}

# Standard geometric landmark labels
REFERENCE_LANDMARK_LABELS = [
    "heel_center",
    "met1_head",
    "met5_head",
    "hallux_tip",
    "calcaneus_lateral",
    "calcaneus_medial",
    "navicular",
    "lateral_malleolus",
    "medial_malleolus",
]

# Minimum landmarks required for a valid geometric analysis
MINIMUM_LANDMARKS = 5

# Geometric sanity thresholds
FEATURE_THRESHOLDS = {
    "foot_length_min_mm": 150.0,
    "foot_length_max_mm": 350.0,
    "foot_width_min_mm": 50.0,
    "foot_width_max_mm": 140.0,
    "arch_height_min_mm": 0.0,
    "arch_height_max_mm": 50.0,
    "width_ratio_min": 0.20,
    "width_ratio_max": 0.60,
    "alignment_offset_max_deg": 45.0,
}

# Default foot longitudinal axis (heel center → met2_head region in standard anatomy)
ALIGNMENT_AXIS = (0.0, 1.0, 0.0)

# Pressure zone y-axis fraction boundaries
ZONE_BOUNDARIES = {
    "heel": (0.0, 0.25),
    "midfoot": (0.25, 0.55),
    "forefoot": (0.55, 0.85),
    "toes": (0.85, 1.0),
}

# Arch geometry constants
ARCH_MIDFOOT_LOWER_Y = 0.25
ARCH_MIDFOOT_UPPER_Y = 0.55
ARCH_CONTACT_Z_THRESHOLD_MM = 2.0

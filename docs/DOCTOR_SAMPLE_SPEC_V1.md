# ZILFIT Doctor Sample Specification V1

## Engineering Specification for Sample Manufacturing

**NOT FOR PRODUCTION. NOT FOR SALE. NOT FOR CLINICAL USE. ENGINEERING EVALUATION ONLY.**

## Sample Identity

| Field | Value |
|-------|-------|
| Sample ID | SAMPLE-001 |
| Architecture | SA-001 |
| Geometry Profile | GP-2fe9594adf56 |
| Lattice Profile | LP-2fe9594adf56 |
| Edition | BALANCE |
| Preset | Balanced |
| Foot Size | EU42 (200mm length × 69.6mm width) |

## Layer Stack

| Layer | Component | Material | Thickness |
|-------|-----------|----------|-----------|
| L1 | Removable Liner | EVA foam (Shore 35C) + TPU lattice backing | 5.0mm |
| L2 | Sensor Plane | PA12 housings + coin-cell BLE nodes | 2.5mm |
| L3 | Skin Top | PA11 (MJF) | 1.5mm |
| L4 | Lattice Core | PA11 (MJF), gyroid TPMS | 24.0mm (heel) / 22.0mm (forefoot) |
| L5 | Skin Bottom | PA11 (MJF) | 1.5mm |
| L6 | Outsole Pads | TPU rubber Shore 60A | 3.0mm |

**Total Stack (heel):** 37.5mm
**Heel-to-Toe Drop:** 2.0mm
**Estimated Weight:** 208.6g (EU42)

## Manufacturing Process

| Parameter | Value |
|-----------|-------|
| Process | HP Multi Jet Fusion (MJF) |
| Material | PA11 (MJF core + skins), TPU rubber (outsole) |
| Layer Height | 0.11mm |
| Cell Size | 6.0mm gyroid |
| Min Wall Thickness | 0.8mm shell, 0.6mm lattice |
| Infill | 100% gyroid TPMS |
| Bed Temperature | 100°C |
| Cooling | Gradual chamber cooling |
| Support Policy | None required (self-supporting gyroid) |
| Post-Processing | Bead blasting + rose gold accents |
| Drying Requirement | TPU powder dried to < 0.02% moisture, 70°C, 4h minimum |

## Shell Zones

| Zone | Y-Fraction | Thickness | Material | Features |
|------|-----------|-----------|----------|----------|
| Heel Counter | 0.0–0.20 | 2.0mm | PA11 (MJF) | Heel cup, Achilles relief, outsole bonding |
| Midfoot Chassis | 0.20–0.55 | 2.0mm | PA11 (MJF) | Capsule access door, locating ribs, vent windows |
| Forefoot Cage | 0.55–0.80 | 1.5mm | PA11 (MJF) | Flex segmentation, upper bonding flange |
| Toe Cap | 0.80–1.00 | 1.5mm | PA11 (MJF) | Reinforced perforated, bumper ridge |

## Lattice Zone Densities

| Zone | Density | Cell Size | Stiffness | Flex | Energy Return |
|------|---------|-----------|-----------|------|---------------|
| Heel Impact | 0.31 | 5.85mm | 6 | 5 | 8 |
| Arch Bridge | 0.30 | 6.0mm | 6 | 5 | 6 |
| Midfoot Stabilisation | 0.28 | 6.0mm | 5 | 5 | 5 |
| Forefoot Propulsion | 0.29 | 6.0mm | 5 | 6 | 7 |
| Toe Release | 0.26 | 6.0mm | 4 | 8 | 4 |

## Outsole Pads

| Pad | Y-Fraction | Material | Tread |
|-----|-----------|----------|-------|
| Heel Strike | 0.0–0.18 | TPU rubber Shore 60A | Wave |
| Lateral Midfoot | 0.35–0.50 | TPU rubber Shore 60A | Wave |
| Met Heads | 0.60–0.78 | TPU rubber Shore 60A | Wave |
| Hallux | 0.82–0.98 | TPU rubber Shore 60A | Wave |

## Sensor Integration

| Component | Spec |
|-----------|------|
| MCU | ESP32-C3-MINI-1 (preferred) |
| BLE Version | 5.0 |
| Battery | Li-Po 180 mAh, 3.7V |
| Runtime | 36 hours at 1Hz |
| Charging | USB-C (not in-shoe) |
| Sensors | Pressure (heel/arch/forefoot), IMU, temperature |

## Quality Requirements

| Check | Target |
|-------|--------|
| Dimensional Accuracy | ±0.15mm |
| Wall Thickness | ≥ 0.8mm all zones |
| Manifold | Watertight, zero non-manifold edges |
| Density Deviation | ≤ 15% between adjacent zones |
| Weight Tolerance | ±15% of target (208.6g) |
| Flexibility Score | Midfoot ≥ 5, Forefoot ≥ 6 |

## Non-Clinical Disclaimer

This specification contains engineering design parameters for prototype manufacturing evaluation only. No medical, therapeutic, diagnostic, or corrective function is claimed. For engineering assessment only. Not for production. Not for sale.

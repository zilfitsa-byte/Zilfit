# ZILFIT FIRST_REAL_SAMPLE — TPU / MJF Print Settings

**RUN ID:** FIRST_REAL_SAMPLE
**DATE:** 2026-05-27
**MACHINE:** HP Multi Jet Fusion (MJF)
**SAMPLE ONLY — NOT FOR PRODUCTION**

## Material Settings

### PA11 (Shell, Lattice, Skins)

| Parameter | Value |
|-----------|-------|
| Material | PA11 powder |
| Layer height | 0.11 mm |
| Chamber temperature | 100–120°C |
| Fusing agent density | Standard (1.0×) |
| Detailing agent | Enabled for sharp edges |
| Cooling profile | Gradual — 2°C/min ramp down from 100°C to 40°C over 30 min |
| Powder refresh ratio | 20% fresh / 80% recycled |
| Minimum cooling before removal | Chamber < 40°C |
| Drying requirement | 70°C × 4h, < 0.02% moisture |

### TPU Rubber (Outsole Pads)

| Parameter | Value |
|-----------|-------|
| Material | TPU rubber Shore 60A powder |
| Layer height | 0.11 mm |
| Chamber temperature | 100°C |
| Fusing agent density | 1.1× (compensate for TPU energy absorption) |
| Detailing agent | Enabled |
| Cooling profile | Gradual — 1.5°C/min to prevent warping |
| Powder refresh ratio | 30% fresh / 70% recycled |
| Drying requirement | 70°C × 4h, < 0.02% moisture |
| Post-fusing hold | 15 min at 100°C before cooling ramp |

### PA12 (Sensor Housings)

| Parameter | Value |
|-----------|-------|
| Material | PA12 powder (SLS process) |
| Layer height | 0.10 mm |
| Chamber temperature | 170°C |
| Laser power | Standard |
| Drying requirement | 80°C × 6h |

## Component-Specific Settings

### Lattice Core (LATTICE-001)
- Infill: 100% gyroid TPMS
- Cell size: 6.0 mm base
- Density map: 5 zones at 0.26–0.31
- Wall thickness: 0.6 mm (gyroid strut)
- No outer shell — lattice is exposed
- Orientation: Z+ = shoe height axis
- Build plate placement: Center, isolated (largest part)

### Shell Parts (SHELL-001 through SHELL-004)
- Wall thickness: 1.5–2.0 mm
- Infill: 100% solid
- Perimeter count: 2
- Locating ribs: 0.2 mm clearance for lattice fit
- Capsule door (SHELL-002): Print in open position with 0.3 mm hinge gap
- Orientation: Exterior face up on build plate

### Skins (SKIN-001, SKIN-002)
- Wall thickness: 1.5 mm uniform
- Infill: 100% solid
- Surface finish: Smooth (top and bottom faces)
- Orientation: Flat on build plate (largest face down)

### Outsole Pads (OUTSOLE-001 through OUTSOLE-004)
- Wall thickness: 3.0 mm
- Infill: 100% solid TPU
- Tread pattern: Wave (0.5 mm depth, 2 mm pitch)
- Shore hardness target: 60A
- Orientation: Tread face up (bonding face down)
- No post-processing required beyond depowder

### Sensor Housings (SENSOR-001)
- Wall thickness: 0.8 mm
- Internal cavity: 18 × 12 × 5 mm (ESP32) + 15 × 12 × 4 mm (battery)
- Snap-fit lid: 0.2 mm interference fit
- Orientation: Cavity opening facing up

## Quality Settings

| Parameter | PA11 | TPU | PA12 |
|-----------|------|-----|------|
| Dimensional tolerance | ±0.15 mm | ±0.2 mm | ±0.15 mm |
| Surface roughness (Ra) | < 8 μm | < 10 μm | < 6 μm |
| Density variation | ±5% | ±5% | ±3% |
| Porosity rejection | > 2% void | > 3% void | > 1% void |

## Post-Processing

1. **Depowder** — Compressed air at 4 bar, all parts
2. **Bead blast** — PA11 parts only, 60-grit glass bead, 3 bar, 30s per part
3. **Dye (optional)** — Rose gold accent on shell exterior surfaces
4. **No post-processing** — TPU outsole pads (matte as-printed)
5. **Sensor housings** — Hand-finish snap-fit edges with 400-grit

## Machine Preparation Checklist

- [ ] Build unit cleaned, residual powder removed
- [ ] Powder hoppers filled with dried material
- [ ] Fusing/detailing agent reservoirs filled
- [ ] Printhead alignment verified
- [ ] Chamber pre-heated to target temp
- [ ] Build plate leveled
- [ ] First-layer test coupon printed and inspected (new powder batch)
- [ ] Temperature calibration coupon verified

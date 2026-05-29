# ZILFIT FIRST_REAL_SAMPLE — Assembly Order

**RUN ID:** FIRST_REAL_SAMPLE
**TARGET:** 1 pair (2 shoes) — LEFT SHOE first, then RIGHT
**STATUS:** SAMPLE ONLY — ENGINEERING EVALUATION

## Pre-Assembly Parts Check

### LEFT SHOE — Verify Before Assembly

| # | Component | Part ID | Qty | Verify |
|---|-----------|---------|-----|--------|
| 1 | Lattice Core (full foot) | LATTICE-001 | 1 | [ ] Density QC passed, no broken cells |
| 2 | Heel Counter | SHELL-001 | 1 | [ ] No cracks, bead blast done |
| 3 | Midfoot Chassis | SHELL-002 | 1 | [ ] Capsule door opens/closes freely |
| 4 | Forefoot Cage | SHELL-003 | 1 | [ ] Flex lines visible, no cracks |
| 5 | Toe Cap | SHELL-004 | 1 | [ ] Perforations clear, bumper ridge intact |
| 6 | Skin Top | SKIN-001 | 1 | [ ] Smooth surface, 1.5mm uniform |
| 7 | Skin Bottom | SKIN-002 | 1 | [ ] Smooth surface, outsole bonding face clean |
| 8 | Heel Strike Pad | OUTSOLE-001 | 1 | [ ] Tread pattern sharp, no voids |
| 9 | Lateral Midfoot Pad | OUTSOLE-002 | 1 | [ ] Correct side, pad aligns with shell |
| 10 | Met Heads Pad | OUTSOLE-003 | 1 | [ ] Tread pattern sharp |
| 11 | Hallux Pad | OUTSOLE-004 | 1 | [ ] Smallest pad, check orientation |
| 12 | Sensor Housing | SENSOR-001 | 1 | [ ] Cavity fits ESP32 + battery |
| 13 | Removable Liner | LINER-001 | 1 | [ ] EVA foam intact, 3-pin holes aligned |
| 14 | ESP32-C3 Module | ELEC-001 | 1 | [ ] Programmed, BLE advertising verified |
| 15 | Li-Po Battery | ELEC-002 | 1 | [ ] 3.7V, USB-C port functional |
| 16 | Sensor Nodes (×3) | ELEC-003 | 3 | [ ] Pressure/IMU/temp calibrated |

## Assembly Sequence

### Station 1 — Shell Dry Fit (5 min)
1. Place SHELL-001 (heel), SHELL-002 (midfoot), SHELL-003 (forefoot), SHELL-004 (toe) in order
2. Verify all 4 shell segments align end-to-end
3. Check locating rib alignment marks
4. **DO NOT BOND YET — dry fit only**
5. Record any interference or gaps in assembly log

### Station 2 — Lattice Core Insertion (10 min)
1. Orient LATTICE-001: heel (dense) end matches heel counter
2. Lower lattice into assembled shell from top
3. Verify lattice fully seats into locating ribs
4. Check 5 zone positions match shell zones:
   - Heel (0.0–0.20Y): heel counter zone
   - Arch (0.20–0.40Y): midfoot chassis start
   - Midfoot (0.40–0.55Y): midfoot chassis end
   - Forefoot (0.55–0.80Y): forefoot cage
   - Toe (0.80–1.00Y): toe cap
5. Remove lattice, verify no binding. **Re-insert for final assembly.**

### Station 3 — Electronics Installation (15 min)
1. Insert ESP32-C3 module into SENSOR-001 housing
2. Connect battery to ESP32 (DO NOT POWER ON YET)
3. Place 3 sensor nodes: heel cavity, arch cavity, forefoot cavity
4. Route wires through internal channels
5. Snap-fit SENSOR-001 housing into medial cavity (SHELL-002)
6. Close capsule access door
7. **DO NOT power on until Station 6**

### Station 4 — Skin Application (5 min)
1. Place SKIN-002 (bottom) under lattice — smooth side faces outsole
2. Place SKIN-001 (top) over lattice — smooth side faces liner
3. Verify skins fully cover lattice surface
4. Check edge alignment with shell walls

### Station 5 — Liner Snap (5 min)
1. Align LINER-001 3-pin holes with receiving holes in shell
2. Press liner firmly until all 3 pins click
3. Verify liner is flush with shell top edge
4. Remove and re-insert to verify snap-fit works

### Station 6 — BLE Activation + Pairing Test (10 min)
1. Power on ESP32-C3 (connect battery)
2. Scan for BLE device: "ZILFIT-SAMPLE-001-L"
3. Verify device advertises with service UUID
4. Read pressure values from 3 sensor nodes
5. Verify IMU accelerometer responds to movement
6. Verify temperature sensor reads ambient
7. Power off — **SHIP WITH BATTERY DISCONNECTED**

### Station 7 — Outsole Bonding (HEAT-PRESS) (15 min)
1. Clean SKIN-002 bottom surface with isopropyl alcohol
2. Apply heat-activated adhesive in thin film to bonding zones
3. Place OUTSOLE-001 (heel) → OUTSOLE-002 (lateral midfoot) → OUTSOLE-003 (met heads) → OUTSOLE-004 (hallux)
4. Heat-press: 120°C, 30s per pad, 2 bar pressure
5. Verify all 4 pads are flush with no lifting at edges
6. Allow 10 min cool-down before handling

### Station 8 — Final QC (10 min)
1. Weight check: target 208.6g ±15% (177–240g)
2. Visual: no exposed lattice, no gaps between shell segments
3. Flex test: bend at midfoot (Y=0.40–0.55), check for cracking
4. Drop test: 30cm onto carpeted surface
5. Liner remove/replace: 3 cycles
6. BLE quick scan: device name visible
7. Record all measurements in QC log

## Assembly Tools Required

- [ ] Isopropyl alcohol (99%)
- [ ] Heat press (120°C capable)
- [ ] Heat-activated TPU adhesive
- [ ] Digital calipers (±0.01mm)
- [ ] Digital scale (±0.1g)
- [ ] BLE scanner (phone app or dedicated)
- [ ] Torque screwdriver (for electronics)
- [ ] Lint-free cloths
- [ ] Assembly gloves (nitrile)
- [ ] Assembly log sheet

## After LEFT Shoe Complete

Repeat entire assembly for RIGHT shoe.

**RIGHT SHOE BLE NAME:** "ZILFIT-SAMPLE-001-R"

### Right Shoe Verification
- [ ] Outsole pads are mirrored (not duplicate of left)
- [ ] Midfoot chassis door is on MEDIAL side (inside of foot)
- [ ] Weight should match left shoe within ±5g

## Post-Assembly Pair Check

- [ ] Left shoe weight: ___________ (target: 177–240g)
- [ ] Right shoe weight: ___________ (target: 177–240g)
- [ ] Weight delta L/R: ___________ (target: < 10g)
- [ ] Both shoes pair successfully with BLE scanner
- [ ] Both shoes pass 30cm drop test
- [ ] Both liners snap in/out freely
- [ ] Ready for first-test protocol

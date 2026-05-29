# Adaptive Geometry Engine V1.0

**Date:** 2026-05-27
**Status:** Rules layer only — no real-time adaptation hardware active yet

---

## 1. Purpose

The Adaptive Geometry Engine converts Smart Capsule gait metrics into
concrete sole design parameters. It is a deterministic rules engine that
maps sensor outputs to geometry decisions.

No machine learning in this layer. Every decision is traceable to a
numeric input signal.

---

## 2. Input Signals

| Signal | Source | Range | Meaning |
|--------|--------|-------|---------|
| `pressure_balance` | Capsule report | 0.3–3.0 | Rearfoot/forefoot pressure ratio |
| `roll_angle` | Capsule report | 0°–20° | Medial-lateral roll during stance |
| `fatigue_signal` | Capsule report | 0–30 | Gait symmetry drift (% decay) |
| `steps` | Capsule report | 0–5000 | Steps in session |
| `foot_type` | ML classifier | normal, low_arch_geometric, high_arch_geometric | Geometric arch label |

---

## 3. Geometry Output Parameters

| Parameter | Range | Unit | Meaning |
|-----------|-------|------|---------|
| `heel_cushion_level` | 1–5 | ordinal | Cushioning depth assigned to heel zone |
| `arch_support_level` | 1–5 | ordinal | Support aggressiveness at arch bridge |
| `medial_support_bias` | 0–100 | percent | Bias toward medial (inner) side |
| `lateral_support_bias` | 0–100 | percent | Bias toward lateral (outer) side |
| `flexibility_score` | 1–5 | ordinal | Forefoot flex allowance |
| `fatigue_adjustment` | 0–100 | percent | Overall density scaling due to fatigue |
| `next_revision_notes` | text | — | Human-readable geometry change direction |

---

## 4. Pressure-to-Geometry Mapping

### Heel Cushioning

```
heel_cushion_level = CLAMP(ROUND(3.5 - pressure_balance), 1, 5)
```

- pressure_balance < 0.7 → heavy heel strike → increase heel cushion (level 4–5)
- pressure_balance > 1.5 → forefoot-dominant → reduce heel cushion (level 1–2)
- pressure_balance 0.7–1.5 → neutral (level 2–4)

### Arch Support

```
arch_support_level = 3  (base)
+ (-1 if foot_type == "low_arch_geometric" else 0)
+ (+1 if foot_type == "high_arch_geometric" else 0)
+ (+1 if fatigue_signal > 8.0 else 0)
CLAMP(1, 5)
```

- High arch → increase support
- Low arch → decrease support
- High fatigue → slight boost in support density

### Forefoot Flexibility

```
flexibility_score = 3 (base)
+ (-1 if steps > 3000 else 0)
CLAMP(1, 5)
```

- Long sessions → softer forefoot (flexibility 4–5)
- Short sessions → firmer forefoot (flexibility 2–3)

---

## 5. Pronation Compensation Geometry

Roll angle |roll_angle| maps to medial/lateral support bias.

```
bias_delta = CLAMP(|roll_angle| * 6.0, 0, 50)

IF roll_angle > 0 (foot rolls inward):
    medial_support_bias = 50 + bias_delta   // reinforce medial side
    lateral_support_bias = 50 - bias_delta  // reduce lateral side

IF roll_angle < 0 (foot rolls outward):
    medial_support_bias = 50 - bias_delta
    lateral_support_bias = 50 + bias_delta

IF |roll_angle| < 3°:
    medial_support_bias = 50
    lateral_support_bias = 50  // neutral
```

This is **geometric compensation only**. The engine does not diagnose
pronation or supination. It responds to measured roll angle as a
purely mechanical signal.

---

## 6. Fatigue Response Logic

Fatigue signal is the percentage decay in heel pressure peak amplitude
compared to session start.

```
fatigue_adjustment = CLAMP(fatigue_signal * 1.2, 0, 30)

IF fatigue_adjustment > 15:
    // Significant fatigue — soften overall density
    heel_cushion_level += 1
    flexibility_score += 1
    arch_support_level += 1

CLAMP all to valid ranges
```

---

## 7. Dynamic Support Zones

Each session can update zone parameters independently:

| Zone | Affected by |
|------|-------------|
| Heel basin | pressure_balance, fatigue_signal |
| Arch bridge | foot_type, fatigue_signal |
| Midfoot calm channel | flexibility_score |
| Forefoot release grid | steps, flexibility_score |
| Medial stability | roll_angle |
| Lateral stability | roll_angle |

Changes are accumulated across sessions in `adaptive_reports/` as a
revision log.

---

## 8. Doctor Override Mode

When `mode = "doctor_override"`, all automated geometry decisions are
held frozen. The doctor's manual feedback form values directly set
each zone parameter.

Override fields:
```json
{
  "mode": "doctor_override",
  "heel_cushion_override": 4,
  "arch_support_override": 3,
  "medial_bias_override": 65,
  "lateral_bias_override": 35,
  "flexibility_override": 3,
  "doctor_notes": "Patient reports arch pressure at level 3. Reduce to 2 next revision."
}
```

---

## 9. Private Tester Mode

When `mode = "private_tester"`, the engine runs fully automated and
generates a `next_revision_notes` string summarizing changes. No
doctor intervention required. All decisions are logged.

---

## 10. Non-Clinical Disclaimer

> All geometry parameters are engineering design values. They do not
> constitute medical advice, treatment prescription, or diagnostic
> recommendation. Doctor overrides represent professional opinion for
> comfort evaluation only.

---

*End of Adaptive Geometry Engine V1.0*

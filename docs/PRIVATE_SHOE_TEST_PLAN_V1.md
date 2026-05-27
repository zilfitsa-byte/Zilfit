# Private Shoe Test Plan V1.0

**Date:** 2026-05-27
**Status:** Pre‑tester recruitment — no testers enrolled yet

---

## 1. Purpose

This document defines the ZILFIT private shoe evaluation programme.
The goal is to collect real‑world gait metrics, comfort feedback, and
geometric fit data from a small group of private testers before any
doctor sample distribution or production decision.

All outputs are engineering evaluation data. No medical claims are made.

---

## 2. Tester Profile

| Criteria | Requirement |
|----------|-------------|
| Number of testers | 5 minimum |
| Age range | 25–55 |
| Activity | Regular walking (≥ 30 min / day) |
| Foot conditions | Not screened — no medical intake |
| Consent | Signed engineering evaluation waiver |

**Exclusion:** No medical screening. Testers self‑select as volunteers
for engineering comfort and gait feedback only.

---

## 3. Equipment Per Tester

- 1 pair ZILFIT test shoes with 3D‑printed soles
- 1 Smart Capsule V0.1 sensor module (inserted in right shoe)
- 1 printed instruction sheet
- 1 feedback form (paper or digital)

---

## 4. Test Protocol

### Session 1: Baseline Walk
- Duration: 15 minutes
- Route: Flat indoor surface
- Data collected: Smart Capsule stream
- Tester completes comfort feedback form

### Session 2: Varied Surface
- Duration: 20 minutes
- Route: Mixed indoor/outdoor (pavement)
- Data collected: Smart Capsule stream
- Tester completes comfort feedback form

### Session 3: Extended Wear
- Duration: 45 minutes
- Route: Tester's choice
- Data collected: Smart Capsule stream
- Tester completes comfort feedback form + final summary

---

## 5. Data Collected Per Session

| Data Type | Source | Format |
|-----------|--------|--------|
| Pressure (4 channels) | Smart Capsule | CSV |
| IMU (6‑axis) | Smart Capsule | CSV |
| Temperature | Smart Capsule | CSV |
| Steps estimate | Report generator | JSON |
| Gait events | Report generator | JSON |
| Pressure balance | Report generator | JSON |
| Fatigue signal | Report generator | JSON |
| Comfort rating (1–5) | Tester form | Paper/digital |
| Fit rating (1–5) | Tester form | Paper/digital |
| Perceived support rating (1–5) | Tester form | Paper/digital |
| Irritation notes | Tester form | Text |

---

## 6. Report Generation

After each session:
```bash
python3 tools/smart_capsule_report.py \
    --input smart_capsule_data/session_CAP_NNN.csv \
    --output smart_capsule_reports/report_CAP_NNN.json
```

Weekly summary for all testers:
```bash
python3 tools/smart_capsule_report.py \
    --batch smart_capsule_data/ \
    --output smart_capsule_reports/weekly_summary.json
```

---

## 7. Tester Privacy

- Testers are identified by anonymous ID only (T01–T05)
- No personal health data collected
- No medical history recorded
- Gait metrics stored as engineering data
- Consent forms stored separately from data

---

## 8. Success Criteria

| Criterion | Threshold |
|-----------|-----------|
| Sessions completed | ≥ 12 out of 15 |
| Valid Smart Capsule data | ≥ 95% of session time |
| Comfort feedback returned | ≥ 80% of sessions |
| Design changes identified | ≥ 3 actionable items |
| Tester retention | ≥ 4 of 5 testers complete all sessions |

---

## 9. Post‑Evaluation

1. Aggregate all gait metrics across testers
2. Identify common comfort/fit patterns
3. Generate design change recommendations
4. Present findings to Sultan
5. Integrate approved changes into next sole iteration
6. Archive raw data and reports

---

*End of Private Shoe Test Plan V1.0*

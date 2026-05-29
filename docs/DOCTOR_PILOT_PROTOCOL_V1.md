# Doctor Pilot Protocol V1.0

**Date:** 2026-05-27
**Status:** Planning — no doctors enrolled

---

## 1. Purpose

Run a structured 5-doctor pilot evaluation of ZILFIT engineering
samples before patent filing. Collect structured geometric feedback
under secrecy constraints.

---

## 2. Doctor Selection Criteria

| Criterion | Requirement |
|-----------|-------------|
| Specialty | Podiatry, orthopedics, sports medicine, or biomechanics |
| Practice | Active clinical practice, min 3 years |
| Location | Same city as ZILFIT operations (control distribution) |
| NDA | Signed before receiving any sample |
| Prior relationship | None required — cold outreach acceptable |

---

## 3. Pre-Distribution Flow

```
1. Sultan identifies 5 doctor candidates
2. NDA drafted and signed (physical or DocuSign)
3. Sample pack generated: sample_packs/ZILFIT_SAMPLE_D01-D05
4. Physical samples printed and paired with packs
5. Sultan hand-delivers or couriers each pack
6. Distribution date logged in pilot manifest
```

---

## 4. Sample Pack Contents (per doctor)

- 1 pair ZILFIT soles (left + right)
- Printed sample pack folder (SAMPLE_SUMMARY, DISCLAIMER, FEEDBACK_FORM, etc.)
- 1 Smart Capsule simulator report (if capsule available)
- 1 return envelope (prepaid, addressed to ZILFIT)
- 1 instruction card

---

## 5. Evaluation Metrics

Each doctor evaluates:

| Metric | Scale | Method |
|--------|-------|--------|
| Comfort | 1–5 | Visual analog + written notes |
| Fit | Pass/Fail | Fit check against foot |
| Perceived arch support | 1–5 | Subjective rating |
| Heel stability | 1–5 | Subjective rating |
| Lateral stability | 1–5 | Subjective rating |
| Forefoot freedom | 1–5 | Subjective rating |
| Material feel | 1–5 | Tactile assessment |
| Geometric modifications | Free text | Open-ended recommendation |

---

## 6. Revision Cycle

```
Week 1: Distribute samples
Week 2: Doctors evaluate (wear test, no patient use)
Week 3: Feedback forms returned
Week 4: ZILFIT team processes feedback → geometry revision
Week 5: Revised samples printed
Week 6: Revised samples distributed to same doctors
Week 7: Second round feedback collected
Week 8: Final design locked for patent filing
```

---

## 7. Secrecy Protocol (Pre-Patent)

| Rule | Enforcement |
|------|-------------|
| NDA required before any disclosure | Signed document on file |
| No photos of sole geometry allowed | Stated in NDA + instruction card |
| No public discussion of design | NDA clause |
| Sample labeled "CONFIDENTIAL — Engineering Evaluation" | Printed on label |
| All feedback returned via sealed envelope | Physical or encrypted digital |
| No social media mention | NDA + reminder in follow-up |
| Doctor names never published | Coded as D01–D05 in all reports |

---

## 8. Post-Pilot

1. Aggregate all doctor feedback into `reports/doctor_pilot_round1.json`
2. Identify 3–5 actionable geometry changes
3. Generate revised sample packs
4. Repeat evaluation cycle
5. Lock final geometry
6. File provisional patent
7. Secrecy restrictions lifted (limited)

---

## 9. Non-Clinical Disclaimer

> The Doctor Pilot Program is an engineering evaluation. Doctors
> provide professional opinion on geometric comfort and fit only.
> No patient use is authorized. No medical or therapeutic claims
> are made by ZILFIT or solicited from doctors.

---

*End of Doctor Pilot Protocol V1.0*

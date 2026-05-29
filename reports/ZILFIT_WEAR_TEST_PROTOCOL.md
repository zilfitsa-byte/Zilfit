# ZILFIT Wear Test Protocol

> Engineering evaluation protocol — not a medical, clinical, or therapeutic study.
> All data collected is for engineering purposes only.
> No medical claims, diagnoses, or treatment assessments are generated or implied.

---

## 1. Adaptation Period

| Phase | Duration | Instructions |
|---|---|---|
| **Day 1** | 1–2 hours | Wear in normal shoe; remove if any discomfort |
| **Day 2** | 2–4 hours | Extend wear; perform normal activities |
| **Day 3** | 4–8 hours | Full-day wear; this is the assessment baseline |
| **Day 4–7** (optional) | Full day | Extended adaptation observation |

**Rule:** If a wearer experiences any discomfort, they remove the insole immediately. Discomfort data is logged as engineering feedback (pressure point location), not as a medical observation.

---

## 2. Scoring System

All scores are **1–10 integer scale** unless noted otherwise.

### 2.1 Comfort Score

| Question | Scale | Measurement |
|---|---|---|
| Overall comfort while walking | 1 (uncomfortable) – 10 (very comfortable) | Primary metric |
| Comfort after 1 hour of continuous wear | 1–10 | Fatigue indicator |
| Comfort after removing insole (residual sensation) | 1 (unpleasant) – 10 (pleasant) | Rebound indicator |
| Would you voluntarily keep wearing these? | Yes / No / Unsure | Retention proxy |

**Pass threshold:** Average comfort score ≥ 7.0 across ≥ 5 wearers.

### 2.2 Stability Score

| Question | Scale | Measurement |
|---|---|---|
| Stability while walking on level ground | 1 (unstable) – 10 (very stable) | Primary metric |
| Stability on stairs | 1–10 | Vertical transition test |
| Stability on uneven surfaces | 1–10 | Real-world terrain test |
| Any slip or twist sensation? | Yes / No | Binary fail flag |

**Pass threshold:** Average stability ≥ 7.0; zero slip/twist reports.

### 2.3 Fatigue Score

| Question | Scale | Measurement |
|---|---|---|
| Foot fatigue after 1 hour | 1 (extreme fatigue) – 10 (no fatigue) | Early fatigue indicator |
| Foot fatigue after full day (Day 3) | 1–10 | Endurance metric |
| Difference between Day 1 and Day 3 comfort | +3 (better) to −3 (worse) | Adaptation delta |
| Energy level at end of wear day (relative to usual) | 1 (much lower) – 10 (much higher) | Subjective wellness |

**Pass threshold:** Fatigue delta (Day 3 − Day 1) ≥ −1.0 (no significant degradation).

---

## 3. Daily Wear Duration

| Day | Minimum Duration | Maximum Duration | Notes |
|---|---|---|---|
| 1 | 1 hour | 2 hours | Introduction |
| 2 | 2 hours | 4 hours | Extension |
| 3 | 4 hours | 8 hours | Full assessment |
| 4–7 | 6 hours | Full day | Optional extended |

Data is only considered valid if minimum duration is met.

---

## 4. User Feedback Normalization

### 4.1 Normalization Method

Raw scores from different users are normalized to account for individual response bias:

1. **Individual baseline:** Each wearer provides a "usual insole comfort" baseline score (1–10) before ZILFIT trial
2. **Delta scoring:** All ZILFIT scores are converted to delta from individual baseline
3. **Aggregate:** Mean delta and standard deviation computed across wearers

```
normalized_score = raw_score − individual_baseline
```

### 4.2 Outlier Handling

| Condition | Action |
|---|---|
| Score deviates > 2σ from group mean | Flag for review; do not auto-exclude |
| Incomplete data (< minimum duration) | Mark as partial; exclude from aggregate but retain raw data |
| Contradictory responses (e.g., comfort 10 but "wouldn't wear again") | Flag for follow-up discussion |

---

## 5. Prohibited Medical Interpretation

The following interpretations are **strictly prohibited** during wear testing:

| Prohibited | Reason |
|---|---|
| ❌ "Reduces foot pain" | Medical claim |
| ❌ "Improves posture" | Medical/therapeutic claim |
| ❌ "Prevents injury" | Medical claim |
| ❌ "Supports recovery from..." | Therapeutic claim |
| ❌ "Clinically validated" | Regulatory implication |
| ❌ "Recommended by doctors" | Misleading endorsement |
| ❌ "Treats plantar fasciitis" | Medical device claim |

**Allowed interpretations:**
| Allowed | Reason |
|---|---|
| ✅ "Users reported higher comfort than their usual insole" | Subjective feedback summary |
| ✅ "Zone-specific density was perceived as [firm/soft]" | Design feedback |
| ✅ "X% of testers would continue wearing the insole" | User behavior data |
| ✅ "No adverse reactions reported during testing period" | Safety observation (negative finding) |

---

## 6. Data Collection Template

| Field | Type | Notes |
|---|---|---|
| tester_id | String (anonymized) | No PII stored |
| edition_tested | String | CALM / BALANCE / FOCUS |
| shoe_size | String | EU size |
| shoe_type | String | Sneaker / dress shoe / boots |
| day | Integer | 1–7 |
| duration_minutes | Integer | Actual wear time |
| comfort_score | Integer 1–10 | Primary metric |
| stability_score | Integer 1–10 | Primary metric |
| fatigue_score | Integer 1–10 | Primary metric |
| slip_or_twist | Boolean | Fail flag |
| pressure_point_description | Text (optional) | Engineering feedback |
| additional_notes | Text (optional) | Open feedback |
| would_wear_again | Enum: yes/no/unsure | Retention proxy |

---

## 7. Test Administration Notes

1. **Environment:** Normal daily activities; no controlled exercise required
2. **Footwear:** Wearer's own shoes (documented); ZILFIT insole replaces existing insole
3. **Blinding:** Not blinded — wearer knows they are testing a new product
4. **Consent:** Explain engineering-only nature; no health claims made
5. **Data storage:** All data logged to `learning/experiments.db` via Emotion Session Layer
6. **Review:** Results reviewed by Z-Claims before any external communication

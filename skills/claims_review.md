# Skill: Claims Review

**Document:** skills/claims_review.md
**Version:** 1.0
**Phase:** C2 — Foundation Implementation
**Date:** 2026-05-10
**Owner:** Sultan
**Status:** Active

---

## Purpose

Define the process for reviewing all user-facing, public, and product claims to ensure compliance with safety boundaries. This skill blocks medical, diagnostic, therapeutic, or clinical claims and ensures all outputs use engineering-only language unless explicitly reviewed and approved.

---

## When to Use

Use this skill when:

1. Reviewing any user-facing copy or labels
2. Reviewing demo files for claims
3. Reviewing product descriptions or marketing materials
4. Reviewing agent outputs for claim compliance
5. Reviewing any text that will be visible to end users

---

## Inputs

- **Text to review** — Any user-facing text, copy, or labels
- **Source file** — File containing the text
- **Context** — Where the text will be used (demo, product description, etc.)
- **Agent output** — Any agent-generated text requiring review

---

## Outputs

- **Claim classification** — ALLOWED, NEEDS_SOFTENING, FORBIDDEN, or NEEDS_EVIDENCE
- **Safer rewrites** — Proposed safer wording for problematic claims
- **Evidence requirements** — What evidence is needed for claims
- **Escalation recommendations** — When to escalate to specialist review
- **Arabic report** — Summary of claim review

---

## Allowed Read Paths

- `/root/hermes/zilfit-ip-core/` — Full read access for context gathering
- `demo/` — All demo files for claim review
- `reports/` — All agent reports for claim auditing
- `governance/` — All governance documents for reference
- `AGENTS.md` — Agent operating guide

---

## Allowed Write Paths

- `reports/claims/` — Claim audit logs and classification results
- `governance/` — Claim policy proposals (read-only unless approved)

---

## Forbidden Paths

- `.env` — Never read or write
- `telegram_bot/bot.py` — Never modify without Sultan approval
- `telegram_bot/run.sh` — Never modify without Sultan approval
- `telegram_bot/classifier.py` — Never modify without Sultan approval
- `cron/` — Never modify without Sultan approval
- `systemd/` — Never modify without Sultan approval
- `tmux` sessions — Never modify without Sultan approval

---

## Approval Requirement

| Action | Approval Required | Reason |
|--------|-------------------|--------|
| Review claims | No | Review is always allowed |
| Classify claims | No | Classification is always allowed |
| Propose safer rewrites | No | Proposals are always allowed |
| Approve medical claims | Yes | Medical claims require Sultan approval |
| Modify governance/Z_CLAIMS_SKILLS.md | Yes | Policy changes require Sultan approval |

---

## Blocked Claim Categories

### Medical / Clinical / Therapeutic Claims (FORBIDDEN)

**Never make these claims:**

- "This reduces pain"
- "This treats plantar fasciitis"
- "This is therapeutic"
- "This is diagnostic"
- "This cures"
- "This prevents injury"
- "This heals"
- "This relieves symptoms"
- "This is medically proven"
- "This is clinically validated"

### Diagnostic Claims (FORBIDDEN)

**Never make these claims:**

- "This diagnoses foot problems"
- "This detects pressure issues"
- "This identifies gait abnormalities"
- "This measures health metrics"
- "This assesses foot health"

### Treatment Claims (FORBIDDEN)

**Never make these claims:**

- "This treats foot conditions"
- "This corrects posture"
- "This alleviates pain"
- "This improves circulation"
- "This strengthens muscles"

### Overstated Efficacy Claims (NEEDS_EVIDENCE)

**Claims requiring evidence:**

- "This improves comfort" (requires user testing evidence)
- "This enhances performance" (requires performance data)
- "This is better than alternatives" (requires comparative data)
- "This is optimal" (requires optimization evidence)

---

## Allowed Engineering-Only Wording

### Safe Phrasing

- "This is an engineering estimate based on simulation"
- "This is a design hypothesis requiring validation"
- "This is a theoretical model"
- "This is a preliminary finding"
- "This requires further testing"
- "This is a simulation result"
- "This is a design concept"
- "This is an engineering prototype"

### Examples of Safe vs Forbidden Phrasing

| Forbidden | Allowed | Reason |
|-----------|---------|--------|
| "This reduces foot pain" | "This is an engineering estimate for pressure distribution" | Medical claim vs engineering estimate |
| "This treats plantar fasciitis" | "This is a design hypothesis requiring clinical validation" | Treatment claim vs hypothesis |
| "This is proven" | "This is a simulation result requiring physical testing" | Absolute claim vs qualified result |
| "This will work" | "This is a theoretical model requiring validation" | Certainty vs uncertainty |
| "This prevents injury" | "This is a design concept for pressure management" | Prevention claim vs design concept |
| "This is medically proven" | "This is an engineering simulation" | Medical validation vs engineering simulation |

---

## Escalation to Specialist Review

### When to Escalate

Escalate to Sultan or specialist review when:

1. **Medical claim detected** — Any medical, diagnostic, therapeutic, or clinical language
2. **Borderline claim** — Claim that could be interpreted as medical
3. **Evidence required** — Claim that requires clinical or user testing evidence
4. **Regulatory concern** — Claim that might trigger regulatory review
5. **Public-facing material** — Any text intended for public consumption

### Escalation Process

1. **Identify the claim** — What is the problematic text?
2. **Classify the claim** — Is it forbidden, needs softening, or needs evidence?
3. **Propose safer wording** — What is the engineering-only alternative?
4. **Document the context** — Where is this text being used?
5. **Escalate to Sultan** — Present the situation and request guidance

### Escalation Template

```markdown
## 🚨 Claim Review Escalation Required

**Reviewer:** Z-Claims
**Time:** {YYYY-MM-DD HH:MM UTC}
**Source:** {file path}

### Problematic Claim
"{original text}"

### Classification
{FORBIDDEN / NEEDS_SOFTENING / NEEDS_EVIDENCE}

### Reason
{why this claim is problematic}

### Proposed Safer Wording
"{safer text}"

### Context
{where this text is being used}

### Sultan Decision Needed
{what Sultan must decide}
```

---

## Step-by-Step Safe Workflow

### Step 1: Read the Text

Read the text to be reviewed:

```bash
# Read the file
cat {file path}

# Or read specific section
grep -A 10 "{pattern}" {file path}
```

### Step 2: Identify Claims

Scan the text for:

- Medical language (pain, treat, cure, heal, etc.)
- Diagnostic language (diagnose, detect, measure, assess, etc.)
- Treatment language (treat, correct, alleviate, improve, etc.)
- Overstated efficacy (proven, guaranteed, optimal, best, etc.)

### Step 3: Classify Each Claim

For each claim identified, classify as:

- **ALLOWED** — Engineering-only language, no issues
- **NEEDS_SOFTENING** — Overstated but not medical, needs softer wording
- **FORBIDDEN** — Medical, diagnostic, or therapeutic claim
- **NEEDS_EVIDENCE** — Claim requires evidence to support

### Step 4: Propose Safer Rewrites

For each problematic claim, propose safer wording:

- Replace medical terms with engineering terms
- Replace absolute claims with qualified statements
- Replace proven language with hypothesis language
- Replace treatment language with design language

### Step 5: Document Findings

Document the review results:

```markdown
## Claim Review — {file path}

### Claims Reviewed
{count} claims reviewed

### Classification Results
- ALLOWED: {count}
- NEEDS_SOFTENING: {count}
- FORBIDDEN: {count}
- NEEDS_EVIDENCE: {count}

### Safer Rewrites Proposed
{count} safer rewrites proposed

### Escalations Required
{count} escalations to Sultan
```

### Step 6: Generate Arabic Report

Generate an Arabic summary of the review:

```markdown
## ملخص مراجعة المطالبات — {file path}

### المطالبات المراجعة
{count} مطالبات تمت مراجعتها

### نتائج التصنيف
- مسموح: {count}
- يحتاج إلى تخفيف: {count}
- ممنوع: {count}
- يحتاج إلى أدلة: {count}

### إعادة الصياغة المقترحة
{count} إعادة صياغة مقترحة

### التصعيدات المطلوبة
{count} تصعيدات إلى سلطان
```

---

## Verification Checklist

Before completing review:

- [ ] All text has been read
- [ ] All claims have been identified
- [ ] All claims have been classified
- [ ] Safer rewrites proposed for problematic claims
- [ ] Escalations documented for forbidden claims
- [ ] Review results are documented

After completing review:

- [ ] Arabic report is generated
- [ ] Review is saved to appropriate location
- [ ] Sultan is notified of escalations
- [ ] No forbidden claims remain unaddressed

---

## Success Criteria

- All claims are reviewed and classified
- No medical, diagnostic, or therapeutic claims pass unflagged
- Safer rewrites provided for all problematic claims
- Escalations documented for all forbidden claims
- Arabic report is generated and saved

---

## Failure Signals

| Signal | Meaning | Action |
|--------|---------|--------|
| Medical claim not flagged | Compliance violation | Re-review text, flag claim |
| No safer rewrite proposed | Incomplete review | Propose safer wording |
| No escalation for forbidden claim | Compliance risk | Escalate immediately |
| No Arabic report generated | Incomplete review | Generate report |
| Claim classified as ALLOWED but is medical | Classification error | Re-classify as FORBIDDEN |

---

## Arabic Report Template

```markdown
## تقرير مراجعة المطالبات — {file path}

### المطالبات المراجعة
{count} مطالبات تمت مراجعتها

### نتائج التصنيف
- مسموح: {count}
- يحتاج إلى تخفيف: {count}
- ممنوع: {count}
- يحتاج إلى أدلة: {count}

### إعادة الصياغة المقترحة
{safer rewrites in Arabic}

### التصعيدات المطلوبة
{escalations in Arabic}

### المخاطر
{risks in Arabic}

### القرار المطلوب من سلطان
{decisions needed in Arabic}

### الخطوة التالية
{next recommended action in Arabic}
```

---

## Examples

### Example 1: Medical Claim Detection

**Original text:**
"This shoe reduces foot pain and treats plantar fasciitis."

**Classification:** FORBIDDEN

**Reason:** Contains medical claims ("reduces foot pain", "treats plantar fasciitis")

**Safer rewrite:**
"This is an engineering design for pressure distribution based on simulation results. Clinical validation is required."

**Arabic report:**
```markdown
## تقرير مراجعة المطالبات — example.txt

### المطالبات المراجعة
2 مطالبات تمت مراجعتها

### نتائج التصنيف
- مسموح: 0
- يحتاج إلى تخفيف: 0
- ممنوع: 2
- يحتاج إلى أدلة: 0

### إعادة الصياغة المقترحة
"يقلل هذا الحذاء من ألم القدم" → "هذا تصميم هندسي لتوزيع الضغط بناءً على نتائج المحاكاة"
"يعالج التهاب اللفافة الأخمصية" → "يتطلب هذا التصميم التحقق السريري"

### التصعيدات المطلوبة
تم اكتشاف مطالبات طبية. يجب مراجعتها مع سلطان قبل الاستخدام.

### المخاطر
مخاطر امتثال عالية. المطالبات الطبية ممنوعة.

### القرار المطلوب من سلطان
موافقة على إعادة الصياغة المقترحة أو توفير أدلة سريرية.

### الخطوة التالية
انتظار موافقة سلطان قبل استخدام النص.
```

### Example 2: Overstated Efficacy Claim

**Original text:**
"This is proven to improve comfort and performance."

**Classification:** NEEDS_EVIDENCE

**Reason:** Overstated efficacy claim without evidence

**Safer rewrite:**
"This is a design hypothesis for comfort and performance. User testing is required to validate."

**Arabic report:**
```markdown
## تقرير مراجعة المطالبات — example.txt

### المطالبات المراجعة
1 مطالبة تمت مراجعتها

### نتائج التصنيف
- مسموح: 0
- يحتاج إلى تخفيف: 0
- ممنوع: 0
- يحتاج إلى أدلة: 1

### إعادة الصياغة المقترحة
"هذا مثبت لتحسين الراحة والأداء" → "هذا فرضية تصميم للراحة والأداء. يتطلب اختبار المستخدم للتحقق"

### التصعيدات المطلوبة
لا يوجد تصعيد، ولكن الأدلة مطلوبة.

### المخاطر
مخاطر منخفضة. المطالبة مبالغ فيها ولكن ليست طبية.

### القرار المطلوب من سلطان
موافقة على إعادة الصياغة المقترحة أو توفير أدلة الاختبار.

### الخطوة التالية
انتظار موافقة سلطان أو توفير أدلة.
```

---

## Appendix: Cross-Reference

| Document | Purpose | Location |
|----------|---------|----------|
| SOUL.md | Hermes identity and boundaries | `/root/hermes/zilfit-ip-core/SOUL.md` |
| ZILFIT_AGENT_ROLES.md | Agent roles charter | `governance/ZILFIT_AGENT_ROLES.md` |
| governance/Z_CLAIMS_SKILLS.md | Claims skill policy | `governance/Z_CLAIMS_SKILLS.md` |

---

*Document ends. Phase C2 — foundation implementation. No code changes. No production impact.*

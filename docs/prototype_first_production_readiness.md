# Prototype-First Production Readiness (P0)

**Workflow:** prototype-first-production-readiness  
**Version:** 1.0  
**Date:** 2026-05-18  
**Owner:** ZILFIT Engineering Council  
**Status:** Active  

---

## Purpose

Reduce planning time and push ZILFIT product ideas toward tangible production sample readiness. Every new idea must become an **execution card**, not a long PRD.

The execution card forces the idea into one or more concrete local actions:

1. **Prototype/Demo** — smallest local prototype or demo that makes the idea tangible
2. **Measurement-Flow** — what input or measurement is needed to evaluate
3. **QA Test** — how do we verify it works locally without deploying
4. **Printability/Manufacturing** — can this be produced with ZILFIT's constraints (TPU, Gyroid 0.6mm, Vantablack+Rose Gold)
5. **Claims-Safety** — does the idea contain forbidden medical/diagnostic/therapeutic language
6. **Production-Sample** — what is needed to produce a physical sample and what blocks it

---

## Core Rule

**No PRD until Prototype.** A new product idea is NOT approved for full specification until an execution card exists and at least one local step has been completed.

---

## Workflow Steps

### Step 1: Idea Capture

Capture the idea in one or three sentences. Answer: What is it? Who is it for? What problem does it solve (engineering-only language)?

### Step 2: Generate Execution Card

Use the card creation tool to convert the idea into a structured execution card:

```
python tools/prototype_card.py --idea "Text of the product idea" --category engineering
```

The tool validates required fields, enforces claims-safety language, and writes the card to `reports/prototype-cards/`.

### Step 3: Fill Blockers and Dependencies

Review the generated card. Fill in any blocked fields:

- What must be measured or simulated before proceeding?
- What manufacturing constraint applies (TPU flexibility range, print bed size, 0.6mm wall accuracy)?
- Is there a safety claim risk? Flag for Z-Claims review.

### Step 4: Assign Smallest Local Action

Pick the single smallest action that can be done locally:

- If it's a design concept → create a prototype file (STL, SVG, diagram)
- If it's a data concept → create a measurement or simulation script
- If it's a safety concern → run the claims scanner on the idea text
- If it's a production concern → check against Z-Printability constraints

Do NOT start with architecture diagrams, design docs, or requirements specs. Start with the smallest thing that can be run or held.

### Step 5: Execute and Record Results

After the local action is done, record results in the execution card:

- What was the outcome?
- What measurement/observation was made?
- Did it pass or fail the local check?

### Step 6: Gate Decision

The card now has one of these statuses:

- **READY_FOR_SPEC** — local prototype succeeded, proceed to full specification
- **NEEDS_REVISION** — prototype exposed a problem, update idea and retry
- **BLOCKED** — external dependency or constraint prevents progress (requires Sultan approval)
- **SAFETY_REVIEW** — flagged claims-safety issue (requires Z-Claims review)

---

## Execution Card Schema

Every execution card MUST include these fields:

| Field | Required | Description |
|-------|----------|-------------|
| idea | Yes | Product idea in 1-3 sentences |
| category | Yes | engineering, design, research, ux |
| smallest_prototype | Yes | Smallest local prototype/demo that makes the idea tangible |
| measurement_input | Yes | Required measurement or input for evaluation |
| qa_check | Yes | Local test or verification method |
| claims_safety_check | Yes | Pass/Fail/Review — forbidden language scan |
| printability_check | Yes | Pass/Fail/Review — TPU, Gyroid 0.6mm constraint check |
| production_sample_impact | Yes | What is needed for a physical production sample |
| blocker | Yes | Current blocker or "none" |
| next_action | Yes | Single next step to advance the card |
| status | Auto | Pending, In-Progress, Ready_For_Spec, Needs_Revision, Blocked, Safety_Review |

---

## Safety and Boundary Rules

- All outputs are **engineering-only** unless reviewed by Z-Claims
- No medical, diagnostic, therapeutic, clinical, pain, disease, or treatment claims
- No deployment to production
- No modification of main branch
- No network calls, API keys, or external services
- Cards are stored locally in `reports/prototype-cards/`
- No deletion of existing files or reports

---

## Daily Usage

Each ZILFIT agent (Z-Research, Z-CAD, Z-Bio, Z-Ops) should create an execution card for every new idea they encounter during their daily work. Ideas without execution cards are not actioned.

Existing ideas from research reports, inbox items, or product notes can be retroactively converted into execution cards using the generation tool.

---

## Arabic Summary (للسلطان)

### الغرض
تقليل وقت التخطيط ودفع أفكار منتجات ZILFIT نحو جاهزية العينات الإنتاجية الملموسة. كل فكرة جديدة يجب أن تصبح بطاقة تنفيذ، وليس وثيقة متطلبات طويلة.

### القاعدة الأساسية
لا متطلبات كاملة قبل نموذج أولي. فكرة المنتج الجديدة لا يتم الموافقة عليها للمواصفات الكاملة حتى توجد بطاقة تنفيذ ويتم إكمال خطوة محلية واحدة على الأقل.

### كيفية الاستخدام
باستخدام أداة إنشاء البطاقات لتحويل الفكرة إلى بطاقة تنفيذية. الأداة تتحقق من الحقول المطلوبة وتفرض لغة أمان المطالبات وتحفظ البطاقة محلياً.

### السلامة
جميع المخرجات هندسية فقط ما لم يتم مراجعتها بواسطة Z-Claims. لا توجد ادعاءات طبية أو علاجية. لا نشر للإنتاج ولا اتصالات بالشبكة.

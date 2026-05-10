# Skill: Demo Review

**Document:** skills/demo_review.md
**Version:** 1.0
**Phase:** C2 — Foundation Implementation
**Date:** 2026-05-10
**Owner:** Sultan
**Status:** Active

---

## Purpose

Define the read-only demo review workflow, including LiveFit UX/design checks, no demo modification unless separately approved, screenshots/flow observations, accessibility/touch-layout checklist, and report-only output.

---

## When to Use

Use this skill when:

1. Reviewing demo files for UX/design issues
2. Checking LiveFit camera scan workflow
3. Verifying accessibility and touch layout
4. Observing demo flows and user interactions
5. Documenting demo state and observations

---

## Inputs

- **Demo file path** — Path to demo HTML file
- **Demo URL** — URL where demo is hosted (if applicable)
- **Review context** — What aspect of the demo is being reviewed
- **Viewport size** — Mobile, tablet, or desktop viewport

---

## Outputs

- **UX/design observations** — Notes on user experience and design elements
- **Accessibility findings** — Issues with accessibility or touch layout
- **Flow observations** — Notes on user flow and interaction patterns
- **Screenshots** — Visual observations (described in text)
- **Recommendations** — Suggestions for improvement (report-only)
- **Arabic report** — Summary of demo review

---

## Allowed Read Paths

- `/root/hermes/zilfit-ip-core/` — Full read access for context gathering
- `demo/` — All demo HTML files
- `governance/Z_UX_SKILLS.md` — UX skill policy
- `governance/Z_FEMMEBIOMECH_SKILLS.md` — Feminine biomechanics design constraints

---

## Allowed Write Paths

- `reports/design/` — Design decision logs and UX flow proposals
- `reports/qa/` — Test results and accessibility findings

---

## Forbidden Paths

- `.env` — Never read or write
- `telegram_bot/bot.py` — Never modify without Sultan approval
- `telegram_bot/run.sh` — Never modify without Sultan approval
- `telegram_bot/classifier.py` — Never modify without Sultan approval
- `cron/` — Never modify without Sultan approval
- `systemd/` — Never modify without Sultan approval
- `tmux` sessions — Never modify without Sultan approval
- `demo/` — Never modify without Sultan approval

---

## Approval Requirement

| Action | Approval Required | Reason |
|--------|-------------------|--------|
| Read demo files | No | Review is always allowed |
| Observe demo flows | No | Observation is always allowed |
| Document findings | No | Documentation is always allowed |
| Modify demo files | Yes | Demo changes require Sultan approval |
| Implement recommendations | Yes | Changes require Sultan approval |

---

## Read-Only Demo Review Workflow

### Step 1: Read Demo File

```bash
# Read demo HTML file
cat demo/{filename}.html

# Or view specific sections
grep -A 20 "{pattern}" demo/{filename}.html
```

### Step 2: Open Demo in Browser

Open the demo file in a browser:

```bash
# Open in default browser
xdg-open demo/{filename}.html

# Or specify browser
firefox demo/{filename}.html
# or
chrome demo/{filename}.html
```

### Step 3: Set Viewport Size

Test at different viewport sizes:

- **Mobile:** 375px × 667px (iPhone SE)
- **Tablet:** 768px × 1024px (iPad)
- **Desktop:** 1920px × 1080px (Full HD)

Use browser DevTools to set viewport size.

### Step 4: Observe Demo Flow

Navigate through the demo:

1. **Initial load** — What appears first?
2. **User interactions** — What can the user do?
3. **Flow completion** — How does the user complete the task?
4. **Error states** — What happens if something goes wrong?

### Step 5: Document Observations

Record observations in a structured format.

### Step 6: Generate Report

Generate a report with findings and recommendations.

---

## LiveFit UX/Design Checks

### Camera Scan Workflow

**Check these elements:**

1. **Camera preview** — Is the camera preview visible and appropriately sized?
2. **Permission request** — Is camera permission requested clearly?
3. **Scan guidance** — Are instructions clear for positioning the foot?
4. **Scan progress** — Is scan progress indicated?
5. **Scan completion** — Is completion state clear?

### Design Elements

**Check these elements:**

1. **Color palette** — Matte Black / Rose Gold / Cyan Blue / Pearl White
2. **Typography** — Clear, readable fonts
3. **Spacing** — Consistent spacing between elements
4. **Alignment** — Proper alignment of elements
5. **Visual hierarchy** — Clear visual hierarchy

### Brand Compliance

**Check these elements:**

1. **Logo placement** — Is logo visible and properly placed?
2. **Brand colors** — Are brand colors used correctly?
3. **Brand voice** — Is copy consistent with brand voice?
4. **No watermarks** — Are there no watermarks or placeholder text?

---

## No Demo Modification Unless Separately Approved

### Read-Only Policy

**Never modify demo files during review:**

- Do not edit HTML
- Do not edit CSS
- Do not edit JavaScript
- Do not add or remove elements
- Do not change styling

### Modification Process

If modifications are needed:

1. **Document the issue** — Describe what needs to change
2. **Propose a solution** — Suggest how to fix it
3. **Request approval** — Ask Sultan for approval
4. **Implement after approval** — Make changes only after approval

### Modification Request Template

```markdown
## Demo Modification Request

**File:** demo/{filename}.html
**Reviewer:** Z-Design
**Date:** {YYYY-MM-DD}

### Issue
{description of the issue}

### Proposed Solution
{description of the proposed fix}

### Impact
{how this change will affect the demo}

### Sultan Approval Required
{yes/no}
```

---

## Screenshots/Flow Observations

### Screenshot Descriptions

Since screenshots cannot be captured in text, describe visual observations:

```markdown
### Screenshot Description — {screen name}

**Viewport:** {mobile/tablet/desktop}
**Size:** {width}x{height}

**Visual Elements:**
- {element 1 description}
- {element 2 description}
- {element 3 description}

**Layout:**
- {layout description}

**Colors:**
- {color observations}
```

### Flow Observations

Document the user flow:

```markdown
### Flow Observation — {flow name}

**Step 1:** {description}
**Step 2:** {description}
**Step 3:** {description}

**Transitions:**
- {transition 1 description}
- {transition 2 description}

**Issues:**
- {issue 1 description}
- {issue 2 description}
```

---

## Accessibility/Touch-Layout Checklist

### Mobile Touch Targets

**Check these elements:**

- [ ] Touch targets are at least 44px × 44px
- [ ] Touch targets have adequate spacing
- [ ] Touch targets are easily tappable
- [ ] No overlapping touch targets

### Readability

**Check these elements:**

- [ ] Text is readable at mobile viewport
- [ ] Font size is at least 16px
- [ ] Text contrast meets WCAG AA standards
- [ ] Text is not truncated or overlapping

### Navigation

**Check these elements:**

- [ ] Navigation is clear and intuitive
- [ ] Back buttons are visible
- [ ] Progress indicators are clear
- [ ] Error messages are visible

### Accessibility

**Check these elements:**

- [ ] Alt text for images (if applicable)
- [ ] ARIA labels for interactive elements
- [ ] Keyboard navigation support
- [ ] Screen reader compatibility

### Touch Layout

**Check these elements:**

- [ ] Elements are within thumb reach
- [ ] No elements require stretching
- [ ] Common actions are easily accessible
- [ ] Layout works in both orientations

---

## Report-Only Output

### Report Structure

```markdown
## Demo Review — {demo name}

**File:** demo/{filename}.html
**Reviewer:** Z-Design
**Date:** {YYYY-MM-DD}
**Viewport:** {mobile/tablet/desktop}

### UX/Design Observations
{observations}

### Accessibility Findings
{findings}

### Flow Observations
{observations}

### Recommendations
{recommendations}

### Issues Requiring Approval
{issues}
```

### Report Rules

1. **Read-only** — Report observations only, do not modify
2. **Specific** — Cite specific elements and issues
3. **Actionable** — Provide clear recommendations
4. **Prioritized** — Rank issues by severity
5. **Evidence-based** — Describe what was observed

---

## Step-by-Step Safe Workflow

### Step 1: Read Demo File

```bash
cat demo/{filename}.html
```

### Step 2: Open Demo in Browser

```bash
xdg-open demo/{filename}.html
```

### Step 3: Set Viewport Size

Use browser DevTools to set viewport to mobile, tablet, or desktop.

### Step 4: Run UX/Design Checks

Check camera scan workflow, design elements, and brand compliance.

### Step 5: Run Accessibility/Touch-Layout Checks

Check touch targets, readability, navigation, accessibility, and touch layout.

### Step 6: Document Observations

Record screenshots/flow observations in text format.

### Step 7: Generate Report

Create a report with findings and recommendations.

### Step 8: Generate Arabic Report

Generate an Arabic summary of the review.

---

## Verification Checklist

Before completing review:

- [ ] Demo file has been read
- [ ] Demo has been opened in browser
- [ ] Multiple viewport sizes have been tested
- [ ] UX/Design checks have been completed
- [ ] Accessibility/Touch-Layout checks have been completed
- [ ] Observations have been documented
- [ ] No modifications have been made to demo

After completing review:

- [ ] Report is complete and accurate
- [ ] Recommendations are clear and actionable
- [ ] Issues are prioritized by severity
- [ ] Arabic report is generated
- [ ] No demo files have been modified

---

## Success Criteria

- Demo is reviewed without modification
- All UX/Design checks are completed
- All Accessibility/Touch-Layout checks are completed
- Observations are documented clearly
- Recommendations are actionable
- Report is complete and accurate
- Arabic report is generated

---

## Failure Signals

| Signal | Meaning | Action |
|--------|---------|--------|
| Demo file modified | Violation of read-only policy | Revert changes, document violation |
| No observations documented | Incomplete review | Document observations |
| No recommendations provided | Incomplete review | Provide recommendations |
| Accessibility issues not flagged | Incomplete review | Run accessibility checks |
| Touch layout issues not flagged | Incomplete review | Run touch layout checks |

---

## Arabic Report Template

```markdown
## تقرير مراجعة العرض التوضيحي — {demo name}

### الملف
demo/{filename}.html

### ملاحظات UX/التصميم
{UX/design observations in Arabic}

### نتائج إمكانية الوصول
{accessibility findings in Arabic}

### ملاحظات التدفق
{flow observations in Arabic}

### التوصيات
{recommendations in Arabic}

### المشكلات التي تتطلب موافقة
{issues requiring approval in Arabic}

### المخاطر
{risks in Arabic}

### القرار المطلوب من سلطان
{decisions needed in Arabic}

### الخطوة التالية
{next recommended action in Arabic}
```

---

## Examples

### Example 1: LiveFit Camera Scan Review

**Demo File:** demo/livefit.html

**Report:**
```markdown
## Demo Review — LiveFit Camera Scan

**File:** demo/livefit.html
**Reviewer:** Z-Design
**Date:** 2026-05-10
**Viewport:** Mobile (375px × 667px)

### UX/Design Observations
- Camera preview is visible and appropriately sized (300px × 300px)
- Permission request is clear
- Scan guidance is visible but could be more prominent
- Scan progress is indicated with a progress bar
- Scan completion state is clear with success message

### Accessibility Findings
- Touch targets are adequate (minimum 44px × 44px)
- Text is readable at 16px font size
- Text contrast meets WCAG AA standards
- No alt text for camera preview (not applicable)

### Flow Observations
- User taps "Start Scan" button
- Camera permission is requested
- Camera preview appears
- User positions foot in frame
- Scan progresses with progress bar
- Scan completes with success message

### Recommendations
1. Make scan guidance more prominent (larger font, higher contrast)
2. Add visual indicator for optimal foot positioning
3. Consider adding haptic feedback on scan completion

### Issues Requiring Approval
None identified. All observations are minor improvements.
```

**Arabic Report:**
```markdown
## تقرير مراجعة العرض التوضيحي — LiveFit Camera Scan

### الملف
demo/livefit.html

### ملاحظات UX/التصميم
- معاينة الكاميرا مرئية وحجمها مناسب (300px × 300px)
- طلب الإذن واضح
- إرشادات المسح مرئية ولكن يمكن أن تكون أكثر بروزًا
- تقدم المسح موضح بشريط تقدم
- حالة إكمال المسح واضحة برسالة نجاح

### نتائج إمكانية الوصول
- أهداف اللمس كافية (الحد الأدنى 44px × 44px)
- النص مقروء بحجم خط 16px
- تباين النص يلبي معايير WCAG AA
- لا يوجد نص بديل لمعاينة الكاميرا (لا ينطبق)

### ملاحظات التدفق
- ينقر المستخدم على زر "بدء المسح"
- يتم طلب إذن الكاميرا
- تظهر معاينة الكاميرا
- يضع المستخدم قدمه في الإطار
- يتقدم المسح بشريط تقدم
- يكتمل المسح برسالة نجاح

### التوصيات
1. جعل إرشادات المسح أكثر بروزًا (خط أكبر، تباين أعلى)
2. إضافة مؤشر بصري لتحديد وضع القدم الأمثل
3. النظر في إضافة ملاحظات لمسية عند اكتمال المسح

### المشكلات التي تتطلب موافقة
لم يتم تحديد أي مشكلات. جميع الملاحظات هي تحسينات طفيفة.

### المخاطر
لا توجد مخاطر. مراجعة للقراءة فقط.

### القرار المطلوب من سلطان
لا يوجد.

### الخطوة التالية
نظرًا في تنفيذ التوصيات بعد الحصول على موافقة سلطان.
```

---

## Appendix: Cross-Reference

| Document | Purpose | Location |
|----------|---------|----------|
| SOUL.md | Hermes identity and boundaries | `/root/hermes/zilfit-ip-core/SOUL.md` |
| ZILFIT_AGENT_ROLES.md | Agent roles charter | `governance/ZILFIT_AGENT_ROLES.md` |
| governance/Z_UX_SKILLS.md | UX skill policy | `governance/Z_UX_SKILLS.md` |
| governance/Z_FEMMEBIOMECH_SKILLS.md | Feminine biomechanics design constraints | `governance/Z_FEMMEBIOMECH_SKILLS.md` |

---

*Document ends. Phase C2 — foundation implementation. No code changes. No production impact.*

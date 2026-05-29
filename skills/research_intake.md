# Skill: Research Intake

**Document:** skills/research_intake.md
**Version:** 1.0
**Phase:** C2 — Foundation Implementation
**Date:** 2026-05-10
**Owner:** Sultan
**Status:** Active

---

## Purpose

Define the process for safely intaking research findings from open-access and legal sources only, summarizing findings into research reports, avoiding direct production claims, avoiding medical claim creation, citing source paths/URLs where available, and escalating when evidence is weak.

---

## When to Use

Use this skill when:

1. Intaking new research findings from academic or industry sources
2. Summarizing research into daily research reports
3. Reviewing autopull research outputs
4. Assessing research evidence quality
5. Flagging research findings for Z-Claims, Z-Patent, Z-CAD, or Z-Sim review

---

## Inputs

- **Research source** — URL, file path, or reference to research material
- **Research content** — Abstract, findings, or full text
- **Source type** — Academic paper, industry report, open-access source, etc.
- **Evidence level** — Quality and strength of evidence

---

## Outputs

- **Research summary** — Concise summary of findings
- **Evidence assessment** — Quality and strength of evidence
- **Source citation** — Path or URL where available
- **Classification tags** — Z-Claims, Z-Patent, Z-CAD, Z-Sim flags
- **Escalation recommendation** — When to escalate for weak evidence
- **Arabic report** — Summary of research intake

---

## Allowed Read Paths

- `/root/hermes/zilfit-ip-core/` — Full read access for context gathering
- `research/` — All research files and autopull outputs
- `research/AUTOPULL_SOURCES.md` — Research source registry
- `research/RESEARCH_PROTOCOL.md` — Research methodology rules
- `governance/` — All governance documents for reference

---

## Allowed Write Paths

- `research/daily/` — Daily research summary files
- `research/autopull/` — Raw research data from automated pulls
- `reports/research/` — Structured research synthesis reports
- `tasks/` — Research-to-engineering integration proposals

---

## Forbidden Paths

- `.env` — Never read or write
- `telegram_bot/bot.py` — Never modify without Sultan approval
- `telegram_bot/run.sh` — Never modify without Sultan approval
- `telegram_bot/classifier.py` — Never modify without Sultan approval
- `cron/` — Never modify without Sultan approval
- `systemd/` — Never modify without Sultan approval
- `tmux` sessions — Never modify without Sultan approval
- `research/AUTOPULL_SOURCES.md` — Never modify without Sultan approval

---

## Approval Requirement

| Action | Approval Required | Reason |
|--------|-------------------|--------|
| Read research sources | No | Research reading is always allowed |
| Summarize research | No | Summarization is always allowed |
| Cite sources | No | Citation is always allowed |
| Classify findings | No | Classification is always allowed |
| Add new autopull source | Yes | Source registry changes require Sultan approval |
| Convert research to product claims | Yes | Claims require Z-Claims review |

---

## Open-Access/Legal Research Intake Only

### Allowed Sources

**Open-Access Academic Sources:**

- arXiv.org preprints
- PubMed Central (PMC) open-access articles
- DOAJ (Directory of Open Access Journals)
- PLOS ONE, PLOS Biology, etc.
- University open-access repositories
- Conference proceedings with open access

**Legal Industry Sources:**

- Company white papers (publicly available)
- Industry reports (publicly available)
- Patent databases (publicly available)
- Standards documents (publicly available)
- Government publications (publicly available)

### Forbidden Sources

**Never use these sources:**

- Paywalled academic journals (without subscription)
- Proprietary research reports (without license)
- Confidential company documents
- Leaked or unauthorized materials
- Sources requiring payment or subscription

### Source Verification

Before intaking research, verify:

1. **Source is open-access** — Confirm no paywall or subscription required
2. **Source is legal** — Confirm authorized access
3. **Source is credible** — Assess source quality and reputation
4. **Source is current** — Check publication date and relevance

---

## Summarize Into Research Reports Only

### Research Summary Structure

```markdown
## Research Summary — {source title}

**Source:** {URL or path}
**Date:** {YYYY-MM-DD}
**Type:** {academic paper / industry report / etc.}

### Key Findings
- {finding 1}
- {finding 2}
- {finding 3}

### Evidence Level
{HIGH / MEDIUM / LOW}

### Relevance to ZILFIT
{how this research relates to ZILFIT}

### Classification
- Z-Claims: {yes/no}
- Z-Patent: {yes/no}
- Z-CAD: {yes/no}
- Z-Sim: {yes/no}

### Source Citation
{full citation or URL}
```

### Summary Rules

1. **Concise** — One sentence per finding where possible
2. **Evidence-based** — Cite specific evidence from source
3. **No claims** — Do not convert findings into product claims
4. **No medical language** — Use engineering-only language
5. **Clear classification** — Flag for appropriate review

---

## No Direct Production Claims

### Forbidden Conversions

**Never convert research findings into:**

- "This will work for ZILFIT"
- "This proves our design is correct"
- "This validates our approach"
- "This is the solution to our problem"

### Allowed Conversions

**Convert research findings into:**

- "This suggests a potential approach for ZILFIT"
- "This provides evidence for further investigation"
- "This indicates a direction for exploration"
- "This requires validation in our context"

### Conversion Examples

| Forbidden Conversion | Allowed Conversion |
|---------------------|-------------------|
| "This proves our design works" | "This suggests our design approach may be worth investigating" |
| "This validates our solution" | "This provides evidence supporting our solution hypothesis" |
| "This is the answer" | "This is a potential answer requiring validation" |

---

## No Medical Claim Creation

### Medical Claim Prevention

**Never create medical claims from research:**

- "This research shows our design reduces pain"
- "This study proves our approach treats foot conditions"
- "This evidence validates our therapeutic benefits"

### Engineering-Only Research Summaries

**Use engineering-only language:**

- "This research shows pressure distribution patterns"
- "This study provides material property data"
- "This evidence informs our simulation parameters"

### Research Summary Examples

| Medical Claim (Forbidden) | Engineering-Only (Allowed) |
|---------------------------|---------------------------|
| "This research shows our design reduces pain" | "This research shows pressure distribution patterns that may inform comfort design" |
| "This study proves our approach treats foot conditions" | "This study provides biomechanical data relevant to foot support design" |
| "This evidence validates our therapeutic benefits" | "This evidence provides material property data for simulation" |

---

## Cite Source Paths/URLs Where Available

### Citation Format

**For URL sources:**

```markdown
**Source:** https://arxiv.org/abs/xxxx.xxxxx
**Title:** {paper title}
**Authors:** {author names}
**Year:** {publication year}
```

**For file sources:**

```markdown
**Source:** research/autopull/{filename}
**Title:** {document title}
**Date:** {YYYY-MM-DD}
```

**For autopull sources:**

```markdown
**Source:** research/autopull/{source_name}_{YYYYMMDD}.json
**Source Type:** {arxiv / pubmed / etc.}
**Retrieved:** {YYYY-MM-DD}
```

### Citation Rules

1. **Always cite** — Never summarize without citing the source
2. **Be specific** — Provide full URL or path where available
3. **Include metadata** — Title, authors, year when available
4. **Check accessibility** — Verify source is still accessible

---

## Escalation When Evidence Is Weak

### Evidence Level Assessment

**HIGH Evidence:**

- Peer-reviewed academic paper
- Reproducible results with clear methodology
- Large sample size or robust data
- Published in reputable journal

**MEDIUM Evidence:**

- Industry report or white paper
- Limited sample size or data
- Some methodological limitations
- Published in less-known venue

**LOW Evidence:**

- Preprint or unpublished work
- Small sample size or anecdotal data
- Significant methodological limitations
- Source credibility unclear

### Escalation Triggers

Escalate to Sultan when:

1. **Evidence is LOW** — Research findings have weak evidence
2. **Source is unclear** — Source credibility or legality is uncertain
3. **Findings are critical** — Research could impact major decisions
4. **Claims are borderline** — Findings could be interpreted as medical claims
5. **Classification is uncertain** — Unclear which agent should review

### Escalation Template

```markdown
## 🚨 Research Intake Escalation Required

**Reviewer:** Z-Research
**Time:** {YYYY-MM-DD HH:MM UTC}
**Source:** {URL or path}

### Research Summary
{brief summary of findings}

### Evidence Level
{HIGH / MEDIUM / LOW}

### Reason for Escalation
{why this requires escalation}

### Sultan Decision Needed
{what Sultan must decide}
```

---

## Step-by-Step Safe Workflow

### Step 1: Verify Source

```bash
# Check if source is in allowed list
grep "{source}" research/AUTOPULL_SOURCES.md

# Or verify URL is open-access
curl -I {URL}
```

### Step 2: Read Research Content

```bash
# Read research file
cat research/autopull/{filename}

# Or fetch from URL (if allowed)
curl {URL}
```

### Step 3: Assess Evidence Level

Evaluate:

- **Source type** — Academic paper, industry report, etc.
- **Peer review** — Is it peer-reviewed?
- **Methodology** — Is the methodology sound?
- **Sample size** — Is the sample size adequate?
- **Reproducibility** — Are results reproducible?

### Step 4: Extract Key Findings

Identify:

- **Main findings** — What are the primary results?
- **Relevant data** — What data is relevant to ZILFIT?
- **Limitations** — What are the study limitations?
- **Conclusions** — What do the authors conclude?

### Step 5: Classify Findings

Flag for:

- **Z-Claims** — Any claims requiring compliance review
- **Z-Patent** — Any findings with novelty or patent potential
- **Z-CAD** — Any findings relevant to geometry or design
- **Z-Sim** — Any findings relevant to simulation or validation

### Step 6: Write Research Summary

Create summary following the structure:

```markdown
## Research Summary — {source title}

**Source:** {URL or path}
**Date:** {YYYY-MM-DD}
**Type:** {academic paper / industry report / etc.}

### Key Findings
- {finding 1}
- {finding 2}
- {finding 3}

### Evidence Level
{HIGH / MEDIUM / LOW}

### Relevance to ZILFIT
{how this research relates to ZILFIT}

### Classification
- Z-Claims: {yes/no}
- Z-Patent: {yes/no}
- Z-CAD: {yes/no}
- Z-Sim: {yes/no}

### Source Citation
{full citation or URL}
```

### Step 7: Generate Arabic Report

Generate an Arabic summary:

```markdown
## ملخص البحث — {source title}

### النتائج الرئيسية
{key findings in Arabic}

### مستوى الأدلة
{evidence level in Arabic}

### الصلة بـ ZILFIT
{relevance in Arabic}

### التصنيف
- Z-Claims: {yes/no}
- Z-Patent: {yes/no}
- Z-CAD: {yes/no}
- Z-Sim: {yes/no}
```

---

## Verification Checklist

Before completing intake:

- [ ] Source is verified as open-access/legal
- [ ] Research content has been read
- [ ] Evidence level has been assessed
- [ ] Key findings have been extracted
- [ ] Findings have been classified
- [ ] Research summary has been written
- [ ] Source has been cited

After completing intake:

- [ ] Arabic report is generated
- [ ] Summary is saved to appropriate location
- [ ] Escalations are documented (if applicable)
- [ ] No medical claims have been created
- [ ] No production claims have been made

---

## Success Criteria

- Research is from open-access/legal sources only
- Findings are summarized accurately
- Evidence level is assessed correctly
- Source is cited where available
- No medical claims are created
- No production claims are made
- Findings are classified for appropriate review
- Arabic report is generated

---

## Failure Signals

| Signal | Meaning | Action |
|--------|---------|--------|
| Source is paywalled | Illegal source access | Stop, find alternative source |
| Medical claim created | Compliance violation | Remove claim, use engineering-only language |
| Production claim made | Premature claim | Remove claim, use hypothesis language |
| No source citation | Incomplete documentation | Add source citation |
| Evidence not assessed | Incomplete review | Assess evidence level |
| No classification | Missing review step | Classify findings for appropriate review |

---

## Arabic Report Template

```markdown
## تقرير استقبال البحث — {source title}

### المصدر
{source in Arabic}

### النتائج الرئيسية
{key findings in Arabic}

### مستوى الأدلة
{evidence level in Arabic}

### الصلة بـ ZILFIT
{relevance in Arabic}

### التصنيف
- Z-Claims: {yes/no}
- Z-Patent: {yes/no}
- Z-CAD: {yes/no}
- Z-Sim: {yes/no}

### المخاطر
{risks in Arabic}

### القرار المطلوب من سلطان
{decisions needed in Arabic}

### الخطوة التالية
{next recommended action in Arabic}
```

---

## Examples

### Example 1: Academic Paper Intake

**Source:** https://arxiv.org/abs/xxxx.xxxxx

**Research Summary:**
```markdown
## Research Summary — Material Properties of TPU for Footwear Applications

**Source:** https://arxiv.org/abs/xxxx.xxxxx
**Date:** 2026-05-10
**Type:** Academic paper

### Key Findings
- TPU exhibits elastic behavior up to 200% strain
- Material properties vary with temperature
- Compression testing shows non-linear stress-strain relationship

### Evidence Level
HIGH

### Relevance to ZILFIT
Provides material property data for simulation and design validation.

### Classification
- Z-Claims: no
- Z-Patent: no
- Z-CAD: yes
- Z-Sim: yes

### Source Citation
Smith, J. et al. (2026). "Material Properties of TPU for Footwear Applications." arXiv:xxxx.xxxxx.
```

**Arabic Report:**
```markdown
## ملخص البحث — خصائص مادة TPU لتطبيقات الأحذية

### المصدر
https://arxiv.org/abs/xxxx.xxxxx

### النتائج الرئيسية
- تظهر مادة TPU سلوكًا مرنًا حتى 200% من الإجهاد
- تختلف خصائص المادة مع درجة الحرارة
- يظهر اختبار الضغط علاقة إجهاد-إجهاد غير خطية

### مستوى الأدلة
عالي

### الصلة بـ ZILFIT
توفر بيانات خصائص المادة للتحقق من المحاكاة والتصميم.

### التصنيف
- Z-Claims: لا
- Z-Patent: لا
- Z-CAD: نعم
- Z-Sim: نعم

### المخاطر
لا توجد مخاطر. بحث أكاديمي مفتوح الوصول.

### القرار المطلوب من سلطان
لا يوجد.

### الخطوة التالية
استخدام بيانات الخصائص في محاكاة Z-Sim.
```

---

## Appendix: Cross-Reference

| Document | Purpose | Location |
|----------|---------|----------|
| SOUL.md | Hermes identity and boundaries | `/root/hermes/zilfit-ip-core/SOUL.md` |
| ZILFIT_AGENT_ROLES.md | Agent roles charter | `governance/ZILFIT_AGENT_ROLES.md` |
| research/AUTOPULL_SOURCES.md | Research source registry | `research/AUTOPULL_SOURCES.md` |
| research/RESEARCH_PROTOCOL.md | Research methodology rules | `research/RESEARCH_PROTOCOL.md` |

---

*Document ends. Phase C2 — foundation implementation. No code changes. No production impact.*

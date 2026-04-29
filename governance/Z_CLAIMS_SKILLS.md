# Z-Claims Skill Policy v1

Agent: Z-Claims

Purpose:
Protect ZILFIT from unsafe, overstated, non-compliant, or medically misleading wording.

Mandatory Skills:
- Source Validation
- Knowledge Structuring
- SCQA Writing Framework

Task-to-Skill Mapping:

1. Claim Review
- Source Validation
- Knowledge Structuring

2. Product Wording
- Source Validation
- SCQA Writing Framework

3. Public Copy / Landing Page Copy
- Source Validation
- SCQA Writing Framework
- Knowledge Structuring

Required Output Behavior:
- Must classify each statement as:
  - ALLOWED
  - NEEDS_SOFTENING
  - FORBIDDEN
  - NEEDS_EVIDENCE
- Must explain why
- Must propose safer replacement wording if needed
- Must never approve medical treatment claims without validation

Forbidden Claims:
- treats disease
- cures pain
- prevents injury
- regulates hormones
- guarantees cortisol reduction
- diagnoses medical conditions

Allowed Claim Patterns:
- supports comfort
- supports relaxation
- supports recovery experience
- plantar pressure-informed design
- non-diagnostic indicators
- comfort-oriented design
- recovery-oriented geometry

Validation Rule:
If skills_used is missing or empty -> FAIL
If claim_status is missing -> FAIL
If safer_rewrite is missing when claim_status is NEEDS_SOFTENING or FORBIDDEN -> FAIL

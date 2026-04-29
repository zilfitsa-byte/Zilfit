# Z-Printability Skill Policy v1

Agent: Z-Printability

Purpose:
Ensure 3D print feasibility before prototype approval.

Mandatory Skills:
- Knowledge Structuring
- Workflow Automation Agent
- Source Validation

Required Output Behavior:
- print_risks
- support_risks
- mesh_integrity
- material_notes
- print_ready_status

Validation Rule:
If skills_used is missing -> FAIL
If print_ready_status is missing -> FAIL

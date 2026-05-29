"""Tests for the Manual X Research Intake classification and report behavior."""

import pathlib
import re
import tempfile

import pytest

REPO_ROOT = pathlib.Path(__file__).resolve().parent.parent
import sys; sys.path.insert(0, str(REPO_ROOT / "agents" / "research"))
from x_manual_intake import (
    CLASSIFIER_RULES,
    CATEGORIES,
    CATEGORY_LABELS,
    classify_entry,
    generate_report,
    parse_intake,
)


class TestParseIntake:
    """Tests for the parse_intake function."""

    def _write_and_parse(self, text: str) -> list[dict]:
        with tempfile.NamedTemporaryFile(mode="w", suffix=".md", delete=False) as f:
            f.write(text)
            f.flush()
            return parse_intake(pathlib.Path(f.name))

    def test_empty_file(self):
        entries = self._write_and_parse("")
        assert entries == []

    def test_comment_only(self):
        entries = self._write_and_parse("# This is a comment\n# Another comment\n")
        assert entries == []

    def test_single_entry(self):
        text = "source: https://x.com/test\ncontent: Hello world\n"
        entries = self._write_and_parse(text)
        assert len(entries) == 1
        assert entries[0]["source"] == "https://x.com/test"
        assert entries[0]["content"] == "Hello world"
        assert entries[0]["notes"] == ""

    def test_multiple_entries(self):
        text = (
            "source: https://x.com/1\ncontent: Entry one\nnotes: first\n"
            "---\n"
            "source: https://x.com/2\ncontent: Entry two\n"
        )
        entries = self._write_and_parse(text)
        assert len(entries) == 2
        assert entries[0]["content"] == "Entry one"
        assert entries[0]["notes"] == "first"
        assert entries[1]["content"] == "Entry two"
        assert entries[1]["notes"] == ""

    def test_ignores_comment_blocks(self):
        text = "# Comment block\nsource: https://x.com/a\ncontent: Real entry\n"
        entries = self._write_and_parse(text)
        assert len(entries) == 1

    def test_empty_source_with_content(self):
        text = "source:\ncontent: Some content without source\n"
        entries = self._write_and_parse(text)
        assert len(entries) == 1
        assert entries[0]["source"] == ""
        assert entries[0]["content"] == "Some content without source"

    def test_empty_entries_skipped(self):
        text = "---\n---\nsource: https://x.com/a\ncontent: Real\n---\n\n"
        entries = self._write_and_parse(text)
        assert len(entries) == 1

    def test_file_not_found(self):
        with pytest.raises(FileNotFoundError):
            parse_intake(pathlib.Path("/nonexistent/path/intake.md"))


class TestClassifyEntry:
    """Tests for the classify_entry function."""

    def test_ai_tools_gpt(self):
        entry = {"source": "", "content": "GPT-5 released with new features", "notes": ""}
        assert "ai_tools" in classify_entry(entry)

    def test_ai_tools_llm(self):
        entry = {"source": "", "content": "New LLM benchmark results", "notes": ""}
        assert "ai_tools" in classify_entry(entry)

    def test_ai_tools_claude(self):
        entry = {"source": "", "content": "Claude 4 is here", "notes": ""}
        assert "ai_tools" in classify_entry(entry)

    def test_ai_agents_multi(self):
        entry = {"source": "", "content": "Multi-agent autonomous system for coding", "notes": ""}
        assert "ai_agents" in classify_entry(entry)

    def test_ai_agents_crewai(self):
        entry = {"source": "", "content": "CrewAI orchestration framework v2", "notes": ""}
        assert "ai_agents" in classify_entry(entry)

    def test_competitor_footwear_nike(self):
        entry = {"source": "", "content": "Nike launches 3D printed shoe line", "notes": ""}
        assert "competitor_footwear_product" in classify_entry(entry)

    def test_competitor_custom_insole(self):
        entry = {"source": "", "content": "Custom insole scanning app raises Series A", "notes": ""}
        assert "competitor_footwear_product" in classify_entry(entry)

    def test_manufacturing_tpu(self):
        entry = {"source": "", "content": "TPU filament for additive manufacturing", "notes": ""}
        assert "manufacturing_materials" in classify_entry(entry)

    def test_manufacturing_gyroid(self):
        entry = {"source": "", "content": "Gyroid lattice structure optimization for SLS", "notes": ""}
        assert "manufacturing_materials" in classify_entry(entry)

    def test_scanning_3d(self):
        entry = {"source": "", "content": "3D scanning measurement accuracy for foot fitting", "notes": ""}
        assert "scanning_3d_measurement" in classify_entry(entry)

    def test_scanning_foot(self):
        entry = {"source": "", "content": "Foot scanning lidar point cloud", "notes": ""}
        assert "scanning_3d_measurement" in classify_entry(entry)

    def test_production_quality_gate(self):
        entry = {"source": "", "content": "Design for manufacturing quality gate process", "notes": ""}
        assert "production_readiness" in classify_entry(entry)

    def test_production_scale(self):
        entry = {"source": "", "content": "Scale up mass production workflow", "notes": ""}
        assert "production_readiness" in classify_entry(entry)

    def test_claims_fda(self):
        entry = {"source": "", "content": "FDA approved medical device", "notes": ""}
        assert "claims_compliance_risk" in classify_entry(entry)

    def test_claims_pain(self):
        entry = {"source": "", "content": "Pain relief guaranteed", "notes": ""}
        assert "claims_compliance_risk" in classify_entry(entry)

    def test_claims_therapeutic(self):
        entry = {"source": "", "content": "Therapeutic treatment for foot conditions", "notes": ""}
        assert "claims_compliance_risk" in classify_entry(entry)

    def test_content_marketing_viral(self):
        entry = {"source": "", "content": "Viral campaign brand strategy trending", "notes": ""}
        assert "content_marketing" in classify_entry(entry)

    def test_content_luxury_aesthetic(self):
        entry = {"source": "", "content": "Luxury aesthetic minimalist design inspiration", "notes": ""}
        assert "content_marketing" in classify_entry(entry)

    def test_uncategorized(self):
        entry = {"source": "", "content": "The weather in Riyadh today", "notes": ""}
        assert classify_entry(entry) == ["uncategorized"]

    def test_multi_category(self):
        entry = {"source": "", "content": "TPU 3D printed custom footwear startup", "notes": ""}
        cats = classify_entry(entry)
        assert "manufacturing_materials" in cats
        assert "competitor_footwear_product" in cats

    def test_no_category_returns_uncategorized(self):
        entry = {"source": "", "content": "xyz abc", "notes": "qwerty"}
        result = classify_entry(entry)
        assert result == ["uncategorized"]

    def test_classification_uses_all_fields(self):
        """Classifier should check source + content + notes"""
        entry = {"source": "", "content": "", "notes": "GPT-4o multi-agent framework"}
        assert "ai_tools" in classify_entry(entry)
        assert "ai_agents" in classify_entry(entry)


class TestGenerateReport:
    """Tests for the generate_report function."""

    def test_report_has_header(self):
        entries = [{"source": "https://x.com/a", "content": "Test", "notes": ""}]
        classifications = {0: ["ai_tools"]}
        report = generate_report(entries, classifications, pathlib.Path("intake.md"))
        assert "# Manual X Research Intake Report" in report

    def test_report_has_safety_guarantees(self):
        entries = [{"source": "", "content": "Test", "notes": ""}]
        classifications = {0: ["uncategorized"]}
        report = generate_report(entries, classifications, pathlib.Path("intake.md"))
        assert "NO X API" in report
        assert "NO AUTH" in report
        assert "NO POSTING" in report
        assert "NO AUTOMATION" in report

    def test_report_has_category_summary(self):
        entries = [
            {"source": "", "content": "GPT-5 tool", "notes": ""},
            {"source": "", "content": "Nike shoe", "notes": ""},
        ]
        classifications = {0: ["ai_tools"], 1: ["competitor_footwear_product"]}
        report = generate_report(entries, classifications, pathlib.Path("intake.md"))
        assert "## Category Summary" in report
        assert "AI Tools" in report
        assert "Competitor Footwear / Product Signals" in report

    def test_report_has_claims_section(self):
        entries = [
            {"source": "https://x.com/risk", "content": "FDA medical device claim", "notes": ""},
        ]
        classifications = {0: ["claims_compliance_risk"]}
        report = generate_report(entries, classifications, pathlib.Path("intake.md"))
        assert "Z-Claims Review Needed" in report
        assert "Z-Claims" in report

    def test_report_no_claims_when_none_flagged(self):
        entries = [{"source": "", "content": "GPT-5 tool", "notes": ""}]
        classifications = {0: ["ai_tools"]}
        report = generate_report(entries, classifications, pathlib.Path("intake.md"))
        assert "Z-Claims Review Needed" in report
        assert "No entries flagged for claims review" in report

    def test_report_has_entries(self):
        entries = [
            {"source": "https://x.com/a", "content": "Content A", "notes": "Note A"},
            {"source": "https://x.com/b", "content": "Content B", "notes": ""},
        ]
        classifications = {0: ["ai_tools"], 1: ["ai_tools"]}
        report = generate_report(entries, classifications, pathlib.Path("intake.md"))
        assert "Entry #1" in report
        assert "Entry #2" in report
        assert "Content A" in report
        assert "Content B" in report

    def test_report_shows_source_and_notes(self):
        entries = [{"source": "https://x.com/123", "content": "Test", "notes": "Important"}]
        classifications = {0: ["ai_tools"]}
        report = generate_report(entries, classifications, pathlib.Path("intake.md"))
        assert "https://x.com/123" in report
        assert "Important" in report
class TestImprovedClassification:
    """Tests for improved classification based on v3 intake report feedback."""

    def test_dna_nanostructures_maps_to_manufacturing_materials(self):
        entry = {
            "source": "",
            "content": "Build DNA nanostructures with precision using programmable molecular assembly and atomic-scale construction",
            "notes": "",
        }
        cats = classify_entry(entry)
        assert "manufacturing_materials" in cats, f"Expected manufacturing_materials, got {cats}"

    def test_ai_prototyping_maps_to_content_and_production(self):
        entry = {
            "source": "",
            "content": "Product leaders should stop hiding behind PRDs and product strategy docs because AI prototyping changed product development",
            "notes": "prototype-first execution, faster validation",
        }
        cats = classify_entry(entry)
        assert "content_marketing" in cats, f"Expected content_marketing, got {cats}"
        assert "production_readiness" in cats, f"Expected production_readiness, got {cats}"

    def test_claude_agent_training_maps_to_ai_agents(self):
        entry = {
            "source": "",
            "content": "2-hour Claude agent training. Structuring agents that manage themselves, terminal access, file system memory, blocking hallucinations with hooks",
            "notes": "Relevant to Hermes architecture, safer agent execution",
        }
        cats = classify_entry(entry)
        assert "ai_agents" in cats, f"Expected ai_agents, got {cats}"

    def test_agent_employment_maps_to_ai_agents(self):
        entry = {
            "source": "",
            "content": "Turn Claude Into a Full-Time AI Employee in 7 Days",
            "notes": "",
        }
        cats = classify_entry(entry)
        assert "ai_agents" in cats, f"Expected ai_agents, got {cats}"

    def test_posture_mechanoreceptor_remains_claims_risk(self):
        entry = {
            "source": "",
            "content": "Nike shoe posture claim about feet, mechanoreceptors, brain signaling, posture, balance, and movement",
            "notes": "Treat as claims compliance risk",
        }
        cats = classify_entry(entry)
        assert "claims_compliance_risk" in cats, f"Expected claims_compliance_risk, got {cats}"

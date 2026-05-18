"""Tests for prototype_card.py execution card generator.

Covers:
- Successful card creation (basic, custom category/target, custom output)
- Claims safety scanning (clean text, forbidden medical terms, clinical terms)
- Validation errors (empty idea, invalid category, invalid target)
- Card counter persistence and unique IDs
- Output file content validation
"""

import json
import pathlib
import shutil
import tempfile

import pytest

# Add tools/ to path for import
import sys
_tools_dir = pathlib.Path(__file__).resolve().parent.parent / "tools"
sys.path.insert(0, str(_tools_dir))

from prototype_card import (
    _claims_status,
    _generate_card_id,
    _load_counter,
    _next_counter,
    _scan_claims,
    generate_card,
)
import prototype_card


# ── Fixtures ────────────────────────────────────────────────────────────────

@pytest.fixture(autouse=True)
def _reset_counter(monkeypatch, tmp_path):
    """Redirect the counter file to a tmp directory and reset reports dir."""
    counter_path = tmp_path / "counter.json"
    monkeypatch.setattr(prototype_card, "CARD_COUNTER_PATH", counter_path)
    reports_dir = tmp_path / "reports" / "prototype-cards"
    reports_dir.mkdir(parents=True)
    monkeypatch.setattr(prototype_card, "REPORTS_DIR", reports_dir)


# ── Claims Scanning ─────────────────────────────────────────────────────────

class TestScanClaims:
    def test_clean_passes(self):
        text = "Lightweight TPU sole with Gyroid 0.6mm structure for comfort"
        findings = _scan_claims(text)
        assert len(findings) == 0

    def test_detects_treats(self):
        text = "Design that treats flat arch"
        findings = _scan_claims(text)
        assert len(findings) >= 1
        matched_words = [f["matched"].lower() for f in findings]
        assert any("treat" in w for w in matched_words)

    def test_detects_diagnoses(self):
        text = "App that diagnoses foot problems"
        findings = _scan_claims(text)
        assert len(findings) >= 1
        matched_words = [f["matched"].lower() for f in findings]
        assert any("diagnos" in w for w in matched_words)

    def test_detects_cures(self):
        text = "Insole that cures pain"
        findings = _scan_claims(text)
        assert len(findings) >= 1

    def test_detects_therapeutic(self):
        text = "A therapeutic approach to insole design"
        findings = _scan_claims(text)
        assert len(findings) >= 1

    def test_detects_clinically_proven(self):
        text = "Clinically proven to reduce discomfort"
        findings = _scan_claims(text)
        assert len(findings) >= 1

    def test_detects_medically_proven(self):
        text = "Medically proven effectiveness"
        findings = _scan_claims(text)
        assert len(findings) >= 1

    def test_detects_plantar_fasciitis(self):
        text = "Support for plantar fasciitis sufferers"
        findings = _scan_claims(text)
        assert len(findings) >= 1

    def test_findings_have_required_keys(self):
        text = "treats pain effectively"
        findings = _scan_claims(text)
        for f in findings:
            assert "category" in f
            assert "matched" in f
            assert "suggestion" in f

    def test_engineering_language_passes(self):
        text = "This is an engineering estimate based on simulation"
        findings = _scan_claims(text)
        assert len(findings) == 0


class TestClaimsStatus:
    def test_pass_on_empty(self):
        assert _claims_status([]) == "PASS"

    def test_review_on_findings(self):
        assert _claims_status([{"category": "medical", "matched": "treats"}]) == "REVIEW"


# ── Card Generation ─────────────────────────────────────────────────────────

class TestGenerateCard:
    def test_basic_creation(self, tmp_path):
        result = generate_card(
            idea="TPU sole with Gyroid pattern for everyday comfort",
            category="engineering",
            target="universal",
        )
        assert result["card_id"].startswith("CARD-")
        assert result["claims_status"] == "PASS"
        assert result["category"] == "engineering"
        assert pathlib.Path(result["output_path"]).exists()

    def test_card_file_contains_idea(self):
        result = generate_card(
            idea="Rose gold accent plate for sports line",
            category="design",
            target="sports",
        )
        content = pathlib.Path(result["output_path"]).read_text()
        assert "Rose gold accent plate for sports line" in content

    def test_card_file_contains_card_id(self):
        result = generate_card(
            idea="Sensor grid prototype for size 42",
            category="engineering",
        )
        content = pathlib.Path(result["output_path"]).read_text()
        assert result["card_id"] in content

    def test_claims_review_in_card(self):
        text = "Design that treats foot pain"
        result = generate_card(idea=text, category="design")
        content = pathlib.Path(result["output_path"]).read_text()
        assert "REVIEW" in result["claims_status"]
        assert "Z-Claims" in content

    def test_invalid_category_raises(self):
        with pytest.raises(ValueError, match="Invalid category"):
            generate_card(idea="Some idea", category="invalid_cat")

    def test_invalid_target_raises(self):
        with pytest.raises(ValueError, match="Invalid target"):
            generate_card(idea="Some idea", target="aliens")

    def test_empty_idea_raises(self):
        with pytest.raises(ValueError, match="Idea text is required"):
            generate_card(idea="")

    def test_custom_output_path(self, tmp_path):
        out = str(tmp_path / "custom_card.md")
        result = generate_card(idea="Test idea", output_path=out)
        assert result["output_path"] == out
        assert pathlib.Path(out).exists()

    def test_unique_ids(self):
        r1 = generate_card(idea="First idea", category="engineering")
        r2 = generate_card(idea="Second idea", category="engineering")
        assert r1["card_id"] != r2["card_id"]

    def test_card_contains_required_sections(self):
        result = generate_card(idea="Test for sections", category="research")
        content = pathlib.Path(result["output_path"]).read_text()
        sections = [
            "## Idea",
            "## Smallest Local Prototype/Demo",
            "## Required Measurement/Input",
            "## QA Check",
            "## Claims-Safety Check",
            "## Printability/Manufacturing Readiness Check",
            "## Production-Sample Impact",
            "## Blocker",
            "## Next Action",
            "## Status History",
            "## Engineering-Only Confirmation",
        ]
        for section in sections:
            assert section in content, f"Missing section: {section}"

    def test_engineering_only_confirmation_present(self):
        result = generate_card(idea="Something here", category="ux")
        content = pathlib.Path(result["output_path"]).read_text()
        assert "no medical, diagnostic, therapeutic" in content
        assert "Z-Claims" in content

    def test_arabic_summary_present(self):
        result = generate_card(idea="Something here", category="ux")
        content = pathlib.Path(result["output_path"]).read_text()
        assert "للسلطان" in content


# ── Counter ─────────────────────────────────────────────────────────────────

class TestCounter:
    def test_counter_starts_at_zero(self):
        # After _reset_counter fixture, counter file doesn't exist yet
        _next_counter()  # Should create and return seq=1
        # The card ID should have seq 001
        card_id = _generate_card_id()
        assert card_id.endswith("-002")  # 001 was consumed, now 002

    def test_counter_persists(self, monkeypatch):
        # _load_counter should read back what _next_counter wrote
        today, seq = _next_counter()
        today2, seq2 = _load_counter()
        assert today == today2
        assert seq == seq2

    def test_card_id_format(self):
        card_id = _generate_card_id()
        parts = card_id.split("-")
        assert parts[0] == "CARD"
        assert len(parts[2]) == 3  # NNN format

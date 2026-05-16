"""Tests for soul_runtime_gate — classifies proposed tasks against ZILFIT SOUL.md boundaries.

Uses only local/mocked task text — no real SOUL.md required, no production impact.
"""

import pathlib
import sys

# Ensure tools dir is importable
TOOLS_DIR = pathlib.Path(__file__).resolve().parent.parent / "tools"
sys.path.insert(0, str(TOOLS_DIR))

from soul_runtime_gate import gate, ALLOW, REVIEW_REQUIRED, BLOCK  # noqa: E402

# ── ALLOW cases ──────────────────────────────────────────────────────

class TestAllow:
    """Tasks that should be allowed without review."""

    def test_local_report(self):
        r = gate("Generate a local daily report in reports/daily/")
        assert r["decision"] == ALLOW
        assert not r["violations"]

    def test_local_test(self):
        r = gate("Run local tests for the z-bio comfort score module")
        assert r["decision"] == ALLOW

    def test_local_parser(self):
        r = gate(
            "Write a local YAML parser for the agent directives config"
        )
        assert r["decision"] == ALLOW

    def test_local_non_production_utility(self):
        r = gate("Create a local utility that formats Markdown tables")
        assert r["decision"] == ALLOW

    def test_read_file(self):
        r = gate("Read SOUL.md and check for required sections")
        assert r["decision"] == ALLOW

    def test_write_own_memory(self):
        r = gate("Update my own memory and skills about TPU material properties")
        assert r["decision"] == ALLOW

    def test_local_simulation(self):
        r = gate("Run local pressure-density simulation for flat arch size 42")
        assert r["decision"] == ALLOW


# ── REVIEW_REQUIRED cases ───────────────────────────────────────────

class TestReviewRequired:
    """Tasks that require human review before proceeding."""

    def test_public_release(self):
        r = gate("Prepare a public release for the ZILFIT insole SDK")
        assert r["decision"] == REVIEW_REQUIRED

    def test_partnership(self):
        r = gate("Draft a partnership proposal for a 3D printing vendor")
        assert r["decision"] == REVIEW_REQUIRED

    def test_investor(self):
        r = gate("Create an investor presentation with pressure data")
        assert r["decision"] == REVIEW_REQUIRED

    def test_sample_production(self):
        r = gate("Initiate sample production run for TPU insole")
        assert r["decision"] == REVIEW_REQUIRED

    def test_changes_outside_worktree(self):
        r = gate("Modify files outside the current worktree in /opt/zilfit/")
        assert r["decision"] == REVIEW_REQUIRED

    def test_funding(self):
        r = gate("Prepare a funding pitch deck for ZILFIT")
        assert r["decision"] == REVIEW_REQUIRED

    def test_go_live(self):
        r = gate("Go live with the new Telegram bot")
        assert r["decision"] == REVIEW_REQUIRED


# ── BLOCK cases ──────────────────────────────────────────────────────

class TestBlock:
    """Tasks that must be blocked — hard boundary violations."""

    def test_merge_to_main(self):
        r = gate("Merge this branch into main")
        assert r["decision"] == BLOCK

    def test_push_to_main(self):
        r = gate("Push the feature directly to main for deployment")
        assert r["decision"] == BLOCK

    def test_production_deploy(self):
        r = gate("Deploy the new bot to production servers")
        assert r["decision"] == BLOCK

    def test_modify_env(self):
        r = gate("Change the .env file with new API secrets")
        assert r["decision"] == BLOCK

    def test_modify_cron(self):
        r = gate("Modify the cron job for nightly reports")
        assert r["decision"] == BLOCK

    def test_modify_systemd(self):
        r = gate("Create a new systemd unit for the agent")
        assert r["decision"] == BLOCK

    def test_modify_tunnel(self):
        r = gate("Change the tunnel configuration for the bot")
        assert r["decision"] == BLOCK

    def test_modify_tmux(self):
        r = gate("Create a new tmux session for background processing")
        assert r["decision"] == BLOCK

    def test_spend_paid_api(self):
        r = gate("Use the paid OpenAI API for the nightly batch")
        assert r["decision"] == BLOCK

    def test_medical_claim_treatment(self):
        r = gate("Claim that the insole treats plantar fasciitis")
        assert r["decision"] == BLOCK

    def test_medical_claim_diagnostic(self):
        r = gate("The scan feature diagnoses foot arch type")
        assert r["decision"] == BLOCK

    def test_medical_claim_therapeutic(self):
        r = gate("This design provides therapeutic pain relief")
        assert r["decision"] == BLOCK

    def test_medical_claim_clinical(self):
        r = gate("Clinical evidence shows reduced heel pressure")
        assert r["decision"] == BLOCK

    def test_delete_file(self):
        r = gate("Delete the telegram_bot directory and all files")
        assert r["decision"] == BLOCK

    def test_rm_command(self):
        r = gate("Run rm -rf /old-data to clean up")
        assert r["decision"] == BLOCK

    def test_send_telegram_message(self):
        r = gate("Send a Telegram notification to all subscribers")
        assert r["decision"] == BLOCK

    def test_execute_telegram_command(self):
        r = gate("Execute the /restart command on the Telegram bot")
        assert r["decision"] == BLOCK

    def test_modify_prod_telegram_bot(self):
        r = gate("Modify production services in telegram_bot/bot.py")
        assert r["decision"] == BLOCK

    def test_paid_cloud_resource(self):
        r = gate("Spend cloud resources for a large batch job")
        assert r["decision"] == BLOCK

    def test_cure_claim(self):
        r = gate("Show that our insole cures foot deformity")
        assert r["decision"] == BLOCK


# ── Edge cases / robustness ──────────────────────────────────────────

class TestEdgeCases:
    """Boundary and robustness checks."""

    def test_empty_string(self):
        r = gate("")
        # Empty should not crash; decision depends on pattern matching
        assert r["decision"] in (ALLOW, REVIEW_REQUIRED, BLOCK)

    def test_none_not_accepted(self):
        # gate expects a string — ensure it handles it gracefully
        try:
            gate(None)
        except (TypeError, AttributeError):
            pass  # acceptable

    def test_uppercase_text(self):
        r = gate("MERGE this branch into MAIN immediately")
        assert r["decision"] == BLOCK

    def test_mixed_case_medical(self):
        r = gate("The device has THERAPEUTIC benefits for PAIN Relief")
        assert r["decision"] == BLOCK

    def test_decision_keys_present(self):
        """Every result must have the required keys."""
        r = gate("Run local tests")
        assert "decision" in r
        assert "reason" in r
        assert "boundary" in r or "violations" in r

    def test_decision_value_is_valid(self):
        """Decision must be one of the three valid values."""
        for text in [
            "local test",
            "public release",
            "merge to main",
        ]:
            r = gate(text)
            assert r["decision"] in (ALLOW, REVIEW_REQUIRED, BLOCK)

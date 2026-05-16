"""Tests for tools/gated_task_runner.py — gate-first task runner.

Covers ALLOW, REVIEW_REQUIRED, and BLOCK via the run_gate() wrapper.
Uses only local/mocked task text — no real SOUL.md required, no production impact.
"""

import pathlib
import sys

# Ensure tools dir is importable
TOOLS_DIR = pathlib.Path(__file__).resolve().parent.parent / "tools"
sys.path.insert(0, str(TOOLS_DIR))

from gated_task_runner import run_gate, ALLOW, REVIEW_REQUIRED, BLOCK  # noqa: E402


# ── ALLOW cases (GATE_ALLOW) ─────────────────────────────────────────

class TestGateAllow:
    """Tasks that should result in GATE_ALLOW."""

    def test_run_local_tests(self):
        r = run_gate("Run local tests for z-bio module")
        assert r == ALLOW

    def test_generate_local_report(self):
        r = run_gate("Generate a local daily report in reports/daily/")
        assert r == ALLOW

    def test_local_utility(self):
        r = run_gate("Create a local utility that formats Markdown tables")
        assert r == ALLOW

    def test_read_file(self):
        r = run_gate("Read SOUL.md and check for required sections")
        assert r == ALLOW


# ── REVIEW_REQUIRED cases (GATE_REVIEW_REQUIRED) ─────────────────────

class TestGateReviewRequired:
    """Tasks that require Sultan approval (GATE_REVIEW_REQUIRED)."""

    def test_public_release(self):
        r = run_gate("Prepare a public release for the ZILFIT insole SDK")
        assert r == REVIEW_REQUIRED

    def test_partnership(self):
        r = run_gate("Draft a partnership proposal for a 3D printing vendor")
        assert r == REVIEW_REQUIRED

    def test_investor(self):
        r = run_gate("Create an investor presentation with pressure data")
        assert r == REVIEW_REQUIRED

    def test_changes_outside_worktree(self):
        r = run_gate("Modify files outside the current worktree in /opt/zilfit/")
        assert r == REVIEW_REQUIRED

    def test_go_live(self):
        r = run_gate("Go live with the new Telegram bot")
        assert r == REVIEW_REQUIRED


# ── BLOCK cases (GATE_BLOCK) ─────────────────────────────────────────

class TestGateBlock:
    """Tasks that must be blocked (GATE_BLOCK)."""

    def test_merge_to_main(self):
        r = run_gate("Merge this branch into main")
        assert r == BLOCK

    def test_push_to_main(self):
        r = run_gate("Push the feature directly to main for deployment")
        assert r == BLOCK

    def test_production_deploy(self):
        r = run_gate("Deploy the new bot to production servers")
        assert r == BLOCK

    def test_modify_env(self):
        r = run_gate("Change the .env file with new API secrets")
        assert r == BLOCK

    def test_modify_cron(self):
        r = run_gate("Modify the cron job for nightly reports")
        assert r == BLOCK

    def test_modify_systemd(self):
        r = run_gate("Create a new systemd unit for the agent")
        assert r == BLOCK

    def test_modify_tunnel(self):
        r = run_gate("Change the tunnel configuration for the bot")
        assert r == BLOCK

    def test_modify_tmux(self):
        r = run_gate("Create a new tmux session for background processing")
        assert r == BLOCK

    def test_spend_paid_api(self):
        r = run_gate("Use the paid OpenAI API for the nightly batch")
        assert r == BLOCK

    def test_medical_claim_treatment(self):
        r = run_gate("Claim that the insole treats plantar fasciitis")
        assert r == BLOCK

    def test_medical_claim_diagnostic(self):
        r = run_gate("The scan feature diagnoses foot arch type")
        assert r == BLOCK

    def test_medical_claim_therapeutic(self):
        r = run_gate("This design provides therapeutic pain relief")
        assert r == BLOCK

    def test_medical_claim_clinical(self):
        r = run_gate("Clinical evidence shows reduced heel pressure")
        assert r == BLOCK

    def test_delete_file(self):
        r = run_gate("Delete the telegram_bot directory and all files")
        assert r == BLOCK

    def test_rm_command(self):
        r = run_gate("Run rm -rf /old-data to clean up")
        assert r == BLOCK

    def test_send_telegram_message(self):
        r = run_gate("Send a Telegram notification to all subscribers")
        assert r == BLOCK

    def test_execute_telegram_command(self):
        r = run_gate("Execute the /restart command on the Telegram bot")
        assert r == BLOCK

    def test_modify_prod_telegram_bot(self):
        r = run_gate("Modify production services in telegram_bot/bot.py")
        assert r == BLOCK

    def test_paid_cloud_resource(self):
        r = run_gate("Spend cloud resources for a large batch job")
        assert r == BLOCK

    def test_cure_claim(self):
        r = run_gate("Show that our insole cures foot deformity")
        assert r == BLOCK


# ── Edge cases ───────────────────────────────────────────────────────

class TestEdgeCases:
    """Boundary and robustness checks."""

    def test_empty_string(self):
        r = run_gate("")
        assert r in (ALLOW, REVIEW_REQUIRED, BLOCK)

    def test_uppercase_text(self):
        r = run_gate("MERGE this branch into MAIN immediately")
        assert r == BLOCK

    def test_mixed_case_medical(self):
        r = run_gate("The device has THERAPEUTIC benefits for PAIN Relief")
        assert r == BLOCK

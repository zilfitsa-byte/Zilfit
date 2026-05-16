#!/usr/bin/env python3
"""P0 Architecture Gate — Z-Agent Import Isolation Test.

Prevents Z-agents from directly importing another Z-agent's runtime module.

RULE: Each Z-agent runtime script ("run_z_*_agent.py") may import:
  - shared_db
  - the claims scanner
  - stdlib / third-party packages

It MUST NOT import:
  - runtime.run_z_<other_agent>  (e.g. Z-Physics importing Z-Bio)

Inter-agent communication must use SharedDB records or shared contracts,
not direct runtime imports.

Run:
    pytest tests/test_architecture_gate.py
    python3 tests/test_architecture_gate.py
"""
from __future__ import annotations

import ast
import re
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

# ---------------------------------------------------------------------------
# Gate definitions
# ---------------------------------------------------------------------------

# Files in runtime/ that are considered "Z-agent runtime scripts"
# Pattern: run_z_*_agent.py  OR  z_claims_scanner.py  OR  z_qa_agent
RUNTIME_DIR = ROOT / "runtime"

# Regex to identify a Z-agent runtime file
Z_AGENT_RUNTIME_PATTERN = re.compile(
    r"run_z_(?:\w+?)_agent\.py"
    r"|z_claims_scanner\.py"
    r"|z_research.*\.py"
)

# Modules that any Z-agent IS allowed to import (allowed = shared infra)
ALLOWED_RUNTIME_IMPORTS = frozenset({
    "runtime.shared_db",
    "runtime.z_claims_scanner",
})

# Files that are orchestrators / handoff builders rather than agents.
# These are allowed to import runtime modules — they coordinate flows.
ORCHESTRATOR_PATTERNS = re.compile(
    r"^(build_|emit_|run_z_ux_|run_local_|compute_|scan_image_)"
)


def _find_agent_scripts(runtime_dir: Path) -> list[Path]:
    """Return sorted list of Z-agent runtime scripts."""
    if not runtime_dir.is_dir():
        return []
    scripts = [
        f for f in sorted(runtime_dir.iterdir())
        if f.is_file() and f.name.endswith(".py") and Z_AGENT_RUNTIME_PATTERN.search(f.name)
    ]
    return scripts


def _is_orchestrator(path: Path) -> bool:
    """True if the file is an orchestrator/handoff script (allowed cross-imports)."""
    return bool(ORCHESTRATOR_PATTERNS.match(path.name))


def _get_imported_runtime_modules(filepath: Path) -> list[tuple[str, int]]:
    """Parse a Python file AST and return [(module, lineno)] for imports
    that match the 'runtime.run_z_*' or 'runtime.z_*' namespace."""
    results: list[tuple[str, int]] = []
    try:
        tree = ast.parse(filepath.read_text(encoding="utf-8"), filename=str(filepath))
    except SyntaxError:
        return results

    for node in ast.walk(tree):
        module_name: str | None = None
        if isinstance(node, ast.Import):
            lineno = getattr(node, "lineno", 0)
            for alias in node.names:
                if alias.name.startswith("runtime."):
                    module_name = alias.name
                    results.append((module_name, lineno))
        elif isinstance(node, ast.ImportFrom):
            if node.module and node.module.startswith("runtime."):
                lineno = getattr(node, "lineno", 0)
                results.append((node.module, lineno))
    return results


def _is_allowed_import(mod: str, agent_name: str) -> bool:
    """Check whether a runtime import is allowed."""
    if mod in ALLOWED_RUNTIME_IMPORTS:
        return True
    # Self-import is fine (e.g. Z-Bio importing from itself — unlikely but legal)
    if mod == agent_name:
        return True
    return False


def _extract_agent_name(filepath: Path) -> str:
    """Derive a module-like agent name from the path, e.g.
    run_z_bio_agent.py -> runtime.run_z_bio_agent"""
    return f"runtime.{filepath.stem}"


# ---------------------------------------------------------------------------
# Test case
# ---------------------------------------------------------------------------

class TestAgentImportIsolationGate(unittest.TestCase):
    """P0 gate: no Z-agent imports another Z-agent runtime module."""

    def test_no_cross_agent_imports(self):
        """Every Z-agent runtime script must not import another Z-agent's module."""
        agent_scripts = _find_agent_scripts(RUNTIME_DIR)
        self.assertTrue(
            len(agent_scripts) > 0,
            "No Z-agent runtime scripts found — gate test should be skipped or paths fixed",
        )

        violations: list[str] = []

        for script in agent_scripts:
            if _is_orchestrator(script):
                continue

            agent_mod = _extract_agent_name(script)
            imports = _get_imported_runtime_modules(script)

            for mod, lineno in imports:
                if mod == agent_mod:
                    continue  # self-reference is fine
                if _is_allowed_import(mod, agent_mod):
                    continue  # allowed shared infra

                # This is a cross-agent import violation
                violations.append(
                    f"{script.name}:{lineno} -> imports '{mod}' "
                    f"(cross-agent import forbidden)"
                )

        if violations:
            header = (
                "ARCHITECTURE GATE VIOLATION — Z-agent(s) import each other directly.\n"
                "Agents MUST communicate through SharedDB or shared contracts.\n"
            )
            self.fail(header + "\n".join(f"  - {v}" for v in violations))

    def test_gate_finds_expected_agents(self):
        """Sanity: we actually discover known agent scripts."""
        agent_scripts = _find_agent_scripts(RUNTIME_DIR)
        names = {s.name for s in agent_scripts}
        # These should exist in the project
        self.assertIn("run_z_bio_agent.py", names, "Z-Bio agent script missing")
        self.assertIn("run_z_physics_agent.py", names, "Z-Physics agent script missing")


# ---------------------------------------------------------------------------
# CLI entry point (no pytest needed)
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    print("=" * 64)
    print("ZILFIT P0 Architecture Gate — Agent Import Isolation")
    print("=" * 64)
    result = unittest.TestLoader().loadTestsFromTestCase(
        TestAgentImportIsolationGate
    )
    runner = unittest.TextTestRunner(verbosity=2)
    outcome = runner.run(result)
    if not outcome.wasSuccessful():
        sys.exit(1)
    print(f"\nGATE RESULT: PASS  ({len(outcome.errors)} errors, {len(outcome.failures)} failures)")

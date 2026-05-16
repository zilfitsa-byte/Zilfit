"""Gate-first task runner for Hermes/ZILFIT.

This is the standard first step before any future local Hermes/ZILFIT task.
It does NOT execute the task — it only gates and prepares the decision.

Usage:
    from gated_task_runner import run_gate
    run_gate("Run local tests for z-bio module")

    # CLI:
    python -m tools.gated_task_runner "Run local tests"
    echo "Run local tests" | python -m tools.gated_task_runner
"""

import sys
import textwrap

# Import the soul runtime gate
import pathlib
_tools_dir = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(_tools_dir))

from soul_runtime_gate import gate  # noqa: E402

ALLOW = "GATE_ALLOW"
REVIEW_REQUIRED = "GATE_REVIEW_REQUIRED"
BLOCK = "GATE_BLOCK"

_SEPARATOR = "=" * 60


def _allow_action(task_text: str) -> None:
    print(f"{_SEPARATOR}")
    print(f"  {ALLOW}")
    print(f"{_SEPARATOR}")
    print(f"Task:       {task_text}")
    print(f"Status:     No boundary violations detected.")
    print()
    print("Next-step instruction template:")
    print("  1. Create or switch to an isolated branch/worktree.")
    print("  2. Make the smallest safe change.")
    print("  3. Run local tests relevant to the change.")
    print("  4. Commit with a clear message.")
    print("  5. Report results (do NOT merge to main).")
    print(f"{_SEPARATOR}")


def _review_action(task_text: str, result: dict) -> None:
    print(f"{_SEPARATOR}")
    print(f"  {REVIEW_REQUIRED}")
    print(f"{_SEPARATOR}")
    print(f"Task:       {task_text}")
    print(f"Reason:     {result['reason']}")
    if result.get("boundary"):
        print(f"Boundary:   {result['boundary']}")
    print()
    print("Sultan approval is required before proceeding.")
    print("Do NOT execute the task until Sultan approves.")
    print(f"{_SEPARATOR}")


def _block_action(task_text: str, result: dict) -> None:
    print(f"{_SEPARATOR}")
    print(f"  {BLOCK}")
    print(f"{_SEPARATOR}")
    print(f"Task:       {task_text}")
    print(f"Reason:     {result['reason']}")
    if result.get("boundary"):
        print(f"Boundary:   {result['boundary']}")
    violations = result.get("violations", [])
    if violations:
        print(f"Violation{'s' if len(violations) > 1 else ''}: {', '.join(violations)}")
    print()
    print("Safer alternative:")
    print("  Reformulate the task to avoid the violated boundary.")
    print("  Remove references to restricted operations.")
    if result.get("boundary") is None or "Section 4" in str(result.get("boundary", "")):
        print("  Consider moving the operation to an isolated branch/worktree.")
    print("  Re-run the gate check with the revised task text.")
    print(f"{_SEPARATOR}")


def run_gate(task_text: str) -> str:
    """Gate a proposed task and print the decision. Returns the decision string."""
    result = gate(task_text)
    decision = result["decision"]

    if decision == "ALLOW":
        _allow_action(task_text)
        return ALLOW
    elif decision == "REVIEW_REQUIRED":
        _review_action(task_text, result)
        return REVIEW_REQUIRED
    else:
        _block_action(task_text, result)
        return BLOCK


def main():
    """CLI entry point."""
    if len(sys.argv) > 1:
        task_text = " ".join(sys.argv[1:])
    else:
        task_text = sys.stdin.read().strip()

    if not task_text:
        print("Usage: python -m tools.gated_task_runner <task text>")
        print("   or: echo '<task text>' | python -m tools.gated_task_runner")
        sys.exit(1)

    decision = run_gate(task_text)

    if decision == BLOCK:
        sys.exit(2)
    elif decision == REVIEW_REQUIRED:
        sys.exit(1)


if __name__ == "__main__":
    main()

"""X Research Radar — Local Planning & Report Tool.

Reads config/x_research_radar.yaml and prints a structured radar plan
with categories, allowed uses, blocked uses, and report template.

This is READ-ONLY planning only. It does NOT connect to X, does NOT
use x_search, and performs no network requests of any kind.

Usage:
    python tools/x_research_radar_plan.py           # full plan
    python tools/x_research_radar_plan.py --summary  # condensed summary
    python tools/x_research_radar_plan.py --validate  # validate config
"""

import argparse
import pathlib
import sys
import textwrap

import yaml  # PyYAML is a standard dependency in most Python envs

# ── Constants ────────────────────────────────────────────────────────
REPO_ROOT = pathlib.Path(__file__).resolve().parent.parent
CONFIG_PATH = REPO_ROOT / "config" / "x_research_radar.yaml"

SEPARATOR = "=" * 64
THIN_SEP = "-" * 64


def load_config(path: pathlib.Path | str | None = None) -> dict:
    """Load the radar config YAML. Returns dict or raises."""
    cfg_path = pathlib.Path(path) if path else CONFIG_PATH
    if not cfg_path.exists():
        raise FileNotFoundError(f"Radar config not found: {cfg_path}")
    with open(cfg_path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)


def _print_header(title: str) -> None:
    print(SEPARATOR)
    print(f"  {title}")
    print(SEPARATOR)
    print()


def _print_section(title: str) -> None:
    print(THIN_SEP)
    print(f"  {title}")
    print(THIN_SEP)
    print()


def print_plan(cfg: dict) -> None:
    """Print the full structured radar plan."""
    radar = cfg.get("radar", {})
    groups = cfg.get("query_groups", [])
    template = cfg.get("report_template", {})

    # ── Header ──────────────────────────────────────────────────────
    _print_header(f"ZILFIT X Research Radar — {radar.get('name', 'Plan')}")
    print(f"  Version:       {radar.get('version', 'N/A')}")
    print(f"  Mode:          {radar.get('mode', 'unknown')}")
    print(f"  Integration:   {radar.get('integration_target', 'none')}")
    print(f"  Constraint:    {radar.get('constraint', 'none')}")
    print(f"  Config path:   {CONFIG_PATH.relative_to(REPO_ROOT)}")
    print()

    # ── Allowed Actions ─────────────────────────────────────────────
    _print_section("Allowed Uses (read-only planning)")
    allowed = radar.get("allowed_actions", [])
    for a in allowed:
        print(f"    [+] {a}")
    if not allowed:
        print("    (none defined)")
    print()

    # ── Blocked Actions ─────────────────────────────────────────────
    _print_section("Blocked Actions (MUST NOT)")
    blocked = radar.get("blocked_actions", [])
    for b in blocked:
        print(f"    [X] {b}")
    if not blocked:
        print("    (none defined)")
    print()

    # ── Query Groups ────────────────────────────────────────────────
    _print_section(f"Query Groups ({len(groups)} total)")
    for i, g in enumerate(groups, start=1):
        print(f"  {i}. [{g.get('priority', 'N/A').upper()}] {g['name']}")
        print(f"     ID:   {g['id']}")
        desc = g.get("description", "")
        # Wrap long descriptions to ~72 chars
        wrapped = textwrap.fill(desc, width=68, initial_indent="     Desc: ", subsequent_indent="           ") if len(desc) > 60 else f"     Desc: {desc}"
        print(wrapped)
        queries = g.get("sample_queries", [])
        if queries:
            print(f"     Sample queries:")
            for q in queries:
                print(f"       - \"{q}\"")
        tags = g.get("tags", [])
        if tags:
            print(f"     Tags: {', '.join(tags)}")
        note = g.get("note")
        if note:
            wrapped_note = textwrap.fill(f"Note: {note}", width=66, initial_indent="     ", subsequent_indent="           ")
            print(wrapped_note)
        print()

    # ── Report Template ─────────────────────────────────────────────
    _print_section("Report Template")
    sections = template.get("sections", [])
    for s in sections:
        print(f"    - {s['name']}: {s.get('description', '')}")
    print()

    # ── Safety & Compliance ─────────────────────────────────────────
    _print_section("Safety & Compliance")
    print("    - No X connection active yet")
    print("    - No auth/API keys used")
    print("    - No posting, replying, liking, following, or DM")
    print("    - All outputs engineering/technical research only")
    print("    - Medical/clinical boundaries: Z-Claims review required")
    print("    - No production, cron, systemd, or tunnel changes")
    print("    - Human approval required before activating x_search")
    print()


def print_summary(cfg: dict) -> None:
    """Print a condensed summary."""
    radar = cfg.get("radar", {})
    groups = cfg.get("query_groups", [])
    blocked = radar.get("blocked_actions", [])
    allowed = radar.get("allowed_actions", [])

    print(f"ZILFIT X Research Radar — Summary")
    print(f"  Mode: {radar.get('mode', 'unknown')}")
    print(f"  Query groups: {len(groups)}")
    print(f"  Allowed actions: {len(allowed)}")
    print(f"  Blocked actions: {len(blocked)}")
    print()
    print(f"  Groups:")
    for g in groups:
        print(f"    [{g.get('priority', '?'):5s}] {g['name']}")
    print()
    
    # Verify critical blocked actions are present
    critical_blocked = {"post", "reply", "like", "follow", "auto_execute"}
    missing = critical_blocked - set(blocked)
    if missing:
        print(f"  WARNING: Missing blocked actions: {', '.join(missing)}")
    else:
        print(f"  All critical actions blocked: post, reply, like, follow, auto_execute")


def validate_config(cfg: dict) -> bool:
    """Validate the radar config structure. Returns True if valid."""
    errors = []

    # Top-level keys
    for key in ("radar", "query_groups", "report_template"):
        if key not in cfg:
            errors.append(f"Missing top-level key: {key}")

    if errors:
        for e in errors:
            print(f"  ERROR: {e}")
        return False

    # Radar block
    radar = cfg["radar"]
    if "mode" not in radar:
        errors.append("Missing radar.mode")
    if radar.get("mode") == "active":
        errors.append("mode must NOT be 'active' without human approval")
    blocked = radar.get("blocked_actions", [])
    required_blocked = {"post", "reply", "like", "follow", "auto_execute"}
    missing_required = required_blocked - set(blocked)
    if missing_required:
        errors.append(f"Missing blocked_actions: {', '.join(missing_required)}")

    # Query groups
    groups = cfg["query_groups"]
    if not groups:
        errors.append("query_groups must not be empty")
    seen_ids = set()
    for g in groups:
        gid = g.get("id")
        if not gid:
            errors.append("query_group missing 'id'")
        elif gid in seen_ids:
            errors.append(f"Duplicate query_group id: {gid}")
        seen_ids.add(gid)
        if "sample_queries" not in g or not g["sample_queries"]:
            errors.append(f"query_group '{gid}' missing sample_queries")
        if "priority" not in g:
            errors.append(f"query_group '{gid}' missing priority")

    # Report template
    template = cfg["report_template"]
    if "sections" not in template or not template["sections"]:
        errors.append("report_template missing sections")

    if errors:
        for e in errors:
            print(f"  ERROR: {e}")
        return False

    print(f"  Config valid: {len(groups)} query groups, {len(blocked)} blocked actions")
    return True


def main() -> int:
    parser = argparse.ArgumentParser(description="X Research Radar — local planning tool")
    parser.add_argument("--summary", action="store_true", help="Print condensed summary")
    parser.add_argument("--validate", action="store_true", help="Validate config only")
    parser.add_argument("--config", type=str, default=None, help="Override config path")
    args = parser.parse_args()

    try:
        cfg = load_config(args.config)
    except FileNotFoundError as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1

    if args.validate:
        _print_header("ZILFIT X Research Radar — Validation")
        ok = validate_config(cfg)
        return 0 if ok else 1

    if args.summary:
        print_summary(cfg)
        return 0

    print_plan(cfg)
    return 0


if __name__ == "__main__":
    sys.exit(main())

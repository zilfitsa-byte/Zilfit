#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
cd "$REPO_ROOT"

DIV="============================================================"
DIV2="------------------------------------------------------------"

echo "$DIV"
echo "  ZILFIT Project Health Check"
echo "  $(date -u '+%Y-%m-%dT%H:%M:%SZ')"
echo "  Root: $REPO_ROOT"
echo "$DIV"
echo ""

# 1. Git status
echo "  ── Git Status ──"
if git rev-parse --git-dir > /dev/null 2>&1; then
    BRANCH=$(git branch --show-current)
    echo "  Branch: $BRANCH"
    echo "  Last commit: $(git log -1 --format='%h %s (%ai)')"
    echo ""
    echo "  Status (short):"
    git status --short
    echo ""
    UNTRACKED=$(git status --porcelain --untracked-files=normal | grep '^??' | wc -l || true)
    MODIFIED=$(git status --porcelain --untracked-files=normal | grep '^[ M]' | wc -l || true)
    echo "  Untracked: $UNTRACKED  Modified: $MODIFIED"
else
    echo "  WARNING: Not a git repository"
fi
echo ""

# 2. Disk space
echo "  ── Disk Space ──"
df -h "$REPO_ROOT" | tail -1 | awk '{printf "  Filesystem: %-20s  Total: %5s  Used: %5s  Avail: %5s  Use%%: %s\n", $1, $2, $3, $4, $5}'
echo ""

# 3. Largest project folders
echo "  ── Largest Project Folders (top 15) ──"
du -sh .[!.]* * 2>/dev/null | sort -rh | head -15 | while read size name; do
    printf "  %-10s %s\n" "$size" "$name"
done
echo ""

# 4. Python compile check
echo "  ── Python Compile Check ──"
COMPILE_OK=0
COMPILE_FAIL=0
while IFS= read -r -d '' pyfile; do
    if python3 -m py_compile "$pyfile" 2>/dev/null; then
        COMPILE_OK=$((COMPILE_OK + 1))
    else
        echo "  FAIL: $pyfile"
        COMPILE_FAIL=$((COMPILE_FAIL + 1))
    fi
done < <(find tools/ validators/ zilfit_orthotics/ telegram_bot/ -name '*.py' -print0 2>/dev/null || true)
echo "  OK: $COMPILE_OK  FAIL: $COMPILE_FAIL"
echo ""

# 5. Key output files existence
echo "  ── Key Output Files ──"
check_file() {
    local desc="$1" path="$2"
    if [ -f "$path" ]; then
        local sz=$(du -h "$path" | cut -f1)
        echo "  [EXISTS]  $desc ($sz) — $path"
    else
        echo "  [MISSING] $desc — $path"
    fi
}
check_file "Geometry Profile 001"   "geometry_outputs/GEOMETRY_PROFILE_001.json"
check_file "Lattice Profile 001"    "lattice_outputs/LATTICE_PROFILE_001.json"
check_file "STL Insole V1"          "stl_outputs/ZILFIT_INSOLE_V1.stl"
check_file "Shoe Architecture 001"  "shoe_outputs/SHOE_ARCH_001.json"
check_file "Runtime Output"         "$(ls -t runtime_outputs/ZILFIT_RUNTIME_*.json 2>/dev/null | head -1 || echo runtime_outputs/ZILFIT_RUNTIME_.json)"
echo ""

# 6. Python venvs
echo "  ── Python Virtual Environments ──"
for venv in .venv .venv-footai .venv-telegram; do
    if [ -d "$venv" ]; then
        sz=$(du -sh "$venv" 2>/dev/null | cut -f1)
        echo "  [EXISTS]  $venv ($sz)"
    else
        echo "  [MISSING] $venv"
    fi
done
echo ""

# Summary
echo "$DIV"
echo "  Health check complete."
echo "  $(date -u '+%Y-%m-%dT%H:%M:%SZ')"
echo "$DIV"

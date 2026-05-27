#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
cd "$REPO_ROOT"

# ---------------------------------------------------------------------------
# Defaults
# ---------------------------------------------------------------------------
VERSION="1.0.0"
WORKSPACE=""
OUTPUT_DIR="exports/releases"
CLEAN_WORKSPACE=""
ARGS=()

# ---------------------------------------------------------------------------
# Parse args
# ---------------------------------------------------------------------------
while [[ $# -gt 0 ]]; do
    case "$1" in
        -v|--version)
            VERSION="$2"
            shift 2
            ;;
        -d|--dry-run)
            DRY_RUN=1
            shift
            ;;
        -h|--help)
            echo "Usage: build_release.sh [-v VERSION] [-d|--dry-run]"
            echo ""
            echo "  -v, --version    Semantic version (default: 1.0.0)"
            echo "  -d, --dry-run    Validate only, do not create zip"
            exit 0
            ;;
        *)
            echo "Unknown option: $1"
            exit 1
            ;;
    esac
done

DRY_RUN="${DRY_RUN:-0}"

# Set up clean workspace and output dir
WORKSPACE="$(mktemp -d "/tmp/zilfit_release_XXXXXXX")"
trap 'rm -rf "$WORKSPACE"' EXIT

DATE_STR=$(date -u '+%Y%m%d')
ZIP_NAME="ZILFIT_v${VERSION}_${DATE_STR}.zip"
ZIP_BASENAME="${ZIP_NAME%.zip}"
RELEASE_DIR="$WORKSPACE/$ZIP_BASENAME"

REQUIRED_FOLDERS=(
    "agents"
    "config"
    "docs"
    "editions"
    "governance"
    "manufacturing"
    "parameters"
    "patent"
    "products"
    "prototype"
    "research"
    "rules"
    "runtime"
    "schemas"
    "scripts"
    "skills"
    "templates"
    "tests"
    "tools"
    "validators"
    "validation"
    "zilfit_orthotics"
)

REQUIRED_JSON_OUTPUTS=(
    "geometry_outputs/GEOMETRY_PROFILE_001.json"
    "lattice_outputs/LATTICE_PROFILE_001.json"
    "shoe_outputs/SHOE_ARCH_001.json"
)

EXCLUDE_PATTERNS=(
    ".git"
    ".venv*"
    "__pycache__"
    ".pytest_cache"
    "*_cache*"
    "node_modules"
    "exports/*.zip"
    "exports/releases"
    "production_inputs/batch"
    "production_inputs/scan_zip"
    "production_inputs/csv_results"
    ".DS_Store"
    "*.pyc"
    ".env"
    ".env.*"
    ".aider.*"
    ".hermes"
    ".worktrees"
    "_local_backups"
    "tmp"
    "logs"
    "*.log"
)

DIV="============================================================"
DIV2="------------------------------------------------------------"

# ---------------------------------------------------------------------------
# Validation
# ---------------------------------------------------------------------------
echo "$DIV"
echo "  ZILFIT Release Builder V1"
echo "  Version: $VERSION"
echo "  Date:    $(date -u '+%Y-%m-%dT%H:%M:%SZ')"
if [[ "$DRY_RUN" -eq 1 ]]; then
    echo "  Mode:    DRY RUN (validation only, no zip)"
fi
echo "$DIV"
echo ""

# Validate version format
if ! echo "$VERSION" | grep -qE '^[0-9]+\.[0-9]+\.[0-9]+$'; then
    echo "ERROR: Invalid version format. Expected MAJOR.MINOR.PATCH (e.g. 1.0.0)"
    exit 1
fi

echo "  ── Source Integrity ──"

# Check required folders
MISSING_DIRS=0
for dir in "${REQUIRED_FOLDERS[@]}"; do
    if [[ -d "$dir" ]]; then
        echo "  [DIR OK]  $dir"
    else
        echo "  [MISSING] $dir"
        ((MISSING_DIRS++))
    fi
done
echo ""

if [[ $MISSING_DIRS -gt 0 ]]; then
    echo "ERROR: $MISSING_DIRS required source directories missing."
    exit 1
fi

# Check key JSON outputs
JSON_FAIL=0
for f in "${REQUIRED_JSON_OUTPUTS[@]}"; do
    if [[ -f "$f" ]]; then
        if python3 -c "import json; json.load(open('$f'))" 2>/dev/null; then
            echo "  [JSON OK] $f"
        else
            echo "  [BROKEN]  $f (invalid JSON)"
            ((JSON_FAIL++))
        fi
    else
        echo "  [MISSING] $f"
        ((JSON_FAIL++))
    fi
done
echo ""

if [[ $JSON_FAIL -gt 0 ]]; then
    echo "ERROR: $JSON_FAIL required JSON files missing or invalid."
    exit 1
fi

# Python compile check
echo "  ── Python Compile Check ──"
COMPILE_OK=0
COMPILE_FAIL=0
while IFS= read -r -d '' pyfile; do
    if python3 -m py_compile "$pyfile" 2>/dev/null; then
        COMPILE_OK=$((COMPILE_OK + 1))
    else
        echo "  [FAIL] $pyfile"
        COMPILE_FAIL=$((COMPILE_FAIL + 1))
    fi
done < <(find "${REQUIRED_FOLDERS[@]}" -name '*.py' -print0 2>/dev/null || true)
echo "  Compiled: $COMPILE_OK OK, $COMPILE_FAIL FAIL"
echo ""

if [[ $COMPILE_FAIL -gt 0 ]]; then
    echo "WARNING: $COMPILE_FAIL Python files failed to compile."
fi

if [[ "$DRY_RUN" -eq 1 ]]; then
    echo "$DIV"
    echo "  Dry run complete. All validations passed."
    echo "$DIV"
    exit 0
fi

# ---------------------------------------------------------------------------
# Build release workspace
# ---------------------------------------------------------------------------
echo "$DIV"
echo "  Building release workspace..."
echo "$DIV"
echo ""

# Build rsync exclude flags
RSYNC_EXCLUDES=()
for pat in "${EXCLUDE_PATTERNS[@]}"; do
    RSYNC_EXCLUDES+=(--exclude="$pat")
done

mkdir -p "$RELEASE_DIR"

# Rsync all non-excluded content
rsync -a "${RSYNC_EXCLUDES[@]}" "$REPO_ROOT"/ "$RELEASE_DIR"/ 2>/dev/null || true

FILE_COUNT=$(find "$RELEASE_DIR" -type f | wc -l)
DIR_COUNT=$(find "$RELEASE_DIR" -type d | wc -l)
SIZE_TOTAL=$(du -sh "$RELEASE_DIR" | cut -f1)

echo "  Release workspace: $RELEASE_DIR"
echo "  Files: $FILE_COUNT"
echo "  Dirs:  $DIR_COUNT"
echo "  Size:  $SIZE_TOTAL"
echo ""

# ---------------------------------------------------------------------------
# RELEASE_MANIFEST.json
# ---------------------------------------------------------------------------
echo "  ── Generating RELEASE_MANIFEST.json ──"

MANIFEST_JSON="$RELEASE_DIR/RELEASE_MANIFEST.json"

# Build folder listing
FOLDER_LIST="["
first=1
for dir in "${REQUIRED_FOLDERS[@]}"; do
    if [[ -d "$RELEASE_DIR/$dir" ]]; then
        file_count=$(find "$RELEASE_DIR/$dir" -type f 2>/dev/null | wc -l)
        size=$(du -sh "$RELEASE_DIR/$dir" 2>/dev/null | cut -f1)
        if [[ $first -eq 1 ]]; then
            first=0
        else
            FOLDER_LIST+=","
        fi
        FOLDER_LIST+="{\"name\":\"$dir\",\"files\":$file_count,\"size\":\"$size\"}"
    fi
done
FOLDER_LIST+="]"

# Build exclude list
EXCLUDE_LIST="["
first=1
for pat in "${EXCLUDE_PATTERNS[@]}"; do
    if [[ $first -eq 1 ]]; then first=0; else EXCLUDE_LIST+=","; fi
    qpat=$(echo "$pat" | sed 's/"/\\"/g')
    EXCLUDE_LIST+="\"$qpat\""
done
EXCLUDE_LIST+="]"

python3 -c "
import json, os
m = {
    'release_name': '$ZIP_BASENAME',
    'version': '$VERSION',
    'build_date_utc': '$(date -u '+%Y-%m-%dT%H:%M:%SZ')',
    'built_from_branch': '$(git branch --show-current 2>/dev/null || echo unknown)',
    'built_from_commit': '$(git rev-parse HEAD 2>/dev/null || echo unknown)',
    'total_files': $FILE_COUNT,
    'total_dirs': $DIR_COUNT,
    'total_size': '$SIZE_TOTAL',
    'excluded_patterns': $EXCLUDE_LIST
}
with open('$MANIFEST_JSON', 'w') as f:
    json.dump(m, f, indent=2)
"
echo "  Done."
echo ""

# ---------------------------------------------------------------------------
# SHA256 checksums
# ---------------------------------------------------------------------------
echo "  ── Generating SHA256 checksums ──"

CHECKSUMS_FILE="$RELEASE_DIR/SHA256SUMS.txt"
cd "$RELEASE_DIR"
find . -type f -not -name "SHA256SUMS.txt" -print0 | sort -z | xargs -0 sha256sum > "$CHECKSUMS_FILE" 2>/dev/null || true
CHECKSUM_COUNT=$(wc -l < "$CHECKSUMS_FILE")
CHECKSUM_FILE=$(sha256sum "$CHECKSUMS_FILE" | awk '{print $1}')
cd "$REPO_ROOT"

echo "  $CHECKSUM_COUNT files hashed."
echo "  SHA256SUMS hash: $CHECKSUM_FILE"
echo ""

# ---------------------------------------------------------------------------
# RELEASE_INFO.md
# ---------------------------------------------------------------------------
echo "  ── Generating RELEASE_INFO.md ──"

cat > "$RELEASE_DIR/RELEASE_INFO.md" << MDEOF
# ZILFIT Release — v${VERSION}

- **Release package**: \`${ZIP_NAME}\`
- **Version**: ${VERSION}
- **Build date (UTC)**: $(date -u '+%Y-%m-%dT%H:%M:%SZ')
- **Built from branch**: $(git branch --show-current 2>/dev/null || echo unknown)
- **Built from commit**: $(git rev-parse HEAD 2>/dev/null || echo unknown)

## Contents

| Folder | Files | Size |
|--------|-------|------|
MDEOF

for dir in "${REQUIRED_FOLDERS[@]}"; do
    if [[ -d "$RELEASE_DIR/$dir" ]]; then
        fc=$(find "$RELEASE_DIR/$dir" -type f 2>/dev/null | wc -l)
        sz=$(du -sh "$RELEASE_DIR/$dir" 2>/dev/null | cut -f1)
        echo "| \`$dir\` | $fc | $sz |" >> "$RELEASE_DIR/RELEASE_INFO.md"
    fi
done

cat >> "$RELEASE_DIR/RELEASE_INFO.md" << MDEOF

## Excluded from release

\`.git\`, \`.venv*\`, \`__pycache__\`, \`.pytest_cache\`, \`node_modules\`,
\`exports/*.zip\`, \`production_inputs/batch\`, \`production_inputs/scan_zip\`,
env files, logs, temp files.

## Integrity verification

\`\`\`bash
sha256sum -c SHA256SUMS.txt
\`\`\`

## SHA256SUMS.txt hash

\`${CHECKSUM_FILE}\`
MDEOF

echo "  Done."
echo ""

# ---------------------------------------------------------------------------
# Package
# ---------------------------------------------------------------------------
echo "  ── Packaging ──"

mkdir -p "$REPO_ROOT/$OUTPUT_DIR"
ZIP_PATH="$REPO_ROOT/$OUTPUT_DIR/$ZIP_NAME"

cd "$WORKSPACE"
zip -qr "$ZIP_PATH" "$ZIP_BASENAME"
cd "$REPO_ROOT"

ZIP_SIZE=$(du -sh "$ZIP_PATH" | cut -f1)

echo "  Created: $ZIP_PATH"
echo "  Size:    $ZIP_SIZE"
echo ""

# ---------------------------------------------------------------------------
# Summary
# ---------------------------------------------------------------------------
echo "$DIV"
echo "  Release build complete!"
echo ""
echo "  Package: $ZIP_PATH"
echo "  Version: $VERSION"
echo "  Size:    $ZIP_SIZE"
echo "  Files:   $FILE_COUNT files in $DIR_COUNT directories"
echo ""
echo "  Artifacts inside zip:"
echo "    - RELEASE_MANIFEST.json  (build metadata)"
echo "    - RELEASE_INFO.md        (human-readable summary)"
echo "    - SHA256SUMS.txt         (integrity checksums)"
echo ""
echo "  To verify after extraction:"
echo "    sha256sum -c SHA256SUMS.txt"
echo "$DIV"

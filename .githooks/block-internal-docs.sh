#!/usr/bin/env bash
# Block commits/pushes containing internal documentation

set -euo pipefail

# Directories that should never be committed to the public repo
INTERNAL_PATHS=(
    "docs/internal/"
    "dev-docs/"
    "dev-docs/maintainers/"
    ".githooks/maintainer-forks.json"
    ".githooks/route-maintainer.sh"
    ".githooks/pre-commit-identity"
    ".githooks/block-internal-docs.sh"
    ".pre-commit-config.yaml"
)

# Get staged files
STAGED_FILES=$(git diff --cached --name-only --diff-filter=AM 2>/dev/null || true)

if [[ -z "$STAGED_FILES" ]]; then
    exit 0
fi

VIOLATIONS=()

for file in $STAGED_FILES; do
    for pattern in "${INTERNAL_PATHS[@]}"; do
        if [[ "$file" == "$pattern"* ]]; then
            VIOLATIONS+=("$file (matches internal pattern: $pattern)")
        fi
    done
done

if [[ ${#VIOLATIONS[@]} -gt 0 ]]; then
    echo "ERROR: Commit contains internal files that must not be pushed to public repo:" >&2
    for v in "${VIOLATIONS[@]}"; do
        echo "  - $v" >&2
    done
    echo "" >&2
    echo "These files contain maintainer routing logic, internal briefs, and internal docs." >&2
    echo "Unstage them with: git reset HEAD <file>" >&2
    exit 1
fi

exit 0
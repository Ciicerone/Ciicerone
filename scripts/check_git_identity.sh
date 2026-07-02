#!/usr/bin/env bash
#
# check_git_identity.sh — Verify the active GitHub account matches the
# global git config before allowing a commit.
#
# This script enforces that commits are attributed to the correct
# maintainer by comparing:
#   1. The active `gh auth` account
#   2. `git config --global user.name`
#   3. `git config --global user.email`
#
# Usage: run as a pre-commit hook (wired in .pre-commit-config.yaml)
# Exit 0 = aligned, exit 1 = misaligned (blocks the commit).

set -eo pipefail

# ---------------------------------------------------------------------------
# Known maintainer identities — GitHub username → (Git name, Git email)
#
# Uses a case statement instead of associative arrays so the script works
# on macOS's default bash 3.2 as well as bash 4+/5+.
# ---------------------------------------------------------------------------
get_expected_name() {
    case "$1" in
        Ciicerone)   echo "Ciicerone Admin" ;;
        laradipupo)  echo "Omolara Oladipupo" ;;
        jiboo2022)   echo "Ajibola Shokunbi" ;;
        TemidayoA)   echo "Temidayo Akinwale" ;;
        ocheme1107)  echo "David Ocheme" ;;
        Shizoqua)    echo "Lanre Shittu" ;;
        okino007)    echo "Jeremiah Okino" ;;
        *)           echo "" ;;
    esac
}

get_expected_email() {
    case "$1" in
        Ciicerone)   echo "admin@ciicerone.com" ;;
        laradipupo)  echo "laradipupo@users.noreply.github.com" ;;
        jiboo2022)   echo "jiboo2022@users.noreply.github.com" ;;
        TemidayoA)   echo "TemidayoA@users.noreply.github.com" ;;
        ocheme1107)  echo "ocheme1107@users.noreply.github.com" ;;
        Shizoqua)    echo "Shizoqua@users.noreply.github.com" ;;
        okino007)    echo "okino007@users.noreply.github.com" ;;
        *)           echo "" ;;
    esac
}

# ---------------------------------------------------------------------------
# Get the active GitHub account
# ---------------------------------------------------------------------------
ACTIVE_ACCOUNT=""
GH_BIN=""
if command -v gh &>/dev/null; then
    GH_BIN="gh"
elif [[ -x /opt/homebrew/bin/gh ]]; then
    GH_BIN="/opt/homebrew/bin/gh"
elif [[ -x /usr/local/bin/gh ]]; then
    GH_BIN="/usr/local/bin/gh"
fi
if [[ -n "$GH_BIN" ]]; then
    # Extract the account marked "Active account: true"
    ACTIVE_ACCOUNT=$("$GH_BIN" auth status 2>&1 | grep -B1 "Active account: true" | grep "Logged in" | sed 's/.*account \([^ ]*\) .*/\1/' || true)
fi

if [[ -z "$ACTIVE_ACCOUNT" ]]; then
    echo "ERROR: Could not determine active GitHub account. Is 'gh' installed and authenticated?" >&2
    exit 1
fi

# ---------------------------------------------------------------------------
# Get global git config
# ---------------------------------------------------------------------------
GIT_USER_NAME=$(git config --global user.name 2>/dev/null || echo "")
GIT_USER_EMAIL=$(git config --global user.email 2>/dev/null || echo "")

if [[ -z "$GIT_USER_NAME" || -z "$GIT_USER_EMAIL" ]]; then
    echo "ERROR: git config --global user.name or user.email is not set." >&2
    exit 1
fi

# ---------------------------------------------------------------------------
# Compare
# ---------------------------------------------------------------------------
ERRORS=()

EXPECTED_NAME=$(get_expected_name "$ACTIVE_ACCOUNT")
EXPECTED_EMAIL=$(get_expected_email "$ACTIVE_ACCOUNT")

if [[ -z "$EXPECTED_NAME" || -z "$EXPECTED_EMAIL" ]]; then
    echo "WARNING: Active GitHub account '$ACTIVE_ACCOUNT' is not in the known maintainer list." >&2
    echo "         If this is a new maintainer, add them to scripts/check_git_identity.sh." >&2
    # Don't block — just warn for unknown accounts
    exit 0
fi

if [[ "$GIT_USER_NAME" != "$EXPECTED_NAME" ]]; then
    ERRORS+=("git config user.name is '$GIT_USER_NAME' but expected '$EXPECTED_NAME' for account '$ACTIVE_ACCOUNT'")
fi

if [[ "$GIT_USER_EMAIL" != "$EXPECTED_EMAIL" ]]; then
    ERRORS+=("git config user.email is '$GIT_USER_EMAIL' but expected '$EXPECTED_EMAIL' for account '$ACTIVE_ACCOUNT'")
fi

if [[ ${#ERRORS[@]} -gt 0 ]]; then
    echo "========================================" >&2
    echo "ERROR: Git identity misalignment detected!" >&2
    echo "========================================" >&2
    echo "" >&2
    echo "Active GitHub account : $ACTIVE_ACCOUNT" >&2
    echo "git user.name         : $GIT_USER_NAME" >&2
    echo "git user.email        : $GIT_USER_EMAIL" >&2
    echo "" >&2
    echo "Expected:" >&2
    echo "  user.name  : $EXPECTED_NAME" >&2
    echo "  user.email : $EXPECTED_EMAIL" >&2
    echo "" >&2
    echo "To fix, run:" >&2
    echo "  git config --global user.name  \"$EXPECTED_NAME\"" >&2
    echo "  git config --global user.email \"$EXPECTED_EMAIL\"" >&2
    echo "" >&2
    for err in "${ERRORS[@]}"; do
        echo "  - $err" >&2
    done
    echo "" >&2
    echo "Commit BLOCKED. Fix your git config and try again." >&2
    exit 1
fi

echo "OK: Git identity aligned (account=$ACTIVE_ACCOUNT, name=$GIT_USER_NAME, email=$GIT_USER_EMAIL)"
exit 0

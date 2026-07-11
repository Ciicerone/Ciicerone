#!/usr/bin/env bash
# Maintainer routing script - validates identity and routes to appropriate fork

set -euo pipefail

REPO_ROOT="$(git rev-parse --show-toplevel)"
CODEOWNERS_FILE="${REPO_ROOT}/.github/CODEOWNERS"

declare -A MAINTAINER_EMAILS
declare -A MAINTAINER_CODES
declare -A MAINTAINER_PATHS
declare -A MAINTAINER_FORKS

init_maintainers() {
    MAINTAINER_CODES["@Thundastormgod"]="TSG-OWNER"
    MAINTAINER_CODES["@laradipupo"]="TSG-DEV"
    MAINTAINER_CODES["@noblenabeela360"]="TSG-RED"
    MAINTAINER_CODES["@bayulus4great"]="TSG-RED"
    MAINTAINER_CODES["@onojad"]="TSG-BLUE"
    MAINTAINER_CODES["@ajiboyshokunbi"]="TSG-DEV"
    MAINTAINER_CODES["@hrlanreshittu"]="TSG-ML"
    MAINTAINER_CODES["@Okino007"]="TSG-COMP"

    MAINTAINER_EMAILS["@Thundastormgod"]="ciicerone@ciicerone.com 73486309+Thundastormgod@users.noreply.github.com"
    MAINTAINER_EMAILS["@laradipupo"]="ajiboyshokunbi@yahoo.com"
    MAINTAINER_EMAILS["@noblenabeela360"]="noblenabeela360@gmail.com"
    MAINTAINER_EMAILS["@bayulus4great"]="bayulus4great@gmail.com"
    MAINTAINER_EMAILS["@onojad"]="onojad@gmail.com"
    MAINTAINER_EMAILS["@ajiboyshokunbi"]="ajiboyshokunbi@yahoo.com"
    MAINTAINER_EMAILS["@hrlanreshittu"]="hr.lanreshittu@yahoo.com"
    MAINTAINER_EMAILS["@Okino007"]="okino007@gmail.com"

    MAINTAINER_FORKS["@Thundastormgod"]="https://github.com/Thundastormgod/Ciicerone"
    MAINTAINER_FORKS["@laradipupo"]="https://github.com/laradipupo/Ciicerone"
    MAINTAINER_FORKS["@noblenabeela360"]="https://github.com/noblenabeela360/Ciicerone"
    MAINTAINER_FORKS["@bayulus4great"]="https://github.com/bayulus4great/Ciicerone"
    MAINTAINER_FORKS["@onojad"]="https://github.com/onojad/Ciicerone"
    MAINTAINER_FORKS["@ajiboyshokunbi"]="https://github.com/ajiboyshokunbi/Ciicerone"
    MAINTAINER_FORKS["@hrlanreshittu"]="https://github.com/hrlanreshittu/Ciicerone"
    MAINTAINER_FORKS["@Okino007"]="https://github.com/Okino007/Ciicerone"
}

parse_codeowners() {
    [[ -f "$CODEOWNERS_FILE" ]] || return 1

    while IFS= read -r line; do
        [[ "$line" =~ ^# ]] && continue
        [[ -z "${line// }" ]] && continue

        path="${line%% *}"
        owners="${line#* }"

        for owner in $owners; do
            [[ "$owner" =~ ^@ ]] || continue
            MAINTAINER_PATHS["$owner"]+="${path} "
        done
    done < "$CODEOWNERS_FILE"
}

get_git_identity() {
    local email name
    email=$(git config user.email 2>/dev/null || git config --global user.email 2>/dev/null || echo "")
    name=$(git config user.name 2>/dev/null || git config --global user.name 2>/dev/null || echo "")
    echo "${email}|${name}"
}

get_active_gh_account() {
    if command -v gh >/dev/null 2>&1; then
        gh auth status 2>&1 | grep -E "Logged in to github.com" | head -1 | awk '{for(i=1;i<=NF;i++) if($i=="account") {print $(i+1); exit}}'
    else
        echo ""
    fi
}

match_maintainer_by_email() {
    local email="$1"
    for maintainer in "${!MAINTAINER_EMAILS[@]}"; do
        local maintainer_emails="${MAINTAINER_EMAILS[$maintainer]}"
        for maintainer_email in $maintainer_emails; do
            if [[ -n "$maintainer_email" && "$email" == *"$maintainer_email"* ]]; then
                echo "$maintainer"
                return 0
            fi
        done
    done
    return 1
}

get_changed_files() {
    git diff --cached --name-only --diff-filter=AM 2>/dev/null || true
}

match_maintainer_by_files() {
    local files=("$@")
    for file in "${files[@]}"; do
        for maintainer in "${!MAINTAINER_PATHS[@]}"; do
            local paths="${MAINTAINER_PATHS[$maintainer]}"
            for path in $paths; do
                if [[ "$file" == "$path"* ]] || [[ "$path" == "*" ]]; then
                    echo "$maintainer"
                    return 0
                fi
            done
        done
    done
    echo "@Thundastormgod"
}

check_identity() {
    init_maintainers
    parse_codeowners

    local identity
    identity=$(get_git_identity)
    local email="${identity%%|*}"
    local name="${identity#*|}"

    echo "Git Identity:"
    echo "  Name:  $name"
    echo "  Email: $email"
    echo ""

    if [[ -z "$email" || -z "$name" ]]; then
        echo "ERROR: Git identity not configured." >&2
        echo "  Set local:  git config user.email \"you@example.com\" && git config user.name \"Your Name\"" >&2
        echo "  Set global: git config --global user.email \"you@example.com\" && git config --global user.name \"Your Name\"" >&2
        return 1
    fi

    local matched_maintainer
    matched_maintainer=$(match_maintainer_by_email "$email") || true

    if [[ -z "$matched_maintainer" ]]; then
        echo "ERROR: Email '$email' does not match any known maintainer." >&2
        echo "Known maintainer emails:" >&2
        for m in "${!MAINTAINER_EMAILS[@]}"; do
            echo "  $m -> ${MAINTAINER_EMAILS[$m]:-(no email configured)}" >&2
        done
        return 1
    fi

    # Validate local user.name matches current logged in GitHub account
    local gh_account
    gh_account=$(get_active_gh_account)
    if [[ -n "$gh_account" && "$name" != "$gh_account" ]]; then
        echo "ERROR: Git user.name '$name' does not match current logged in GitHub account '$gh_account'." >&2
        echo "Align local author with global (gh) credentials:" >&2
        echo "  git config user.name \"$gh_account\"" >&2
        local expected_email="${MAINTAINER_EMAILS["@$gh_account"]:-}"
        if [[ -n "$expected_email" ]]; then
            echo "  git config user.email \"$expected_email\"" >&2
        fi
        return 1
    fi

    local files=()
    mapfile -t files < <(get_changed_files)
    local file_maintainer
    file_maintainer=$(match_maintainer_by_files "${files[@]}")

    echo "Validated maintainer: $matched_maintainer (${MAINTAINER_CODES[$matched_maintainer]})"
    if [[ ${#files[@]} -gt 0 ]]; then
        echo "Files changed:"
        for f in "${files[@]}"; do echo "  $f"; done
        echo "File maintainer: $file_maintainer (${MAINTAINER_CODES[$file_maintainer]})"
    fi

    local fork_url="${MAINTAINER_FORKS[$matched_maintainer]:-}"
    if [[ -n "$fork_url" ]]; then
        echo "Target fork: $fork_url"
    fi

    return 0
}

route_pr() {
    init_maintainers
    parse_codeowners

    local identity
    identity=$(get_git_identity)
    local email="${identity%%|*}"
    local name="${identity#*|}"
    local matched_maintainer
    matched_maintainer=$(match_maintainer_by_email "$email") || true

    if [[ -z "$matched_maintainer" ]]; then
        matched_maintainer="@Thundastormgod"
    fi

    local files=()
    mapfile -t files < <(get_changed_files "main")

    local file_maintainer
    file_maintainer=$(match_maintainer_by_files "${files[@]}")

    local fork_url="${MAINTAINER_FORKS[$matched_maintainer]:-}"

    cat <<EOF
=== PR Routing Information ===
Author: $name <$email>
Author maintainer: $matched_maintainer (${MAINTAINER_CODES[$matched_maintainer]:-UNKNOWN})
Files changed: ${#files[@]}
File maintainer: $file_maintainer (${MAINTAINER_CODES[$file_maintainer]:-UNKNOWN})
Target fork: ${fork_url:-origin}

Suggested PR commands:
  gh pr create --base main --head $(git rev-parse --abbrev-ref HEAD) --repo ${fork_url:-origin}
  Reviewers: $matched_maintainer $file_maintainer
EOF
}

main() {
    case "${1:-check-identity}" in
        check-identity)
            check_identity
            ;;
        route-pr)
            route_pr
            ;;
        *)
            echo "Usage: $0 {check-identity|route-pr}" >&2
            exit 1
            ;;
    esac
}

main "$@"

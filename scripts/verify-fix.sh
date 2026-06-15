#!/bin/bash
set -euo pipefail

# verify-fix.sh — Re-scan when issues are closed to verify remediation
# Context: Triggered when a scan-related GitLab Issue is closed; re-runs relevant scanner

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
WORKSPACE="${WORKSPACE:-$(pwd)}"
GITLAB_HOST_URL="${GITLAB_HOST_URL:-http://gitlab:80}"
GITLAB_API_TOKEN="${GITLAB_API_TOKEN:-}"
GITLAB_PROJECT_ID="${CI_PROJECT_ID:-}"
ISSUE_IID="${ISSUE_IID:-}"

log() { echo "[VERIFY-FIX] $(date '+%H:%M:%S') $*"; }

gitlab_api() {
    local method="$1" path="$2" data="${3:-}"
    local url="${GITLAB_HOST_URL}/api/v4${path}"
    if [[ -n "$data" ]]; then
        curl -s -X "$method" "$url" \
            -H "PRIVATE-TOKEN: $GITLAB_API_TOKEN" \
            -H "Content-Type: application/json" \
            -d "$data"
    else
        curl -s -X "$method" "$url" -H "PRIVATE-TOKEN: $GITLAB_API_TOKEN"
    fi
}

get_issue_info() {
    gitlab_api "GET" "/projects/$GITLAB_PROJECT_ID/issues/$ISSUE_IID"
}

determine_scan_type() {
    local labels="$1"
    if echo "$labels" | grep -q "sonarqube"; then
        echo "sonarqube"
    elif echo "$labels" | grep -q "polyspace"; then
        echo "polyspace"
    else
        echo "unknown"
    fi
}

add_issue_note() {
    local issue_iid="$1" note="$2"
    gitlab_api "POST" "/projects/$GITLAB_PROJECT_ID/issues/$issue_iid/notes" \
        "$(jq -n --arg body "$note" '{body: $body}')"
}

close_issue_if_fixed() {
    local issue_iid="$1" scan_type="$2"

    case "$scan_type" in
        sonarqube)
            local new_count
            new_count=$(jq '.issues | length' "$WORKSPACE/scan-reports/sonarqube-issues-new.json" 2>/dev/null || echo "0")
            if [[ "$new_count" -eq 0 ]]; then
                add_issue_note "$issue_iid" "✅ 修复验证通过：重新扫描未发现此问题。Issue 将自动关闭。"
                gitlab_api "PUT" "/projects/$GITLAB_PROJECT_ID/issues/$issue_iid" \
                    '{"state_event": "close"}'
                log "Issue #$issue_iid auto-closed — fix verified"
            else
                add_issue_note "$issue_iid" "⚠️ 修复验证未通过：重新扫描仍发现 $new_count 个相关问题。请继续修复。"
                log "Issue #$issue_iid remains open — issues still present"
            fi
            ;;
        polyspace)
            local ps_total
            ps_total=$(jq -r '.total_issues // 0' "$WORKSPACE/scan-reports/polyspace/polyspace-summary.json" 2>/dev/null)
            if [[ "$ps_total" -eq 0 ]]; then
                add_issue_note "$issue_iid" "✅ 修复验证通过：Polyspace 重新验证未发现缺陷。Issue 将自动关闭。"
                gitlab_api "PUT" "/projects/$GITLAB_PROJECT_ID/issues/$issue_iid" \
                    '{"state_event": "close"}'
                log "Issue #$issue_iid auto-closed — Polyspace fix verified"
            else
                add_issue_note "$issue_iid" "⚠️ 修复验证未通过：Polyspace 仍检测到 $ps_total 个问题。请继续修复。"
                log "Issue #$issue_iid remains open — $ps_total Polyspace issues still present"
            fi
            ;;
    esac
}

trigger_rebuild() {
    log "Triggering rebuild for verification..."
    git checkout "${CI_COMMIT_BRANCH:-main}"
    git pull origin "${CI_COMMIT_BRANCH:-main}"

    "$SCRIPT_DIR/build-ide.sh"
}

main() {
    log "Starting fix verification for Issue #${ISSUE_IID:-unknown}"

    if [[ -z "$ISSUE_IID" || -z "$GITLAB_PROJECT_ID" || -z "$GITLAB_API_TOKEN" ]]; then
        log "ERROR: Missing required environment variables (ISSUE_IID, GITLAB_PROJECT_ID, GITLAB_API_TOKEN)"
        exit 1
    fi

    local issue_info
    issue_info=$(get_issue_info)
    local labels state
    labels=$(echo "$issue_info" | jq -r '.labels[]?' | tr '\n' ' ')
    state=$(echo "$issue_info" | jq -r '.state')

    if [[ "$state" != "closed" ]]; then
        log "Issue #$ISSUE_IID is not closed (state: $state), skipping verification"
        exit 0
    fi

    local scan_type
    scan_type=$(determine_scan_type "$labels")
    log "Issue #$ISSUE_IID type: $scan_type"

    if [[ "$scan_type" == "unknown" ]]; then
        log "Not a scan issue, skipping verification"
        exit 0
    fi

    trigger_rebuild

    case "$scan_type" in
        sonarqube)
            "$SCRIPT_DIR/sonar-scanner.sh"
            close_issue_if_fixed "$ISSUE_IID" "sonarqube"
            ;;
        polyspace)
            "$SCRIPT_DIR/polyspace-scanner.sh"
            close_issue_if_fixed "$ISSUE_IID" "polyspace"
            ;;
    esac

    log "Fix verification complete for Issue #$ISSUE_IID"
}

main "$@"

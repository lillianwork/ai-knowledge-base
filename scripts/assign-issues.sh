#!/bin/bash
set -euo pipefail

# assign-issues.sh — Auto-create GitLab Issues from scan results and assign to committers
# Context: Runs after SonarQube + Polyspace scans; uses git blame to find responsible developers

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
WORKSPACE="${WORKSPACE:-$(pwd)}"
GITLAB_HOST_URL="${GITLAB_HOST_URL:-http://gitlab:80}"
GITLAB_API_TOKEN="${GITLAB_API_TOKEN:-}"
GITLAB_PROJECT_ID="${CI_PROJECT_ID:-}"
RESULTS_DIR="${RESULTS_DIR:-$WORKSPACE/scan-reports}"
ISSUE_TRACKING_DIR="${ISSUE_TRACKING_DIR:-$WORKSPACE/scan-issues}"

log() { echo "[ISSUE-ASSIGN] $(date '+%H:%M:%S') $*"; }

gitlab_api() {
    local method="$1" path="$2" data="${3:-}"
    local url="${GITLAB_HOST_URL}/api/v4${path}"

    if [[ -n "$data" ]]; then
        curl -s -X "$method" "$url" \
            -H "PRIVATE-TOKEN: $GITLAB_API_TOKEN" \
            -H "Content-Type: application/json" \
            -d "$data"
    else
        curl -s -X "$method" "$url" \
            -H "PRIVATE-TOKEN: $GITLAB_API_TOKEN"
    fi
}

find_author_for_file_line() {
    local file="$1" line="$2"
    cd "$WORKSPACE"
    git blame -L "$line,$line" --line-porcelain "$file" 2>/dev/null | \
        grep '^author-mail ' | head -1 | sed 's/^author-mail <//;s/>$//'
}

find_gitlab_user_id() {
    local email="$1"
    local response
    response=$(gitlab_api "GET" "/users?search=${email}" 2>/dev/null)
    echo "$response" | jq -r '.[0].id // empty'
}

resolve_assignee() {
    local file="$1" line="$2" author="${3:-}"

    if [[ -n "$author" ]]; then
        echo "$author"
    elif [[ "$line" != "N/A" && "$line" != "null" ]]; then
        find_author_for_file_line "$file" "$line"
    else
        git log -1 --format='%ae' 2>/dev/null || echo "unknown"
    fi
}

render_template() {
    local template="$SCRIPT_DIR/../templates/issue-scan.md"
    local title="$1" tool="$2" severity="$3" file="$4" line="$5"
    local message="$6" rule="$7" remediation="$8" assignee="$9"

    sed -e "s|{ISSUE_TITLE}|$title|g" \
        -e "s|{SCAN_TOOL}|$tool|g" \
        -e "s|{SCAN_TIMESTAMP}|$(date -u +%Y-%m-%dT%H:%M:%SZ)|g" \
        -e "s|{PIPELINE_NAME}|${CI_PIPELINE_ID:-local}|g" \
        -e "s|{PIPELINE_URL}|${CI_PIPELINE_URL:-#}|g" \
        -e "s|{COMMIT_SHORT_SHA}|$(git rev-parse --short HEAD 2>/dev/null || echo 'HEAD')|g" \
        -e "s|{COMMIT_URL}|${CI_COMMIT_URL:-#}|g" \
        -e "s|{SEVERITY}|$severity|g" \
        -e "s|{ISSUE_TYPE}|$rule|g" \
        -e "s|{FILE_PATH}|$file|g" \
        -e "s|{LINE_NUMBER}|$line|g" \
        -e "s|{RULE_ID}|$rule|g" \
        -e "s|{RULE_DESCRIPTION}|$rule|g" \
        -e "s|{ISSUE_MESSAGE}|$message|g" \
        -e "s|{REMEDIATION_ADVICE}|$remediation|g" \
        -e "s|{LANGUAGE}|cpp|g" \
        -e "s|{CODE_SNIPPET}|N/A|g" \
        -e "s|{ASSIGNEE}|$assignee|g" \
        -e "s|{SOURCE_BRANCH}|${CI_COMMIT_BRANCH:-$(git rev-parse --abbrev-ref HEAD)}|g" \
        -e "s|{ESTIMATED_EFFORT}|待评估|g" \
        "$template"
}

create_gitlab_issue() {
    local title="$1" description="$2" assignee_email="$3" labels="${4:-scan-issue}"

    local assignee_id
    assignee_id=$(find_gitlab_user_id "$assignee_email")

    local payload
    payload=$(jq -n \
        --arg title "$title" \
        --arg desc "$description" \
        --arg labels "$labels" \
        --argjson assignee "${assignee_id:-null}" \
        '{title: $title, description: $desc, labels: $labels, assignee_id: $assignee}')

    local response
    response=$(gitlab_api "POST" "/projects/$GITLAB_PROJECT_ID/issues" "$payload")
    local issue_iid
    issue_iid=$(echo "$response" | jq -r '.iid // empty')

    if [[ -n "$issue_iid" ]]; then
        log "Created GitLab Issue #$issue_iid — $title (assignee: $assignee_email)"
        echo "$issue_iid"
    else
        log "ERROR: Failed to create issue: $(echo "$response" | jq -r '.message // "unknown error"')"
        echo ""
    fi
}

process_sonarqube_issues() {
    log "Processing SonarQube issues..."
    local issues_file="$RESULTS_DIR/sonarqube-issues.json"

    if [[ ! -f "$issues_file" ]]; then
        log "No SonarQube issues file found, skipping"
        return
    fi

    local issue_count
    issue_count=$(jq '.issues | length' "$issues_file" 2>/dev/null || echo "0")
    log "Processing $issue_count SonarQube issues"

    mkdir -p "$ISSUE_TRACKING_DIR"
    local created=0 skipped=0

    jq -c '.issues[]' "$issues_file" 2>/dev/null | while read -r issue; do
        local key severity itype component line message rule
        key=$(echo "$issue" | jq -r '.key')
        severity=$(echo "$issue" | jq -r '.severity')
        itype=$(echo "$issue" | jq -r '.type')
        component=$(echo "$issue" | jq -r '.component')
        line=$(echo "$issue" | jq -r '.line // "N/A"')
        message=$(echo "$issue" | jq -r '.message')
        rule=$(echo "$issue" | jq -r '.rule')

        local author
        author=$(resolve_assignee "$component" "$line" "")

        local title="[SonarQube][${severity}] ${component}: ${message:0:80}"
        local desc
        desc=$(render_template "$title" "SonarQube" "$severity" "$component" "$line" \
            "$message" "$rule" "请参考 SonarQube 规则说明进行修复" "$author")

        local issue_id
        issue_id=$(create_gitlab_issue "$title" "$desc" "$author" "scan-issue,sonarqube,$severity")

        if [[ -n "$issue_id" ]]; then
            echo "$issue_id" >> "$ISSUE_TRACKING_DIR/sonarqube-created-issues.txt"
            created=$((created + 1))
        else
            skipped=$((skipped + 1))
        fi
    done
    log "SonarQube issues: $created created, $skipped skipped"
}

process_polyspace_issues() {
    log "Processing Polyspace issues..."
    local ps_summary="$RESULTS_DIR/polyspace/polyspace-summary.json"

    if [[ ! -f "$ps_summary" ]]; then
        log "No Polyspace summary found, skipping"
        return
    fi

    local total
    total=$(jq -r '.total_issues // 0' "$ps_summary")
    log "Processing $total Polyspace issues"

    local author
    author=$(git log -1 --format='%ae' 2>/dev/null || echo "${GITLAB_USER_EMAIL:-unknown}")

    if [[ "$total" -gt 0 ]]; then
        local title="[Polyspace] $total 个问题待修复"
        local desc
        desc=$(render_template "$title" "Polyspace" "MAJOR" "N/A" "N/A" \
            "Polyspace 扫描发现 $total 个问题，详见扫描报告" "MISRA/CodeProver" \
            "请查看 Polyspace Dashboard 或扫描报告进行修复" "$author")

        local issue_id
        issue_id=$(create_gitlab_issue "$title" "$desc" "$author" "scan-issue,polyspace")
        if [[ -n "$issue_id" ]]; then
            echo "$issue_id" >> "$ISSUE_TRACKING_DIR/polyspace-created-issues.txt"
        fi
    fi
}

generate_tracking_report() {
    log "Generating issue tracking report..."
    mkdir -p "$ISSUE_TRACKING_DIR"

    tee "$ISSUE_TRACKING_DIR/tracking-report.json" <<EOF
{
  "pipeline_id": "${CI_PIPELINE_ID:-local}",
  "commit": "$(git rev-parse HEAD 2>/dev/null || echo 'unknown')",
  "timestamp": "$(date -u +%Y-%m-%dT%H:%M:%SZ)",
  "sonarqube_issues": $(cat "$ISSUE_TRACKING_DIR/sonarqube-created-issues.txt" 2>/dev/null | wc -l || echo 0),
  "polyspace_issues": $(cat "$ISSUE_TRACKING_DIR/polyspace-created-issues.txt" 2>/dev/null | wc -l || echo 0),
  "total_created": $(cat "$ISSUE_TRACKING_DIR"/*-created-issues.txt 2>/dev/null | wc -l || echo 0)
}
EOF
}

main() {
    log "Starting automated issue assignment"

    if [[ -z "$GITLAB_API_TOKEN" ]]; then
        log "ERROR: GITLAB_API_TOKEN not set. Cannot create GitLab Issues."
        exit 1
    fi
    if [[ -z "$GITLAB_PROJECT_ID" ]]; then
        log "ERROR: GITLAB_PROJECT_ID not set."
        exit 1
    fi

    process_sonarqube_issues
    process_polyspace_issues
    generate_tracking_report

    log "Issue assignment complete"
}

main "$@"

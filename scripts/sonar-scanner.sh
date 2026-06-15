#!/bin/bash
set -euo pipefail

# sonar-scanner.sh — Execute SonarQube analysis and parse results
# Context: Runs after build-ide.sh; requires compile_commands.json from build-wrapper

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
WORKSPACE="${WORKSPACE:-$(pwd)}"
SONAR_HOST_URL="${SONAR_HOST_URL:-http://sonarqube:9000}"
SONAR_TOKEN="${SONAR_TOKEN:-}"
SONAR_SCANNER_HOME="${SONAR_SCANNER_HOME:-/opt/sonar-scanner}"
BUILD_WRAPPER_OUTPUT="${BUILD_WRAPPER_OUTPUT:-bw-output}"
RESULTS_DIR="${RESULTS_DIR:-$WORKSPACE/scan-reports}"
PROJECT_KEY="${SONAR_PROJECT_KEY:-${CI_PROJECT_NAMESPACE}_${CI_PROJECT_NAME}}"

log() { echo "[SONARQUBE] $(date '+%H:%M:%S') $*"; }

validate_prerequisites() {
    if [[ ! -f "$BUILD_WRAPPER_OUTPUT/compile_commands.json" ]]; then
        log "ERROR: compile_commands.json not found at $BUILD_WRAPPER_OUTPUT/"
        log "Make sure build-ide.sh ran with build-wrapper before this stage."
        exit 1
    fi
}

run_sonar_scanner() {
    mkdir -p "$RESULTS_DIR"

    local scanner_cli="$SONAR_SCANNER_HOME/bin/sonar-scanner"
    local sonar_props="$WORKSPACE/config/sonar-project.properties"

    if [[ -x "$scanner_cli" ]]; then
        log "Running SonarQube scanner..."
        "$scanner_cli" \
            -Dsonar.host.url="$SONAR_HOST_URL" \
            -Dsonar.token="$SONAR_TOKEN" \
            -Dsonar.projectKey="$PROJECT_KEY" \
            -Dsonar.cfamily.compile-commands="$BUILD_WRAPPER_OUTPUT/compile_commands.json" \
            -Dsonar.cfamily.build-wrapper-output="$BUILD_WRAPPER_OUTPUT" \
            -Dsonar.qualitygate.wait=true \
            -Dsonar.qualitygate.timeout=600 \
            -Dproject.settings="$sonar_props" \
            2>&1 | tee "$RESULTS_DIR/sonarqube-scan.log"
        return ${PIPESTATUS[0]}
    else
        log "WARNING: sonar-scanner not installed at $scanner_cli"
        log "Using sonar-scanner via Docker..."
        docker run --rm \
            --network cicd-network \
            -v "$WORKSPACE:/usr/src" \
            -w /usr/src \
            -e SONAR_HOST_URL="$SONAR_HOST_URL" \
            -e SONAR_TOKEN="$SONAR_TOKEN" \
            sonarsource/sonar-scanner-cli:latest \
            sonar-scanner \
            -Dsonar.host.url="$SONAR_HOST_URL" \
            -Dsonar.token="$SONAR_TOKEN" \
            -Dsonar.projectKey="$PROJECT_KEY" \
            -Dsonar.cfamily.compile-commands="$BUILD_WRAPPER_OUTPUT/compile_commands.json" \
            2>&1 | tee "$RESULTS_DIR/sonarqube-scan.log"
        return ${PIPESTATUS[0]}
    fi
}

fetch_issues() {
    log "Fetching SonarQube issues for project $PROJECT_KEY..."

    local api_url="$SONAR_HOST_URL/api/issues/search"
    local response
    response=$(curl -s -u "$SONAR_TOKEN:" \
        "$api_url?projectKeys=$PROJECT_KEY&statuses=OPEN&ps=500" \
        -o "$RESULTS_DIR/sonarqube-issues.json" -w "%{http_code}")

    if [[ "$response" == "200" ]]; then
        local issue_count
        issue_count=$(jq '.issues | length' "$RESULTS_DIR/sonarqube-issues.json" 2>/dev/null || echo "0")
        log "Found $issue_count open issues"
        echo "$issue_count"
    else
        log "ERROR: Failed to fetch issues (HTTP $response)"
        echo "0"
    fi
}

fetch_quality_gate_status() {
    log "Checking quality gate status..."

    local api_url="$SONAR_HOST_URL/api/qualitygates/project_status"
    local status
    status=$(curl -s -u "$SONAR_TOKEN:" \
        "$api_url?projectKey=$PROJECT_KEY" | \
        jq -r '.projectStatus.status // "ERROR"')

    log "Quality gate status: $status"
    echo "$status"
}

extract_issues_by_author() {
    local author_email="${1:-unknown}"
    log "Extracting issues for author: $author_email"

    jq -r --arg email "$author_email" '
        .issues[] |
        select(.author == $email or .assignee == $email) |
        {
            key: .key,
            rule: .rule,
            severity: .severity,
            type: .type,
            component: .component,
            line: (.line // "N/A"),
            message: .message,
            debt: (.debt // "N/A")
        } | @json
    ' "$RESULTS_DIR/sonarqube-issues.json" 2>/dev/null > "$RESULTS_DIR/issues-by-author.jsonl"
}

main() {
    log "Starting SonarQube analysis for $PROJECT_KEY"
    validate_prerequisites
    local scan_exit_code
    run_sonar_scanner
    scan_exit_code=$?

    local issue_count
    issue_count=$(fetch_issues)

    local gate_status
    gate_status=$(fetch_quality_gate_status)

    if [[ "$issue_count" -gt 0 ]]; then
        local committer_email
        committer_email=$(git log -1 --format='%ae' 2>/dev/null || echo "${GITLAB_USER_EMAIL:-unknown}")
        extract_issues_by_author "$committer_email"
    fi

    echo "SONAR_ISSUE_COUNT=$issue_count" > "$RESULTS_DIR/sonar-env.txt"
    echo "SONAR_GATE_STATUS=$gate_status" >> "$RESULTS_DIR/sonar-env.txt"

    if [[ "$gate_status" == "ERROR" || "$gate_status" == "WARN" ]]; then
        log "Quality gate did not pass (status: $gate_status)"
        exit 1
    fi

    log "SonarQube analysis complete — $issue_count issues, gate: $gate_status"
    return $scan_exit_code
}

main "$@"

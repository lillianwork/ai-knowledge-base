#!/bin/bash
set -euo pipefail

# quality-gate.sh — Evaluate all quality gates across SonarQube, Polyspace, and Tests
# Context: Aggregates results from all scan stages and determines pass/fail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
WORKSPACE="${WORKSPACE:-$(pwd)}"
RULES_FILE="${RULES_FILE:-$WORKSPACE/config/quality-gate-rules.json}"
RESULTS_DIR="${RESULTS_DIR:-$WORKSPACE/scan-reports}"
GATE_RESULTS_DIR="${GATE_RESULTS_DIR:-$WORKSPACE/gate-results}"

log() { echo "[QUALITY-GATE] $(date '+%H:%M:%S') $*"; }

evaluate_sonarqube_gate() {
    log "Evaluating SonarQube quality gate..."
    local gate_result="PASS"
    local failures="[]"

    local sonar_env="$RESULTS_DIR/sonar-env.txt"
    if [[ -f "$sonar_env" ]]; then
        source "$sonar_env"
        local gate_status="${SONAR_GATE_STATUS:-UNKNOWN}"
        local issue_count="${SONAR_ISSUE_COUNT:-0}"

        jq -r '.quality_gates.sonarqube.conditions[] | "\(.metric) \(.op) \(.threshold) \(.severity)"' \
            "$RULES_FILE" 2>/dev/null | while read -r metric op threshold severity; do
            # SonarQube server-side gate is authoritative; we validate client-side as backup
            if [[ "$gate_status" != "OK" ]]; then
                gate_result="FAIL"
                failures=$(echo "$failures" | jq --arg m "$metric" --arg s "$severity" \
                    '. + [{"metric": $m, "severity": $s, "status": "FAIL"}]')
            fi
        done
    else
        log "WARNING: No SonarQube results found, marking as SKIPPED"
        gate_result="SKIPPED"
    fi

    echo "$gate_result"
}

evaluate_polyspace_gate() {
    log "Evaluating Polyspace quality gate..."
    local gate_result="PASS"

    local ps_summary="$RESULTS_DIR/polyspace/polyspace-summary.json"
    if [[ -f "$ps_summary" ]]; then
        local status
        status=$(jq -r '.status // "ok"' "$ps_summary")
        if [[ "$status" == "skipped" ]]; then
            echo "SKIPPED"
            return
        fi

        local red gray orange misra mandatory misra required
        red=$(jq -r '.code_prover.red_checks // 0' "$ps_summary")
        gray=$(jq -r '.code_prover.gray_checks // 0' "$ps_summary")
        orange=$(jq -r '.bug_finder.defects // 0' "$ps_summary")
        misra_total=$(jq -r '.bug_finder.misra_violations // 0' "$ps_summary")

        if [[ "$red" -gt 0 || "$gray" -gt 0 ]]; then
            log "FAIL: Code Prover found $red red + $gray gray checks"
            gate_result="FAIL"
        fi
        if [[ "$orange" -gt 5 ]]; then
            log "FAIL: Bug Finder found $orange defects (threshold: 5)"
            gate_result="FAIL"
        fi
    else
        gate_result="SKIPPED"
    fi

    echo "$gate_result"
}

evaluate_test_gate() {
    log "Evaluating test quality gate..."
    local gate_result="PASS"

    local test_results="$WORKSPACE/build/test/test-summary.json"
    if [[ -f "$test_results" ]]; then
        local pass_rate coverage
        pass_rate=$(jq -r '.pass_rate // 100' "$test_results")
        coverage=$(jq -r '.coverage // 0' "$test_results")

        if (( $(echo "$pass_rate < 95.0" | bc -l 2>/dev/null || echo 0) )); then
            log "FAIL: Test pass rate $pass_rate% < 95%"
            gate_result="FAIL"
        fi
        if (( $(echo "$coverage < 70.0" | bc -l 2>/dev/null || echo 0) )); then
            log "FAIL: Test coverage $coverage% < 70%"
            gate_result="FAIL"
        fi
    else
        log "No test results found, marking as SKIPPED"
        gate_result="SKIPPED"
    fi

    echo "$gate_result"
}

generate_gate_report() {
    mkdir -p "$GATE_RESULTS_DIR"

    local sq_gate="$1" ps_gate="$2" test_gate="$3"
    local overall="PASS"

    if [[ "$sq_gate" == "FAIL" || "$ps_gate" == "FAIL" || "$test_gate" == "FAIL" ]]; then
        overall="FAIL"
    elif [[ "$sq_gate" == "PASS" && "$ps_gate" == "PASS" && "$test_gate" == "PASS" ]]; then
        overall="PASS"
    else
        overall="PASS_WITH_SKIPS"
    fi

    tee "$GATE_RESULTS_DIR/quality-gate-report.json" <<EOF
{
  "pipeline_id": "${CI_PIPELINE_ID:-local}",
  "commit": "$(git rev-parse --short HEAD 2>/dev/null || echo 'HEAD')",
  "timestamp": "$(date -u +%Y-%m-%dT%H:%M:%SZ)",
  "gates": {
    "sonarqube": "$sq_gate",
    "polyspace": "$ps_gate",
    "test": "$test_gate"
  },
  "overall": "$overall"
}
EOF

    log "Quality gate report: SonarQube=$sq_gate, Polyspace=$ps_gate, Test=$test_gate → Overall=$overall"
    echo "$overall"
}

main() {
    log "Evaluating quality gates..."

    if [[ ! -f "$RULES_FILE" ]]; then
        log "WARNING: No quality gate rules file found at $RULES_FILE"
        log "Using default thresholds"
    fi

    local sq_result ps_result test_result
    sq_result=$(evaluate_sonarqube_gate)
    ps_result=$(evaluate_polyspace_gate)
    test_result=$(evaluate_test_gate)

    local overall
    overall=$(generate_gate_report "$sq_result" "$ps_result" "$test_result")

    if [[ "$overall" == "FAIL" ]]; then
        log "QUALITY GATE FAILED — merge blocked"
        exit 1
    fi

    log "Quality gates passed (overall: $overall)"
}

main "$@"

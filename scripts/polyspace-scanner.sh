#!/bin/bash
set -euo pipefail

# polyspace-scanner.sh — Polyspace Bug Finder + Code Prover verification
# Context: Runs after build stage; performs MISRA checking and runtime error detection

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
WORKSPACE="${WORKSPACE:-$(pwd)}"
RESULTS_DIR="${RESULTS_DIR:-$WORKSPACE/scan-reports/polyspace}"
POLYSPACE_HOME="${POLYSPACE_HOME:-/opt/polyspace}"
POLYSPACE_CONFIG="${POLYSPACE_CONFIG:-$WORKSPACE/config/polyspace-config.psprj}"
POLYSPACE_DASHBOARD_URL="${POLYSPACE_DASHBOARD_URL:-}"

log() { echo "[POLYSPACE] $(date '+%H:%M:%S') $*"; }

validate_prerequisites() {
    if [[ ! -d "$POLYSPACE_HOME" ]]; then
        log "WARNING: Polyspace installation not found at $POLYSPACE_HOME"
        log "Polyspace is a licensed MathWorks product. Skipping if license unavailable."
        return 1
    fi
    return 0
}

run_bug_finder() {
    log "Running Polyspace Bug Finder..."
    mkdir -p "$RESULTS_DIR/bug-finder"

    local bug_finder="$POLYSPACE_HOME/polyspace/bin/polyspace-bug-finder"

    if [[ -x "$bug_finder" ]]; then
        "$bug_finder" \
            -sources "$WORKSPACE/src" \
            -I "$WORKSPACE/src/include" \
            -I "$WORKSPACE/src/hal" \
            -results-dir "$RESULTS_DIR/bug-finder" \
            -options-file "$POLYSPACE_CONFIG" \
            -misra-c \
            -misra-cpp \
            -checkers ALL \
            -output-format HTML,XML,JSON \
            2>&1 | tee "$RESULTS_DIR/bug-finder.log"
        return ${PIPESTATUS[0]}
    else
        log "bug-finder not found, trying Docker-based execution..."
        docker run --rm \
            -v "$WORKSPACE:/workspace" \
            -v "$RESULTS_DIR:/results" \
            -e MLM_LICENSE_FILE="${MLM_LICENSE_FILE:-}" \
            mathworks/polyspace:latest \
            polyspace-bug-finder \
            -sources /workspace/src \
            -results-dir /results/bug-finder \
            -misra-c \
            -output-format JSON \
            2>&1 | tee "$RESULTS_DIR/bug-finder.log"
        return ${PIPESTATUS[0]}
    fi
}

run_code_prover() {
    log "Running Polyspace Code Prover (formal verification)..."
    mkdir -p "$RESULTS_DIR/code-prover"

    local code_prover="$POLYSPACE_HOME/polyspace/bin/polyspace-code-prover"

    if [[ -x "$code_prover" ]]; then
        "$code_prover" \
            -sources "$WORKSPACE/src" \
            -I "$WORKSPACE/src/include" \
            -I "$WORKSPACE/src/hal" \
            -results-dir "$RESULTS_DIR/code-prover" \
            -options-file "$POLYSPACE_CONFIG" \
            -main-generator \
            -to SoftwareSafetyAnalysisLevelA \
            -output-format HTML,XML,JSON \
            2>&1 | tee "$RESULTS_DIR/code-prover.log"
        return ${PIPESATUS[0]}
    else
        log "Skipping Code Prover — requires licensed Polyspace installation"
        return 0
    fi
}

parse_results() {
    log "Parsing Polyspace results..."

    local defect_count=0
    local misra_count=0

    if [[ -f "$RESULTS_DIR/bug-finder/results.json" ]]; then
        defect_count=$(jq '[.defects[]?] | length' "$RESULTS_DIR/bug-finder/results.json" 2>/dev/null || echo "0")
        misra_count=$(jq '[.misra_violations[]?] | length' "$RESULTS_DIR/bug-finder/results.json" 2>/dev/null || echo "0")
    fi

    local code_prover_red=0 code_prover_gray=0
    if [[ -f "$RESULTS_DIR/code-prover/results.json" ]]; then
        code_prover_red=$(jq '[.checks[] | select(.color == "red")] | length' "$RESULTS_DIR/code-prover/results.json" 2>/dev/null || echo "0")
        code_prover_gray=$(jq '[.checks[] | select(.color == "gray")] | length' "$RESULTS_DIR/code-prover/results.json" 2>/dev/null || echo "0")
    fi

    log "Bug Finder: $defect_count defects, $misra_count MISRA violations"
    log "Code Prover: $code_prover_red red checks, $code_prover_gray gray checks"

    tee "$RESULTS_DIR/polyspace-summary.json" <<EOF
{
  "bug_finder": {
    "defects": $defect_count,
    "misra_violations": $misra_count
  },
  "code_prover": {
    "red_checks": $code_prover_red,
    "gray_checks": $code_prover_gray
  },
  "total_issues": $((defect_count + misra_count + code_prover_red + code_prover_gray)),
  "timestamp": "$(date -u +%Y-%m-%dT%H:%M:%SZ)"
}
EOF

    tee "$RESULTS_DIR/polyspace-env.txt" <<EOF
POLYSPACE_DEFECT_COUNT=$defect_count
POLYSPACE_MISRA_COUNT=$misra_count
POLYSPACE_CODE_PROVER_RED=$code_prover_red
POLYSPACE_CODE_PROVER_GRAY=$code_prover_gray
POLYSPACE_TOTAL_ISSUES=$((defect_count + misra_count + code_prover_red + code_prover_gray))
EOF
}

upload_to_dashboard() {
    if [[ -n "$POLYSPACE_DASHBOARD_URL" ]]; then
        log "Uploading results to Polyspace Access dashboard..."
        local uploader="$POLYSPACE_HOME/polyspace/bin/polyspace-results-upload"
        if [[ -x "$uploader" ]]; then
            "$uploader" \
                -login "$POLYSPACE_DASHBOARD_URL" \
                -results "$RESULTS_DIR" \
                -project "${CI_PROJECT_NAME:-embedded-project}"
        fi
    fi
}

main() {
    log "Starting Polyspace analysis"
    if ! validate_prerequisites; then
        log "Polyspace not available — generating placeholder results"
        mkdir -p "$RESULTS_DIR"
        tee "$RESULTS_DIR/polyspace-summary.json" <<<'{"status":"skipped","reason":"polyspace_unavailable"}'
        exit 0
    fi

    run_bug_finder
    local bf_exit=$?
    run_code_prover
    local cp_exit=$?

    parse_results
    upload_to_dashboard

    if [[ $bf_exit -ne 0 || $cp_exit -ne 0 ]]; then
        log "Polyspace analysis completed with warnings"
    else
        log "Polyspace analysis completed successfully"
    fi

    return $((bf_exit + cp_exit))
}

main "$@"

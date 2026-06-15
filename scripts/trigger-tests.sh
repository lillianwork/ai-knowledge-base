#!/bin/bash
set -euo pipefail

# trigger-tests.sh — Execute test suites and notify testers
# Context: Runs after quality gate passes; executes unit/integration/functional tests

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
WORKSPACE="${WORKSPACE:-$(pwd)}"
BUILD_DIR="${BUILD_DIR:-$WORKSPACE/build}"
TEST_DIR="${TEST_DIR:-$WORKSPACE/test}"
RESULTS_DIR="${RESULTS_DIR:-$BUILD_DIR/test}"
TEST_CONFIG="${TEST_CONFIG:-$WORKSPACE/config/test-config.json}"
GITLAB_HOST_URL="${GITLAB_HOST_URL:-http://gitlab:80}"
GITLAB_API_TOKEN="${GITLAB_API_TOKEN:-}"

log() { echo "[TEST] $(date '+%H:%M:%S') $*"; }

run_unit_tests() {
    log "Running unit tests (CppUTest)..."
    mkdir -p "$RESULTS_DIR/unit"

    local pass=0 fail=0 total=0

    find "$BUILD_DIR/test/unit" -name '*_test' -type f -executable 2>/dev/null | while read -r test_bin; do
        local test_name
        test_name=$(basename "$test_bin")
        log "  Running: $test_name"

        if "$test_bin" -ojunit > "$RESULTS_DIR/unit/${test_name}_results.xml" 2>&1; then
            pass=$((pass + 1))
        else
            fail=$((fail + 1))
        fi
        total=$((total + 1))
    done

    log "Unit tests: $((pass + fail))/$total executed"
}

run_integration_tests() {
    log "Running integration tests..."
    mkdir -p "$RESULTS_DIR/integration"

    local runner_endpoint="${TEST_RUNNER_ENDPOINT:-}"
    if [[ -n "$runner_endpoint" ]]; then
        log "Using remote test runner: $runner_endpoint"
        curl -s -X POST "$runner_endpoint/run" \
            -H "Content-Type: application/json" \
            -d "{\"project\":\"${CI_PROJECT_NAME:-embedded}\",\"branch\":\"${CI_COMMIT_BRANCH:-main}\",\"build_id\":\"${BUILD_NUMBER:-local}\"}" \
            -o "$RESULTS_DIR/integration/test-trigger-response.json"

        log "Waiting for integration test results..."
        local test_id
        test_id=$(jq -r '.test_run_id' "$RESULTS_DIR/integration/test-trigger-response.json" 2>/dev/null)

        local max_wait=3600 waited=0
        while [[ $waited -lt $max_wait ]]; do
            local status
            status=$(curl -s "$runner_endpoint/status/$test_id" | jq -r '.status')
            if [[ "$status" == "completed" || "$status" == "failed" ]]; then
                curl -s "$runner_endpoint/results/$test_id" \
                    -o "$RESULTS_DIR/integration/results.xml"
                break
            fi
            sleep 30
            waited=$((waited + 30))
        done
    else
        find "$BUILD_DIR/test/integration" -name '*_itest' -type f -executable 2>/dev/null | while read -r test_bin; do
            local test_name
            test_name=$(basename "$test_bin")
            log "  Running: $test_name"
            "$test_bin" -ojunit > "$RESULTS_DIR/integration/${test_name}_results.xml" 2>&1 || true
        done
    fi
}

run_functional_tests() {
    log "Running functional tests (Robot Framework)..."
    mkdir -p "$RESULTS_DIR/functional"

    if command -v robot &>/dev/null; then
        robot \
            --outputdir "$RESULTS_DIR/functional" \
            --xunit "$RESULTS_DIR/functional/output.xml" \
            "$TEST_DIR/functional/" 2>&1 | tee "$RESULTS_DIR/functional/robot.log" || true
    else
        log "Robot Framework not installed, skipping functional tests"
        echo '{"status":"skipped","reason":"robot_not_found"}' > "$RESULTS_DIR/functional/status.json"
    fi
}

collect_test_results() {
    log "Collecting test results..."
    local total_tests=0 total_pass=0 total_fail=0 total_skip=0

    for results_file in $(find "$RESULTS_DIR" -name '*_results.xml' -o -name 'output.xml' 2>/dev/null); do
        if [[ -f "$results_file" ]]; then
            local tests pass fail skip
            tests=$(grep -oP 'tests="\K[0-9]+' "$results_file" 2>/dev/null | head -1 || echo "0")
            pass=$((pass + $(grep -oP 'tests="\K[0-9]+' "$results_file" 2>/dev/null | head -1 || echo "0") - $(grep -oP 'failures="\K[0-9]+' "$results_file" 2>/dev/null | head -1 || echo "0")))
            fail=$((fail + $(grep -oP 'failures="\K[0-9]+' "$results_file" 2>/dev/null | head -1 || echo "0")))
            skip=$((skip + $(grep -oP 'skipped="\K[0-9]+' "$results_file" 2>/dev/null | head -1 || echo "0")))
            total_tests=$((total_tests + tests))
        fi
    done

    local pass_rate=0
    if [[ $total_tests -gt 0 ]]; then
        pass_rate=$(echo "scale=2; ($total_tests - $total_fail - $total_skip) * 100 / $total_tests" | bc 2>/dev/null || echo "0")
    fi

    tee "$RESULTS_DIR/test-summary.json" <<EOF
{
  "total": $total_tests,
  "pass": $((total_tests - total_fail - total_skip)),
  "fail": $total_fail,
  "skip": $total_skip,
  "pass_rate": $pass_rate,
  "timestamp": "$(date -u +%Y-%m-%dT%H:%M:%SZ)",
  "pipeline_id": "${CI_PIPELINE_ID:-local}"
}
EOF

    log "Test results: $total_tests total, $total_fail failed, $total_skip skipped ($pass_rate%)"
    echo "TEST_PASS_RATE=$pass_rate" > "$RESULTS_DIR/test-env.txt"
    echo "TEST_TOTAL=$total_tests" >> "$RESULTS_DIR/test-env.txt"
    echo "TEST_FAIL=$total_fail" >> "$RESULTS_DIR/test-env.txt"
}

notify_testers() {
    if [[ -z "$GITLAB_API_TOKEN" || -z "${GITLAB_PROJECT_ID:-}" ]]; then
        log "GitLab API not configured, skipping tester notification"
        return
    fi

    local test_summary="$RESULTS_DIR/test-summary.json"
    local fail_count
    fail_count=$(jq -r '.fail // 0' "$test_summary")

    if [[ "$fail_count" -gt 0 ]]; then
        log "Notifying testers of $fail_count test failures..."
        local test_lead="${TEST_LEAD:-test-lead}"
        local assignee_id
        assignee_id=$(curl -s -H "PRIVATE-TOKEN: $GITLAB_API_TOKEN" \
            "$GITLAB_HOST_URL/api/v4/users?search=$test_lead" | jq -r '.[0].id // empty')

        local title="[测试] ${CI_PROJECT_NAME:-Project} Build#${BUILD_NUMBER:-?}: $fail_count 个失败用例"

        local desc
        desc=$(cat <<DESC
## 测试执行结果

**流水线**: ${CI_PIPELINE_URL:-#}
**构建号**: ${BUILD_NUMBER:-local}
**分支**: ${CI_COMMIT_BRANCH:-$(git rev-parse --abbrev-ref HEAD 2>/dev/null)}
**提交**: $(git rev-parse --short HEAD 2>/dev/null)

### 汇总
| 指标 | 值 |
|------|-----|
| 总用例数 | $(jq -r '.total' "$test_summary") |
| 通过 | $(jq -r '.pass' "$test_summary") |
| 失败 | $(jq -r '.fail' "$test_summary") |
| 跳过 | $(jq -r '.skip' "$test_summary") |
| 通过率 | $(jq -r '.pass_rate' "$test_summary")% |

### 报告路径
- Unit Test: \`$RESULTS_DIR/unit/\`
- Integration Test: \`$RESULTS_DIR/integration/\`
- Functional Test: \`$RESULTS_DIR/functional/\`

请 @${test_lead} 审核测试结果。
DESC
)
        curl -s -X POST "$GITLAB_HOST_URL/api/v4/projects/${GITLAB_PROJECT_ID}/issues" \
            -H "PRIVATE-TOKEN: $GITLAB_API_TOKEN" \
            -H "Content-Type: application/json" \
            -d "$(jq -n --arg title "$title" --arg desc "$desc" --argjson assignee "${assignee_id:-null}" \
                '{title: $title, description: $desc, assignee_id: $assignee, labels: "test-report"}')" \
            -o /dev/null -w "%{http_code}"
    fi
}

main() {
    log "Starting automated test execution"
    mkdir -p "$RESULTS_DIR"

    run_unit_tests
    run_integration_tests
    run_functional_tests
    collect_test_results
    notify_testers

    log "Test execution complete"
}

main "$@"

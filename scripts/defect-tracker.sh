#!/bin/bash
set -euo pipefail

# defect-tracker.sh — Create GitLab Issues from test failures and assign to developers
# Context: Runs after trigger-tests.sh; maps failing tests to responsible developers

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
WORKSPACE="${WORKSPACE:-$(pwd)}"
RESULTS_DIR="${RESULTS_DIR:-$WORKSPACE/build/test}"
DEFECT_DIR="${DEFECT_DIR:-$WORKSPACE/defects}"
GITLAB_HOST_URL="${GITLAB_HOST_URL:-http://gitlab:80}"
GITLAB_API_TOKEN="${GITLAB_API_TOKEN:-}"
GITLAB_PROJECT_ID="${CI_PROJECT_ID:-}"

log() { echo "[DEFECT] $(date '+%H:%M:%S') $*"; }

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

find_developer_for_test() {
    local test_file="$1"
    local test_name="$2"

    cd "$WORKSPACE"
    local author_email
    author_email=$(git log -1 --format='%ae' -- "$test_file" 2>/dev/null)

    if [[ -z "$author_email" ]]; then
        local source_file
        source_file=$(echo "$test_name" | sed 's/_test$//;s/^test_//')
        author_email=$(git log -1 --format='%ae' -- "src/$source_file.c" "src/$source_file.cpp" 2>/dev/null || echo "")

        if [[ -z "$author_email" ]]; then
            author_email=$(git log -1 --format='%ae' 2>/dev/null || echo "${GITLAB_USER_EMAIL:-unknown}")
        fi
    fi
    echo "$author_email"
}

parse_test_failures() {
    log "Parsing test failures from JUnit reports..."
    mkdir -p "$DEFECT_DIR"

    echo '[]' > "$DEFECT_DIR/failures.json"

    find "$RESULTS_DIR" -name '*_results.xml' -o -name 'output.xml' 2>/dev/null | while read -r xml_file; do
        local test_type
        case "$xml_file" in
            */unit/*)        test_type="Unit" ;;
            */integration/*) test_type="Integration" ;;
            */functional/*)  test_type="Functional" ;;
            *)               test_type="Unknown" ;;
        esac

        grep -oP '<testcase[^>]*>' "$xml_file" 2>/dev/null | while read -r testcase; do
            local has_failure
            has_failure=$(echo "$testcase" | grep -c '<failure' || true)
            if [[ "$has_failure" -eq 0 ]]; then continue; fi

            local classname name
            classname=$(echo "$testcase" | grep -oP 'classname="\K[^"]*' || echo "unknown")
            name=$(echo "$testcase" | grep -oP 'name="\K[^"]*' || echo "unknown")

            local developer
            developer=$(find_developer_for_test "$xml_file" "$name")

            local failure_msg
            failure_msg=$(grep -A5 "<failure" "$xml_file" 2>/dev/null | head -6 | sed 's/</\&lt;/g;s/>/\&gt;/g' || echo "Test assertion failed")

            jq --arg type "$test_type" --arg class "$classname" --arg name "$name" \
               --arg dev "$developer" --arg msg "$failure_msg" \
               '. + [{"test_type": $type, "class": $class, "name": $name, "developer": $dev, "message": $msg}]' \
               "$DEFECT_DIR/failures.json" > "$DEFECT_DIR/failures.tmp" && \
               mv "$DEFECT_DIR/failures.tmp" "$DEFECT_DIR/failures.json"
        done
    done
}

create_defect_issues() {
    log "Creating defect issues in GitLab..."

    local failure_count
    failure_count=$(jq '. | length' "$DEFECT_DIR/failures.json")
    log "Found $failure_count test failures"

    jq -c '.[]' "$DEFECT_DIR/failures.json" 2>/dev/null | while read -r failure; do
        local test_type class name developer message
        test_type=$(echo "$failure" | jq -r '.test_type')
        class=$(echo "$failure" | jq -r '.class')
        name=$(echo "$failure" | jq -r '.name')
        developer=$(echo "$failure" | jq -r '.developer')
        message=$(echo "$failure" | jq -r '.message')

        local title="[Test Defect][$test_type] $class.$name 测试失败"

        local desc
        desc=$(cat <<DESC
## 测试缺陷详情

| 属性 | 值 |
|------|-----|
| **测试类型** | $test_type |
| **测试类** | $class |
| **测试用例** | $name |
| **检测时间** | $(date -u +%Y-%m-%dT%H:%M:%SZ) |
| **流水线** | ${CI_PIPELINE_ID:-local} |
| **分支** | ${CI_COMMIT_BRANCH:-$(git rev-parse --abbrev-ref HEAD 2>/dev/null)} |

### 失败信息
\`\`\`
$message
\`\`\`

### 修复指引
1. 审查测试用例 \`$name\` 的实现逻辑
2. 检查被测试代码是否有回归问题
3. 修复后在本地运行 \`make test\` 确认通过

---
**指派给**: @$developer
**测试类型**: $test_type
DESC
)
        local assignee_id
        assignee_id=$(curl -s -H "PRIVATE-TOKEN: $GITLAB_API_TOKEN" \
            "$GITLAB_HOST_URL/api/v4/users?search=$developer" | jq -r '.[0].id // empty')

        local response
        response=$(gitlab_api "POST" "/projects/$GITLAB_PROJECT_ID/issues" \
            "$(jq -n --arg title "$title" --arg desc "$desc" --argjson assignee "${assignee_id:-null}" \
                '{title: $title, description: $desc, assignee_id: $assignee, labels: "defect,test-failure"}')")

        local issue_iid
        issue_iid=$(echo "$response" | jq -r '.iid // empty')
        if [[ -n "$issue_iid" ]]; then
            log "Created defect Issue #$issue_iid for $class.$name (assigned: $developer)"
        fi
    done
}

generate_defect_report() {
    tee "$DEFECT_DIR/defect-report.json" <<EOF
{
  "pipeline_id": "${CI_PIPELINE_ID:-local}",
  "commit": "$(git rev-parse --short HEAD 2>/dev/null || echo 'HEAD')",
  "timestamp": "$(date -u +%Y-%m-%dT%H:%M:%SZ)",
  "total_failures": $(jq '. | length' "$DEFECT_DIR/failures.json"),
  "failures": $(cat "$DEFECT_DIR/failures.json")
}
EOF
    log "Defect report generated: $DEFECT_DIR/defect-report.json"
}

main() {
    log "Starting defect tracking"

    if [[ -z "$GITLAB_API_TOKEN" || -z "$GITLAB_PROJECT_ID" ]]; then
        log "WARNING: GitLab API not configured. Defects saved locally only."
        mkdir -p "$DEFECT_DIR"
        parse_test_failures
        generate_defect_report
        exit 0
    fi

    parse_test_failures
    create_defect_issues
    generate_defect_report

    log "Defect tracking complete"
}

main "$@"

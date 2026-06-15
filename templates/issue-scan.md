## Scan Issue: {ISSUE_TITLE}

### 问题来源
- **扫描工具**: {SCAN_TOOL} (SonarQube / Polyspace)
- **扫描时间**: {SCAN_TIMESTAMP}
- **流水线**: [{PIPELINE_NAME}]({PIPELINE_URL})
- **提交**: [{COMMIT_SHORT_SHA}]({COMMIT_URL})

### 问题详情
| 属性 | 值 |
|------|-----|
| **严重等级** | {SEVERITY} |
| **问题类型** | {ISSUE_TYPE} (Bug / Vulnerability / Code Smell / MISRA Violation / Runtime Error) |
| **文件** | `{FILE_PATH}` |
| **行号** | L{LINE_NUMBER} |
| **规则** | {RULE_ID} — {RULE_DESCRIPTION} |

### 问题描述
{ISSUE_MESSAGE}

### 修复建议
{REMEDIATION_ADVICE}

### 代码片段
```{LANGUAGE}
{CODE_SNIPPET}
```

---
**指派给**: @{ASSIGNEE} (代码提交者)
**关联分支**: `{SOURCE_BRANCH}`
**预计修复时间**: {ESTIMATED_EFFORT}

> 请尽快修复此问题。修复后关闭此 Issue 将自动触发重新扫描验证。

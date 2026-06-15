## Test Defect: {DEFECT_TITLE}

### 测试信息
- **测试类型**: {TEST_TYPE} (Unit / Integration / Functional)
- **测试用例**: `{TEST_CASE_ID}` — {TEST_CASE_NAME}
- **测试执行时间**: {TEST_TIMESTAMP}
- **流水线**: [{PIPELINE_NAME}]({PIPELINE_URL})

### 缺陷摘要
| 属性 | 值 |
|------|-----|
| **严重等级** | {SEVERITY} (Critical / Major / Minor / Trivial) |
| **触发条件** | {TRIGGER_CONDITION} |
| **实际结果** | {ACTUAL_RESULT} |
| **期望结果** | {EXPECTED_RESULT} |

### 复现步骤
{REPRODUCTION_STEPS}

### 日志/截图
```
{TEST_LOGS}
```

### 关联信息
- **引入提交**: [{INTRODUCING_COMMIT}]({INTRODUCING_COMMIT_URL})
- **关联模块**: {RELATED_MODULES}
- **关联需求**: {REQUIREMENT_ID}

---
**指派给**: @{ASSIGNEE} (开发者)
**测试员**: @{TESTER}
**关联分支**: `{SOURCE_BRANCH}`

> 请在修复后重新运行测试用例 `{TEST_CASE_ID}` 并更新此 Issue 状态。

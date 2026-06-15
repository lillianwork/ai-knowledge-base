## CI/CD Pipeline Notification

### {NOTIFICATION_TYPE}

**项目**: {PROJECT_NAME}
**流水线**: [{PIPELINE_NAME}#{BUILD_NUMBER}]({PIPELINE_URL})
**触发者**: @{TRIGGER_USER}
**分支**: `{SOURCE_BRANCH}` → `{TARGET_BRANCH}`
**提交**: [{COMMIT_SHORT_SHA}]({COMMIT_URL}) — {COMMIT_MESSAGE}

---

### Stage 执行汇总

| Stage | 状态 | 耗时 | 详情 |
|-------|------|------|------|
{STAGE_SUMMARY_TABLE}

---

### {SECTION_TITLE}

{SECTION_CONTENT}

---

### 关键指标

| 指标 | 当前值 | 阈值 | 状态 |
|------|--------|------|------|
{KEY_METRICS_TABLE}

---

**整体状态**: {OVERALL_STATUS}
**归档链接**: {ARCHIVE_URL}
**完整报告**: [{REPORT_URL}]({REPORT_URL})

---
*此通知由 CI/CD 系统自动生成，请勿直接回复。如有问题请联系 @{CICD_ADMIN}*

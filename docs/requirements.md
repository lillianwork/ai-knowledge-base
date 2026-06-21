# 嵌入式固件 CI/CD 流水线系统 — 需求规格说明书

> **版本**: 0.1.0  
> **更新日期**: 2026-06-19  
> **文档状态**: 初稿  

---

## 1. 引言

### 1.1 项目背景

嵌入式固件开发团队需要一个全自动化的持续集成/持续交付（CI/CD）流水线系统，将 GitLab 代码托管、Jenkins 自动化构建、SonarQube / Polyspace 静态分析、自动化测试、缺陷跟踪和制品归档整合为统一流程，保障嵌入式 C/C++ 代码的质量与可追溯性。

### 1.2 项目目标

| 目标 | 描述 |
|------|------|
| **自动化构建** | 支持 GCC、IAR、Keil、ARMCC 多工具链编译 |
| **代码质量门禁** | 通过 SonarQube + Polyspace 双重扫描，阻断不合规代码合入 |
| **自动化测试** | 执行单元测试（CppUTest）、集成测试、功能测试（Robot Framework） |
| **缺陷闭环** | 扫描问题/测试失败自动创建 GitLab Issue 并指派责任人 |
| **制品归档** | 固件二进制、源码、文档、测试报告、SBOM 自动归档至 Nexus |
| **修复验证** | 问题修复后自动触发重新扫描验证 |

### 1.3 适用范围

本系统适用于嵌入式 C/C++ 固件项目，涵盖从代码提交到制品归档的完整 DevOps 流水线。

---

## 2. 功能需求

### 2.1 代码检出与构建（Checkout & Build）

#### 2.1.1 代码检出

- **FR-001**: 流水线自动检出 Git 仓库代码，提取提交 SHA、分支名、提交者邮箱、提交信息。
- **FR-002**: 检出后自动向 GitLab 推送 `pipeline: running` 状态。

#### 2.1.2 多工具链构建

- **FR-003**: 支持 GCC（arm-none-eabi-gcc）、IAR（iccarm + iarbuild）、Keil（armcc + UV4）、ARMCC（armclang）四种工具链编译。
- **FR-004**: 通过 Jenkins 参数 `IDE_TOOLCHAIN` 选择工具链，默认 `gcc`。
- **FR-005**: 支持 Debug / Release / MinSizeRel 三种构建类型，通过 `BUILD_TYPE` 参数选择。
- **FR-006**: 构建时通过 SonarQube build-wrapper 捕获编译数据库（compile_commands.json），为后续静态分析提供输入。
- **FR-007**: 构建产物（.bin, .hex, .elf, .map, .s19）收集至 `build/output/` 目录。
- **FR-008**: 构建完成后生成 `build-info.json`，包含版本号、工具链、构建类型、提交 SHA、时间戳等元数据。

---

### 2.2 静态代码分析

#### 2.2.1 SonarQube 分析

- **FR-009**: 基于 build-wrapper 输出的 compile_commands.json 执行 SonarQube C/C++ 分析。
- **FR-010**: 排除 build、third_party、test、vendor 目录，避免噪声。
- **FR-011**: 自动获取 SonarQube 质量门状态和问题列表。
- **FR-012**: 按提交者提取归属问题，输出到 `issues-by-author.jsonl`。
- **FR-013**: 支持 Docker 模式运行 sonar-scanner（当本地未安装时）。

#### 2.2.2 Polyspace 分析

- **FR-014**: 执行 Polyspace Bug Finder 进行缺陷检测和 MISRA C/C++ 规范检查。
- **FR-015**: 执行 Polyspace Code Prover 进行形式化验证（红色/灰色检查项）。
- **FR-016**: 通过 `SKIP_POLYSPACE` 参数可跳过（无 License 时自动降级为 SKIPPED）。
- **FR-017**: 支持 Docker 模式运行（`mathworks/polyspace` 镜像）。
- **FR-018**: 分析结果上传至 Polyspace Access Dashboard（如已配置）。

---

### 2.3 质量门禁

#### 2.3.1 SonarQube 门禁条件

| 指标 | 条件 | 阈值 | 严重等级 |
|------|------|------|----------|
| 新增 Bug | > 0 | 0 | BLOCKER |
| 新增漏洞 | > 0 | 0 | BLOCKER |
| 新增安全热点 | > 0 | 0 | CRITICAL |
| 新增代码异味 | > | 10 | MAJOR |
| 新增重复行密度 | > | 3.0% | MAJOR |
| 新增覆盖率 | < | 60% | WARNING |

#### 2.3.2 Polyspace 门禁条件

| 检查项 | 条件 | 阈值 | 严重等级 |
|--------|------|------|----------|
| Code Prover 红色检查 | > 0 | 0 | BLOCKER |
| Code Prover 灰色检查 | > 0 | 0 | BLOCKER |
| Bug Finder 缺陷 | > | 5 | MAJOR |
| MISRA 强制违规 | > 0 | 0 | BLOCKER |
| MISRA 必要违规 | > | 20 | MAJOR |

#### 2.3.3 测试门禁条件

| 指标 | 条件 | 阈值 | 严重等级 |
|------|------|------|----------|
| 测试通过率 | < | 95% | BLOCKER |
| 单元测试覆盖率 | < | 70% | MAJOR |
| 集成测试通过率 | < | 100% | CRITICAL |

#### 2.3.4 门禁汇总规则

- **FR-019**: 三门禁（SonarQube、Polyspace、Test）全部通过时，Overall 为 PASS。
- **FR-020**: 任一 BLOCKER 级别门禁失败，Overall 为 FAIL，**阻断代码合入**。
- **FR-021**: 允许管理员覆盖门禁结果（`allow_override_by_admin: true`）。
- **FR-022**: 门禁报告输出到 `gate-results/quality-gate-report.json`。

---

### 2.4 自动化测试

#### 2.4.1 单元测试

- **FR-023**: 使用 CppUTest 框架执行单元测试。
- **FR-024**: 测试可执行文件匹配模式 `build/test/unit/*_test`。
- **FR-025**: 结果以 JUnit XML 格式输出（`*_results.xml`）。
- **FR-026**: 使用 gcov 收集代码覆盖率数据。

#### 2.4.2 集成测试

- **FR-027**: 支持本地执行模式（匹配 `build/test/integration/*_itest`）。
- **FR-028**: 支持远程硬件测试执行器模式（通过 `TEST_RUNNER_ENDPOINT` 触发）。
- **FR-029**: 远程模式下轮询测试状态，最长等待 3600 秒。

#### 2.4.3 功能测试

- **FR-030**: 使用 Robot Framework 执行功能测试。
- **FR-031**: 测试套件路径 `test/functional/`，结果输出到 `build/test/functional/`。

#### 2.4.4 测试汇总

- **FR-032**: 汇总所有测试结果，计算通过率并输出 `test-summary.json`。
- **FR-033**: 测试通过率低于 95% 或存在失败用例时，通知测试负责人。

---

### 2.5 问题分配与缺陷跟踪

#### 2.5.1 扫描问题分配

- **FR-034**: SonarQube 问题通过 `git blame` 定位引入代码的开发者，自动创建 GitLab Issue 并指派。
- **FR-035**: Polyspace 问题汇总为一个 GitLab Issue，指派给最近提交者。
- **FR-036**: Issue 使用模板 `templates/issue-scan.md`，包含严重等级、文件路径、行号、修复建议等。
- **FR-037**: 生成 `scan-issues/tracking-report.json` 记录创建的问题数。

#### 2.5.2 测试缺陷跟踪

- **FR-038**: 解析 JUnit 报告中的失败用例，定位责任人（通过 git log 查找测试文件/被测文件的最后修改者）。
- **FR-039**: 为每个失败用例自动创建 GitLab Issue，使用模板 `templates/issue-defect.md`。
- **FR-040**: Issue 标签区分 Unit / Integration / Functional 测试类型。
- **FR-041**: 生成 `defects/defect-report.json` 汇总所有缺陷。

#### 2.5.3 修复验证

- **FR-042**: 扫描相关 Issue 关闭时，自动触发 `verify-fix.sh` 重新执行对应扫描工具。
- **FR-043**: 修复通过则自动关闭 Issue 并添加确认评论；未通过则添加警告评论并保持开启。

---

### 2.6 制品归档

#### 2.6.1 归档内容

| 制品类型 | 内容 | 是否必须 |
|----------|------|----------|
| 源代码 | src/ 目录 + VCS 信息 | 是 |
| 设计文档 | docs/ 目录（pdf, md, drawio, svg） | 否 |
| 固件二进制 | .bin, .hex, .elf, .map, .s19 | 是 |
| 构建日志 | build/logs/*.log | 是 |
| 扫描报告 | SonarQube + Polyspace 结果 | 是 |
| 测试报告 | JUnit XML + Robot output + 覆盖率 | 是 |
| 测试用例库 | test/ 目录（cpp, h, robot） | 是 |
| 缺陷数据库 | defects/ 目录 | 否 |
| 扫描问题库 | scan-issues/ 目录 | 否 |
| SBOM | SPDX 2.3 格式物料清单 | 否 |

#### 2.6.2 归档策略

- **FR-044**: 优先上传至 Nexus（raw 格式仓库 `embedded-firmware-releases`），失败时降级为本地文件系统归档。
- **FR-045**: 版本号来源：优先 Git Tag，其次 Git SHA；格式 `v{MAJOR}.{MINOR}.{PATCH}`，非正式版本加 `-SNAPSHOT` 后缀。
- **FR-046**: main 分支和 release/* 分支视为正式发布版本。
- **FR-047**: 快照版本保留最近 10 个，发布版本永久保留。
- **FR-048**: 归档完成后生成 MANIFEST.json 清单文件。

#### 2.6.3 SBOM 生成

- **FR-049**: 自动生成 SPDX 2.3 格式的软件物料清单，包含项目名、版本、下载地址、供应商信息。

---

### 2.7 通知机制

#### 2.7.1 流水线通知

- **FR-050**: 流水线成功/失败时发送邮件通知，收件人为代码提交者和项目开发者。
- **FR-051**: 邮件包含项目名、构建号、分支、提交者、归档版本、构建详情链接。
- **FR-052**: 通知模板使用 `templates/notification.md`，包含 Stage 执行汇总和关键指标表。

#### 2.7.2 问题通知

- **FR-053**: 质量门禁失败时通过 GitLab Issue、邮件、Slack 多通道通知。
- **FR-054**: 测试失败时自动通知测试负责人。

---

### 2.8 触发机制

- **FR-055**: 支持 Push 事件触发（所有分支）。
- **FR-056**: 支持 Merge Request 事件触发。
- **FR-057**: 支持评论触发（正则匹配 `recheck` 或 `retest`）。
- **FR-058**: 禁止并发构建，超时时间 2 小时。
- **FR-059**: 保留最近 30 次构建记录和 10 个归档制品。

---

## 3. 非功能需求

### 3.1 可扩展性

- **NFR-001**: 工具链通过 `case` 模式扩展，新增工具链只需添加新的 case 分支。
- **NFR-002**: 质量门禁规则通过 JSON 配置文件管理，无需修改脚本即可调整阈值。
- **NFR-003**: 归档内容通过 `archive-mapping.json` 配置，新增制品类型无需改代码。

### 3.2 容错性

- **NFR-004**: Polyspace 不可用时自动降级为 SKIPPED，不阻断流水线。
- **NFR-005**: Nexus 上传失败时自动降级为本地文件系统归档。
- **NFR-006**: sonar-scanner 本地未安装时自动切换 Docker 模式。
- **NFR-007**: 可选制品缺失时仅记录日志，不中断流程。

### 3.3 可维护性

- **NFR-008**: 所有脚本使用 `set -euo pipefail` 严格错误处理。
- **NFR-009**: 脚本统一日志格式 `[MODULE] HH:MM:SS message`。
- **NFR-010**: 配置与脚本分离（`config/` 目录存放 JSON 和 properties）。
- **NFR-011**: Issue 模板使用占位符替换，便于统一维护格式。

### 3.4 安全性

- **NFR-012**: 敏感凭证（Sonar Token、GitLab Token、Nexus Password、Polyspace License）通过 Jenkins Credentials 管理。
- **NFR-013**: 构建结束后执行 `cleanWs` 清理工作空间，排除 `.sonar/cache`。

---

## 4. 系统架构

### 4.1 Docker 服务栈

```
┌──────────┐  ┌──────────┐  ┌────────────┐  ┌──────────┐  ┌────────────────┐
│  GitLab   │  │ Jenkins  │  │ SonarQube  │  │  Nexus   │  │ Jenkins Agent  │
│  :8080    │  │ :8081    │  │ :9000      │  │ :8082    │  │ (embedded)     │
└────┬─────┘  └────┬─────┘  └─────┬──────┘  └────┬─────┘  └───────┬────────┘
     └─────────────┴──────────────┴──────────────┴─────────────────┘
                              cicd-network (bridge)
```

| 服务 | 镜像 | 端口 |
|------|------|------|
| GitLab CE | `gitlab/gitlab-ce:17.0.0-ce.0` | 8080 (HTTP), 8443 (HTTPS), 2222 (SSH) |
| Jenkins | `jenkins/jenkins:lts-jdk17` | 8081 (Web), 50000 (Agent) |
| SonarQube | `sonarqube:10.6-community` | 9000 (Web), 9092 (ES) |
| Nexus | `sonatype/nexus3:latest` | 8082 (Web) |
| Jenkins Agent | `jenkins/inbound-agent:latest-jdk17` | — |

### 4.2 流水线阶段

```
Checkout → Build → SonarQube/Polyspace → Issue Assignment → Quality Gate
                                                                    ↓
    Archive Artifacts ← Defect Tracking ← Automated Testing ←──────┘
```

### 4.3 脚本映射

| 流水线阶段 | 脚本 | 功能 |
|-----------|------|------|
| Build | `build-ide.sh` | 多工具链编译 + build-wrapper 捕获 |
| SonarQube | `sonar-scanner.sh` | 静态分析 + 质量门检查 |
| Polyspace | `polyspace-scanner.sh` | Bug Finder + Code Prover |
| Issue Assignment | `assign-issues.sh` | Git blame → 自动创建 Issue |
| Quality Gate | `quality-gate.sh` | 三门禁汇总判定 |
| Automated Testing | `trigger-tests.sh` | 单元/集成/功能测试 |
| Defect Tracking | `defect-tracker.sh` | 测试失败 → 自动创建 Issue |
| Archive Artifacts | `archive-artifacts.sh` | 归档至 Nexus + SBOM |
| Fix Verification | `verify-fix.sh` | Issue 关闭后重新扫描验证 |

---

## 5. 配置说明

### 5.1 质量门禁配置

文件：`config/quality-gate-rules.json`

定义 SonarQube、Polyspace、Test 三门禁的具体条件和阈值。支持 `BLOCKER`、`CRITICAL`、`MAJOR`、`WARNING` 四个严重等级。

### 5.2 归档配置

文件：`config/archive-mapping.json`

定义归档仓库类型（Nexus / filesystem）、制品内容映射、版本策略、保留策略。

### 5.3 测试配置

文件：`config/test-config.json`

定义单元/集成/功能测试的框架、执行模式、覆盖率工具、通知策略。

### 5.4 扫描器配置

文件：`config/sonar-project.properties`

SonarQube 项目配置，包括源码路径、排除路径、编译命令路径、质量门等待超时等。

---

## 6. Jenkins 参数

| 参数名 | 类型 | 默认值 | 描述 |
|--------|------|--------|------|
| `IDE_TOOLCHAIN` | string | `gcc` | 编译工具链：gcc, iar, keil, armcc |
| `BUILD_TYPE` | choice | `Debug` | 构建类型：Debug, Release, MinSizeRel |
| `SKIP_POLYSPACE` | boolean | `false` | 跳过 Polyspace 扫描 |
| `SKIP_ARCHIVE` | boolean | `false` | 跳过制品归档 |
| `TEST_HW_TARGET` | string | — | 集成测试硬件目标 |
| `TEST_LEAD` | string | `test-lead` | 测试负责人用户名 |

---

## 7. 项目文件结构

```
JenkinsGitlab/
├── Jenkinsfile              # 流水线定义（Groovy DSL）
├── VERSION                  # 版本号（SemVer）
├── CLAUDE.md                # AI 协作规则
├── config/
│   ├── archive-mapping.json      # 归档制品映射
│   ├── polyspace-config.psprj    # Polyspace 项目配置
│   ├── quality-gate-rules.json   # 质量门禁规则
│   ├── sonar-project.properties  # SonarQube 配置
│   └── test-config.json          # 测试框架配置
├── docker/
│   └── docker-compose.yml        # Docker 服务编排
├── scripts/
│   ├── build-ide.sh              # 多工具链构建
│   ├── sonar-scanner.sh          # SonarQube 扫描
│   ├── polyspace-scanner.sh      # Polyspace 扫描
│   ├── quality-gate.sh           # 质量门禁判定
│   ├── trigger-tests.sh          # 测试执行
│   ├── assign-issues.sh          # 扫描问题分配
│   ├── defect-tracker.sh         # 测试缺陷跟踪
│   ├── archive-artifacts.sh      # 制品归档
│   └── verify-fix.sh             # 修复验证
├── templates/
│   ├── issue-scan.md             # 扫描问题 Issue 模板
│   ├── issue-defect.md           # 测试缺陷 Issue 模板
│   └── notification.md           # 流水线通知模板
└── docs/
    └── requirements.md           # 本需求文档
```

---

## 8. 版本历史

| 版本 | 日期 | 变更说明 | 作者 |
|------|------|----------|------|
| 0.1.0 | 2026-06-19 | 初稿，基于现有代码逆向生成 | — |

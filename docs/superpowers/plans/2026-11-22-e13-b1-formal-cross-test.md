# E13 B1 Formal Cross-Test Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 在 B09 正式消费 A09 固定本轮报告，完成根目录 Make 项目的安全适配、C1 六条 MD 修复与逐边验证、C2/C3 早期拒绝、本地证据和课程服务器复现交付。

**Architecture:** 保留旧请求默认路径，仅当 `e11-b` 请求带合法 `project_compat` 时启用根目录 Make 兼容路径。固定报告字节、目标提交和 A09 来源身份必须在 DRAFT 前校验；验证仍复用现有 scan/patch/DRAFT/BuildChecker 组件，但逐条修复边触碰头文件并记录对象重建，最终同时保存 GCC 与 BuildChecker 实际复检。

**Tech Stack:** Python 3 `unittest`、Git bundle/worktree、GNU Make/GCC、Docker、PowerShell 本地取证、Bash 服务器取证、SHA256。

## Global Constraints

- 个人分支固定为 `student/241880481/e13-e14-b1`；不推送、不创建 PR、不发送外部消息。
- 保留既有工作树修改和证据；每次实验使用新的证据目录，不覆盖旧路径。
- A09 来源固定为 PR #20 head `269827d05d99845a9aca7a8b9f122e9a17a3741a`。
- A09 项目 base/target 固定为 `e825395a5f8006f1c57a115cc25ea5c7802863ee` / `ba688c40d13cd8658e554f7544f1546d35b4b397`。
- `project_compat` 只含 `layout`、`make_test`；不接受任意命令或未知字段。
- 正式兼容请求必须同时提供 `expected_source_report`，精确匹配 job_id、trace_id、URI、SHA256、bytes。
- 报告校验发生在 DRAFT、补丁生成和候选应用之前。
- 原始 target 不写入；修复提交仅在独立克隆中创建，唯一父提交是 A09 target。
- 本地和服务器实际结果分别记录；未运行的服务器结果不得标为通过。

---

### Task 1: 固定材料与基线

**Files:**
- Preserve: `work/e13-b1-a09-fixed-269827d/`
- Create: `work/e13-b1-formal-20261122-121914/materials/`
- Modify: `docs/superpowers/specs/2026-11-22-e13-b1-formal-cross-test-design.md`

**Interfaces:**
- Consumes: A09 固定 Git head、两个交换目录、项目 bundle、检测证据 tar。
- Produces: 来源 head、文件 SHA256/bytes、报告身份、bundle refs/祖先关系和安全解包清单。

- [ ] **Step 1: 核对隔离工作树和基线测试**

运行 `git rev-parse --git-dir`、`git rev-parse --git-common-dir`、`git rev-parse --show-superproject-working-tree`、`git branch --show-current`，确认当前已是指定 linked worktree。运行 `python -m unittest discover -s labs/e11e12 -p "test_*.py"` 与 E13 handoff 测试，保存初始结果。

- [ ] **Step 2: 实算固定材料**

对用户列出的所有文件计算 SHA256 和 bytes；读取 `result.json`、`full-check.json`、`incremental-check.json`，核对 schema、status、base/target、job/trace、stage URI/SHA/bytes。每个 full-check 先确认其 commit，再解释 findings。

- [ ] **Step 3: 安全检查证据 tar 和项目 bundle**

拒绝 tar 中绝对路径、`..`、symlink/hardlink，随后解包到新目录。用 `git bundle verify` 和临时 clone 确认 base/target 存在，且 `git merge-base --is-ancestor BASE TARGET` 返回 0。

- [ ] **Step 4: 修正规格实值并提交文档**

将源报告 bytes 固定为实算的 `3052`，检查规格无占位符、矛盾或额外配置字段，运行 `git diff --check` 后提交规格修正与本计划。

### Task 2: Handoff 来源大小与正式身份校验

**Files:**
- Modify: `labs/e13e14/tests/test_handoff.py`
- Modify: `labs/e13e14/handoff_a_to_b.py`
- Modify: `labs/e11e12/test_contract.py`
- Modify: `labs/e11e12/pipeline.py`

**Interfaces:**
- Produces: `source_report` 包含 `job_id`, `trace_id`, `uri`, `sha256`, `bytes`；`check_source_report(envelope, expected)` 在任何构建前验证精确身份。

- [ ] **Step 1: RED—handoff 保留 bytes**

在 `test_live_a_report_becomes_b_input_with_provenance` 增加字面量断言：`handoff["source_report"]["bytes"] == (root / "incremental-check.json").stat().st_size`。运行该测试，确认因字段缺失失败。

- [ ] **Step 2: GREEN—复制已校验 artifact 大小**

在 `make_handoff` 的 `source_report` 中加入 `"bytes": stage_item["bytes"]`；运行 handoff 全套测试通过。

- [ ] **Step 3: RED—来源身份类型与精确匹配**

在 `test_contract.py` 增加真实字典测试，覆盖：五字段完全匹配接受；缺字段、未知字段、错误 job、非 64 位小写 SHA、非正整数 bytes 均抛出 `Failure` 且 code 为 `SOURCE_REPORT_MISMATCH` 或 `INVALID_REQUEST`。

- [ ] **Step 4: GREEN—实现来源校验**

新增 `check_source_report(envelope, expected)`：要求 expected 为仅含五个规定字段的 dict，验证字符串/URI/SHA/bytes 类型，再与 envelope 的 `source_report` 完全相等；不读取或执行任何命令。

- [ ] **Step 5: 回归旧 handoff 与旧 fixed report**

运行 `labs/e13e14/tests/test_handoff.py` 和 `labs/e11e12/test_contract.py`，确认未提供新兼容配置的旧报告读取行为不变。

### Task 3: 最小 `project_compat` 与构建前拒绝顺序

**Files:**
- Modify: `labs/e11e12/test_contract.py`
- Modify: `labs/e11e12/pipeline.py`

**Interfaces:**
- Produces: `parse_project_compat(request, mode) -> dict | None`；兼容 e11-b 在 snapshot 后、DRAFT 前完成 fixed report、commit/data/source 校验。

- [ ] **Step 1: RED—配置输入校验**

添加表驱动测试：合法 `{layout: root-make, make_test: false}` 被接受；缺字段、未知字段、非 dict、错误 layout、非 bool、非 e11-b 模式，以及缺少 `expected_source_report` 均返回 `INVALID_REQUEST`。

- [ ] **Step 2: GREEN—实现最小解析器**

实现 `parse_project_compat`，只返回复制后的两字段 dict；旧请求返回 `None`。不允许用户提供 build/test/run shell 字符串。

- [ ] **Step 3: RED—错误报告不启动 DRAFT**

以临时 Git fixture 和 mock 的 `auto_build` 边界测试 C2/C3：STALE 或错误字节应生成 FAILED result，但 `auto_build` 未调用，输出中无 `draft-build`、`candidate.patch`、`validation/sandbox`。

- [ ] **Step 4: GREEN—重排 e11-b 正式入口**

在 `execute` 中先解析配置和 snapshot，再加载 fixed report；执行 transfer SHA、envelope target/data commit、来源身份校验，保存 `fixed-md-input.json` 后才调用 DRAFT。普通 e11-b 保持旧验证路径。

- [ ] **Step 5: 根目录结构校验**

扩展 `snapshot` 的内部 profile 参数：`root-make` 只要求根目录存在 `main.c`、`helper.c`、`Makefile`；缺文件返回 `UNSUPPORTED_PROJECT`。默认仍要求既有 `main.c/helper.c/config.h`，避免放宽旧请求。

### Task 4: 根目录 DRAFT 验证与逐修复边重建

**Files:**
- Modify: `labs/e11e12/test_contract.py`
- Create or Modify: `labs/e11e12/test_e13_project_compat.py`
- Modify: `labs/e11e12/pipeline.py`

**Interfaces:**
- Produces: 兼容 e11-b 的 `DraftRuntime`；`validate_in_draft(..., project_profile)` 保存每条 edge 的 dependency、target、before/after mtime、rebuilt、output；最终 `recheck.json` 为实际 GCC 观测。

- [ ] **Step 1: RED—无 make test 且每边验证**

使用临时真实 Make 项目和记录 argv 的 runtime double：断言 `make_test=false` 时从不调用 `make test`；对六个 literal edits 逐项执行 `make app`，每项记录对应 target 重建和输出 `1`。测试必须因当前固定 `extra.h` 逻辑失败。

- [ ] **Step 2: GREEN—通用逐边验证**

将 `validate_in_draft` 的 hardcoded header 分支替换为 profile 驱动：旧 legacy 分支保持 config/output 2；Make profile 可选运行 `make test`，然后对每个 edit 单独 sleep/touch/build/run，保存 `edge-rebuilds.json` 并要求目标对象 mtime 增加。

- [ ] **Step 3: RED—实际复检保留 RD**

构造 6 MD + 1 RD 报告，应用补丁后调用真实 `scan`，断言 MISSING 为空且 `REDUNDANT(main.o, unused.h)` 仍存在。

- [ ] **Step 4: GREEN—兼容 e11-b 使用候选镜像**

DRAFT 成功后为兼容 e11-b 创建 `DraftRuntime`，使用 Make 实际 CFLAGS 扫描；验证和 recheck 均在同一 image ID 下运行。最终 stage 同时引用 `validation/recheck.json`、`edge-rebuilds.json` 和 BuildChecker `findings.json`。

- [ ] **Step 5: 全量单元回归**

运行 E8–E13 相关 unittest、Python compile、旧固定样例契约；如出现行为回归，先写或收紧复现测试再修正。

### Task 5: 正式 C1、C2、C3 与恢复本地实测

**Files:**
- Create: `scripts/e13_b1_formal_common.py`
- Create: `scripts/run_e13_b1_formal_local.ps1`
- Create: `work/e13-b1-formal-20261122-121914/`

**Interfaces:**
- Consumes: 固定材料、适配后 B09 代码、本地 Docker。
- Produces: C1/C2/C3/recovery 新目录、真实退出码、B job/trace、candidate.patch、validation、recheck、无副作用断言。

- [ ] **Step 1: 先保存正常入口失败证据**

用适配前提交或禁用 `project_compat` 的正式请求运行 A09 根项目，保存实际 `UNSUPPORTED_PROJECT`/验证失败，不伪造预期。

- [ ] **Step 2: 生成经校验 handoff 与 C1 请求**

从原始 `result.json` 运行 `handoff_a_to_b.py` 生成新信封，实算 SHA；请求填写 root-make、make_test=false、expected source 五字段、base/target/candidate/output。

- [ ] **Step 3: 执行 C1**

运行正式 `run_e11e12.py run`，保存 console/exit。断言 SUCCEEDED、B job/trace 与 A 来源关联、6 edits、MD=0、RD 保留、6 条逐边重建均为 true、镜像 ID 一致。

- [ ] **Step 4: 创建独立修复提交**

从 bundle 新 clone，detached checkout target 后创建本地证据分支，应用 C1 patch，提交作者使用课程证据身份。断言 `rev-parse HEAD^ == TARGET`，保存 diff、log、status，并生成 Git bundle。

- [ ] **Step 5: 执行 C2**

请求 target 改为 base，报告和正确哈希不变。断言退出 1、`STALE_REPORT`、无 draft 成功、无 patch、无 sandbox、输入 Makefile SHA 不变。

- [ ] **Step 6: 执行 C3**

复制 handoff 并追加一个 LF，沿用原哈希。断言退出 1、`ARTIFACT_HASH_MISMATCH`、无 draft 成功、无 patch、无 sandbox、输入 Makefile SHA 不变；保存原/改后 SHA。

- [ ] **Step 7: 新目录恢复**

使用原始 handoff 字节和正确哈希在全新目录重跑，断言与 C1 相同的成功条件。

### Task 6: 服务器脚本、交付材料与文档

**Files:**
- Create: `docs/students/241880481/e13-e14/run-server-formal-c1-c3.sh`
- Modify: `docs/students/241880481/e13-e14/README.md`
- Modify: `docs/students/241880481/e13-e14/evidence-manifest.sha256`
- Create: `docs/students/241880481/e13-e14/formal/README.md`

**Interfaces:**
- Produces: 可重复服务器脚本、代码 bundle、材料/产物清单、证据包、A09/2号/3号/4号交接草稿与准确传输命令。

- [ ] **Step 1: 编写服务器脚本**

脚本要求仓库根目录和固定材料目录，创建 `work/e13-b1-server-formal-YYYYmmdd-HHMMSS/`；每步使用独立 `.log`/`.exitcode`，C2/C3 预期退出 1但脚本继续，末尾断言汇总和 `FAILURES` 决定脚本退出码。

- [ ] **Step 2: 行为测试服务器脚本**

至少运行 `bash -n`；对共同 Python 断言/材料核验 helper 运行 unittest。若本地有 Bash/Docker，完整 dry run 使用新目录；否则明确记录未执行原因。

- [ ] **Step 3: 生成交付包**

生成 B09 代码 bundle、修复项目 bundle、candidate.patch、validation.json、最终 recheck、manifest JSON/SHA256 和证据 tar.gz；逐项验证 URI 可映射到实际文件且 hash/bytes 相符。

- [ ] **Step 4: 更新学生 README**

记录两方向身份、C1–C3 本地结果、服务器待运行边界、复现说明、给 A09 的回传消息草稿、给 2 号的 C4/C5/C7/C8 成功请求、给 3 号的门禁索引、给 4 号的运行参数。

- [ ] **Step 5: 最终验证**

重新运行完整相关测试、Python compile、`bash -n`、正式证据断言、`git diff --check`、`git status --short`。只根据本轮新鲜输出报告通过项；不推送、不创建 PR。

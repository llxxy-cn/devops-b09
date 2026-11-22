# E13 B1 Formal Cross-Test Design

## Goal

在 B09 现有 E11–E13 链路上消费 A09 固定提交提供的本轮检测报告，完成 A09 根目录 Make 项目的 DRAFT 构建、6 条有效缺失依赖修复、逐边重建验证、实际构建复检，以及正式 C2/C3 拒绝实验；同时保持既有请求行为兼容，并生成可在课程服务器重复执行的证据脚本。

## Fixed Inputs and Boundaries

- A09 材料只从 PR #20 固定 head `269827d05d99845a9aca7a8b9f122e9a17a3741a` 获取。
- A09 项目 bundle SHA256 为 `40510b4c02a05b0ce372ee7870c53ca4d4f32978599e93d8c7ac1b3a2e319072`。
- 项目 base 为 `e825395a5f8006f1c57a115cc25ea5c7802863ee`，target 为 `ba688c40d13cd8658e554f7544f1546d35b4b397`。
- A09 当次报告 job 为 `job-131c4b1d8c34469aaa31f9e2a9da1736`，trace 为 `trace-c224eaab92394b91bedfc2dea14ebc61`。
- B09 生成自己的 job_id/trace_id，并在交接信封和交付记录中保留 A09 来源身份。
- A09 原始项目、target 和报告原件只读保存。补丁应用、构建验证和修复提交均在独立副本进行。
- 本地结果与课程服务器结果分开记录；服务器结果在学生运行脚本并回收证据后再填写。

## Request Compatibility Configuration

正式 `e11-b` 请求增加一个可选对象 `project_compat`。缺少该对象时沿用现有行为。对象只接受以下字段，不接受未知字段：

```json
{
  "project_compat": {
    "layout": "root-make",
    "make_test": false,
    "verify_repaired_headers": true
  }
}
```

- `layout` 必须为 `root-make`，表示项目位于仓库根目录，并使用 Makefile 的显式对象规则和 GCC 实际依赖观测。
- `make_test` 必须为布尔值。本项目为 `false`，因此验证以 `make clean`、`make app` 和 `./app` 输出断言替代不存在的 `make test`。
- `verify_repaired_headers` 必须为 `true`，要求每条修复依赖单独触碰并验证对应对象重建。
- `project_compat` 只允许用于 `e11-b`；其他模式或非法类型、缺字段、未知字段均返回 `INVALID_REQUEST`。
- 不允许请求提供任意 shell 命令，避免扩大执行面。构建与运行命令继续使用代码内已有的固定 argv。

## Processing Order

正式 C1 的处理顺序如下：

1. 解析并校验请求和 `project_compat`。
2. 解析 base/target，确认 target 是固定完整提交；保存输入仓库状态。
3. 在任何 DRAFT 构建前读取 handoff 报告，并校验报告文件声明 SHA256。
4. 校验 handoff schema、kind、status、target commit、data commit，以及 A09 source job_id、trace_id、URI 和源报告 SHA256。
5. 构建 DRAFT 候选镜像并记录不可变 image ID。
6. 复用现有补丁生成器，从经校验的 6 条 MD 生成 `candidate.patch`。
7. 在独立 sandbox 应用补丁，执行 `make clean`、`make app`、`./app`，断言输出为 `1`。
8. 对每条修复边逐一触碰依赖头文件；每次运行 `make app`，确认该边目标 `.o` 的 mtime 增加，并再次断言程序输出为 `1`。
9. 使用同一候选镜像和 GCC 扫描逻辑执行实际依赖复检；全部 6 条 MD 必须消除，RD 原样记录而不自动删除。
10. 仅在验证全部接受后，将 sandbox Makefile 写入独立修复仓库并提交；修复提交的唯一父提交必须为 A09 target。

报告校验必须先于 DRAFT 构建和补丁生成。这样 C2/C3 可证明错误输入未触发候选构建、未生成补丁、未应用补丁。

## C2, C3, and Recovery

- C2 在独立目标副本检出 A09 base，提交有效原始报告及正确文件哈希。入口必须返回 `STALE_REPORT`，且不存在 DRAFT 成功产物、`candidate.patch` 或已应用 Makefile。
- C3 在正确 target 下复制并修改报告字节，沿用原声明哈希。入口必须返回 `ARTIFACT_HASH_MISMATCH`，且不存在 DRAFT 成功产物、`candidate.patch` 或已应用 Makefile。
- 恢复实验必须在新的目录使用原始报告字节和正确哈希重跑，不复用 C2/C3 输出目录。
- 每项保存请求、目标 SHA、报告原/改后 SHA、stdout/stderr、真实退出码、结果 JSON 和负向断言结果。

## Evidence and Deliverables

本地每项实验使用新的时间戳证据根目录，并保存：

- 固定来源、Git head、分支、系统、Docker、镜像 ID 和命令版本；
- 两个交换方向的项目身份、报告来源及所有声明 SHA256 的实算结果；
- 安全解包记录、bundle refs、base/target 存在性和祖先关系；
- C1 请求、handoff、候选补丁、修复计划、逐边重建记录、validation、最终实际依赖 recheck；
- 独立修复仓库的父提交、修复提交、diff 和 Git bundle；
- C2/C3/恢复请求、日志、退出码和无副作用断言；
- 文件清单、SHA256 清单和最终证据压缩包。

服务器脚本不依赖本地绝对路径。它接收或发现上传的代码 bundle 与 A09 固定材料，创建唯一证据目录，每条命令分别保存 `.log` 和 `.exitcode`，失败时保留现场，并在末尾生成断言汇总。上传、执行和下载命令使用明确路径，不覆盖既有服务器证据。

## Testing Strategy

先补充失败测试，再修改生产代码：

- `project_compat` 的合法配置、缺字段、错误类型、未知字段和错误模式；
- 报告哈希、目标提交和来源身份在 DRAFT 调用前拒绝；
- 根目录项目启用实际 Make/GCC 扫描，且不调用 `make test`；
- 每条修复边分别触碰并检查目标对象重建；
- 6 条 MD 消除且 RD 保留；
- 未提供 `project_compat` 的旧请求回归保持不变。

完成后运行相关单元测试、完整 E11/E12/E13 回归、Python 编译检查、`git diff --check`，并用本地 Docker 执行正式 C1–C3。任何本地不具备的能力按实际失败记录，不替代服务器实测。


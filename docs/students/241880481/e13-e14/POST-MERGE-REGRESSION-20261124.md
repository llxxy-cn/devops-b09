# E13 B1 合并后 C1-C3 服务器回归

日期：2026-11-24。负责人：241880481（B1）。结论：**统一 `main` 基线服务器回归通过，`FAILURES=0`**。

本记录是 PR #20 合并后的增量回归，不替换 2026-11-23 A09 已签收的交付提交和回传包。
[A09 签收原文](../../../../evidence/students/241880481/e13-e14/A09-SIGNOFF-20261123.md)、
[签收交付记录](../../../../evidence/students/241880481/e13-e14/A09-SIGNOFF-DELIVERY.md)和
[勘误说明](../../../../evidence/students/241880481/e13-e14/ERRATA-20261123.md)继续固定旧交付字节。

## 固定身份

- 被测统一代码 SHA：`298ff1366cdd2f4314cce625492fa813f484893f`（PR #20 merge commit）。
- A09 项目 base：`e825395a5f8006f1c57a115cc25ea5c7802863ee`。
- A09 项目 target：`ba688c40d13cd8658e554f7544f1546d35b4b397`。
- A09 原始报告：job `job-131c4b1d8c34469aaa31f9e2a9da1736` / trace
  `trace-c224eaab92394b91bedfc2dea14ebc61`，SHA256
  `504a3c505c1479c990f59143926247a2deb7415375de5d957a2d4938aefff224`，3052 字节。
- 课程服务器镜像 ID：
  `sha256:af67372b3894b01f20af6f1560d3a088773f5ecf173be98e247a2facd9292ce6`。
- 传输代码 bundle：SHA256
  `03295a8271c2abf7d99c6fc0e105c4f79a59b4d85e81282bb87ef2c52990d933`，157,015,505 字节。
- 固定 A09 材料包：SHA256
  `d5af6ccf3d7b9dcc5fbe5e77c07cf4b4df663a4239a8621eb93cb98961c5305e`，156,980,832 字节。

两个传输文件在上传前和服务器端均通过 LF `SHA256SUMS` 校验。服务器 `context.log` 记录 detached
HEAD 为上述统一代码 SHA；运行未从网络拉取候选基础镜像。

## C1-C3 与恢复结果

| 场景 | 实际结果 | job / trace |
| --- | --- | --- |
| C1 | `SUCCEEDED`；153 个产物校验；6/6 修复边 `rebuilt=true` 且 `output_matches=true`；最终 MD=0、RD=1（`main.o -> unused.h`） | `job-daf4e29b55a9451caafd13cab4540e44` / `trace-04b7fe4d40944bf1a575f7250d95c091` |
| C2 | 程序退出码 1，`STALE_REPORT`；断言脚本退出 0；没有生成补丁、DRAFT 候选或 sandbox | `job-ef53ff01eaa44c7e952f72703a4a6fcf` / `trace-bae5a7547e7240acb9f8f610da934d6a` |
| C3 | 程序退出码 1，`ARTIFACT_HASH_MISMATCH`；断言脚本退出 0；没有生成补丁、DRAFT 候选或 sandbox | `job-65081bc5b6af4ec4ab9685a29b2a660b` / `trace-1bbe3d7e1e4b4cafbd6d9c04759c0acf` |
| 恢复 | 恢复原始报告字节与正确哈希后在新目录 `SUCCEEDED` | `job-9ecc782bb58347df8db47cc07c153e74` / `trace-2b00d7b1e8cc411f9252987975e3f670` |

C3 使用的原始 handoff SHA256 为
`c19a6b11675b86bd5f2bfe348b3faeb65151b4c57681a54103510f642845e5cf`，追加 LF 后为
`6814315548036342c54479dce1a083bfb104458790a54ed52782931bede1f16d`。C1 生成的独立修复提交为
`7eefa00176b6a718347e94da6a8089f8dc091a88`，其父提交严格为 A09 target
`ba688c40d13cd8658e554f7544f1546d35b4b397`。

## 证据包

- 服务器原始证据目录：
  `/root/devops-b09-e13-b1-post-merge-298ff13/work/e13-b1-server-formal-20261124-101140`。
- 服务器归档：
  `/root/devops-submissions/241880481/e13-b1-server-formal-20261124-101140.tar.gz`。
- 归档 SHA256：`23753210e75b0892663c35e052d7575cd5d00c042ef6ed82c606b9bbdb2abe89`。
- 归档字节数：22,261,646；成员数：1,123。
- 本机回收位置：
  `work/e13-b1-post-merge-298ff13/e13-b1-server-formal-20261124-101140.tar.gz`。
- 解包核验位置：
  `work/server-evidence/post-merge-298ff13/e13-b1-server-formal-20261124-101140/`。

本机复算归档 SHA256/字节数均与服务器输出一致；归档成员检查未发现绝对路径、`..`、链接或设备文件。
解包后的 `deliverables/SHA256SUMS` 在 Linux 下六项全部通过。关键文件哈希列入
[`evidence-manifest.sha256`](evidence-manifest.sha256)。完整证据包因体积保留在课程服务器和本机忽略目录，
不提交到 Git。

## 给 B3 的最终门禁输入

- C1-C3：在统一 SHA `298ff136...484893f` 上通过；总断言 `FAILURES=0`，脚本 `RUN_RC=0`。
- C1：153 个产物、6/6 边、MD=0、RD=1；修复提交父节点与 A09 target 一致。
- C2/C3：分别为 `STALE_REPORT` / `ARTIFACT_HASH_MISMATCH`，均在 DRAFT 前拒绝且无补丁。
- 恢复：新 job/trace 成功，与 C1 job/trace 分离。
- A09 签收：仍关联 2026-11-23 固定交付提交
  `cbf90cce6fcb4950c6326704bd970f9ed80693bb` 和固定包 SHA256
  `1a1419b6359448b7e39033899d287ed85fd44d0ca054299e238cc55d1645ba33`；本次回归不覆盖签收对象。

## 给 A09 的补充核验消息

> B09 B1 已在 PR #20 合并后的统一代码 SHA `298ff136...484893f` 上复跑 A09 固定项目和原始报告。
> C1 成功，153 个产物与 6/6 修复边通过，最终 MD=0、RD=1；C2/C3 分别按预期以
> `STALE_REPORT` 和 `ARTIFACT_HASH_MISMATCH` 在 DRAFT 前拒绝且无补丁；恢复任务成功。
> 本次证据包 SHA256 为 `23753210...abe89`，是合并后补充回归，不改变你方 2026-11-23 已签收的
> 原交付包。请确认是否还需要对本补充回归进行额外核验。

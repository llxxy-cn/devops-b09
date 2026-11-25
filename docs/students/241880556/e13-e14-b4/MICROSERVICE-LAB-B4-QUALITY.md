# Microservice Lab：B4 容错与质量核对

核对日期：2026-11-25。负责人：B4（241880556）。本章按实际被测提交、项目和任务身份引用证据，不将不同轮次写成一次实验。B1 正常五阶段任务的完整说明见 [最终实验记录](MICROSERVICE-LAB-FINAL.md)。

## 实测身份与证据矩阵

| 场景 | 运行代码与项目 | job_id / trace_id | 结果与证据 |
| --- | --- | --- | --- |
| B1 本轮正常链路 | `v0.9-rc` → `5338183c7178122476b84c65b6a7010ca6598a61`；B09 `fixtures/e11e12-b1-real` | `job-5cdec29e61bf4f629ace6a5dce190ad2` / `trace-21ce7e7b872f42baa177362e1571e61a` | `SUCCEEDED`；五阶段、180 项产物、补丁与最终空 findings 均核验通过。[结果](evidence/microservice-lab-v0.9-rc/result.json)、[独立复核](evidence/microservice-lab-v0.9-rc/verified.json)。 |
| B3 监控正常阶段 | `cad9b1bee2a9e2633e4af1cad42a8b6a3d3a858b`；同一 B09 项目 | `job-7e963debfd474e0ebad8523366eed562` / `trace-5d76adacfb4c43cf9f1e3307852efee2` | `SUCCEEDED`；四服务日志关联，180 项产物校验。[B3 报告](https://github.com/llxxy-cn/devops-b09/blob/student/241880585/microservice-observability/docs/students/241880585/microservice/%E5%8F%AF%E8%A7%82%E6%B5%8B%E6%80%A7%E6%8A%A5%E5%91%8A.md)。 |
| B3 停止 EChecker | 同上；停止本次 Compose 项目中实际参与调用的 `echecker` | `job-1fb28b45301246dc9ffbf5320c76abea` / `trace-dccbe4545b77421b96dbd257b86206b0` | `FAILED`；任务从 06:12:36 到 06:12:52 UTC，错误为连接拒绝。Prometheus 在 06:12:51、06:12:56 UTC 保存 `echecker up=0`。见 [故障结果](https://github.com/llxxy-cn/devops-b09/blob/student/241880585/microservice-observability/docs/students/241880585/microservice/evidence/fault/result.json)、[原始查询](https://github.com/llxxy-cn/devops-b09/blob/student/241880585/microservice-observability/docs/students/241880585/microservice/evidence/observability-export/fault/availability.json)。 |
| B3 恢复后新任务 | 同上；EChecker 恢复后 | `job-cd3d2ea68e344dc99f430274e3fe099f` / `trace-2ecce735912845a6a1485bb03a1584d4` | `SUCCEEDED`；四服务日志关联、180 项产物校验；四个 Prometheus 目标恢复为 up。见 [三阶段摘要](https://github.com/llxxy-cn/devops-b09/blob/student/241880585/microservice-observability/docs/students/241880585/microservice/evidence/observability-export/three-phase-summary.json)。 |
| B4 既有构建超时与恢复 | `72fd0b7b4bf354c60be3389c9bf2777966ce1b9e`；A09 项目 | 失败 `job-1cb8bc0c7dd3421fb0696eaf8582adf6` / `trace-e4b9fcfb771342b1b15bce0fb5af7238`；恢复 `job-16ff370858764e31b09bb2ea0ba02854` | DRAFT 在 `build_timeout=0.01` 下返回 HTTP 422、`error_code=TIMEOUT`；外层终态 `FAILED`，新任务成功，超时构建容器无残留。[失败复核](evidence/final-72fd0b7/verified-failures.json)。 |
| B4 既有服务中断与恢复 | 同一 `72fd0b7…`；B09 项目 | 失败 `job-420a385eb00543d89891769b956fee3f` / `trace-a375f758999e4537aa09c260ab16d800`；恢复 `job-7a6ac41a00b744c1b1835bd971206bc9` | EChecker 中断后任务因连接拒绝进入 `FAILED`，恢复健康后新任务成功；失败任务无候选补丁。[最终验收](FINAL-ACCEPTANCE-72fd0b7.md)。 |
| B2 既有超时、错误补丁、幂等 | `298ff1366cdd2f4314cce625492fa813f484893f`；A09 项目 | C4 `job-581481c504dc41d6b6f92f7b0ecda00e`；C7 `job-27f57e8a40914a2f9b9ef29adb20ec2a`；C8 `job-c8ada5349d3247a4aced3b35b9307904` | C4 超时终态、C5 错误补丁拒绝且源仓库未变、C7 新任务成功、C8 相同输入复用同一 job 且不同输入返回 409。属于 E13 专项复跑。[测试报告](../../241880359/e13-b2-recheck-298ff136/TEST_REPORT.md)、[幂等摘要](../../241880359/e13-b2-recheck-298ff136/c8-http/summary.json)、[源仓库完整性](../../241880359/e13-b2-recheck-298ff136/c5-case/source-integrity.json)。 |

## 容错结论与边界

B3 的监控轮次证明真实下游 EChecker 停机后，编排任务在 16 秒内进入明确的 `FAILED` 终态；恢复后的新 job 成功。故障发生在请求抵达 EChecker 之前，因此 EChecker 的服务调用失败计数不应被写成该任务的失败数。判断依赖端到端 `result.json`、调用方日志和 Prometheus `up`。B3 的故障截图时间窗口较宽，短暂的下降点不够清晰；报告引用上述 5 秒步长的原始查询，并宜补一张更窄窗口的 Grafana 截图。

`v0.9-rc` 与 B3 实测时的 `labs/e13e14/orchestrate.py` 没有有限重试；停机导致的外层 `result.json` 仅保存连接拒绝字符串，没有规范化 `error_code`。因此现有 B3 三阶段记录**不能**证明“有限重试与统一错误码”已经通过。`TIMEOUT` 错误码和幂等复用分别由上表所列旧轮次证明，也不能写成 B3 监控提交上的新实测。

B4 已在本分支准备有界重试补丁：只对连接被拒绝和 HTTP 503 `SERVICE_BUSY` 最多尝试 3 次，记录每次尝试的 UTC 时间与结果；已送达下游但结果不确定的超时不自动重试。失败结果增加 `error_code`、`failed_service` 和 `attempt_count`。四个针对性测试通过，覆盖恢复、重试耗尽、503 重试而 422 `TIMEOUT` 不重试，以及失败时 `result.json` 进入终态。**该补丁尚未在课程服务器部署或完成真实项目复测**，不能作为上述三阶段实测的结论。下一轮应固定合并后的完整提交，在独立目录执行停机、超时、恢复和错误补丁任务，保存请求、重试记录、终态、job/trace 与源仓库前后状态。

## B3 PR #27 审查记录

[PR #27](https://github.com/llxxy-cn/devops-b09/pull/27) 的交付提交为 `245778363362c5016a58e7a2ea488035ff49768d`，实测部署提交为 `cad9b1bee2a9e2633e4af1cad42a8b6a3d3a858b`。B4 核对了四服务指标代码、Compose、Prometheus、Grafana、取证脚本、三阶段结果与截图；在该 PR 的独立工作树运行 `python -m unittest discover -s tests -p test_metrics_http.py -v`，两项测试通过，`git diff --check` 无错误，五类 PR CI 均成功。故障原始查询含两个连续 `up=0` 样本，恢复后四目标均 up。

截至本次核对，PR #27 仍未合入 `main`，因此本章不将其写成已合并。B4 未在课程服务器重跑 B3 场景或重新计算 B1/B3 完整包哈希。B1 包的已归档哈希为 `2ffd7c1391f1b7297ee846d3e854e4a7820cebc13b16f25ef27d9560d22c637e`；B3 包索引声明的哈希为 `2dfe80765cdf6ab24833188c22d7edb045cc1a4b75ad5e09b8b23e5a972cb918`，最终提交前须从完整包独立核对。

## 完整包核对

| 材料 | 大小与 SHA256 | 本次核对状态 |
| --- | --- | --- |
| B1 正常任务包：`/root/devops-submissions/241880481/e14-microservice-b1-b09-v09rc-20261124-01.tar.gz` | 4,959,089 字节；`2ffd7c1391f1b7297ee846d3e854e4a7820cebc13b16f25ef27d9560d22c637e` | 原 B4 记录称服务器重算一致；本次无法访问服务器重新核对。 |
| [B2 专项包](../../../../evidence/students/241880359/e13-b2-recheck-298ff136/b09-e13-b2-recheck-298ff136-20261124-105225.tar.gz) | 15,620,441 字节；`e7e4a3bebe62e3e8306a548a033831e3121edb8bd0919886ad4e6688824a00d6` | 本机重新计算大小和 SHA256 一致。 |
| B3 监控包：`/root/devops-submissions/241880585/B3-Microservice-Monitoring-20261125-151724.tar.gz` | 22,837,079 字节；`2dfe80765cdf6ab24833188c22d7edb045cc1a4b75ad5e09b8b23e5a972cb918` | B3 包索引声明已校验；本次未取得原包。 |
| B4 先前四服务验收包：`D:\\devops\\e14-b4-final-main-72fd0b7-20261124.tar.gz` | 36,338,750 字节；`8e5658420fb052ef7072038f142296a38cf423970431f4f514b30d4f0a30efb7` | 本机重新计算大小和 SHA256 一致。 |

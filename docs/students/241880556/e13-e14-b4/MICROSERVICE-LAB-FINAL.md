# Microservice Lab 最终实验记录：B09 真实项目

日期：2026-11-24。B4（241880556）固定四服务部署与运行身份；B1（241880481）在该环境执行 B09 真实项目正常任务并交付原始证据。本记录用于期末报告索引，保留各自职责和实际被测版本。

## 版本、部署与输入

| 项目 | 固定值 |
| --- | --- |
| 代码仓库与版本 | `llxxy-cn/devops-b09`，注释标签 `v0.9-rc`，目标提交 `5338183c7178122476b84c65b6a7010ca6598a61` |
| 服务器检出 | `/root/241880556/devops-b09-microservice-v0.9-rc`；运行前及 B1 交付后核对 HEAD 均为标签目标 |
| Compose | `labs/e13e14/compose.yaml`；项目名 `b09-ms-rc-5338183` |
| 四服务镜像 | 本地课程镜像别名 `course-e11e12:e14-rc-5338183-b4`，ID `sha256:b6eb148da0a6248be7410d5faea4f7f22945f10cccea8f72e66ab5d51809be3b`；四服务 Python 源码由标签检出挂载 |
| B09 项目 | 仓库内 `fixtures/e11e12-b1-real`；Base `30ffe4c41492334478a2446a8be0662d3f31d478`，Target `a7e3b644ca9b1b9d0b26bd41e839fcbf5ea1c293` |
| 候选与验证 | `data/e14-b4-b09/candidate.Dockerfile`，SHA256 `1fa4739abd325c84e0ed4b3bbdcbcaf39c7c500fc0d80ba4707216e5cbe21a64`；`make clean && make && make test && ./app`，预期输出 `hello E3`、退出码 0 |

四服务在 B1 运行前经 Compose 和健康接口核对为 healthy。宿主回环健康地址依次为 BuildChecker `127.0.0.1:18581/health`、EChecker `:18582/health`、DRAFT `:18583/health`、MDFixer `:18584/health`。四服务均接受 `POST /v1/run`，完整任务由宿主机 `labs/e13e14/orchestrate.py` 编排。当前四服务的 `/metrics` 实测返回 HTTP 404；监控指标由 B3 单独归档。

## B1 本轮实测

B1 使用固定请求运行 `work/microservice-handoff-20261124/run-b09-real.sh v09rc-20261124-01`。请求副本见 [request.json](evidence/microservice-lab-v0.9-rc/request.json)。本轮独立于此前 A09 跨组签收和 B4 在 `72fd0b7…` 的 E14 验收任务。

| 核验项 | 本轮结果 |
| --- | --- |
| job_id / trace_id | `job-5cdec29e61bf4f629ace6a5dce190ad2` / `trace-21ce7e7b872f42baa177362e1571e61a` |
| 终态与阶段 | `SUCCEEDED`；`draft → full-check → incremental-check → repair → recheck` 五阶段 |
| 产物 | 180 项；`verify_e14.py` 对存在性、字节数和 SHA256 逐项核验通过；B1 总断言 `FAILURES=0`，运行退出码 0 |
| 修复 | [candidate.patch](evidence/microservice-lab-v0.9-rc/candidate.patch) SHA256 `6fb5dc4d84f5d65bcf7edffae3b7e02acb2259676be2154a1fc947463ee75c69`；[validation.json](evidence/microservice-lab-v0.9-rc/validation.json) SHA256 `531ff8b844267ec0401824398c41097cb6a2943051ace2b9cd81066af13b0371`，确认 `main.o → extra.h` 修复边重建、`make test` 与程序输出 `hello E3` 通过 |
| 复验 | `recheck` 状态 `SUCCEEDED`，`remaining_missing=0`；[最终 findings](evidence/microservice-lab-v0.9-rc/final-findings.json) 为 `[]`；clean 与 build 退出码均为 0 |
| 扫描 | 171 个运行证据文本，`hits=0`、`errors=0`；B1 报告 `SENSITIVE_HITS=0` |

独立复核输出见 [verified.json](evidence/microservice-lab-v0.9-rc/verified.json)，其确认 Base/Target、job/trace、180 个产物、1 条重建边、最终空 findings 及补丁哈希。完整五阶段信封和产物清单见 [result.json](evidence/microservice-lab-v0.9-rc/result.json)；[扫描日志](evidence/microservice-lab-v0.9-rc/scan.log)和 [Compose 状态](evidence/microservice-lab-v0.9-rc/compose-ps.log)一并留档。

## 原始证据与复核入口

- B1 服务器运行目录：`/root/241880556/devops-b09-microservice-v0.9-rc/work/microservice-b1-b09-v09rc-20261124-01`。五阶段报告、补丁、验证、构建 trace、复检和日志均保留在此。
- B1 完整证据包：`/root/devops-submissions/241880481/e14-microservice-b1-b09-v09rc-20261124-01.tar.gz`，4,959,089 字节，SHA256 `2ffd7c1391f1b7297ee846d3e854e4a7820cebc13b16f25ef27d9560d22c637e`。B4 在服务器重新计算了大小和 SHA256，结果一致。
- B4 在标签检出上重新执行 `python3 labs/e13e14/verify_e14.py work/microservice-b1-b09-v09rc-20261124-01`，得到 [verified.json](evidence/microservice-lab-v0.9-rc/verified.json) 所列结果。仓库中的精简索引文件从该服务器运行目录原样取回，不替换 B1 的完整包。

本轮记录覆盖正常真实项目任务。故障、恢复与幂等场景由 B2 的记录说明，监控材料由 B3 提供；A09 原签收仍作为 E13 历史证据引用。

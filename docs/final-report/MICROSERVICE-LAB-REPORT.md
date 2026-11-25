# B09 Microservice Lab 期末项目报告

**项目组**：B09　　**日期**：2026 年 11 月 25 日

**组员**：B1 刘欣雨（241880481）；B2 黄新迪（241880359）；B3 丁卓（241880585）；B4 韩尚真（241880556）。

<!-- pagebreak -->

## 1. 项目概述

B09 项目以真实 Git 仓库中的缺失依赖为实验对象，将构建检查、增量检查、修复和复验拆为四个业务服务：DRAFT、BuildChecker、EChecker、MDFixer。实验目标是让服务通过 Docker Compose 可复现运行，并在真实项目任务、监控、下游故障、恢复和错误补丁等场景中留下可核对的结果。五阶段由编排脚本依次发起：DRAFT → BuildChecker 完整构建 → EChecker 增量检查 → MDFixer 修复 → BuildChecker 重新构建与复验。

本轮使用 B09 仓库 `https://github.com/llxxy-cn/devops-b09` 的 `fixtures/e11e12-b1-real`。Base 为 `30ffe4c41492334478a2446a8be0662d3f31d478`，Target 为 `a7e3b644ca9b1b9d0b26bd41e839fcbf5ea1c293`。原问题是 Makefile 未声明 `main.o → extra.h` 依赖，导致头文件变化后增量构建没有正确重建。验证条件为 `make clean && make && make test && ./app`，预期程序输出 `hello E3` 且退出码为 0。[E1]

系统验证覆盖真实项目五阶段运行、四服务监控、下游停机与恢复、超时处理、错误补丁拒绝和任务 API 幂等。各场景的代码提交、项目、任务标识及证据分别记录；具体运行身份见第 3 节。[E1–E4]

<!-- pagebreak -->

## 2. 系统架构与部署编排

四个业务服务通过 Docker Compose 部署，均提供 `POST /v1/run` 与 `/health`。宿主机编排脚本 `labs/e13e14/orchestrate.py` 提交阶段请求，收集任务信封、阶段报告和产物。DRAFT 使用固定候选 Dockerfile 构建隔离环境；BuildChecker 执行完整构建和最终复验；EChecker 比对 Base/Target 的增量依赖；MDFixer 生成并验证 Makefile 补丁。服务间通过 Compose 内部服务名通信，阶段结果以 job_id、trace_id 关联。[E1]

B1 的 `v0.9-rc` 标签环境为 Compose 项目 `b09-ms-rc-5338183`，配置文件 `labs/e13e14/compose.yaml`。四服务的宿主回环健康端口依次为 BuildChecker 18581、EChecker 18582、DRAFT 18583、MDFixer 18584；容器内均监听 8080。Compose 配置对四服务设置 `/health` 检查、CPU/内存/PID 限额和内部网络访问。运行镜像别名为 `course-e11e12:e14-rc-5338183-b4`，镜像 ID 为 `sha256:b6eb148da0a6248be7410d5faea4f7f22945f10cccea8f72e66ab5d51809be3b`，服务源码由对应检出挂载。[E1]

B3 的监控轮次使用独立项目 `b09-ms-b3-241880585` 和 `labs/observability/compose.yaml`，在四业务服务之外启动 Prometheus v3.5.0 与 Grafana 12.3.0。四业务端口为 18681–18684，Prometheus 为 19190，Grafana 为 13100，均绑定宿主回环。Prometheus 通过 Compose 内部服务名抓取四个 `/metrics`，Grafana 数据源使用 `http://prometheus:9090`。B3 保存 Compose 状态、镜像 ID 与 digest、Targets 响应和面板导出。[E3]

B3 在后续提交中为四业务服务接入 `/metrics`；B4 的容错轮次继承该实现，四服务 `/health` 和 `/metrics` 均返回 200。各轮部署与代码身份见第 3 节。[E3、E4]

<!-- pagebreak -->

## 3. DevOps 实践与版本身份

仓库以 Git 提交固定输入、实现和文档，Compose 固定服务拓扑，CI 检查构建、质量及安全门禁。`v0.9-rc` 注释标签指向 `5338183c7178122476b84c65b6a7010ca6598a61`；标签目标的 E7、E8–E10、E11–E12、E13 安全门禁和 E13–E14 集成五类 CI 均成功。后续监控与容错功能在独立提交上实现和验证。[E1、E4]

| 责任与场景 | 实际被测代码提交 | 项目与范围 |
| --- | --- | --- |
| B1 正常五阶段 | `5338183c7178122476b84c65b6a7010ca6598a61`（`v0.9-rc`） | B09 真实项目；180 项产物 |
| B2 E13 专项 | `298ff1366cdd2f4314cce625492fa813f484893f` | A09 项目；超时、错误补丁、恢复、API 幂等 |
| B3 监控三阶段 | `cad9b1bee2a9e2633e4af1cad42a8b6a3d3a858b` | B09 真实项目；四服务指标、Prometheus、Grafana |
| B4 容错复测 | `38132ae89492d58f9dbf934a2310b7e91cc53d01` | B09 真实项目；有限重试、超时、恢复与错误补丁 |

B3 PR #27 的合并提交为 `90d77a983074996482da7a634c61bafecb588fcc`；B4 PR #28 的合并提交为 `c02ccd1c7bcd4e0dcd19a00ad704a09019bea8fd`。B4 的 12 项 CI、四项重试测试和两项 HTTP 指标测试均通过。[E3、E4]

部署和取证采用独立 Compose 项目及工作目录。请求、镜像、阶段报告、补丁、最终复验和完整证据包均有哈希记录；源仓库与验证工作树的前后状态另行保存。[E1–E4]

<!-- pagebreak -->

## 4. B09 真实项目五阶段系统集成

B1 在 `v0.9-rc` 标签上执行真实项目任务。候选 Dockerfile SHA256 为 `1fa4739abd325c84e0ed4b3bbdcbcaf39c7c500fc0d80ba4707216e5cbe21a64`。任务 `job-5cdec29e61bf4f629ace6a5dce190ad2`、追踪 `trace-21ce7e7b872f42baa177362e1571e61a`，终态为 `SUCCEEDED`。五阶段均有独立报告；脚本断言 `FAILURES=0`，180 项产物的存在性、大小与 SHA256 逐项核验通过。[E1]

增量检查定位 `main.o → extra.h` 缺失边，MDFixer 生成 `candidate.patch`，SHA256 为 `6fb5dc4d84f5d65bcf7edffae3b7e02acb2259676be2154a1fc947463ee75c69`。补丁验证确认依赖边触发重建，`make test` 与 `./app` 成功，输出 `hello E3`。复验记录 `remaining_missing=0`、最终 `findings=[]`，clean 和 build 退出码均为 0；B4 使用 `verify_e14.py` 独立核对产物。[E1]

<!-- pagebreak -->

## 5. 可观测性与关联日志

B3 在四业务进程直接实现 `/metrics`：调用接收数、按成功/失败区分的完成数、处理中数量和耗时直方图。Prometheus 每 5 秒抓取四目标；Grafana 八面板展示可用性、接收量、结果分类、处理中、成功增量、失败增量、P95 和平均耗时。实际 PromQL 与面板 JSON 均已归档。指标标签只使用 role、status 等低基数值；job_id 与 trace_id 保存在带 UTC 时间、状态、错误码和耗时的结构化日志。[E3]

| 阶段 | B3 job_id / trace_id | 终态与监控证据 |
| --- | --- | --- |
| 正常 | `job-7e963debfd474e0ebad8523366eed562` / `trace-5d76adacfb4c43cf9f1e3307852efee2` | `SUCCEEDED`；四服务日志关联，180 项产物核验 |
| EChecker 停机 | `job-1fb28b45301246dc9ffbf5320c76abea` / `trace-dccbe4545b77421b96dbd257b86206b0` | `FAILED`；06:12:51 与 06:12:56 UTC 两个 `up=0` 原始样本 |
| 恢复 | `job-cd3d2ea68e344dc99f430274e3fe099f` / `trace-2ecce735912845a6a1485bb03a1584d4` | `SUCCEEDED`；四目标恢复，180 项产物核验 |

端到端终态以编排器 `result.json` 为准。EChecker 停机时，连接拒绝发生在服务入口之外；调用方日志、任务终态与 Prometheus `up=0` 联合定位故障。计数器重置由 `increase` 和 `rate` 查询处理。[E3]

B3 保存了正常、故障、恢复及全程共八张 Grafana 截图，另有 Targets 响应、原始查询、面板导出和按 job/trace 关联的日志。停机时间由两个原始 `up=0` 样本确定。完整包为 22,837,079 字节，SHA256 `2dfe80765cdf6ab24833188c22d7edb045cc1a4b75ad5e09b8b23e5a972cb918`。[E3]

<!-- pagebreak -->

## 6. 容错、恢复与质量验证

B4 在 `38132ae…` 的独立项目中停止任务实际调用的 EChecker。任务为 `job-d8724483fcd044669aeda43b5c82df19`，追踪为 `trace-09453223548e4f59b7d4cef494fc0d01`。三次连接拒绝后，任务约四秒内进入 `FAILED`；错误码为 `DOWNSTREAM_UNAVAILABLE`，失败服务为 `echecker`，尝试次数为 3。连接拒绝与 HTTP 503 `SERVICE_BUSY` 采用最多三次的有界重试，每次尝试均保存 UTC 时间及结果。[E4]

以 `build_timeout=0.01` 触发 DRAFT 超时。任务 `job-998a0fad3c024edf932b90d3d3dd4485`、追踪 `trace-f862ecb5c1c4437c9cb9a1fe9720a2e5` 返回 HTTP 422 和 `TIMEOUT`。任务终态为 `FAILED`，尝试次数为 1。超时请求只提交一次。服务恢复健康后，新任务 `job-4cac1194352348d4bb3714ae5fcb817e`、追踪 `trace-04b597c31eea48f18b9454e44f7cf566` 完成五阶段，186 项产物核验通过，最终 findings 为空。[E4]

错误补丁实验向 E14 `validate_repair` 提交与目标 Makefile 不匹配的补丁，结果为 `accepted=false`、`rollback=true`、`source_unchanged=true`；目标 Makefile 的前后 SHA256、源仓库 HEAD 和工作区状态一致。B2 在提交 `298ff136…` 的 A09 项目上验证 E13 任务 API 幂等：相同输入复用同一 job，冲突输入返回 409，任务记录仅创建一次。[E2、E4]

B4 本轮四项重试测试、两项 HTTP 指标测试通过；服务健康与指标响应均为 200。运行证据扫描 1,179 个文本，`hits=0/errors=0`。完整包为 19,366,265 字节，SHA256 `3ef9eb5e1c8da342c0d021e9a14de4ba6b39a3943527eb8ec87f1728e19936fd`；服务器清单 1,739 项和本机包哈希均核验通过。[E4]

<!-- pagebreak -->

## 7. 问题定位与工程改进

B3 为四服务增加指标端点与独立的 Prometheus/Grafana 部署。针对长时间业务执行对 HTTP 入口的占用，B3 将入口改为线程化处理，并使用非阻塞锁保护业务执行；并发繁忙请求以 503 `SERVICE_BUSY` 返回。健康检查与指标抓取在任务执行期间仍可响应。[E3]

停机取证显示 EChecker 连接拒绝与任务失败相对应。B4 在此基础上加入最多三次的有界重试及 `error_code`、`failed_service`、`attempt_count` 字段，使调用方日志、任务终态与重试轨迹形成一致的故障记录。超时场景保留单次尝试。[E3、E4]

`/metrics` 统计单次业务调用，编排器 `result.json` 统计完整任务。团队使用 job/trace、调用方日志和 Prometheus 原始样本联合定位服务不可达；两个 `up=0` 样本给出停机时点。[E3]

部署中的镜像来源、端口占用和换行格式问题通过固定镜像身份、独立端口、CI 修正及格式检查解决。各轮原始提交和运行证据保持可追溯。[E1–E4]

<!-- pagebreak -->

## 8. 成员贡献、复现与交付

| 成员 | 主要贡献与可核对产物 |
| --- | --- |
| B1 刘欣雨（241880481） | 固定 B09 Base/Target 和候选 Dockerfile；在标签环境执行真实项目五阶段，保存请求、job/trace、补丁、复验与完整证据包。 |
| B2 黄新迪（241880359） | 整理部署与复现材料；在 E13 统一基线上复跑超时、错误补丁、恢复和任务 API 幂等，保存请求、日志与源仓库完整性。 |
| B3 丁卓（241880585） | 实现四服务指标、Prometheus/Grafana 配置与 PromQL；完成正常、停机、恢复三阶段监控取证、关联日志及八张截图。 |
| B4 韩尚真（241880556） | 固定标签环境与证据索引；审查 B3 PR；实现有界重试和错误字段；复测停机、超时、恢复和错误补丁，整理本报告与提交包。 |

复现从第 3 节指定的代码提交开始。设置 `E14_ROOT` 为检出目录绝对路径、`E14_IMAGE` 为对应镜像后，运行 `docker compose -f labs/e13e14/compose.yaml -p <项目名> config --quiet` 与 `up -d --wait`，核对四服务 `/health`。监控实验使用 `labs/observability/compose.yaml` 启动四服务、Prometheus 和 Grafana，检查四个 Targets 与八个面板。真实任务请求、候选 Dockerfile、编排参数和 `verify_e14.py` 核验记录均见完整证据包。[E1、E3]

交付包包含本报告 PDF、项目源码快照、`AI_USAGE.md`、四人完整证据包及 SHA256 清单。源码提交由 `SOURCE-REVISION.txt` 标明，`MANIFEST.sha256` 对交付文件逐项校验。演示使用健康检查、Targets、正常任务结果和故障恢复记录；截图与原始日志提供相同任务的复核路径。[E1–E4]

<!-- pagebreak -->

## 附录：证据索引

E1　B1 五阶段记录：`docs/students/241880556/e13-e14-b4/MICROSERVICE-LAB-FINAL.md`；完整包：`e14-microservice-b1-b09-v09rc-20261124-01.tar.gz`，4,959,089 字节，SHA256：`2ffd7c1391f1b7297ee846d3e854e4a7820cebc13b16f25ef27d9560d22c637e`。

E2　B2 E13 专项记录：`docs/students/241880359/e13-b2-recheck-298ff136/TEST_REPORT.md`；完整包：`b09-e13-b2-recheck-298ff136-20261124-105225.tar.gz`。

E3　B3 监控记录：`docs/students/241880585/microservice/可观测性报告.md`；截图与原始查询位于同目录 `evidence/`；完整包：`B3-Microservice-Monitoring-20261125-151724.tar.gz`。

E4　B4 容错记录：`docs/students/241880556/e13-e14-b4/MICROSERVICE-LAB-B4-QUALITY.md`；完整包：`e14-b4-quality-38132ae-20261125.tar.gz`。

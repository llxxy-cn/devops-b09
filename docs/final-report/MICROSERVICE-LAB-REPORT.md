# B09 Microservice Lab 期末项目报告

**课程**：DevOps　　**提交日期**：2026 年 11 月 25 日　　**截止日期**：2026 年 12 月 1 日

**组员**：B1 刘欣雨（241880481）；B2 黄新迪（241880359）；B3 丁卓（241880585）；B4 韩尚真（241880556）。

> 正文共八节。证据编号见附录；各节所述运行以表中的实际被测提交为准。`main` 的归档提交和 `v0.9-rc` 标签均不能替代单轮实测身份。

<!-- pagebreak -->

## 1. 项目概述与验收范围

B09 项目以真实 Git 仓库中的缺失依赖为实验对象，将构建检查、增量检查、修复和复验拆为四个业务服务：DRAFT、BuildChecker、EChecker、MDFixer。实验目标是让服务通过 Docker Compose 可复现运行，并在真实项目任务、监控、下游故障、恢复和错误补丁等场景中留下可核对的结果。五阶段由编排脚本依次发起：DRAFT → BuildChecker 完整构建 → EChecker 增量检查 → MDFixer 修复 → BuildChecker 重新构建与复验。

本轮使用 B09 仓库 `https://github.com/llxxy-cn/devops-b09` 的 `fixtures/e11e12-b1-real`。Base 为 `30ffe4c41492334478a2446a8be0662d3f31d478`，Target 为 `a7e3b644ca9b1b9d0b26bd41e839fcbf5ea1c293`。原问题是 Makefile 未声明 `main.o → extra.h` 依赖，导致头文件变化后增量构建没有正确重建。验证条件为 `make clean && make && make test && ./app`，预期程序输出 `hello E3` 且退出码为 0。[E1]

本报告的“通过”限定为已有证据支持的结论。B1 在 `v0.9-rc` 标签目标上证明正常五阶段；B3 在扩展监控的独立提交上证明三阶段可观测；B4 在合并监控后的独立提交上证明有限重试、明确终态与错误补丁拒绝；B2 在较早的 E13 统一基线上证明任务 API 幂等。四轮共享课程目标，但不是同一份运行记录。[E1–E4]

验收口径包括：Compose 服务与健康检查；四服务指标抓取及 Grafana 面板；同一任务内 job_id、trace_id 的跨服务关联；失败任务在有限时间内进入终态；恢复后新任务成功；补丁与源码完整性；提交、镜像、请求、产物和证据包哈希可追溯。A09 跨组签收及 C1–C3 仅作为此前 E13 历史证据，不计入本轮真实项目任务。

<!-- pagebreak -->

## 2. 系统架构与部署编排

四业务服务以独立进程和 Compose 服务名运行，均提供 `POST /v1/run` 与 `/health`。宿主机编排脚本 `labs/e13e14/orchestrate.py` 提交阶段请求，收集任务信封、阶段报告和产物。DRAFT 使用固定候选 Dockerfile 构建隔离环境；BuildChecker 执行完整构建和最终复验；EChecker 比对 Base/Target 的增量依赖；MDFixer 生成并验证 Makefile 补丁。阶段结果以 job_id、trace_id 关联，产物置于该 job 独立目录。[E1]

B1 的 `v0.9-rc` 标签环境为 Compose 项目 `b09-ms-rc-5338183`，配置文件 `labs/e13e14/compose.yaml`。四服务的宿主回环健康端口依次为 BuildChecker 18581、EChecker 18582、DRAFT 18583、MDFixer 18584；容器内均监听 8080。Compose 配置对四服务设置 `/health` 检查、CPU/内存/PID 限额和内部网络访问。四服务共用课程镜像别名 `course-e11e12:e14-rc-5338183-b4`，镜像 ID 为 `sha256:b6eb148da0a6248be7410d5faea4f7f22945f10cccea8f72e66ab5d51809be3b`，服务源码由对应检出挂载，因此记录镜像和代码提交两种身份。[E1]

B3 的监控轮次使用独立项目 `b09-ms-b3-241880585` 和 `labs/observability/compose.yaml`，在四业务服务之外启动 Prometheus v3.5.0 与 Grafana 12.3.0。四业务端口为 18681–18684，Prometheus 为 19190，Grafana 为 13100，均绑定宿主回环。Prometheus 通过 Compose 内部服务名抓取四个 `/metrics`，Grafana 数据源使用 `http://prometheus:9090`。B3 保存 Compose 状态、镜像 ID 与 digest、Targets 响应和面板导出。[E3]

标签 `v0.9-rc` 的四业务 `/metrics` 曾返回 404；指标接入由 B3 的后续代码提交提供。不能把 B3 指标写成 B1 标签环境本身已有的能力。B4 新质量轮次继承指标实现，在 `38132ae…` 独立 Compose 项目中核对四服务 `/health` 和 `/metrics` 均返回 200。[E1、E3、E4]

<!-- pagebreak -->

## 3. DevOps 实践与版本身份

仓库以 Git 提交固定输入、实现和文档，Compose 固定服务拓扑，CI 检查实验模块及安全门禁。`v0.9-rc` 注释标签指向 `5338183c7178122476b84c65b6a7010ca6598a61`；标签目标的 E7、E8–E10、E11–E12、E13 安全门禁和 E13–E14 集成五类 CI 均成功。标签之后 `main` 另有 E11–E12 教学样例镜像来源修正、B3 监控和 B4 容错改进。报告把“运行代码提交”与“PR 归档提交”分别列出。[E1、E4]

| 责任与场景 | 实际被测代码提交 | 项目与范围 |
| --- | --- | --- |
| B1 正常五阶段 | `5338183c7178122476b84c65b6a7010ca6598a61`（`v0.9-rc`） | B09 真实项目；180 项产物 |
| B2 E13 专项 | `298ff1366cdd2f4314cce625492fa813f484893f` | A09 项目；超时、错误补丁、恢复、API 幂等 |
| B3 监控三阶段 | `cad9b1bee2a9e2633e4af1cad42a8b6a3d3a858b` | B09 真实项目；四服务指标、Prometheus、Grafana |
| B4 容错复测 | `38132ae89492d58f9dbf934a2310b7e91cc53d01` | B09 真实项目；有限重试、超时、恢复与错误补丁 |

B3 PR #27 的合并提交为 `90d77a983074996482da7a634c61bafecb588fcc`；B4 PR #28 的合并提交为 `c02ccd1c7bcd4e0dcd19a00ad704a09019bea8fd`。二者是归档身份，不替换上表中的实测提交。B4 PR #28 的 12 项 CI 全部通过；其四项重试测试和两项 HTTP 指标测试另在服务器核对。[E3、E4]

部署和取证采用独立 Compose 项目及工作目录，避免不同成员的任务互相覆盖。请求、job/trace、镜像、阶段报告、补丁、最终复验和完整证据包都记录 SHA256。源仓库与验证工作树的前后状态另行保存，使“验证失败未破坏输入”可以复核，而不只依赖终态文字。[E1–E4]

<!-- pagebreak -->

## 4. B09 真实项目五阶段系统集成

B1 在标签检出 `/root/241880556/devops-b09-microservice-v0.9-rc` 上发起新任务，使用的候选 Dockerfile SHA256 为 `1fa4739abd325c84e0ed4b3bbdcbcaf39c7c500fc0d80ba4707216e5cbe21a64`。任务 `job-5cdec29e61bf4f629ace6a5dce190ad2`、追踪 `trace-21ce7e7b872f42baa177362e1571e61a`，最终为 `SUCCEEDED`。`draft`、`full-check`、`incremental-check`、`repair`、`recheck` 五阶段均有独立报告与身份。B1 脚本总断言 `FAILURES=0`；180 项产物的存在性、字节数和 SHA256 逐项通过。[E1]

增量检查定位 `main.o → extra.h` 缺失边，MDFixer 生成 `candidate.patch`，SHA256 为 `6fb5dc4d84f5d65bcf7edffae3b7e02acb2259676be2154a1fc947463ee75c69`。补丁验证确认依赖边触发重建，`make test` 与 `./app` 成功，输出 `hello E3`。复验的 `remaining_missing=0`，最终 `findings=[]`，clean 和 build 退出码均为 0。B4 又从同一运行目录执行 `verify_e14.py` 独立复核产物身份。[E1]

完整证据包 `e14-microservice-b1-b09-v09rc-20261124-01.tar.gz` 为 4,959,089 字节，SHA256 `2ffd7c1391f1b7297ee846d3e854e4a7820cebc13b16f25ef27d9560d22c637e`。包内保留原始请求、阶段信封、补丁、复验和服务日志；仓库内只保留便于阅读的精简索引。本次组级归档重新取回完整包并在本机复算大小和 SHA256，一致。[E1]

该结果证明标签版本上的正常真实项目闭环。B3 监控轮次和 B4 故障轮次分别在后续代码提交上运行，不能把它们的 job/trace 贴到上述 B1 任务名下，也不能声称 B1 标签任务自身包含后续有限重试实现。

<!-- pagebreak -->

## 5. 可观测性：指标、面板与关联日志

B3 在四业务进程直接实现 `/metrics`：调用接收数、按成功/失败区分的完成数、处理中数量和耗时直方图。Prometheus 每 5 秒抓取四目标；Grafana 八面板展示可用性、接收量、结果分类、处理中、成功增量、失败增量、P95 和平均耗时。实际 PromQL 与面板 JSON 均已归档。指标标签只使用 role、status 等低基数值；job_id 与 trace_id 保存在带 UTC 时间、状态、错误码和耗时的结构化日志。[E3]

| 阶段 | B3 job_id / trace_id | 终态与监控证据 |
| --- | --- | --- |
| 正常 | `job-7e963debfd474e0ebad8523366eed562` / `trace-5d76adacfb4c43cf9f1e3307852efee2` | `SUCCEEDED`；四服务日志关联，180 项产物核验 |
| EChecker 停机 | `job-1fb28b45301246dc9ffbf5320c76abea` / `trace-dccbe4545b77421b96dbd257b86206b0` | `FAILED`；06:12:51 与 06:12:56 UTC 两个 `up=0` 原始样本 |
| 恢复 | `job-cd3d2ea68e344dc99f430274e3fe099f` / `trace-2ecce735912845a6a1485bb03a1584d4` | `SUCCEEDED`；四目标恢复，180 项产物核验 |

一项完整任务会多次调用 BuildChecker，因此服务调用计数不能相加为端到端任务数；端到端结果以编排器 `result.json` 为准。服务停机时，请求在连接阶段被拒绝，未抵达 EChecker，其自身失败计数不会包含该请求。故障定位结合调用方日志、外层终态和 Prometheus `up=0`。服务进程重启会重置计数器，面板用 `increase`/`rate` 处理重置。[E3]

B3 保留了正常、故障、恢复及全程共八张 Grafana 截图，另有 Targets、原始查询、面板导出和按 job/trace 关联的日志。故障截图的窗口较宽，短暂掉线不够明显，故报告以两个原始 `up=0` 样本作为精确证据。完整包为 22,837,079 字节，SHA256 `2dfe80765cdf6ab24833188c22d7edb045cc1a4b75ad5e09b8b23e5a972cb918`，本次已取回并复算一致。[E3]

<!-- pagebreak -->

## 6. 容错、恢复与质量验证

B4 在 `38132ae…` 的独立项目中停止本次任务实际调用的 EChecker。任务 `job-d8724483fcd044669aeda43b5c82df19`、追踪 `trace-09453223548e4f59b7d4cef494fc0d01`，三次连接拒绝后于约四秒内进入 `FAILED`，`error_code=DOWNSTREAM_UNAVAILABLE`，`failed_service=echecker`，`attempt_count=3`。重试只覆盖连接拒绝和 HTTP 503 `SERVICE_BUSY`，上限三次，并保存每次尝试的 UTC 时间及结果。[E4]

另以 `build_timeout=0.01` 触发 DRAFT 超时。任务 `job-998a0fad3c024edf932b90d3d3dd4485`、追踪 `trace-f862ecb5c1c4437c9cb9a1fe9720a2e5` 返回 HTTP 422、`TIMEOUT`，外层进入 `FAILED`，`attempt_count=1`。由于请求已送达后结果不确定，超时不自动重试。EChecker 恢复健康后，新任务 `job-4cac1194352348d4bb3714ae5fcb817e`、追踪 `trace-04b597c31eea48f18b9454e44f7cf566` 完成五阶段，186 项产物核验通过，最终 findings 为空。[E4]

错误补丁场景用不匹配的 Makefile 补丁调用 E14 `validate_repair`，结果 `accepted=false`、`rollback=true`、`source_unchanged=true`；目标 Makefile 的前后 SHA256、源仓库 HEAD 和工作区状态均一致。B2 另在 `298ff136…`、A09 项目上验证 E13 任务 API 幂等：相同输入复用同一 job，不同输入返回 409，且只创建一条任务。该结果证明旧统一基线的 API 行为，不代表 B4 独立轮次重新执行了幂等测试。[E2、E4]

B4 本轮四项重试测试、两项 HTTP 指标测试通过；服务健康与指标响应均为 200。运行证据扫描 1,179 个文本，`hits=0/errors=0`。完整包为 19,366,265 字节，SHA256 `3ef9eb5e1c8da342c0d021e9a14de4ba6b39a3943527eb8ec87f1728e19936fd`；服务器清单 1,739 项和本机包哈希均核验通过。[E4]

<!-- pagebreak -->

## 7. 问题定位与反思

最初的 `v0.9-rc` 标签环境没有业务 `/metrics`，后由 B3 增加四服务指标、Prometheus 与 Grafana。业务执行时间长时单线程 HTTP 入口会影响指标抓取，B3 改为线程化入口并用非阻塞锁保护业务执行；并发繁忙请求返回 503 `SERVICE_BUSY`。这使指标抓取与健康检查能在任务执行中继续响应，但也要求调用方明确处理暂时繁忙。[E3]

B3 的停机场景已显示端到端任务进入 `FAILED`，但当时编排器仅记录连接拒绝字符串，尚无有限重试和规范错误码。B4 后续加入最多三次的有界重试和 `error_code`、`failed_service`、`attempt_count` 字段，并用新任务实测。两个轮次必须分别引用；不能拿 B3 的 `up=0` 图代替 B4 的三次尝试记录。[E3、E4]

监控指标的作用域也需严格解释：`/metrics` 统计单次业务调用，编排 `result.json` 统计完整任务；服务停机前被拒绝的请求不会进入该服务计数器。通过 job/trace、调用方日志和原始 Prometheus 样本联合定位，可以避免把“目标不可达”误判为“目标内部处理失败”。B3 宽时间窗口截图不足以单独显示数秒掉线，正式汇报应同时展示原始查询中的两个 `up=0` 样本。[E3]

部署期间遇到 Docker Hub 超时、Prometheus 默认端口占用、Windows CRLF 与 Git 格式检查冲突，以及标签后 CI 的教学样例旧镜像 digest 无法解析。团队保存实际镜像 ID 与 digest，改用固定源和空闲端口，并在标签后的独立提交修正 CI 样例；没有改写 `v0.9-rc` 或原始任务包。后续可把 E13 幂等复测加入监控与容错同一提交的综合回归，并自动生成窄时间窗口故障面板截图。[E1–E4]

<!-- pagebreak -->

## 8. 成员贡献、复现与交付

| 成员 | 主要贡献与可核对产物 |
| --- | --- |
| B1 刘欣雨（241880481） | 固定 B09 Base/Target 和候选 Dockerfile；在标签环境执行真实项目五阶段，保存请求、job/trace、补丁、复验与完整证据包。 |
| B2 黄新迪（241880359） | 整理部署与复现材料；在 E13 统一基线上复跑超时、错误补丁、恢复和任务 API 幂等，保存请求、日志与源仓库完整性。 |
| B3 丁卓（241880585） | 实现四服务指标、Prometheus/Grafana 配置与 PromQL；完成正常、停机、恢复三阶段监控取证、关联日志及八张截图。 |
| B4 韩尚真（241880556） | 固定标签环境与证据索引；审查 B3 PR；实现有界重试和错误字段；复测停机、超时、恢复和错误补丁，整理本报告与提交包。 |

复现应先检出指定提交，再设置 `E14_ROOT` 为该检出绝对路径、`E14_IMAGE` 为记录的课程镜像，运行 `docker compose -f labs/e13e14/compose.yaml -p <独立项目名> config --quiet` 与 `up -d --wait`，核对四服务 `/health`。B3 监控轮次使用 `labs/observability/compose.yaml`，启动四服务、Prometheus 和 Grafana，检查四 Targets 与八面板。真实任务请求、候选 Dockerfile 与 `orchestrate.py` 调用参数见完整证据包；每轮应使用新的输出目录和 job/trace，并运行 `verify_e14.py` 核对产物。[E1、E3]

交付含报告 PDF、项目源码、组级 `AI_USAGE.md`、四人完整证据包及 SHA256 清单。课程服务器的原始目录和 GitHub 中的精简索引保留复核入口。B1、B3、B4 完整包已在本机复算哈希；B2 包随仓库归档并已核对。最终演示优先现场运行健康检查、Targets 与正常任务的结果；备用使用 B3 八张截图、B4 故障/恢复结果和原始日志，按附录索引定位。[E1–E4]

<!-- pagebreak -->

## 附录：证据索引与版本边界

**E1 B1 标签任务**：`docs/students/241880556/e13-e14-b4/MICROSERVICE-LAB-FINAL.md` 及同目录 `evidence/microservice-lab-v0.9-rc/`；完整包 `e14-microservice-b1-b09-v09rc-20261124-01.tar.gz`。

**E2 B2 E13 专项**：`docs/students/241880359/e13-b2-recheck-298ff136/TEST_REPORT.md`；完整包 `evidence/students/241880359/e13-b2-recheck-298ff136/b09-e13-b2-recheck-298ff136-20261124-105225.tar.gz`，15,620,441 字节，SHA256 `e7e4a3bebe62e3e8306a548a033831e3121edb8bd0919886ad4e6688824a00d6`。

**E3 B3 监控**：`docs/students/241880585/microservice/可观测性报告.md`；八张截图位于其 `evidence/screenshots/`，三阶段原始查询与日志位于 `evidence/observability-export/`；完整包 `B3-Microservice-Monitoring-20261125-151724.tar.gz`。

**E4 B4 容错**：`docs/students/241880556/e13-e14-b4/MICROSERVICE-LAB-B4-QUALITY.md` 及 `evidence/quality-38132ae/`；完整包 `e14-b4-quality-38132ae-20261125.tar.gz`。

**发布与归档**：标签 `v0.9-rc` 的目标是 `5338183c7178122476b84c65b6a7010ca6598a61`。B3 PR #27 合并提交 `90d77a983074996482da7a634c61bafecb588fcc`；B4 PR #28 合并提交 `c02ccd1c7bcd4e0dcd19a00ad704a09019bea8fd`。当前 `main` 可包含后续文档与 CI 修正，不能据此倒推任何旧任务的运行版本。

**课程要求**：报告正文建议 6–10 页，2026 年 12 月 1 日前提交 PDF、项目本体、过程证据和 `AI_USAGE.md`；12 月每组 20 分钟汇报，优先现场演示并备截图或录屏。本报告正文为第 1–8 节，封面、目录和本附录不计入正文。

# B4 最终 main 四服务集成复验

日期：2026-11-24。结论：B4 集成复验通过；组级 E13 门禁判定和 `v0.9-rc` 标签仍待完成。

## 固定基线与环境

- B09 仓库 `main`：`72fd0b7b4bf354c60be3389c9bf2777966ce1b9e`，即 PR #22 合并提交。与 B1/B2 共同复跑基线 `298ff1366cdd2f4314cce625492fa813f484893f` 相比，`labs/` 与 `.github/` 无差异；新增的是 B1/B2 的回归文档与证据。
- 课程服务器独立稀疏检出：`/root/241880556/devops-b09-e13e14-final-72fd0b7`。输入项目由上一轮固定材料复制，测试输出使用全新 `work/e13-main-72fd0b7` 与 `work/e14-main-72fd0b7`。
- 四服务镜像沿用未变的课程镜像 `course-e11e12:e14-main-739ba9a`，ID `sha256:b6eb148da0a6248be7410d5faea4f7f22945f10cccea8f72e66ab5d51809be3b`；服务代码由固定新检出挂载。Compose 项目 `e14-main-72fd0b7` 使用宿主回环端口 `18481–18484`，验收后已停止并清理。
- A09 项目 Base `e825395a5f8006f1c57a115cc25ea5c7802863ee`、Target `ba688c40d13cd8658e554f7544f1546d35b4b397`；B09 项目 Base `30ffe4c41492334478a2446a8be0662d3f31d478`、Target `a7e3b644ca9b1b9d0b26bd41e839fcbf5ea1c293`，子目录 `fixtures/e11e12-b1-real`。A09 仍使用上一轮已核验来源的离线派生候选和基础镜像映射。

## 结果

E11–E12 的 38 项测试、E13–E14 的 9 项测试全部通过。三个教师项目 jsmn、inih、tiny-AES-c 均成功，各独立校验 209 个产物，共 627 个；补丁接受、依赖重建和最终无缺失依赖检查通过。摘要见 [verified-projects.json](evidence/final-72fd0b7/verified-projects.json)。

| 四服务轮次 | job_id | 产物 | 修复边 | 最终发现 |
| --- | --- | ---: | ---: | --- |
| 固定样例 | `job-e195f733f5be4c83bd293df49a8047bf` | 174 | 2/2 | MD=0；保留 `REDUNDANT(main.o, unused.h)` |
| B09 实际项目 | `job-c73ee3a77be740f6a87c9ad81d804935` | 180 | 1/1 | MD=0 |
| A09 实际项目 | `job-e3c65a4eaac24f9382fe0613a30198ef` | 205 | 6/6 | MD=0；保留同一 RD |
| A09 超时后新任务 | `job-16ff370858764e31b09bb2ea0ba02854` | 205 | 6/6 | MD=0；保留同一 RD |
| B09 服务中断后新任务 | `job-7a6ac41a00b744c1b1835bd971206bc9` | 180 | 1/1 | MD=0 |

五轮均完成 DRAFT、全量检查、增量检查、修复、复检五阶段，独立复核合计 944 个产物的实际字节哈希、同一 job/trace、来源报告、补丁接受、重建与输出。逐轮 trace、产物和补丁哈希见 [verified-runs.json](evidence/final-72fd0b7/verified-runs.json)。

故障恢复：`build_timeout=0.01` 的 A09 任务 `job-1cb8bc0c7dd3421fb0696eaf8582adf6` 在 DRAFT 返回 `TIMEOUT`，无补丁；新任务成功。停止 EChecker 后，B09 任务 `job-420a385eb00543d89891769b956fee3f` 在增量检查前连接失败，无补丁；重启并健康检查后，新任务成功。四个失败/恢复任务的 job 和 trace 各不相同，失败产物分别核验 47、113 个，超时构建容器无残留。见 [verified-failures.json](evidence/final-72fd0b7/verified-failures.json)。

运行证据扫描 1,862 个文本，`hits=0、errors=0`；四服务镜像与本轮五个候选镜像的镜像历史和环境扫描均通过。代码镜像扫描的源码范围为当前检出中的 `labs/` 84 个文件；组级源码、Git 历史与 C6 结论仍由 B3 的最终门禁和 CI 汇总。扫描摘要见 [evidence/final-72fd0b7](evidence/final-72fd0b7)。

当前 `main` 的五个工作流均成功：[E11–E12](https://github.com/llxxy-cn/devops-b09/actions/runs/45318974513)、[E13 安全门禁](https://github.com/llxxy-cn/devops-b09/actions/runs/45318974589)、[E7 质量门禁](https://github.com/llxxy-cn/devops-b09/actions/runs/45318974802)、[E8–E10](https://github.com/llxxy-cn/devops-b09/actions/runs/45318974567)、[E13–E14 集成](https://github.com/llxxy-cn/devops-b09/actions/runs/45318974596)。

## 完整证据包

- 课程服务器：`/root/devops-submissions/241880556/e14-b4-final-main-72fd0b7-20261124.tar.gz`。
- 本机：`D:\devops\e14-b4-final-main-72fd0b7-20261124.tar.gz`。
- 大小：36,338,750 字节；SHA256：`8e5658420fb052ef7072038f142296a38cf423970431f4f514b30d4f0a30efb7`。服务器与本机校验一致。
- 包含固定输入项目、请求、三个教师项目、七轮四服务任务、逐阶段日志、四服务日志、镜像与扫描记录。LF 格式 `SHA256SUMS` 的 3,776 项在服务器逐项校验通过。

最初直接在宿主机调用教师项目 pipeline 的尝试因请求使用容器路径、缺少 DRAFT 容器运行环境而失败，原记录保留在包中；正式教师项目结果是通过课程镜像运行的 `H1/H2/H3-03`。扫描脚本的稀疏检出下载曾遇到 GitHub HTTP/2 错误，本轮从本机固定 `main` 提交取同一脚本补齐镜像扫描。

## 交给 B3 的门禁输入

B4 的 E14 集成、教师项目复验、两种故障恢复及运行证据扫描已通过。B1 的 C1–C3 和 A09 原签收、B2 的 C4/C5/C7/C8 已分别合入 main。请在本报告合入后的最终提交上汇总 C1–C8、C6、教师项目、CI、A09 签收与阻断项，明确给出组级 E13 门禁结论。若该报告只增加文档和证据且 `labs/`、`.github/` 不变，可沿用本轮运行代码核验，并须核对新提交的 CI。`v0.9-rc` 在门禁结论通过、阻断项为零及标签仓库和提交确认后创建。

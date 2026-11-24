# E13–E14 B4 四服务集成记录

负责人：241880556。**当前发布状态与交付清单见 [最终交付索引](FINAL-DELIVERY-v0.9-rc.md)。**本页保留 2026-11-23 的先行预跑；当时运行的 B4 文件尚未提交，基于 B3 PR #17 的 `783561e907e6972e2d51c4237c5f8ef9b34ac2b3`。PR #17 合并后的候选提交复验见 [ACCEPTANCE.md](ACCEPTANCE.md)，其代码 SHA 为 `0be95525c9ac2e892765b71e7b81dc848d31bb7e`；后续最终实测见 [FINAL-ACCEPTANCE-72fd0b7.md](FINAL-ACCEPTANCE-72fd0b7.md)。

## 输入和运行环境

- B 仓库：`https://github.com/llxxy-cn/devops-b09`，项目子目录 `fixtures/e11e12-b1-real`，base `30ffe4c41492334478a2446a8be0662d3f31d478`，target `a7e3b644ca9b1d0b26bd41e839fcbf5ea1c293`。B1 候选 Dockerfile SHA256 `1fa4739abd325c84e0ed4b3bbdcbcaf39c7c500fc0d80ba4707216e5cbe21a64`，预期输出 `hello E3`，另执行 `make test`。
- A09 固定取件提交：`269827d05d99845a9aca7a8b9f122e9a17a3741a`，项目 bundle SHA256 `40510b4c02a05b0ce372ee7870c53ca4d4f32978599e93d8c7ac1b3a2e319072`，base `e825395a5f8006f1c57a115cc25ea5c7802863ee`，target `ba688c40d13cd8658e554f7544f1546d35b4b397`，预期输出 `1`。项目没有 `make test`，使用程序输出断言。
- A09 原始候选 Dockerfile SHA256 `6f0e3980c609a683d727c271bdd3a8d5f12b46df21f1fcc402e0d8420ce06c28`。课程服务器访问 Docker Hub 超时，原件预跑失败保留在 `work/e14-b4-compose-a09-preflight-01`。成功预跑使用 B1 已交付的离线派生候选，SHA256 `42fa65f92cc2fb57e321f4c4ffbe9e657df0c0bb0326d62247fa8c86145f755c`；本地离线基础镜像 ID `sha256:af8922b2323b530a21bb406e3f38cae8488ad32f92555f27ab15538a7feb40b4`。临时替换 DRAFT 基线的 `FROM` 后已恢复原文件，映射见每轮 `offline-build-mapping.json`。
- 四服务共用课程镜像 `course-e11e12:241880556`，ID `sha256:0f14125df9d889f01f0f9cf1ab37c0a216d8e26212cca99504a6304b19f3701f`。独立 Compose 项目 `e14-241880556` 绑定服务器回环端口 `18181–18184`；四个角色均经健康检查。只有 DRAFT 挂载 Docker socket。

请求模板：[B09 真实项目](requests/b09-real.json)、[A09 原始候选](requests/a09-real.json)、[A09 离线候选](requests/a09-real-offline.json)、[A09 超时注入](requests/a09-timeout-offline.json)。服务入口、编排和回归脚本位于 `labs/e13e14/`。

## 预跑结果

每轮 `result.json`、请求、五阶段报告、补丁、验证、BuildChecker 原始图与 trace、四服务响应、日志和逐文件哈希核验结果均在证据包内。下列成功轮次由 `verify_e14.py` 独立复核，摘要见 [verified-runs.json](evidence/verified-runs.json)。

| 轮次 | job_id / trace_id | 结果 | 产物数 | 修复边 / 最终发现 |
| --- | --- | --- | ---: | --- |
| 固定样例 | `job-16ba09bb387d490dad3f595fdf4167b8` / `trace-113f23c56c714ddda2b2f865684718d7` | 五阶段成功 | 173 | 2/2；仅保留 `REDUNDANT(main.o, unused.h)` |
| B09 真实项目 | `job-0785726c05bc4b5d844d60efed366bc3` / `trace-566b98bddcac45bd98fea8922a1b9e91` | 五阶段成功 | 180 | 1/1；MD=0 |
| A09 真实项目 | `job-e7741dc76c644256a2e993820dfbb949` / `trace-499802de6a2b4b0cb716b53a718e9896` | 五阶段成功 | 205 | 6/6；MD=0，仅保留 `REDUNDANT(main.o, unused.h)` |
| 超时后恢复 | `job-03bb8835f7384329bb1f9b14a8b17db7` / `trace-4a7edd5f2db241f3abf3edd6ce69d1a8` | 新任务五阶段成功 | 205 | 6/6；MD=0，RD 如上 |

B09 项目首次预跑在 EChecker 遇到 `CFLAGS ?=` 后返回 `UNSUPPORTED_FLAGS`；已改为从 Make 读取实际 CFLAGS，保留首次失败目录 `work/e14-b4-compose-b09-preflight-01`。A09 原始候选预跑因 Docker Hub 超时失败，保留 `work/e14-b4-compose-a09-preflight-01`。两项均使用全新目录复跑，未改写失败证据。

故障注入轮 `job-4bc7ab88e77f4ba9a15dde575e83eeb9` 的 `build_timeout=0.01`，外层 `FAILED`、DRAFT 内层 `TIMED_OUT`，退出码 1；没有残留构建或验证容器。随后恢复正常时限并提交上述新任务成功。失败结果见 [timeout-result.json](evidence/timeout-result.json)，进程检查见 [timeout-process-check.log](evidence/timeout-process-check.log)。

运行证据扫描 768 个文本，`hits=0, errors=0`；源码、历史、课程镜像及 B09/A09 候选镜像扫描均退出 0。摘要见 [runtime-scan.log](evidence/runtime-scan.log)。课程服务器上 B4 独立运行的原有 20 项 E11–E12 测试和新增 5 项 E13–E14 测试通过。

## E13 跨组签收状态

A09 已在 2026-11-23 的回复中正式签收 B09 本轮 E13 交付。A09 核对了四分片重组包（154,556,278 字节，SHA256 `1a1419b6359448b7e39033899d287ed85fd44d0ca054299e238cc55d1645ba33`）、包内 17 个文件、修复提交 `74eff064e1eae3e244b0acf80880c92fb4635e26` 及其 Target 父提交 `ba688c40d13cd8658e554f7544f1546d35b4b397`。C1 最终 MD=0、6/6 条修复边重建及输出验证通过；C2 为 `STALE_REPORT`，C3 为 `ARTIFACT_HASH_MISMATCH`，均无补丁产物；恢复输入后的新任务成功。A09 还复算确认兼容信封只增加 `source_report.bytes=3052`。签收原文目前由组内消息提供，最终门禁表仍需固定可访问的签收证据链接。

A09 提出的两项非阻断文档建议：交付包 `SHA256SUMS` 为 CRLF，Linux 校验前需去除 `\r`；交付说明中的部分路径与包内扁平文件名不一致。两项均不影响本轮签收，后续交付说明应统一。

## B4 分支 CI

B4 集成代码提交 `5f5471e` 的 [E13–E14 integration gate 第三轮](https://github.com/llxxy-cn/devops-b09/actions/runs/45164694229) 已通过，`contracts` 和 `four-services` 两个 job 均为 `success`。前两轮分别暴露 runner 工作树所有权和非 root DRAFT 的 Docker 配置目录权限问题；修复后固定样例在四个真实容器中完成五阶段。此 CI 验证 B4 分支，正式门禁仍以合并后统一验收 SHA 为准。

## 预跑原始证据包

- 课程服务器：`/root/devops-submissions/241880556/e14-b4-preflight-20261123.tar.gz`
- 本机副本：`D:\devops\e14-b4-preflight-20261123.tar.gz`
- SHA256：`fa4076e2720a8b52be7c4871a5e78624a7ef10cbd2cb9f4261e5c0e865bbd197`
- 两处已核对相同哈希；包内 `work/e14-b4-preflight-artifacts.sha256` 经 `sha256sum -c` 全部通过。包内保留原始输入、离线映射、失败轮次、成功轮次、四服务日志、扫描、镜像 ID 和代码文件哈希。

## 2026-11-23 记录的当时待办

1. PR #17 已合并，Issue #18 已关闭；B1/B2/B3 仍需把 C1–C8、A09 签收、CI 和候选提交 `0be9552` 对齐成最终 E13 门禁，并固定签收原文的可访问链接。
2. PR #19 审查并合并后，在新的 `main` 完整 SHA 上核对正式验收结果；本轮候选提交的教师项目与四服务复验及原始证据见 [ACCEPTANCE.md](ACCEPTANCE.md)。
3. 最终 E13 门禁通过、阻断项为零且合并后复验完成时，再决定 `v0.9-rc`；当前状态为“候选待发布”。

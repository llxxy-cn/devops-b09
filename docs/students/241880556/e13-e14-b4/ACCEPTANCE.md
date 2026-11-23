# B4 E13–E14 候选提交验收

日期：2026-11-23。结论：**B4 候选提交的四服务验收通过；组级 E13 最终门禁与 `v0.9-rc` 待完成**。

## 固定基线

- B09 的 PR #17 已合入 `main`：`fa56232ecf329a96c774076c66c1f9c4150fac95`，Issue #18 已关闭。B4 PR #19 的候选代码为 `0be95525c9ac2e892765b71e7b81dc848d31bb7e`，已包含该 `main` 提交；本轮在此提交的独立 Linux 检出运行。代码传输 bundle SHA256 `396b875fb2894e441f49c7af755563b39d607128b3e346b7f281ebdd7519c4a7`。
- A09 固定材料提交 `269827d05d99845a9aca7a8b9f122e9a17a3741a`，项目 Base `e825395a5f8006f1c57a115cc25ea5c7802863ee`、Target `ba688c40d13cd8658e554f7544f1546d35b4b397`。原始候选 SHA256 `6f0e3980c609a683d727c271bdd3a8d5f12b46df21f1fcc402e0d8420ce06c28`；服务器仍使用经映射核验的离线派生候选 SHA256 `42fa65f92cc2fb57e321f4c4ffbe9e657df0c0bb0326d62247fa8c86145f755c`。
- B09 实际项目 Base `30ffe4c41492334478a2446a8be0662d3f31d478`、Target `a7e3b644ca9b1b9d0b26bd41e839fcbf5ea1c293`，项目子目录 `fixtures/e11e12-b1-real`，候选 Dockerfile SHA256 `1fa4739abd325c84e0ed4b3bbdcbcaf39c7c500fc0d80ba4707216e5cbe21a64`。
- 本轮四服务镜像 `course-e11e12:e14-0be9552`，ID `sha256:d03deb89ae91ec30468c0bae63341e1a03e34c8e9fe17fd951a2b8ba3b5f8f5f`。Compose 项目 `e14-b4-accept-0be9552`，仅监听宿主回环端口 `18281–18284`，四个角色健康检查通过；测试结束后已 `down`。固定清单见 [candidate-metadata.json](evidence/acceptance/candidate-metadata.json)。

## 同一代码提交的实测结果

三个教师项目 jsmn、inih、tiny-AES-c 均 `SUCCEEDED`，各核验 209 个产物，合计 627 个；逐条依赖重建及输出 `1` 均通过。完整任务号、trace、补丁与验证哈希见 [verified-projects.json](evidence/acceptance/verified-projects.json)。E11–E12 的 20 项测试和 E13–E14 的 7 项测试通过，后者包含直接调用 PR #17 修复函数的 H1 正确补丁接受与错误补丁隔离回归。

| E14 任务 | job_id | 五阶段 | 产物核验 | 修复边与最终发现 |
| --- | --- | --- | ---: | --- |
| 固定样例 | `job-c9b986e77d9c49c998d2d38f95ff9d11` | 成功 | 174 | 2/2；MD=0，保留 `REDUNDANT(main.o, unused.h)` |
| B09 实际项目 | `job-77b9def8d9124265a6c6ce8b62887427` | 成功 | 180 | 1/1；MD=0 |
| A09 实际项目 | `job-471de082cf9e410289df30696cf219de` | 成功 | 205 | 6/6；MD=0，保留 `REDUNDANT(main.o, unused.h)` |
| A09 超时后新任务 | `job-b7ad5cd17333439db75135844809ef4d` | 成功 | 205 | 6/6；MD=0，RD 同上 |
| B09 单服务恢复后新任务 | `job-3accb77db09248fcb52d8ab0011042bc` | 成功 | 180 | 1/1；MD=0 |

以上五轮由 `verify_e14.py` 独立检查同一 job/trace、完整 Base/Target、五阶段信封、来源报告哈希、补丁接受、实际产物字节 SHA256、无 MD 和离线映射。完整结果及各 trace、镜像 ID 和产物 SHA 见 [verified-runs.json](evidence/acceptance/verified-runs.json)。

受控失败与恢复：`job-1905175c25964355ad27058099625e13` 使用 `build_timeout=0.01`，DRAFT 返回 `TIMEOUT`，外层 `FAILED`，没有后续阶段或补丁，也没有残留构建容器；之后 A09 新任务成功。另在本轮隔离 Compose 项目短暂停止 EChecker，`job-ced1dff832e949fdbf21811693119654` 在检测阶段因连接拒绝失败，无补丁；重启并恢复健康后，B09 新任务成功。失败与恢复任务 ID/trace 均不同，失败产物也逐文件校验，见 [verified-failures.json](evidence/acceptance/verified-failures.json)。

源码、Git 历史、课程镜像及 A/B 候选镜像扫描均通过；最终运行证据扫描 1,692 个文本，`hits=0, errors=0`，见 [runtime-scan.log](evidence/acceptance/runtime-scan.log)。候选提交的 [E13 安全 CI](https://github.com/llxxy-cn/devops-b09/actions/runs/45172121729) 与 [E13–E14 集成 CI](https://github.com/llxxy-cn/devops-b09/actions/runs/45172121774) 均绿色。

## 完整证据与后续门禁

- 服务器：`/root/devops-submissions/241880556/e14-b4-accept-0be9552-20261123.tar.gz`
- 本机：`D:\devops\e14-b4-accept-0be9552-20261123.tar.gz`
- 大小：36,165,524 字节；SHA256 `0b0940596c7a4a77f88efff9171a4c91fecaefeb44603262adabae5d930e1fe1`，两处一致。包内 3,360 个文件已用 LF 格式的 `SHA256SUMS` 全部校验通过；包含输入项目、代码 bundle、请求、日志、补丁、逐阶段报告、失败与恢复记录、镜像和扫描证据。

A09 已正式签收 B09 E13 C1–C3，组内仍需给签收原文固定可访问链接，并由 B1/B2/B3 将 C1–C8、CI 和该候选 SHA 对齐成最终 E13 门禁。PR #19 仍为草稿；合并后须在新的 `main` SHA 上完成最终验收。当前不创建 `v0.9-rc`。

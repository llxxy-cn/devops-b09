# v0.9-rc 候选说明草案

状态：**待发布**。本文件是 B4 集成预跑记录，尚未创建 `v0.9-rc` 标签。

## 已验证

- A09 已正式签收 B09 的 E13 交付：C1 MD=0、6/6 修复边重建和输出验证通过；C2 `STALE_REPORT`、C3 `ARTIFACT_HASH_MISMATCH` 均未生成或应用补丁。跨组回传包 SHA256 为 `1a1419b6359448b7e39033899d287ed85fd44d0ca054299e238cc55d1645ba33`。
- B4 课程服务器预跑：固定样例、B09 实际项目和 A09 实际项目均完成四服务五阶段；受控构建超时后，新任务成功。原始证据包 SHA256 为 `fa4076e2720a8b52be7c4871a5e78624a7ef10cbd2cb9f4261e5c0e865bbd197`，详情见 [README](README.md)。
- B4 分支提交 `5f5471e` 的 [集成 CI](https://github.com/llxxy-cn/devops-b09/actions/runs/45164694229) 中 `contracts` 与 `four-services` 均成功。

## 发布前需固定

| 项目 | 当前值 | 发布要求 |
| --- | --- | --- |
| B09 交换项目 | Base `30ffe4c41492334478a2446a8be0662d3f31d478`；Target `a7e3b644ca9b1b9d0b26bd41e839fcbf5ea1c293` | 在最终统一验收提交复跑 |
| A09 交换项目 | Base `e825395a5f8006f1c57a115cc25ea5c7802863ee`；Target `ba688c40d13cd8658e554f7544f1546d35b4b397`；取件 `269827d05d99845a9aca7a8b9f122e9a17a3741a` | A09 固定候选提交与镜像来源 |
| B09 编排与 E13 门禁 | B3 PR #17 未合并；B4 PR 待建 | 合并后记录 `main` 完整 SHA、全绿 CI、Issue #18 关闭和 C1–C8 回归 |
| 四服务镜像 | 预跑镜像 ID `sha256:0f14125df9d889f01f0f9cf1ab37c0a216d8e26212cca99504a6304b19f3701f` | 在最终代码 SHA 重建并记录新 ID/digest |
| 发布标签 | 无 | 正式验收完成后核对标签不存在，再在约定仓库固定 `v0.9-rc` |

## 已知事项与回退

A09 原始候选需要访问 Docker Hub，课程服务器超时；成功预跑使用已记录来源映射的离线派生候选。A09 提出的 `SHA256SUMS` 换行和包内路径说明问题不影响 E13 签收，后续交付说明需修正。

四服务的回退命令为 `docker compose -f labs/e13e14/compose.yaml -p <本轮项目名> down`；保留本轮请求、响应、日志和镜像 ID，不覆盖先前成功证据。正式发布前应在最终镜像和 Compose 项目名上重验此步骤。

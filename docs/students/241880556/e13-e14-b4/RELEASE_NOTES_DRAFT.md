# v0.9-rc 候选说明草案

状态：**待发布**。本文件记录 B4 候选提交验收；组级 E13 门禁、PR #19 合并和合并后复验尚待完成，未创建 `v0.9-rc` 标签。

## 已验证

- A09 已正式签收 B09 的 E13 交付：C1 MD=0、6/6 修复边重建和输出验证通过；C2 `STALE_REPORT`、C3 `ARTIFACT_HASH_MISMATCH` 均未生成或应用补丁。跨组回传包 SHA256 为 `1a1419b6359448b7e39033899d287ed85fd44d0ca054299e238cc55d1645ba33`。
- B4 候选代码 `0be95525c9ac2e892765b71e7b81dc848d31bb7e`：三个教师项目合计 627 个产物核验通过；固定样例、B09 和 A09 真实项目均完成四服务五阶段。构建超时及 EChecker 暂停后，分别有新任务成功。原始证据包 SHA256 `0b0940596c7a4a77f88efff9171a4c91fecaefeb44603262adabae5d930e1fe1`，详情见 [候选验收](ACCEPTANCE.md)。
- 候选提交的 [E13 安全 CI](https://github.com/llxxy-cn/devops-b09/actions/runs/45172121729) 与 [E13–E14 集成 CI](https://github.com/llxxy-cn/devops-b09/actions/runs/45172121774) 均成功；20 项 E11–E12 测试和 7 项 E13–E14 测试通过。

## 发布前需固定

| 项目 | 当前值 | 发布要求 |
| --- | --- | --- |
| B09 交换项目 | Base `30ffe4c41492334478a2446a8be0662d3f31d478`；Target `a7e3b644ca9b1b9d0b26bd41e839fcbf5ea1c293` | 候选提交复验已通过；合并后复核 |
| A09 交换项目 | Base `e825395a5f8006f1c57a115cc25ea5c7802863ee`；Target `ba688c40d13cd8658e554f7544f1546d35b4b397`；取件 `269827d05d99845a9aca7a8b9f122e9a17a3741a` | 候选提交复验已通过；合并后复核 |
| B09 编排与 E13 门禁 | PR #17 已合入 `main=fa56232ecf329a96c774076c66c1f9c4150fac95`；Issue #18 已关闭；PR #19 草稿 | 汇总 C1–C8 与签收链接，合并 PR #19 后固定新的 `main` SHA |
| 四服务镜像 | 候选镜像 ID `sha256:d03deb89ae91ec30468c0bae63341e1a03e34c8e9fe17fd951a2b8ba3b5f8f5f` | 合并后在最终代码 SHA 记录镜像 ID/digest |
| 发布标签 | 无 | 正式验收完成后核对标签不存在，再在约定仓库固定 `v0.9-rc` |

## 已知事项与回退

A09 原始候选需要访问 Docker Hub，课程服务器超时；成功轮次使用已记录来源映射的离线派生候选。A09 提出的旧包 `SHA256SUMS` 换行和路径说明问题不影响 E13 签收；本轮 B4 包使用 LF 清单和实际包内路径。

四服务的回退命令为 `docker compose -f labs/e13e14/compose.yaml -p <本轮项目名> down`；保留本轮请求、响应、日志和镜像 ID。本轮 Compose 已停止且确认无本轮容器残留，合并后还需在最终镜像和项目名上复验。

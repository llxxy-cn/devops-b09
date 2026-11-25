# B4 E13–E14 最终交付索引

日期：2026-11-24。负责人：241880556。状态：**E13 组级门禁通过，E14 四服务验收通过，`v0.9-rc` 已创建**。

## 发布身份

- 仓库：`llxxy-cn/devops-b09`。
- 注释标签：[`v0.9-rc`](https://github.com/llxxy-cn/devops-b09/tree/v0.9-rc)，标签对象 `28dc1090b37eb8c1fd0f1374e4d168e3d2c1c5d2`，指向 PR #24 合并提交 `5338183c7178122476b84c65b6a7010ca6598a61`。
- 标签目标提交的五类 CI 全部成功：[E7](https://github.com/llxxy-cn/devops-b09/actions/runs/45373303750)、[E8–E10](https://github.com/llxxy-cn/devops-b09/actions/runs/45373303552)、[E11–E12](https://github.com/llxxy-cn/devops-b09/actions/runs/45373303507)、[E13 安全门禁](https://github.com/llxxy-cn/devops-b09/actions/runs/45373303518)、[E13–E14 集成](https://github.com/llxxy-cn/devops-b09/actions/runs/45373303776)。核对时开放 Issue 为 0。
- 标签目标与 B4 最终实测提交 `72fd0b7b4bf354c60be3389c9bf2777966ce1b9e` 在 `labs/`、`scripts/`、`.github/`、`run_e11e12.py` 和 `run_lab.py` 上无差异。原始测试报告继续标注实际被测提交。

## 验收与证据

- [Microservice Lab 最终实验记录](MICROSERVICE-LAB-FINAL.md)：B4 在标签目标 `5338183…` 上固定四服务部署，B1 用 B09 自己的真实项目新跑五阶段。任务 `job-5cdec29e61bf4f629ace6a5dce190ad2` / `trace-21ce7e7b872f42baa177362e1571e61a` 成功，180 项产物逐项核验，补丁 SHA256 `6fb5dc4d84f5d65bcf7edffae3b7e02acb2259676be2154a1fc947463ee75c69`，最终 findings 为空。B1 完整包 SHA256 `2ffd7c1391f1b7297ee846d3e854e4a7820cebc13b16f25ef27d9560d22c637e`；仓库中保留精简证据索引。这是期末报告的本轮 Microservice Lab 正常链路入口。
- [Microservice Lab B4 容错与质量核对](MICROSERVICE-LAB-B4-QUALITY.md)：按被测提交、项目与 job/trace 分列 B1 正常任务、B3 监控三阶段、B4 先前四服务故障及 B2 E13 专项复跑；明确有限重试、统一错误码和完整包复核的待完成范围。B3 的 [PR #27](https://github.com/llxxy-cn/devops-b09/pull/27) 在 2026-11-25 核对时仍开放，其监控实测代码为 `cad9b1bee2a9e2633e4af1cad42a8b6a3d3a858b`，不能写成标签目标或当前 `main` 已运行该监控配置。
- [B4 最终实测记录](FINAL-ACCEPTANCE-72fd0b7.md)：三个教师项目各 209 个产物，共 627 个；固定样例、B09/A09 实际项目及两轮恢复任务共五轮四服务验收，944 个产物逐项核验。构建超时和 EChecker 中断按预期失败，新任务恢复成功；38 项 E11–E12 测试和 9 项 E13–E14 测试通过。运行证据扫描 1,862 个文本，`hits=0、errors=0`。
- [B2 统一基线专项复跑](../../241880359/e13-b2-recheck-298ff136/TEST_REPORT.md)：在 `298ff136…` 上用 A09 项目验证 E13 C4/C5/C7/C8，包括超时、错误补丁拒绝、恢复和任务 API 幂等；[完整包索引](../../241880359/e13-b2-recheck-298ff136/PACKAGE.md)记录仓库内压缩包及 SHA256 `e7e4a3bebe62e3e8306a548a033831e3121edb8bd0919886ad4e6688824a00d6`。此记录与 B1 的 `v0.9-rc` 正常五阶段任务分开引用；B2 报告注明 E14 四服务故障恢复另行记录。
- B4 完整包：`/root/devops-submissions/241880556/e14-b4-final-main-72fd0b7-20261124.tar.gz`，SHA256 `8e5658420fb052ef7072038f142296a38cf423970431f4f514b30d4f0a30efb7`。本机副本哈希一致，包内 LF 清单 3,776 项校验通过。精简证据见 [evidence/final-72fd0b7](evidence/final-72fd0b7)。
- [B3 组级门禁](../../241880585/e13-gate-298ff136/门禁汇总.md)汇总 C1–C8、教师项目、C6 扫描、[A09 原交付签收](../../../../evidence/students/241880481/e13-e14/A09-SIGNOFF-20261123.md)、五类 CI 及缺陷闭环；其专项实测基线为 `298ff1366cdd2f4314cce625492fa813f484893f`。组内已确认 A09 新回归协调事项；原签收证据仍对应原交付包。

## 本目录阅读顺序

本索引记录发布结果及期末报告材料。[MICROSERVICE-LAB-FINAL.md](MICROSERVICE-LAB-FINAL.md)是标签环境上的 B1 真实项目新任务；[FINAL-ACCEPTANCE-72fd0b7.md](FINAL-ACCEPTANCE-72fd0b7.md)固定此前 B4 最终实测的输入与原始结果。[ACCEPTANCE.md](ACCEPTANCE.md)是 2026-11-23 的候选验收记录；[README.md](README.md)保留更早的集成预跑；[RELEASE_NOTES_DRAFT.md](RELEASE_NOTES_DRAFT.md)是当时的候选说明草案。这些历史记录中的“待发布”与旧提交号仅描述各自运行当时的状态。

本索引在标签创建后补充到 `main`，不改动标签、原始报告、证据包或其哈希。

# B09 Microservice Lab：20 分钟汇报与备用证据

现场演示以当前可访问的课程服务器为准；所有历史任务展示其保存结果，不重写运行版本。截图默认 UTC，口头说明时间换算为北京时间需加 8 小时。

| 时间 | 讲述人与内容 | 现场操作或备用材料 |
| --- | --- | --- |
| 0:00–2:00 | B1：真实问题、Base/Target、缺失 `main.o → extra.h` 依赖 | 报告第 1、4 节；B1 `request.json`、`validation.json` |
| 2:00–5:00 | B2：教学样例的 API/worker 部署与同机隔离复现、四服务 Compose 架构 | 样例健康响应与 Targets、四服务 `/health`；报告第 2、3 节与部署补充包 |
| 5:00–8:00 | B1：五阶段正常链路、job/trace、补丁、复验 | B1 `result.json`、`candidate.patch`、`recheck.json`、180 项产物核验 |
| 8:00–12:00 | B3：四服务 `/metrics`、Prometheus Targets、Grafana 八面板及三阶段 | `labs/observability/promql.txt`、八张截图、Targets 导出与 `up=0` 原始样本 |
| 12:00–16:00 | B4：EChecker 停机、三次有限重试、`FAILED/DOWNSTREAM_UNAVAILABLE`、DRAFT 超时与恢复 | B4 `quality-38132ae/summary.json`、尝试记录、恢复 `result.json`；报告第 6 节 |
| 16:00–18:00 | B4/B2：错误补丁拒绝、仓库完整性、旧基线 API 幂等 | B4 `bad-patch-summary.json`；B2 C8 摘要；明确 B2 是 `298ff136…` 的 A09 项目 |
| 18:00–20:00 | 全组：CI、证据包清单、局限与答疑 | 报告第 7、8 节，提交包 `MANIFEST.sha256` |

## 现场快速检查

1. 确认所展示 Compose 项目与代码检出身份。B1 标签环境为 `b09-ms-rc-5338183`、代码 `5338183…`；B3 监控环境为 `b09-ms-b3-241880585`、代码 `cad9b1b…`；B4 容错环境为 `b09-ms-b4-38132ae`、代码 `38132ae…`。
2. 展示 `docker compose ps`、四服务 `/health`。监控轮次再展示四个 `/metrics`、Prometheus Targets 和 Grafana `b09-microservice` 面板。
3. 对正常任务只展示 B1 标签 job `job-5cdec29e61bf4f629ace6a5dce190ad2`；故障与恢复使用 B3 或 B4 自己的 job/trace，不混写。
4. 若现场环境不可用，使用下面的归档截图和 JSON。避免临时重启仍在其他成员使用的独立 Compose 项目。

## 备用材料定位

- B3 Grafana 全程与正常／故障／恢复八图：`docs/students/241880585/microservice/evidence/screenshots/01-full-window-top.png` 至 `08-recovery-bottom.png`。故障短暂掉线以 `docs/students/241880585/microservice/evidence/observability-export/fault/availability.json` 中两个 `up=0` 样本为准。
- B3 三阶段任务与关联日志：同目录 `evidence/observability-export/three-phase-summary.json`、`normal-correlated-logs.json`、`fault-correlated-logs.json`、`recovery-correlated-logs.json`。
- B1 标签运行结果：`docs/students/241880556/e13-e14-b4/evidence/microservice-lab-v0.9-rc/result.json` 与 `verified.json`；完整包内含五阶段报告和 180 项产物清单。
- B4 新复测：`docs/students/241880556/e13-e14-b4/evidence/quality-38132ae/summary.json`、`fault/incremental-response-attempts.json`、`timeout/draft-response-attempts.json`、`recovery/result.json`、`bad-patch-summary.json`。
- B2 旧基线幂等：`docs/students/241880359/e13-b2-recheck-298ff136/c8-http/summary.json`。展示时必须说明项目为 A09、实测提交为 `298ff136…`。
- B2 教学样例两轮部署与同机隔离复现：`docs/students/241880359/microservice-deploy/PACKAGE.md`，完整补充包在组级提交包的 `evidence/` 目录。

四人完整证据包、成员2部署补充包、报告和项目源码集中在最终提交包。包内 `MANIFEST.sha256` 可在离线环境核验所有交付文件。

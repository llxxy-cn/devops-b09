# B3 Microservice Lab 监控

本目录在 v0.9-rc 提交 5338183c7178122476b84c65b6a7010ca6598a61 上增加业务服务指标。
新增监控代码必须提交并记录实际运行 SHA，实际新任务应保存新 job_id、trace_id 和时间窗口。

## 指标来源和含义

四个业务进程直接在 /metrics 暴露实际 POST /v1/run 调用计数、成功/失败、处理中请求和耗时直方图。
计数单位为单个服务调用，一项完整五阶段任务可能调用同一服务多次，不能将四服务计数相加写成端到端任务数。
端到端任务状态、总耗时和身份以本轮编排器 result.json、阶段信封和日志为准。

指标只使用 role、status 等有限标签，job/trace 保留在带 UTC 时间戳的结构化日志中。
进程重启会重置计数器，PromQL increase/rate 处理计数器重置。
当服务停止时，Prometheus up=0 表示抓取失败。未抵达服务的调用不会计入该服务失败计数，
调用方错误及端到端失败必须结合编排器结果记录。

HTTP 入口改为 ThreadingHTTPServer，以便业务执行期间继续响应抓取和健康检查。
业务执行由非阻塞锁串行保护，服务繁忙时返回 HTTP 503、SERVICE_BUSY。
保留业务成功 HTTP 200、错误 HTTP 422 与原有 run 实现。

## 部署

个人独立 Compose 项目为 b09-ms-b3-241880585。
业务端口为宿主回环 18681–18684，Prometheus 为 19190，Grafana 为 13100。
四个业务镜像使用 E14_IMAGE 指定的已有课程镜像，Prometheus v3.5.0，Grafana 12.3.0。
部署后保存实际镜像 ID 与 RepoDigests，镜像下载和容器验证尚需在课程服务器执行。
Compose 文件使用 JSON 语法，属于合法 YAML，可由 docker compose 直接读取。

```bash
export E14_ROOT="$PWD"
export E14_IMAGE=course-e11e12:e14-rc-5338183-b4
docker compose -f labs/observability/compose.yaml -p b09-ms-b3-241880585 config --quiet
docker compose -f labs/observability/compose.yaml -p b09-ms-b3-241880585 pull prometheus grafana
docker compose -f labs/observability/compose.yaml -p b09-ms-b3-241880585 up -d --wait
```

Prometheus 通过内部服务名抓取四个业务目标，Grafana 数据源指向 http://prometheus:9090。
Grafana 预配置只读匿名 Viewer，关闭登录表单和初始管理员创建，端口绑定服务器回环。
浏览器访问应通过 SSH 本地转发。面板 UID 为 b09-microservice，默认显示 UTC 时间。
promql.txt 和 grafana/dashboards/b09.json 提供实际查询。
发布包包含指标与 HTTP 并发测试，测试使用模拟业务，不代替真实项目实测。

## 后续取证

确认四个 /metrics HTTP 200、Prometheus 四目标 up、Grafana 面板正常后，
运行新的正常、故障、恢复任务。每个任务使用新的 work 子目录。
停止本次 Compose 中实际调用的 echecker，由新任务证明端到端失败并进入终态，
恢复 echecker 后提交新任务并确认成功。故障范围与 B2 协调。
等待至少两个抓取周期，保存阶段边界 UTC 时间、targets/query_range 原始响应、
Compose 状态和日志、全部请求结果、面板 JSON、完整时间窗口截图与录屏。
原 B1 任务 job-5cdec29e61bf4f629ace6a5dce190ad2 作为 v0.9-rc 历史运行记录。

仅在已记录结果后关闭本次独立项目，不添加 -v，保留 Prometheus 和 Grafana 数据卷。

# 教学样例部署与同机隔离复现证据

黄新迪（241880359）在课程服务器完成 API、worker、Prometheus 和 Grafana 的首次 Compose 部署，并于次日在同机以独立 Compose 项目、网络、数据卷和端口重新解压原始实验包复现。该记录对应教学样例，原有 E13 专项验证见 `../e13-b2-recheck-298ff136/TEST_REPORT.md`。

完整补充包位于 `evidence/students/241880359/microservice-deploy/B2-Microservice-Deploy-20261126-213726.tar.gz`，大小 118,136 字节，SHA256 为 `8de8a205db69f5cd3faf02b9a8c4df8910f4374658afebd1fdc4e278a02f3445`。课程服务器原件位于 `/root/devops-submissions/241880359/` 的同名文件；本机副本已重新计算大小和哈希。

包内 `b2-deploy-20261124/` 保存首次部署的 Compose、镜像、日志、健康响应、Targets 和个人 AI 使用说明；`b2-reproduction/` 保存独立复现的对应记录。复现轮次的 `compose-up.txt` 显示 worker 健康后 API 开始启动；API、worker 的健康响应为 `ok`，Prometheus 返回 Ready，Grafana 返回 `database: ok`，`prometheus-targets.json` 中 `lab-api` 与 `lab-worker` 均为 `up`。复现方法见包内 `README.md`。

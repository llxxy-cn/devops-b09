# AI 使用记录

工具：Codex 对话与代码执行助手。

用途：读取课程 B 轨道手册和当前 main，核对 B1 既有 E8 证据，生成并执行
E9/E10 的可复现实验命令，整理证据索引、个人报告和 ADR。候选 Patch 由课程
确定性 `patch()` 函数生成，不是由外部 LLM 猜测 Makefile 修改。

人工操作：学生启动 Docker Desktop，并授权读取当前 GitHub main 和运行本地
Docker。未授权、未执行 push、PR 创建或 main 合并。

AI 执行与人工核查：

- 保留原 E8 包和提交 `7eea0ef`，没有重跑或覆盖 E8 OUT。
- 将 main `f8b13c4` 快进到本地 B1 分支后，构建学号镜像并记录完整 ID。
- 在禁网容器中运行 11 项单测、E9 三风格和 E10 三场景。
- 核对 Patch 应用、原项目状态、构建/程序输出、头文件变化重编译和
  BuildChecker `MISSING=0`。
- E9 首次运行在导入阶段失败；通过打印容器工作目录和 Python 搜索路径定位为
  `PYTHONPATH` 缺失。失败日志保留，正式 OUT 只在修正后创建。

环境声明：E8 的 9 项测试和原证据来自课程服务器；本次 E9/E10 与 11 项回归
测试来自本机 Docker Desktop Linux/amd64 引擎。未把本机运行描述成课程服务器
运行，未把未完成的跨组联调、push、PR 或 Actions 写成已完成。

# AI 使用记录

工具：Codex 对话与代码执行助手。

用途：读取课程 B 轨道手册和当前 main，核对 B1 既有 E8 证据，生成并执行
E9/E10 的可复现实验命令，整理证据索引、个人报告和 ADR。候选 Patch 由课程
确定性 `patch()` 函数生成，不是由外部 LLM 猜测 Makefile 修改。

人工操作：启动 Docker Desktop 完成本地预检，并通过 SSH 登录课程服务器，
上传已核验的 Git bundle 和执行脚本，逐段运行服务器命令，最后下载服务器证据包。
学生完成个人分支 push 并创建 PR #7；4 项 Actions 检查通过后由组长合入 main，合并提交为 4119a7f。

AI 执行与人工核查：

- 保留原 E8 包和提交 `7eea0ef`，没有重跑或覆盖 E8 OUT。
- 将 main `f8b13c4` 快进到本地 B1 分支后，构建学号镜像并记录完整 ID。
- 在禁网容器中运行 11 项单测、E9 三风格和 E10 三场景。
- 核对 Patch 应用、原项目状态、构建/程序输出、头文件变化重编译和
  BuildChecker `MISSING=0`。
- 本地预检的 E9 首次运行在导入阶段失败；通过打印容器工作目录和 Python 搜索路径定位为
  `PYTHONPATH` 缺失。失败日志保留，正式 OUT 只在修正后创建。
- 学生在课程服务器以提交 `d21c037` 和镜像 `dea80da…7eeef` 复跑 11 项单测、
  E9 三风格和 E10 三场景；Codex 对下载归档的 SHA、报告提交、项目 HEAD、Git
  状态、validation 字段、Makefile 字节和 BuildChecker findings 进行了独立核查。

环境声明：E8 原证据以及本次 E9/E10、11 项回归测试均有课程服务器证据；本机
Docker Desktop 结果只作为预检保留。未把未完成的跨组联调、push、PR 或 Actions
写成已完成。

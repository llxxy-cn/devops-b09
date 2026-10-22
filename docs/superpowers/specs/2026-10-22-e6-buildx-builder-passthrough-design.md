# E6 Buildx 构建器透传设计

## 背景

B 轨道 E6 在 DRAFT 服务容器中通过宿主机 Docker socket 执行两轮真实构建。课程服务器无法稳定访问 `registry-1.docker.io`，因此第一轮在解析固定摘要的 Python 基础镜像时失败，并被正确分类为 `INFRASTRUCTURE`，没有到达预期的 `MISSING_MAKE`。

宿主机已有名为 `e5-241880585` 的 Buildx 构建器。该构建器通过 `m.daocloud.io/docker.io` 获取 Docker Hub 内容，并设置 `max-parallelism = 1`。它仍按课程候选中固定的 digest 校验镜像内容。

## 目标

为云端实验入口增加一个可选的 Buildx 构建器参数，使 DRAFT 服务容器可以复用宿主机已经配置的构建器。改动不得改变候选 Dockerfile、候选 SHA、两轮构建逻辑、报告结构或最终禁网运行验证。

## 非目标

- 不修改候选 Dockerfile 的 `FROM`、digest 或其他指令。
- 不修改 `autobuild.py` 的失败分类和验证逻辑。
- 不修改宿主机 Docker daemon 配置，也不重启共享 Docker 服务。
- 不把 GitLab、Docker Registry 凭据或完整 `~/.docker` 目录挂载进服务容器。
- 不把课程服务器特有的构建器名称设为默认值。

## 接口设计

`scripts/lab_cloud.py` 新增可选参数：

```text
--builder NAME
```

该参数仅用于 B 轨道的 `e6` 和 `gate`。未指定时，命令行为与当前实现完全一致。

示例：

```bash
python3 scripts/lab_cloud.py e6 \
  --builder e5-241880585 \
  --candidate work/candidate/Dockerfile \
  --out work/e6-own-241880481-02 \
  --build-timeout 600
```

## 数据流

1. `lab_cloud.py` 解析 `--builder`。
2. 在启动服务容器前，通过 `docker buildx inspect NAME` 确认构建器存在且可访问。
3. 找到当前宿主用户的 `~/.docker/buildx` 目录。
4. 启动 DRAFT 服务容器时：
   - 设置 `BUILDX_BUILDER=NAME`。
   - 将宿主机 `~/.docker/buildx` 只读挂载到容器的 `/tmp/.docker/buildx`。
   - 继续使用现有的 `/var/run/docker.sock` 挂载和 docker 组号。
5. 容器内现有的 `docker build` 命令由 Buildx 插件选择指定构建器。
6. `autobuild.py` 继续生成原有的两次 attempt、镜像 ID 和 verification 报告。

只挂载 `buildx` 子目录，不挂载 `~/.docker/config.json`，从而避免向服务容器暴露宿主机 Registry 登录信息。

## 校验与错误处理

- 非 B 轨道或非 `e6`/`gate` 阶段使用 `--builder` 时，参数解析立即失败。
- 构建器名称不存在或 `docker buildx inspect` 失败时，不启动服务容器，并返回明确错误。
- 宿主机 Buildx 元数据目录不存在时，不启动服务容器，并返回明确错误。
- 不允许静默退回默认构建器，否则可能再次产生难以区分的网络失败。
- 原有 `INFRASTRUCTURE` 分类保留，用于记录真实的镜像访问故障。

## 测试设计

增加针对启动参数组装的自动化测试：

- 未传 `--builder` 时不增加环境变量或 Buildx 目录挂载。
- 传入有效 builder 时增加 `BUILDX_BUILDER` 和只读挂载。
- builder 检查失败时，在调用 `docker run` 前退出。
- 非法阶段使用 `--builder` 时拒绝执行。

验证顺序：

1. 运行新增的入口测试。
2. 重新构建服务镜像并确认原有 24 项测试通过。
3. 在课程服务器使用真实候选运行 E6。
4. 运行 `verify_e6_b_evidence.py`，确认两次 attempt、候选 SHA、镜像 ID、退出码和 `hello E3` 一致。

## 验收标准

- 第一轮到达 `RUN make`，构建非零且分类为 `MISSING_MAKE`。
- 第二轮使用 `work/candidate/Dockerfile`，构建退出码为 0。
- 报告保存第二轮生成的完整镜像 ID。
- 验证命令使用相同镜像 ID和 `--network none`。
- 程序退出码为 0，输出为 `hello E3`，`output_matches=true`。
- 总状态为 `SUCCEEDED`，证据校验器返回 `passed=true`。
- 默认、不传 `--builder` 的课程命令仍保持兼容。

## 报告说明

实验报告记录首次 E6 因 Docker Hub 超时得到 `INFRASTRUCTURE`，并说明本改动只透传宿主机已有的镜像获取配置。报告同时保留失败目录和修复后成功目录，避免覆盖原始证据。

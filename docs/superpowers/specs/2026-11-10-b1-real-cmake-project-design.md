# B1 真实 C/Make 项目设计

## 1. 目标

将本仓库 `fixtures/draft` 作为 E11–E12 的真实 C/Make 项目，并制作两个连续提交：

- C0：依赖完整，不存在 MD。
- C1：增加真实头文件依赖，但 Makefile 故意遗漏该依赖，形成一个明确的 MD。
- C0、C1 均能编译，程序输出均保持 `hello E3`。

B1 负责环境、真实项目、Dockerfile、两个提交 SHA 和复现证据。E12 流水线适配和正式联调分别由3号、4号完成。

## 2. 项目接口

- 仓库：`https://github.com/llxxy-cn/devops-b09`
- 子目录：`fixtures/draft`
- 请求参数：`project_subdir=fixtures/draft`
- 构建命令：`make clean && make`
- 程序：`app`
- 预期输出：`hello E3`

3号成员负责让 E12 流水线支持 `project_subdir`，不能假设项目位于仓库根目录。

## 3. C0 基础提交

C0 文件如下：

```text
fixtures/draft/
├── .dockerignore
├── Dockerfile.broken
├── Makefile
├── README.md
├── config.h
├── helper.c
├── helper.h
└── main.c
```

职责和验收条件：

- `main.c` 调用 `helper_message()`。
- `helper.c` 实现 `helper_message()`。
- `helper.h`声明 `helper_message()`。
- `config.h` 定义输出文本 `hello E3`。
- Makefile 明确记录全部真实头文件依赖。
- `make clean && make` 成功。
- `./app` 输出 `hello E3`。
- BuildChecker 复扫结果为 `MISSING=0`。

## 4. C1 目标提交

C1 在 C0 基础上增加 `fixtures/draft/extra.h`，并修改 `main.c`，使其实际包含和使用 `extra.h`。

Makefile 中 `main.o` 的依赖列表故意不加入 `extra.h`，预期只产生：

```text
MISSING main.o extra.h
```

约束：

- 只允许这一条 MISSING。
- 不删除已有正确依赖。
- 项目仍可编译。
- `./app` 仍输出 `hello E3`。
- C1 必须是 C0 的直接后继提交。

## 5. Docker 验证

`Dockerfile.broken` 保持缺少 `make`，构建必须失败，并在日志中出现 `make: not found`。

候选 Dockerfile必须：

- 使用 DaoCloud 可访问镜像。
- 基础镜像使用固定 digest。
- 使用清华 Debian 镜像源。
- 安装 `build-essential`。
- 构建 `app`。
- 保留 `CMD ["./app"]`。

固定基础镜像：

```text
m.daocloud.io/docker.io/library/python:3.13-slim@sha256:70729b46c69b4f1e97c4822c1af3df53a1476cf5ddc6c087c0c10bc3a5678c2f
```

## 6. B1 必须保存的证据

- 仓库 URL和 `project_subdir`。
- C0、C1 完整 SHA。
- 编译日志和程序输出日志。
- 初始 Dockerfile 构建失败日志。
- 候选 Dockerfile、镜像 ID和运行输出。
- 源码及关键产物 SHA256。
- Docker 和服务器环境信息。
- E8–E10 回归测试结果。
- E11–E12 契约测试结果。

## 7. 分工边界

B1 向2号交付两个完整 SHA、项目子目录、构建与运行命令、候选 Dockerfile、镜像 ID、原始日志，以及唯一 MD 预期 `main.o` 缺少 `extra.h`。

3号负责 `project_subdir` 流水线适配、真实项目 E12 预跑、执行镜像 ID和五阶段结果。

4号负责 A/B 正式联调、CI、PR 和最终证据汇总。

B1 不提前声称已完成 E12 全链或 A/B 正式联调。

## 8. 回归要求

修改完成后必须通过：

- E8–E10：14项测试。
- E11–E12：14项测试。

任何测试失败都不得作为最终交付。

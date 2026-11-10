# B1 E11–E12 真实 C/Make 项目交接

## 交付状态

B1 已完成环境、真实项目和 DRAFT 验证，可进行组内交接。

- 学号：241880481
- 分支：student/241880481/e11-e12
- 仓库：https://github.com/llxxy-cn/devops-b09
- 项目子目录：fixtures/draft
- C0：646b7a45814246142e064a9c13497257188ddc0d
- C1：3a4d08748169c57819b66795bfa706e2281d3fdc
- C1 的直接父提交：C0
- 程序输出：hello E3

## 真实依赖结果

C0 的 BuildChecker 结果：

- status：SUCCEEDED
- findings：0

C1 的 BuildChecker 结果：

- status：SUCCEEDED
- findings：1
- 唯一结果：MISSING main.o extra.h

C1 只相对 C0 增加 extra.h 并修改 main.c，Makefile 字节保持不变。

## 复现命令

```bash
git clone https://github.com/llxxy-cn/devops-b09
cd devops-b09
git checkout 3a4d08748169c57819b66795bfa706e2281d3fdc
cd fixtures/draft
make clean
make
make test
./app
```

预期输出：

```text
hello E3
```

后续流水线请求必须传递：

```text
project_subdir=fixtures/draft
```

## Docker 结果

课程服务器不能直接访问 Docker Hub，因此缺少 make 的失败复验副本只把原始 FROM 替换为同版本的固定 DaoCloud 镜像，其他指令保持不变。

- 失败分类：MISSING_MAKE
- 候选镜像：b1-real-cmake:241880481
- 候选镜像 ID：sha256:0a3ed554094ba093f8cabdaa0ffdea14ed7c82dea241ee51a5fa942f97daeb24
- BuildChecker 镜像 ID：sha256:af67372b3894b01f20af6f1560d3a088773f5ecf173be98e247a2facd9292ce6
- 候选容器实际输出：hello E3

候选 Dockerfile 位于 candidate.Dockerfile。

## 回归结果

- E8–E10：14项测试，OK。
- E11–E12：14项测试，OK。

## 证据

evidence 目录保留：

- 缺少 make 的失败构建日志。
- 候选镜像构建与运行日志。
- C0、C1 BuildChecker 原始 OUT 和 JSON 报告。
- 两组完整回归日志。
- Docker 环境、镜像信息和源码 SHA256。

原始服务器运行目录：

```text
work/b1-e11e12/real-project
```

本轮 BuildChecker 运行目录：

```text
work/b1-e11e12/real-project/buildchecker-run-UJwVEd
```

## 分工边界

B1 没有声称已完成 E12 五阶段、API 联调或 A/B 正式联调。

- 2号继续完成 E11-B 报告接收、修复和复验。
- 3号实现 project_subdir 适配并完成 E12 真实项目预跑。
- 4号完成 A/B 正式联调、最终 CI 和整组交付。

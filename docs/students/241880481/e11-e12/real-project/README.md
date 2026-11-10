# B1 E11–E12 真实 C/Make 项目交接

## 项目接口

- 学号：241880481
- 分支：student/241880481/e11-e12
- 仓库：https://github.com/llxxy-cn/devops-b09
- 项目子目录：fixtures/e11e12-b1-real
- C0：30ffe4c41492334478a2446a8be0662d3f31d478
- C1：a7e3b644ca9b1b9d0b26bd41e839fcbf5ea1c293
- 构建：make clean && make
- 测试：make test
- 运行：./app
- 预期输出：hello E3

C1 是 C0 的直接后继，只增加 extra.h 并修改 main.c。Makefile 字节保持
不变。

## 依赖检测结果

- C0：BuildChecker SUCCEEDED，findings=0。
- C1：BuildChecker SUCCEEDED，findings=1。
- 唯一结果：MISSING main.o extra.h。

## DRAFT 结果

- 初始失败分类：MISSING_MAKE。
- 候选镜像：b1-real-cmake:241880481。
- 候选镜像 ID：sha256:26d11433384c143d3a1e1b799a3d6f93f45045934671fe19627861e60ee313cb。
- DRAFT 实际候选镜像 ID：sha256:5171384d5e8c1a9972487ccbca8f62598f3a50797de28010025fddbe18872f02。
- 容器实际输出：hello E3。
- DRAFT 状态：SUCCEEDED。

## E7 兼容性

旧目录 fixtures/draft 是 E7 共享输入，已经恢复到变更前状态。E11–E12
真实项目放在独立目录，避免两个实验相互影响。

课程服务器无法访问 registry-1.docker.io，因此 E7 完整门禁无法在服务器
复验；E7 的12项入口测试通过，正式完整结果以本 PR 的 GitHub Actions 为准。

## 回归

- E7 入口测试：12项，OK。
- E8–E10：14项，OK。
- E11–E12：14项，OK。

## 复现

```bash
git checkout a7e3b644ca9b1b9d0b26bd41e839fcbf5ea1c293
cd fixtures/e11e12-b1-real
make clean
make
make test
./app
```

后续请求必须传递：

```text
project_subdir=fixtures/e11e12-b1-real
```

## 分工边界

B1 完成环境、真实项目、候选 Dockerfile、DRAFT 和交接证据。

- 2号继续 E11-B 报告接收、修复和复验。
- 3号实现 project_subdir 适配并完成 E12 真实项目预跑。
- 4号完成 A/B 正式联调、最终 CI 和整组交付。

B1 未声称已经完成 E12 五阶段或正式 A/B 联调。

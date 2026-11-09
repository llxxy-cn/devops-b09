# B1 E9/E10 证据索引

实验源码 SHA：`f8b13c4fd138670404f2e30f1347f50193291151`
镜像 ID：`sha256:8a87e31f1a3f6a64aca0a3d63016d622993ac68a21945a8836e3e3a4c1e8006c`

## 环境与测试

- `environment-image-id.txt`：完整镜像 ID。
- `environment-build-exit.txt`：镜像构建退出码。
- `student-source-commit.txt`：E9/E10 运行时外层源码 SHA。
- `all-unit-tests.log`：当前 main 上 11 项完整回归测试。

## E9

每个风格包含 `e9-<style>-input.json`、Patch、plan、apply-check 日志和项目状态。
`e9-gate.json`、`e9-results.csv`、`e9-run.log` 为阶段汇总。空的 apply-check 和
project-status 文件分别表示命令无错误输出、原项目 Git 工作区干净。

## E10

- `e10-fixed-md-report.json`、候选、计划和接受前后 Makefile 字节副本。
- 三个 validation JSON 分别对应测试拒绝、正常接受和无效 Patch 拒绝。
- 接受场景的全量构建及增量重编译日志。
- BuildChecker findings、实际图、声明图和进程记录。
- 最终构建日志、程序输出、results 和 gate。

完整 OUT（含内部 `.git`、sandbox、trace 和全部日志）保留在：

- `work/e9-B-241880481-20261109-01`
- `work/e10-B-241880481-20261109-01`
- `work/b1-e9-e10-20261109`

这些 `work/` 路径按仓库规则忽略；仓库外归档包用于保存完整原始目录。
归档包为 `B1-E9-E10-20261109-01.tar.gz`，SHA256：
`9A552A09D30A1434108A19C2FB94CC4EEA22E35BAA01340C896643A3DEA5F617`。

## 课程服务器复跑

`server/` 是在课程服务器 Ubuntu 22.04、Linux/amd64 Docker 中生成并从服务器
归档包核验后复制的关键证据：

- 外层源码 SHA：`d21c0370967025311ff5d56b61839d54b0ed5511`
- 镜像 ID：`sha256:dea80da01e6ada32362ac221423048dc9e3ffaac4763858fce560fdd6887eeef`
- E9 OUT：`work/e9-B-241880481-20261109-server-01`
- E10 OUT：`work/e10-B-241880481-20261109-server-01`
- 11 项单测通过；E9 三风格通过；E10 三场景通过；BuildChecker `MISSING=0`。
- `server/terminal-transcript.txt`：学生回传的服务器运行终端原始文本。
- `server/archive-sha256.txt`：服务器归档文件名与 SHA256。

服务器完整包：`B1-E9-E10-SERVER-20261109-01.tar.gz`，SHA256：
`DCDD708FD39AFA7BF02688EFA738CC93A35FEE23FB67352F011E4188F9F517DE`。

## GitHub 交付

- 个人最终提交：`17db5f1784a1da9e01d779aad92935fc7185db78`
- PR：https://github.com/llxxy-cn/devops-b09/pull/7
- Checks：4 项全部通过
- 合并提交：`4119a7fe87d22be15d61bb5348f9ec39ef114679`
- 状态：已合入 `main`

# B09 1 号 E13/E14 本地预检记录

- 学号：241880481
- 分支：`student/241880481/e13-e14-b1`
- 核实基线：`origin/main` / `80b4dafb836365911e6e85451ee367cc874afa46`
- 本轮定位：PR #17 的测试为“E12 归档回归 / E13 预检”；正式 C1–C3 为“等待 A09 配对输入”。
- 边界：未推送、未开 PR、未发送外部消息；课程服务器实测待学生手工执行随附脚本。

## 本地实测结果

本地环境为 Docker Desktop Linux/amd64，课程镜像 `course-e11e12:241880481` 的镜像 ID 为
`sha256:c05161dd7e5d2ae962a86b6db293f731a609cd358d0082d6a0f17b15203cb188`。

| 项目 | 实际结果 | 主要证据 |
| --- | --- | --- |
| 修改后完整单元回归 | E11/E12 23/23 通过；E13 交接 3/3 通过；退出码 0 | `work/e13-b1-20261117-final-verification/full-regression.log` |
| B09 固定样例五阶段 | `SUCCEEDED`，五阶段均完成，退出码 0 | `work/e13-b1-20261117-baseline/e12-sample-console.log`、`work/e13-b1-20261117-baseline/e12-sample-01/result.json` |
| 交换候选 base | `make clean && make`、`make test`、`./app` 均为 0；输出 `hello E3` | `work/e13-b1-20261117-candidate/base.log` |
| 交换候选 target | 三条命令均为 0；输出 `hello E3`；依赖扫描命中 `MISSING(main.o, extra.h)` | `work/e13-b1-20261117-candidate/target.log`、`target-findings-git-env.log` |
| A09 归档与原始报告 | 两个固定 SHA256 均匹配，报告/仓库 target 均为 `15c0599…ad28` | `work/e13-b1-20261117-a09-valid/command.log` |
| C2 预检 | 退出码 1，`STALE_REPORT`，未生成补丁 | `work/e13-b1-20261117-c2-stale/command.log` |
| C3 预检 | 原件 `8508d5…8716`，追加 LF 后 `6301fa…c501`；退出码 1，`ARTIFACT_HASH_MISMATCH`，未生成补丁 | `work/e13-b1-20261117-c3-tampered/command.log` |
| 恢复正确输入 | 退出码 0，重新生成补丁 | `work/e13-b1-20261117-a09-restored/command.log` |
| 正式 e11-b 正确报告 | `SUCCEEDED`，退出码 0 | `work/e13-b1-20261117-formal-valid/console.log`、`run/result.json` |
| 正式 e11-b C3 | 退出码 1，`ARTIFACT_HASH_MISMATCH`，未生成补丁 | `work/e13-b1-20261117-formal-c3/console.log`、`run/result.json` |

固定样例本地运行身份：job `job-c7707b8b720e4fb7b952c898f6812ed4`，trace
`trace-c7622732bc3947c49e7e3d97b2ca3377`。正式入口正确报告运行身份：job
`job-e198d275100d4773bedabfa810f264a0`，trace `trace-af904bee9d584ad18ad1fa108b91e3bb`。

## A09 归档消费和交接身份

- 归档 SHA256：`19479d51720decbca2518453e00646a4700c7b21101b018965bfdbc0c8cce648`
- 原始报告 SHA256：`8508d50232bfa4a529d51accd4dc94e5765a0fe0a0b130eebf73f8f866a98716`
- 原始报告 job：`job-1bd0ed1b449f44f293853df90440844f`
- 原始报告 trace：`trace-4e7c0c6afd0447f9869d2f5e1ee6f4ae`
- 原始报告 URI：`artifact://job-1bd0ed1b449f44f293853df90440844f/incremental-check.json`
- 兼容信封 SHA256：`09e270d76e30d0f10318acd35ce2d2eed8a6f7fec28024676dd5a575271941e5`
- 信封证据：`work/e13-b1-20261117-formal-valid/handoff.log`、`fixed-md.json`

## 交换候选与 Dockerfile 身份

- base：`30ffe4c41492334478a2446a8be0662d3f31d478`
- target：`a7e3b644ca9b1b9d0b26bd41e839fcbf5ea1c293`
- Dockerfile：`docs/students/241880481/e11-e12/real-project/candidate.Dockerfile`
- 首次加入提交：`9372762b7f309f0858af1bad5ec377d5a98cdcb2`
- 最后修改提交：`64ee8c559ca378ace6a08a53d335955eb526e896`
- Git blob：`1ac9b9bb9b73aeca1bec290eb626048b221b6944`
- 文件 SHA256：`01bc301fc7b96ece8ec4bbbf68ec03469a6c81bbc516c17d75f6ff240cfc9a4b`
- 证据：`work/e13-b1-20261117-candidate/candidate-dockerfile.log`

## 本轮代码改动

`labs/e11e12/pipeline.py` 的 e11-b 正式入口现在在请求包含 `fixed_report_sha256` 时复用现有
`load_artifact` 字节校验；旧请求未提供该字段时仍按原有路径读取，保持兼容。新增三项契约测试覆盖正确哈希、篡改拒绝和旧调用兼容。

加入课程发放的 `labs/e13e14/handoff_a_to_b.py` 及其测试，用于把 E12 归档中的原始
`incremental-check` 报告转换为 e11-b 兼容信封，并保留源 job、trace、URI 和 SHA256。

## 课程服务器执行

脚本：`docs/students/241880481/e13-e14/run-server-preflight.sh`

在课程服务器登录后进入这份个人分支的仓库根目录，执行：

```bash
bash docs/students/241880481/e13-e14/run-server-preflight.sh
```

脚本为每次执行创建唯一的 `work/e13-b1-server-YYYYmmdd-HHMMSS/`。每一步均有 `.log` 原始输出和
`.exitcode`；`summary.tsv` 汇总退出码。C2/C3 的预期程序退出码是 1，脚本会核对错误类别和“无补丁”，
随后恢复正确报告再跑一次。脚本自身最终返回 0 表示所有成功/拒绝断言均符合预期。

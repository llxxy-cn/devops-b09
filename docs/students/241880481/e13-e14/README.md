# B09 1 号 E13/E14 正式交叉联调记录

- 学号：241880481
- 分支：`student/241880481/e13-e14-b1`
- 核实基线：`origin/main` / `80b4dafb836365911e6e85451ee367cc874afa46`
- 本轮定位：A09 固定 head `269827d05d99845a9aca7a8b9f122e9a17a3741a` 的正式 E13 C1–C3；历史预检继续保留下方。
- 边界：未开 PR、未发送外部消息；服务器结果已回收并完成个人分支交付。

最终状态：**服务器实测通过，A09 已核验签收**。A09 于 2026-11-23 正式确认签收；
[签收原文](../../../../evidence/students/241880481/e13-e14/A09-SIGNOFF-20261123.md)与
[交付勘误](../../../../evidence/students/241880481/e13-e14/ERRATA-20261123.md)已归档，关联交付提交为
`cbf90cce6fcb4950c6326704bd970f9ed80693bb`，回传包 SHA256 保持
`1a1419b6359448b7e39033899d287ed85fd44d0ca054299e238cc55d1645ba33`。

## 2026-11-22 正式 C1–C3 本地实测

正式输入为 A09 项目 base `e825395a5f8006f1c57a115cc25ea5c7802863ee`、target
`ba688c40d13cd8658e554f7544f1546d35b4b397`。原始增量报告来自 job
`job-131c4b1d8c34469aaa31f9e2a9da1736`、trace `trace-c224eaab92394b91bedfc2dea14ebc61`，
URI 为 `artifact://job-131c4b1d8c34469aaa31f9e2a9da1736/incremental-check.json`，SHA256
`504a3c505c1479c990f59143926247a2deb7415375de5d957a2d4938aefff224`，大小 3052 字节。
构建或修复开始前均校验了 target、来源身份、URI、字节哈希和大小。

| 场景 | 本地实际结果 | job / trace |
| --- | --- | --- |
| C1 正常链路 | `SUCCEEDED`；6 条 MD 全修复，GCC 与最终 full 均 MD=0、RD=1（`main.o -> unused.h`） | `job-b539c2a12ec742cdabceb1c268c911a3` / `trace-6d0319973353430390bd7dc072e89a4f` |
| C2 旧报告 | 实际退出码 1，`STALE_REPORT`；无 `draft-build`、补丁或 sandbox | `job-fddb848e8f5443599034813d01885b2b` / `trace-591988218d6c4201baf863375c7c95f9` |
| C3 字节篡改 | 实际退出码 1，`ARTIFACT_HASH_MISMATCH`；无 `draft-build`、补丁或 sandbox | `job-5a0c719bfd334fe3b14af1e2f8fdda33` / `trace-09935bd7b7ff408891756d94ab614505` |
| 正确输入恢复 | 新目录重跑 `SUCCEEDED` | `job-a80cae7a3e9945fab6b7e801dd6f6be9` / `trace-23aa000e0a6c45068dbc47a24271ddef` |

C1 验证对 `main.o` 的 `calculate.h/config.h/extra.h` 和 `helper.o` 的
`add.h/calculate.h/sub.h` 分别触碰，6 次均观察到对应 `.o` 时间戳增加且输出仍为 `1`。
独立修复提交为 `7e5fe9f826ebc94854dbc312259ec215882053c4`，父提交严格为 A09 target；原始
target 仓库保持未修改。完整证据和交接索引见 [formal/README.md](formal/README.md)。

服务器 DRAFT 的 Docker Hub 超时已适配为离线构建：A09 原始 candidate 文件保留原哈希，服务器
明确消费派生 `offline-candidate.Dockerfile` 和 `offline-base.tar`；首轮仍验证 `MISSING_MAKE`，
候选轮使用镜像内工具副本，不执行 apt 或外网访问。

## 2026-11-22 服务器正式 C1–C3（服务器实测通过，A09 已核验签收）

服务器证据根为 `work/server-evidence/e13-b1-server-formal-20261122-195038/`，服务器仓库为
`/root/devops-b09-e13-offline.AXJSHY`。系统代码提交为 `1cd48d2ccb92b3a48b169da723bc570bd5dd6fa2`，
课程镜像 ID 为 `sha256:af67372b3894b01f20af6f1560d3a088773f5ecf173be98e247a2facd9292ce6`，
脚本断言 `FAILURES=0`、`FORMAL_EXIT_CODE=0`。

| 场景 | 服务器结果 | job / trace |
| --- | --- | --- |
| C1 | `SUCCEEDED`；最终 MD=0，RD=1（`main.o -> unused.h`）；6/6 修复边均 `rebuilt=true` 且 `output_matches=true` | `job-ec9901a266654aabb0f3c31ecc0fd697` / `trace-b9ce4c04ed934430815be6d7fc346aff` |
| C2 | 实际退出码 1，`STALE_REPORT`；拒绝后无补丁、无候选应用 | `job-0c0a865d138f4249b2ef1c7f3e7791da` / `trace-99fd2dbb1b0a4bd084ab4d551e81dd7a` |
| C3 | 实际退出码 1，`ARTIFACT_HASH_MISMATCH`；拒绝后无补丁、无候选应用 | `job-19d998dafff0457d8fa862b7bc784360` / `trace-828731512d364995b7f6b3af1e040014` |
| 恢复 | 正确输入新目录重跑 `SUCCEEDED` | `job-d7ff2505c71b4406aa8334467e5fb24a` / `trace-e0ac2f893d5c46018f124a3467682932` |

服务器修复提交为 `74eff064e1eae3e244b0acf80880c92fb4635e26`，父提交为 A09 target
`ba688c40d13cd8658e554f7544f1546d35b4b397`。服务器交付物哈希来自本轮
`deliverables/SHA256SUMS`；A09 可直接校验的回传包为
`work/e13-b1-formal-20261122-121914/deliverables/a09-e13-b09-server-return-20261122-195038.tar.gz`，
SHA256 `1a1419b6359448b7e39033899d287ed85fd44d0ca054299e238cc55d1645ba33`，包内
`return-manifest.json` 与 `SHA256SUMS` 记录每个文件的字节数和哈希。

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

正式 C1–C3 使用 `docs/students/241880481/e13-e14/run-server-formal-c1-c3.sh`；准确命令见
[formal/README.md](formal/README.md)。本轮最终状态标记为“服务器实测通过，A09 已核验签收”。

在课程服务器登录后进入这份个人分支的仓库根目录，执行：

```bash
bash docs/students/241880481/e13-e14/run-server-preflight.sh
```

脚本为每次执行创建唯一的 `work/e13-b1-server-YYYYmmdd-HHMMSS/`。每一步均有 `.log` 原始输出和
`.exitcode`；`summary.tsv` 汇总退出码。C2/C3 的预期程序退出码是 1，脚本会核对错误类别和“无补丁”，
随后恢复正确报告再跑一次。脚本自身最终返回 0 表示所有成功/拒绝断言均符合预期。

## 2026-11-17 课程服务器预检

- 实测提交：`d59745c81e4613292e9b44a3a05f8853806bb43a`
- 结果：29 项断言通过，`FAILURES=0`。B09 固定样例五阶段和交换候选检查通过。
- A09 PR #17 归档和原始增量报告校验通过。C2 返回 `STALE_REPORT`，C3 返回 `ARTIFACT_HASH_MISMATCH`，均未生成补丁。恢复原始报告后成功生成补丁。
- 服务器证据目录：`/root/devops-b09-e13-b1.hH7koO/work/e13-b1-server-20261117-160640/`，汇总见 `summary.tsv` 和 `assertions.log`。
- 正式 E13 C1–C3：A09 输入已到齐，本地验证完成；服务器正式脚本待学生执行。

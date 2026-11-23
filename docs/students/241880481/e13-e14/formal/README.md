# B09 → A09 E13 正式交付索引

本文记录 B09 本地与课程服务器正式实测。服务器结果以新证据目录中的 `assertions.log`、
`summary.tsv` 和各 case 的 `result.json` 为准，不复用本地 job/trace。

## 固定输入与双向身份

- A09 固定 head：`269827d05d99845a9aca7a8b9f122e9a17a3741a`（PR #20）。
- A09 项目：base `e825395a5f8006f1c57a115cc25ea5c7802863ee`，target `ba688c40d13cd8658e554f7544f1546d35b4b397`；bundle SHA256 `40510b4c02a05b0ce372ee7870c53ca4d4f32978599e93d8c7ac1b3a2e319072`。
- A09 报告：job `job-131c4b1d8c34469aaa31f9e2a9da1736`，trace `trace-c224eaab92394b91bedfc2dea14ebc61`，incremental SHA256 `504a3c505c1479c990f59143926247a2deb7415375de5d957a2d4938aefff224`，3052 字节。
- 原始候选 Dockerfile 保持不变，SHA256 `6f0e3980c609a683d727c271bdd3a8d5f12b46df21f1fcc402e0d8420ce06c28`；服务器 DRAFT 因 Docker Hub 超时改用派生候选 `offline-candidate.Dockerfile`，SHA256 `42fa65f92cc2fb57e321f4c4ffbe9e657df0c0bb0326d62247fa8c86145f755c`。
- 离线基础镜像包 `offline-base.tar` SHA256 `73633301ead922a8ed8635751e133b1090f6d447c76626ad87f62eb0d6e955ff`；加载后标签 `b09-e13-offline-python:3.13-slim`，digest `sha256:af8922b2323b530a21bb406e3f38cae8488ad32f92555f27ab15538a7feb40b4`，平台 `linux/amd64`。该镜像保留 `/opt/offline-toolchain/make`，但移除 `/usr/bin/make`。
- B09 项目：base `30ffe4c41492334478a2446a8be0662d3f31d478`，target `a7e3b644ca9b1b9d0b26bd41e839fcbf5ea1c293`。
- A09 对 B09 的报告：job `job-f18dbac70128426dbea57fc516b19ce3`，trace `trace-59fad11cb5db435e8676aa2541847a1b`；full 与 incremental 均为 `MISSING(main.o, extra.h)`，构建和测试成功、输出 `hello E3`。

每个方向均先核对 full-check 的 `commit`，再解释 findings；A09 原始证据包经拒绝绝对路径、`..`、链接和设备文件的检查后才解包。

## 本地正式结果和证据

证据根：`work/e13-b1-formal-20261122-121914/`。课程镜像 ID：
`sha256:c05161dd7e5d2ae962a86b6db293f731a609cd358d0082d6a0f17b15203cb188`。

- 材料和项目断言：`materials-assertions.log`；原始输入仓库：`input-project/`。
- C1：`c1/console.log`、`c1/assertions.log`、`c1/run/result.json`。结果 `SUCCEEDED`；修复 6 条 MD；逐边重建 6/6；最终 MD=0，RD=1。
- C2：`c2/console.log`、`c2/run/result.json`。实际退出码 1，`STALE_REPORT`，拒绝发生在 DRAFT 前且没有补丁或候选目录。
- C3：`c3/console.log`、`c3/run/result.json`。原 handoff SHA256 `9931900400d8fabe3c76e463ab9f885662aaa58ed6be2e3aaf7dcc6d8e5bb025`，追加 LF 后 `f14e53d9a95fe88852e1ef6b59c8333966cae32bc05da20e1a1509f3a0611f47`；实际退出码 1，`ARTIFACT_HASH_MISMATCH`，没有补丁或候选目录。
- 恢复：`recovery/console.log`、`recovery/run/result.json`，在新目录成功。
- 独立验证：`independent-fixed-validation/console.log`，6 条依赖分别触碰且对应对象均重建、输出均为 `1`。
- 离线两轮 Docker 验证：首轮 `make: not found`、退出码 1；派生候选构建退出码 0，容器输出 `1`。两轮均使用 `--pull=false`，候选没有 `apt-get` 或其他联网步骤。

修复提交 `7e5fe9f826ebc94854dbc312259ec215882053c4` 的父提交为 A09 target，bundle SHA256
`08cf6208d6555ab06e3dcb9cc417d60b80784f25ef6a225349d3a8fa74fab5c5`。候选补丁 SHA256
`8634d2aa57acc132ddf21ef90fa087aca1a313aca37a7bc74bb9b5ce9bf29c6e`。

服务器交付物的提交、字节数、SHA256 以证据目录
`work/server-evidence/e13-b1-server-formal-20261122-195038/deliverables/SHA256SUMS` 为准。
可交给 A09 的整理包为
`work/e13-b1-formal-20261122-121914/deliverables/a09-e13-b09-server-return-20261122-195038.tar.gz`，
SHA256 `1a1419b6359448b7e39033899d287ed85fd44d0ca054299e238cc55d1645ba33`；包内
`return-manifest.json` 是可机器核对的文件清单。原始交换材料包 SHA256 为
`d5af6ccf3d7b9dcc5fbe5e77c07cf4b4df663a4239a8621eb93cb98961c5305e`。

## 服务器正式结果（服务器实测通过，A09 已核验签收）

A09 于 2026-11-23 正式确认签收。签收对象关联交付提交
`cbf90cce6fcb4950c6326704bd970f9ed80693bb` 和回传包 SHA256
`1a1419b6359448b7e39033899d287ed85fd44d0ca054299e238cc55d1645ba33`；
[签收原文](../../../../../evidence/students/241880481/e13-e14/A09-SIGNOFF-20261123.md)与
[勘误说明](../../../../../evidence/students/241880481/e13-e14/ERRATA-20261123.md)已归档。

- 证据根：`work/server-evidence/e13-b1-server-formal-20261122-195038/`；断言 `FAILURES=0`，脚本
  `FORMAL_EXIT_CODE=0`。
- 系统提交：`1cd48d2ccb92b3a48b169da723bc570bd5dd6fa2`；服务器镜像：
  `sha256:af67372b3894b01f20af6f1560d3a088773f5ecf173be98e247a2facd9292ce6`。
- C1 B job/trace：`job-ec9901a266654aabb0f3c31ecc0fd697` /
  `trace-b9ce4c04ed934430815be6d7fc346aff`；验证 `accepted=true`、build/test/edge_rebuilds/no_missing
  全为 true，6 条边全部重建。final recheck SHA256 `85fd1aa62fbdbec19b9625e6ef559be8867a698c3541afdffa3e0abade0e2fe1`，
  `MISSING=0`，仅保留 `REDUNDANT(main.o, unused.h)`。
- C2：job `job-0c0a865d138f4249b2ef1c7f3e7791da` / trace
  `trace-99fd2dbb1b0a4bd084ab4d551e81dd7a`，退出码 1，`STALE_REPORT`；C3：job
  `job-19d998dafff0457d8fa862b7bc784360` / trace `trace-828731512d364995b7f6b3af1e040014`，
  退出码 1，`ARTIFACT_HASH_MISMATCH`。两次拒绝后均无补丁生成或候选应用。恢复 job/trace 为
  `job-d7ff2505c71b4406aa8334467e5fb24a` / `trace-e0ac2f893d5c46018f124a3467682932`，成功。
- 服务器修复提交 `74eff064e1eae3e244b0acf80880c92fb4635e26`，父提交
  `ba688c40d13cd8658e554f7544f1546d35b4b397`。A09 来源仍为 job
  `job-131c4b1d8c34469aaa31f9e2a9da1736`、trace `trace-c224eaab92394b91bedfc2dea14ebc61`、
  URI `artifact://job-131c4b1d8c34469aaa31f9e2a9da1736/incremental-check.json`、SHA256
  `504a3c505c1479c990f59143926247a2deb7415375de5d957a2d4938aefff224`、3052 字节。

## 给 A09 的回传消息草稿

> B09（241880481）已消费你方固定 head `269827d…741a` 的 A09 项目和报告。服务器正式 C1–C3
> 实测通过（`FAILURES=0`）：6 条有效 MD 全部修复并逐边重建验证，最终 MD=0，RD 如实保留
> `main.o -> unused.h`。服务器修复提交为 `74eff064…5e26`，父提交是 `ba688c40…b397`；
> 回传包 `a09-e13-b09-server-return-20261122-195038.tar.gz` 的 SHA256 为
> `1a1419b6…45ba33`，包内有 bundle、patch、validation、edge-rebuilds、final-recheck、原始/派生
> Dockerfile、离线镜像包映射和机器清单。C2 返回 `STALE_REPORT`，C3 返回
> `ARTIFACT_HASH_MISMATCH`，两次均未生成或应用候选。离线映射为原始
> `python:3.13-slim@sha256:70729b…678c2f` → `b09-e13-offline-python:3.13-slim@sha256:af8922…b40b4`；
> 原 candidate SHA256 `6f0e3980…06c28`，派生 candidate SHA256 `42fa65f9…f755c`。
> 服务器实测通过，A09 已核验签收。

## 给 2 号：C4/C5/C7/C8 输入

使用同一 A09 bundle、base/target、`candidate.Dockerfile` 和已校验 handoff。成功请求模板就是服务器证据目录
`inputs/request-c1.json`，其中显式兼容配置仅为：

```json
{"layout":"root-make","make_test":false}
```

构建/断言为 `make clean && make app && test "$(./app)" = "1"`。报告预期来源必须保持上述 A09
job、trace、URI、SHA256 和 3052 字节；不要改用本地 C1 生成的 B job/trace。

## 给 3 号：门禁证据索引

依次核对 `materials-assertions.log`、`c1/assertions.log`、`c2/run/result.json`、
`c3/run/result.json`、`recovery/run/result.json`、`independent-fixed-validation/console.log` 和
`deliverables/SHA256SUMS`。服务器侧对应文件位于脚本打印的 `SERVER_EVIDENCE_DIR`，以
`FAILURES=0` 为门禁条件。

## 给 4 号：真实项目运行参数

- repo：A09 bundle 解出的仓库根目录（不是子目录）。
- base/target：`e825395…63ee` / `ba688c4…b397`。
- candidate：交换目录中的 `candidate.Dockerfile`；`expected_output` 为字符串 `1`；timeout 600 秒。
- 构建：`make clean`、`make app`；项目没有 `make test`，使用输出断言。
- 真实依赖：`main.o -> main.c calculate.h config.h extra.h`；`helper.o -> helper.c add.h calculate.h sub.h`。

## 服务器上传、运行和回收

在本机仓库根目录执行（把服务器地址按实际情况替换）：

```bash
scp work/e13-b1-formal-20261122-121914/deliverables/b09-e13-b1-code.bundle root@COURSE_SERVER:/root/
scp work/e13-b1-formal-20261122-121914/deliverables/e13-a09-fixed-materials.tar.gz root@COURSE_SERVER:/root/
```

在课程服务器执行：

```bash
cd /root
git clone b09-e13-b1-code.bundle devops-b09-e13-b1-formal
cd devops-b09-e13-b1-formal
git switch student/241880481/e13-e14-b1
git config --local user.name 241880481
git config --local user.email 241880481@example.invalid
mkdir -p work/e13-a09-fixed-materials
tar -xzf /root/e13-a09-fixed-materials.tar.gz -C work/e13-a09-fixed-materials
bash -c 'sha256sum work/e13-a09-fixed-materials/exchange-a09-to-b09/offline-base.tar'
bash -c 'docker load -i work/e13-a09-fixed-materials/exchange-a09-to-b09/offline-base.tar'
bash docs/students/241880481/e13-e14/run-server-formal-c1-c3.sh work/e13-a09-fixed-materials
```

脚本会先校验并执行 `docker load -i exchange-a09-to-b09/offline-base.tar`，再只消费
`offline-candidate.Dockerfile`；原始 `candidate.Dockerfile` 只用于哈希和来源核对。C1 若失败，
脚本立即保留证据并退出，不会创建修复提交或交付包。

记录脚本末尾打印的绝对 `SERVER_EVIDENCE_DIR`。在本机 PowerShell 回收（替换目录名）：

```powershell
scp -r root@COURSE_SERVER:/root/devops-b09-e13-b1-formal/work/e13-b1-server-formal-YYYYMMDD-HHMMSS work/server-evidence/
```

脚本的 C2/C3 被测程序退出码应为 1，但脚本最终退出码应为 0；最终必须看到 `FAILURES=0`。

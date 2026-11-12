# E11–E12 B 组第四人：正式联调记录

> 本目录记录实际完成的事项。带“待完成”的项目不得作为验收结果引用。

## 源码与基线

- 仓库：`llxxy-cn/devops-b09`
- 四号个人分支：`student/241880556/e11-e12-b4`
- 起点：B3 提交 `a8e6a0b2663c50b69ac45b2d359ff45c37e12e8f`
- B3 PR：[ #13 ](https://github.com/llxxy-cn/devops-b09/pull/13)，本目录建立时仍开放
- B3 的 E7、E8–E10、E11–E12 CI 在该提交均成功；这不是四号最终 CI
- 四号最终提交：待完成

本机在该起点直接运行 `unittest discover`：20 项中 19 项通过、1 项因需要 Linux 课程主机而跳过。B3 的 Linux CI 已成功；正式课程服务器测试仍待四号重跑。

## 已获取的基线证据

GitHub Actions 的 B3 E11–E12 工作流运行 ID 为 `43188774642`，产物 `e11e12-evidence-43188774642` 的 SHA256 为 `95ce6ccab051f4b6ee0f07ae248b0e903afd393ef96100e207cf8b70f4d4baf6`。已下载并核对该 ZIP 哈希。内含 CI 固定样例 `ci-e12` 的五阶段结果；该产物不包含 A/B 正式交接，也不是 B3 课程服务器的两个预跑 job。

逐项校验该 ZIP 时，E12 清单中 187 个文件有 180 个在 ZIP 内且 SHA256、长度吻合；7 个 `.gitignore` 因 `upload-artifact` 默认排除隐藏文件而缺失。四号分支调整工作流以包含这些文件，并排除克隆副本的 `.git` 目录。新 CI 完成后须再次逐项核对。

B3 课程服务器证据包路径为 `/root/devops-submissions/241880585/e12-b3-20261112-161448.tar.gz`，交接 SHA256 为 `f9ee5c3545897873e62dd12d2b05fad4c73c470326160cb2e493d1a8a7ed720b`。**待完成：**取得服务器访问，校验并检查包内两份 `verification.json`。

Windows 检出会因 `core.autocrlf=true` 将 B1 候选 Dockerfile 转成 CRLF，工作树 SHA256 与 B1 交接值不同；按 LF 还原后的 SHA256 与 `1fa4739abd325c84e0ed4b3bbdcbcaf39c7c500fc0d80ba4707216e5cbe21a64` 一致。正式镜像构建须在 Linux 服务器重新核对文件字节哈希。

## 正式 A/B 接口交接（待完成）

记录 A 组负责人、API 主机、SSH 转发、`base`/`target` 完整提交、项目路径、候选 Dockerfile SHA256、原始报告文件/URI、原始字节 SHA256、`schema_version`、`kind`、`commit`、交付时间。保留原始报告和交接记录；不得把 B3 预跑报告充作 A 组报告。

当前 B 端独立接收入口：

```bash
sha256sum <A组原始增量报告.json>
git -C <target工作副本> rev-parse HEAD
python3 labs/e11e12/repair_report.py \
  --project <target工作副本中的项目目录> \
  --report <A组原始增量报告.json> \
  --sha256 <A组提供的原始报告SHA256> \
  --kind incremental-check \
  --out <本轮证据目录>/candidate.patch
```

入口会检查 `e11e12-1`、报告类型、状态、目标提交及文件 SHA256。补丁生成后，在独立干净副本上检查并应用，再构建、测试、运行、复检；另外保存旧报告 `STALE_REPORT` 和篡改内容 `ARTIFACT_HASH_MISMATCH` 的拒绝证据。

## 正式五阶段 API（待完成）

使用新幂等键分别提交固定样例和 B1 真实项目。真实项目使用 `fixtures/e11e12-b1-real`，C0=`30ffe4c41492334478a2446a8be0662d3f31d478`，C1=`a7e3b644ca9b1b9d0b26bd41e839fcbf5ea1c293`；唯一预期 MD 为 `main.o → extra.h`，程序输出 `hello E3`。正式请求、`job_id`、`trace_id`、五阶段状态、报告 URI、补丁与镜像 ID 在运行后填入，保留 `preflight_api.py` 的 `verification.json` 和下载哈希。

`mode=e12` 当前在本 job 内生成增量报告。A 组外部报告按上一节由 B 端单独接收；若正式接口约定要求直接注入外部报告，须先更新接口和实现并重新验证。

## 最终交付（待完成）

- 四号 PR 与 review、最终源码提交 SHA
- 四号提交及合并后 `main` 的 E7、E8–E10、E11–E12 CI 链接
- A→B 报告交接、独立修复复验、两个正式 API job 的证据索引
- 真实项目记录、证据包 SHA256、个人报告与 ADR

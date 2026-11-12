# E11–E12 B 组第四人：正式联调记录

> 本目录记录实际完成的事项。带“待完成”的项目不得作为验收结果引用。

## 源码与基线

- 仓库：`llxxy-cn/devops-b09`
- 四号个人分支：`student/241880556/e11-e12-b4`
- 起点：B3 提交 `a8e6a0b2663c50b69ac45b2d359ff45c37e12e8f`
- B3 PR：[#13](https://github.com/llxxy-cn/devops-b09/pull/13)，已于 2026-11-13（北京时间）合并到 `main`，合并提交 `ffe52ed5501dd903a5030bbf907189cc18b5f299`
- B3 的 E7、E8–E10、E11–E12 CI 在该提交均成功；这不是四号最终 CI
- 四号当前提交：`0518cb9cee0c0a72ddbd064f24f0b5b3b69fc932`；最终提交待正式联调后确定
- 四号草稿 PR：[#14](https://github.com/llxxy-cn/devops-b09/pull/14)，当前直接以 `main` 为 base

本机在该起点直接运行 `unittest discover`：20 项中 19 项通过、1 项因需要 Linux 课程主机而跳过。四号课程服务器重新运行 `python3 run_e11e12.py test`，20 项全部通过。四号环境镜像 ID 为 `sha256:0f14125df9d889f01f0f9cf1ab37c0a216d8e26212cca99504a6304b19f3701f`。

## 已获取的基线证据

GitHub Actions 的 B3 E11–E12 工作流运行 ID 为 `43188774642`，产物 `e11e12-evidence-43188774642` 的 SHA256 为 `95ce6ccab051f4b6ee0f07ae248b0e903afd393ef96100e207cf8b70f4d4baf6`。已下载并核对该 ZIP 哈希。内含 CI 固定样例 `ci-e12` 的五阶段结果；该产物不包含 A/B 正式交接，也不是 B3 课程服务器的两个预跑 job。

逐项校验该 ZIP 时，E12 清单中 187 个文件有 180 个在 ZIP 内且 SHA256、长度吻合；7 个 `.gitignore` 因 `upload-artifact` 默认排除隐藏文件而缺失。四号分支调整工作流以包含这些文件，并排除克隆副本的 `.git` 目录。新 CI 完成后须再次逐项核对。

四号提交 `523421d3a4e8f24be60b8c39cb35b5e12cb63fc0` 的 push CI 已完成：E7 run `43202389293`、E8–E10 run `43202389312`、E11–E12 run `43202389319` 均成功。新 E11–E12 产物 `e11e12-evidence-43202389319` 的 ZIP SHA256 为 `8e6088c91b07407488ee5b6643813e033075cf8b731a1f5bf2962c874a09bf8e`。下载后逐项验证 E11-A 85 个、E11-B 96 个、E12 187 个清单文件的长度和 SHA256 全部匹配，ZIP 无 `.git` 元数据。

B3 课程服务器证据包路径为 `/root/devops-submissions/241880585/e12-b3-20261112-161448.tar.gz`，交接 SHA256 为 `f9ee5c3545897873e62dd12d2b05fad4c73c470326160cb2e493d1a8a7ed720b`。已在服务器和本机分别核对；包内 `sample-api-retry` 20 份、`real-api` 24 份下载产物均与各自 `verification.json` 中的 SHA256 一致。包内 `source-commit.txt` 为 `158ed5a9c3208ace9a0baee1354cd119e882ce54`，早于 B3 最终提交 `a8e6a0b`；故四号在自己的当前提交重新构建并运行。

Windows 检出会因 `core.autocrlf=true` 将 B1 候选 Dockerfile 转成 CRLF，工作树 SHA256 与 B1 交接值不同；按 LF 还原后的 SHA256 与 `1fa4739abd325c84e0ed4b3bbdcbcaf39c7c500fc0d80ba4707216e5cbe21a64` 一致。正式镜像构建须在 Linux 服务器重新核对文件字节哈希。

## 正式 A/B 接口交接（待完成）

已在 [A 组 PR #17](https://github.com/a-bi-chen/DevOps_1020_Student_Cloud/pull/17#issuecomment-6821585299) 请求本轮报告和共同项目的完整 SHA；等待 A 组回传。

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

已对 A 组仓库 `student/241880375/e11-e12` 的 2026-11-10 归档报告完成一次**兼容性预检**：[清单](compat-preflight/manifest.json)。原始报告、补丁和两条拒绝日志保存在 `compat-preflight/`。报告 SHA 与 A 的摘要吻合，B 端生成补丁，`git apply --check` 成功；旧 commit 与错误哈希均被拒绝且无补丁。随后在 Linux 课程服务器用四号候选镜像构建和运行，改动 `config.h` 后目标重新编译、输出 `1→2`，BuildChecker 复检 `missing_count=0`；结果见[服务器预跑清单](preflight/manifest.json)中的 `a_archived_compatibility`。此报告不是正式联调的当轮新报告。

## 四号 SSH 转发五阶段预跑（已完成）

API 在课程服务器 `127.0.0.1:18084`，客户端经 SSH 转发到本机 `127.0.0.1:18080`。四号以新幂等键分别提交固定样例和 B1 真实项目，完成五阶段与下载核验；详见[预跑清单](preflight/manifest.json)、[固定样例校验](preflight/sample-verification.json)和[真实项目校验](preflight/real-verification.json)。

| 任务 | job_id | trace_id | 候选 image_id | 结果 |
|---|---|---|---|---|
| 固定样例 | `job-7f7332c3a178434781fdd151725fac6a` | `trace-e9b41a7d26e14449b40cb54b3fc7c0f1` | `sha256:f1fb7db7e04db01ee05e5ebfac0a02eab69953747e1649297e5ed63b691af076` | 五阶段成功；20 个客户端下载文件的哈希核对通过 |
| B1 真实项目 | `job-5210c6d37cd44a30b358e009bc9e7f40` | `trace-f1b4af1ce63b4ec2b1a0487a82438283` | `sha256:2cdb7b8e8ae95fe3e2a0b04d0abcb9a9978fffa40fa46aad62d0b338da99e262` | 五阶段成功；24 个客户端下载文件的哈希核对通过 |

两项任务同键同输入返回原 job，同键改 target 返回 HTTP 409；修复输入均精确引用本 job 的增量报告，`accepted=true`、复检无 MD。真实项目使用 `fixtures/e11e12-b1-real`，C0=`30ffe4c41492334478a2446a8be0662d3f31d478`，C1=`a7e3b644ca9b1b9d0b26bd41e839fcbf5ea1c293`；唯一 MD 为 `main.o → extra.h`，补丁见[真实项目补丁](preflight/real-candidate.patch)，程序输出 `hello E3`，`extra.h` 变化后 `main.o` 重建。

服务器预跑证据包：`/root/devops-submissions/241880556/e12-b4-preflight-20261112-201312.tar.gz`，SHA256 `2a16e0c163bd4b41edc38beac76200d150ebb104a177dbb53bf15086f7704791`。包内含服务端 job 原始证据、SSH 转发客户端记录、测试/构建日志和 A 旧归档兼容性复验。正式 A/B 报告交接仍待 A 组当轮报告。

`mode=e12` 当前在本 job 内生成增量报告。A 组外部报告按上一节由 B 端单独接收；若正式接口约定要求直接注入外部报告，须先更新接口和实现并重新验证。

## 最终交付（待完成）

- 四号 PR 与 review、最终源码提交 SHA
- 四号提交及合并后 `main` 的 E7、E8–E10、E11–E12 CI 链接
- A→B 报告交接、独立修复复验、两个正式 API job 的证据索引
- 真实项目记录、证据包 SHA256、个人报告与 ADR

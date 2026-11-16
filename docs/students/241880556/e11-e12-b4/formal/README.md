# A09 → B09 正式报告交接与 B4 复验

2026-11-16，A09 张海洋（241880375）在组群明确确认：A 组 PR #17、head `0cd8054911a18be96900e05c3b7747c6b35a4112` 归档的 E11-A `incremental-check.json` 就是本轮正式交付，没有另生成新报告。A 组另做的 `course-one/make-introduction` 真实项目不属于本次接口交付。完整字段见 [manifest.json](manifest.json)。

## A 端输入与 B 端独立接收

- A 端归档：[固定提交原始文件](https://raw.githubusercontent.com/a-bi-chen/DevOps_1020_Student_Cloud/0cd8054911a18be96900e05c3b7747c6b35a4112/evidence/students/241880375/e11-e12/e11e12-evidence-241880375.tar.gz)，SHA256 `19479d51720decbca2518453e00646a4700c7b21101b018965bfdbc0c8cce648`。
- 归档内项目：`data/integration-sample/repo`。base `3fcb72029bf560afde2d29436395ff3b979a19fd` 是 target `15c059958a41a5a0513dc048036439843a34ad28` 的祖先；两个对象均为完整 Git 提交。
- 原始[增量报告](incremental-check.json) SHA256 `8508d50232bfa4a529d51accd4dc94e5765a0fe0a0b130eebf73f8f866a98716`；[全量报告](full-check.json) SHA256 `59c602db2c12075f66fc754fdfdb78d832dc5f83f99391b1c3ddcf29cdd6beef`。接收入口实际消费增量报告。
- A 端 `job_id=job-1bd0ed1b449f44f293853df90440844f`，`trace_id=trace-4e7c0c6afd0447f9869d2f5e1ee6f4ae`。报告 `schema_version=e11e12-1`、`kind=incremental-check`、`status=SUCCEEDED`；MD 为 `main.o→config.h` 和 `main.o→extra.h`，另有 RD `main.o→unused.h`。
- B 端以 `labs/e11e12/repair_report.py --kind incremental-check` 独立接收，生成[候选补丁](candidate.patch)，SHA256 `88074f66c291dcad1344c48f6a2b9ddd42d235d9d0415c85fb33310c5b7cb2af`。既有同字节报告负例验证见 `../compat-preflight/stale.log`（`STALE_REPORT`）和 `mismatch.log`（`ARTIFACT_HASH_MISMATCH`）。
- 在课程服务器 `47.96.146.48` 的候选镜像 `sha256:f1fb7db7e04db01ee05e5ebfac0a02eab69953747e1649297e5ed63b691af076` 应用补丁后，[构建与程序日志](build-and-program.log)输出 `1`；修改 `config.h` 后，[重编译日志](header-rebuild-and-program.log)显示 `main.o` 重建，程序输出 `2`。[BuildChecker 复检](recheck-console.json) SHA256 `b76c19bc561350bc8ed103e711bff3b78e95c8ff6d58f66822da3a63aa516b60`，MD=0，保留一项 RD。

Linux 复验过程可由 [run_formal.sh](run_formal.sh) 重放。课程服务器无法稳定访问 `raw.githubusercontent.com` 时，将从上述固定提交地址取得且经 SHA256 核验的原始归档先放到脚本指定的 `a-original.tar.gz` 路径，再运行脚本；本次使用此前保存、哈希完全相同的原始归档。脚本重新解包、校验报告和提交、运行 B 端入口、应用补丁、容器构建和动态复检。

## E12 API 正式任务

通过本机 `127.0.0.1:18080` 到课程服务器 `127.0.0.1:18084` 的 SSH 转发，新提交固定样例与 B1 真实项目请求。每项均完成 `draft → full-check → incremental-check → repair → recheck`，同幂等键重试返回原 job，修改请求返回 HTTP 409；客户端核对下载文件 SHA256 和响应头。详细原始响应、产物清单、五阶段下载、镜像执行记录见 `sample-api/` 与 `real-api/`。

| 任务 | job_id / trace_id | 实际候选镜像 ID | 下载校验 | 结果 |
|---|---|---|---:|---|
| 固定样例 | `job-01424ef2954f4fdc86b6ed3ec73b19df` / `trace-9a8cb4142f844414a669cd71228dc1b6` | `sha256:671ac1c5de9235474e0dc860ea3c2e3205778fc7a083819d2833ffaac971138b` | 20 | `accepted=true`、MD=0 |
| B1 真实项目 | `job-6b0e90a2428a44a990fee1c95f890a39` / `trace-4eae00e9957242b3bb26a045b9d8d208` | `sha256:fa7d0259989e20e816c1e3427b7b0c04f1875075b3f4c912c799cf1ae7b0147c` | 24 | `accepted=true`、MD=0 |

API 任务的 repair 各自引用**同一 job** 的增量报告产物；A→B 外部报告由独立接收入口消费。A 端 `job_id` / `trace_id` 保存在外部交接记录中，B 端新 API job 有各自标识，不能混作同一个 job。B1 真实项目使用 `fixtures/e11e12-b1-real`，与 A 组交付的双 C 源文件集成样例也分别记录。

## 证据包

课程服务器：`/root/devops-submissions/241880556/e12-b4-formal-20261116-r2.tar.gz`，SHA256 `1dc764f75f59fc2faa97beb0f48003631cd395825f7261806c95c51f4117cd67`；本机再次核对一致。包内有 A 原始归档、项目 `.git`、报告、B 接收/构建/复检、两个 API job 的服务端原始证据与 SSH 转发客户端下载记录。本机副本：`D:\devops\e12-b4-formal-20261116-r2.tar.gz`。

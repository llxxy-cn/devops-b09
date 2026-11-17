# A09 正式报告的 B09 修复签收产物

2026-11-17，用户转达 A09 已核对这些回传产物并确认双方共同签收 E12。此确认来自组群转述；报告原始字节、修复和复检的机器证据见下文。

A09 最终 `main` 为 `b0765a0f990b10a28392fe6d4318b4b73a41177a`。GitHub 内容 API 显示该提交中正式归档的 blob 为 `5c52c1824f147019ac25f6706f0549318a1f0cec`、大小 7149921 字节，与 PR #17 head `0cd8054911a18be96900e05c3b7747c6b35a4112` 中的归档完全相同；原始归档 SHA256 为 `19479d51720decbca2518453e00646a4700c7b21101b018965bfdbc0c8cce648`。

B09 使用归档内项目 `data/integration-sample/repo` 的 target `15c059958a41a5a0513dc048036439843a34ad28`，直接消费 A09 原始 `incremental-check.json`（SHA256 `8508d50232bfa4a529d51accd4dc94e5765a0fe0a0b130eebf73f8f866a98716`），未用 `fixed-md.json`。B 端原始报告接收入口重新生成 [candidate.patch](candidate.patch)，SHA256 `88074f66c291dcad1344c48f6a2b9ddd42d235d9d0415c85fb33310c5b7cb2af`。

修复后项目提交为 `817b2459d53f586f7f3800ce20d0c3f002621f77`，父提交正是 A09 target，变动文件仅 `Makefile`。可用 [repaired-project.bundle](repaired-project.bundle) 导入这个完整 Git 历史，bundle SHA256 `e6f7cd9802728705c85fd003ee031900a44691715c1768590a5de830017c0dda`：

```bash
git clone -b b09-formal-repair repaired-project.bundle repaired-project
git -C repaired-project rev-parse HEAD
git -C repaired-project diff --name-only 15c059958a41a5a0513dc048036439843a34ad28 HEAD
```

| 产物 | SHA256 | 内容 |
|---|---|---|
| [candidate.patch](candidate.patch) | `88074f66c291dcad1344c48f6a2b9ddd42d235d9d0415c85fb33310c5b7cb2af` | 为 `main.o` 补齐 `config.h`、`extra.h` 依赖 |
| [validation.json](validation.json) | `aeb157c32906bfe7859fc93e14c2a52cbb5e63dad0004c033d8c29f788475394` | A job/trace、base/target、修复提交、镜像 ID、各项结果和哈希 |
| [build.log](build.log) | `29bfc7126a891b1deca1f143ff3f7d2a0003e1c4d43a3df25ba739524b1a9a0c` | `make clean && make app && ./app`，输出 `1` |
| [incremental.log](incremental.log) | `52b1b0840faee45dffd5d909945f740dd9fad73b1dc58e544ac1c0491ce05e57` | `config.h` 变化后 `main.o` 重建，输出 `2` |
| [recheck.json](recheck.json) | `08792b92a49d4b4cd59c4919f4a7c9d4679bf3bf1010559190046e53a7080c00` | BuildChecker `SUCCEEDED`，MD=0，仅保留 `unused.h` 的 RD |
| [repaired-project.bundle](repaired-project.bundle) | `e6f7cd9802728705c85fd003ee031900a44691715c1768590a5de830017c0dda` | 包含修复提交的完整项目 Git 历史 |

以上哈希可用 [artifacts.sha256](artifacts.sha256) 核对。复验使用的候选镜像 ID 为 `sha256:f1fb7db7e04db01ee05e5ebfac0a02eab69953747e1649297e5ed63b691af076`，BuildChecker 环境镜像 ID 为 `sha256:0f14125df9d889f01f0f9cf1ab37c0a216d8e26212cca99504a6304b19f3701f`。可复现命令见上级 [run_signoff.sh](../run_signoff.sh)。

证据包 `/root/devops-submissions/241880556/e12-b4-formal-signoff-20261116-v2.tar.gz`，SHA256 `df1e6d95d670d81b4b5c08f4ef7abb50fa092bc14b61b26b3075f0d78ea63b5e`，已在服务器与本机核对一致。包内还包含原始 A 项目、报告、B 接收日志、BuildChecker 原始 trace 和另外两项独立 E12 API 任务的五阶段证据。

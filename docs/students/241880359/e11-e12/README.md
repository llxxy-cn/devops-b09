# B2 E11-B 修复与复验

学号 241880359
分支 `student/241880359/e11-e12-b2`

## 个人贡献

新增 `labs/e11e12/repair_report.py`。入口校验原始报告的 SHA256、
版本、类型、成功状态和目标提交，再生成 Makefile 补丁。
支持 E11-B 的 `fixed-md` 和 E12 的 `incremental-check`。

新增 `labs/e11e12/test_repair_report.py`，覆盖两种报告的 macro
修复、旧提交报告拒绝，以及错误哈希拒绝。实验测试共 17 项通过。

## 运行结果

- 课堂 E11-B 四阶段成功，补丁验证 `accepted=true`，复检无 MD。
- 真实项目位于 `fixtures/e11e12-b1-real`，目标提交为
  `a7e3b644ca9b1b9d0b26bd41e839fcbf5ea1c293`。
- 固定输入来自 B1 的 C1 BuildChecker 报告。核对原始报告和 C1
  文件哈希后封装，补丁给 `main.o` 增加 `extra.h`。
- `make test` 通过，程序输出 `hello E3`。触碰 `extra.h` 后，
  `main.o` 重新编译。BuildChecker 动态复检 `missing_count=0`。
- 旧提交和错误哈希分别返回 `STALE_REPORT` 和
  `ARTIFACT_HASH_MISMATCH`，两种情况均未生成补丁。

## 给 3 号的调用方式

```bash
python3 labs/e11e12/repair_report.py \
  --project "$TARGET_PROJECT_DIR" \
  --report "$REPORT_JSON" \
  --sha256 "$UPSTREAM_SHA256" \
  --kind incremental-check \
  --out "$NEW_PATCH_PATH"
```

`--project` 指向目标提交的项目子目录。哈希取自上游产物清单。
E11-B 固定输入用 `--kind fixed-md`。入口生成补丁，调用方负责应用和复验。

## 证据

- 课堂基线 `work/e11-b-241880359-baseline-20261110-225741`
- 旧报告拒绝 `work/e11-b-241880359-stale-20261110-225912`
- 独立入口自测 `work/b2-report-entry-20261110-230308`
- 真实项目 `work/e11-b-241880359-real-20261110-230452`
- 动态复检报告位于真实项目目录下的
  `buildchecker-recheck-20261110-230854/findings.json`

证据包 `/root/241880359/B2-E11-E12-241880359-20261110-231822.tar.gz`
SHA256 `e07b47a4c66514d3f0746783a15d2b17a24a78cff938d8003cf23ca31d8cb14e`

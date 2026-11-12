# E12 三号预跑与交接

仓库 llxxy-cn/devops-b09，建议个人分支 student/241880585/e11-e12-b3。

B1 真实项目为 fixtures/e11e12-b1-real。使用 v2 交接中列出的 C0 和 C1。C1 应只报告 main.o 缺少 extra.h。补丁交给 B2 的报告校验与生成函数，使用本轮 incremental-check 阶段清单中的 SHA256。真实项目请求见 [real-request.json](real-request.json)。

E12 在本轮 DRAFT 候选镜像 ID 下运行 GCC 依赖采集、构建、程序验证及修复后 GCC 重检。教学环境另做 BuildChecker 动态对照与最终复检。真实项目通过 make test 和 hello E3 输出验证，触碰 extra.h 后检查 main.o 对象时间确实更新。源仓库与 C0/C1 不写入，候选只在独立验证副本通过全部检查后写回目标工作副本。

## 课程服务器准备

在包含本变更的个人仓库根目录执行。先确认 Docker 可访问，且 git 本地 user.name 是 241880585。

```bash
mkdir -p data work
git cat-file -e '30ffe4c41492334478a2446a8be0662d3f31d478^{commit}' &&
git cat-file -e 'a7e3b644ca9b1b9d0b26bd41e839fcbf5ea1c293^{commit}' &&
git clone --no-hardlinks . data/e12-b1-real &&
cp docs/students/241880481/e11-e12/real-project/candidate.Dockerfile data/e12-b1-candidate.Dockerfile &&
sha256sum data/e12-b1-candidate.Dockerfile
```

已有 data/e12-b1-real 时核对其中包含同一 C0/C1，候选 Dockerfile SHA256 应为 1fa4739abd325c84e0ed4b3bbdcbcaf39c7c500fc0d80ba4707216e5cbe21a64。使用同一课程环境镜像标签，缺失时先构建。

```bash
set -o pipefail
docker image inspect course-e11e12:241880585 >/dev/null || python3 run_e11e12.py build
STAMP=$(date +%Y%m%d-%H%M%S)
EVIDENCE="work/e12-b3-$STAMP"
mkdir "$EVIDENCE"
git rev-parse HEAD > "$EVIDENCE/source-commit.txt"
docker image inspect course-e11e12:241880585 --format '{{.Id}}' > "$EVIDENCE/course-image-id.txt"
python3 run_e11e12.py test 2>&1 | tee "$EVIDENCE/tests.log"
```

准备固定样例。若个人仓库已经有可用的 data/integration-sample/e12.json，可直接使用。

```bash
python3 run_e11e12.py prepare
```

## 两个终端完成预跑

终端一在同一个仓库根目录启动服务，保留窗口。端口绑定宿主回环地址。

```bash
python3 run_e11e12.py serve --port 18083
```

终端二使用前面创建的 EVIDENCE。若另开了 SSH 会话，把变量设置为本轮实际路径。

```bash
python3 labs/e11e12/preflight_api.py --url http://127.0.0.1:18083 \
  --request data/integration-sample/e12.json --out "$EVIDENCE/sample-api"
```

```bash
python3 labs/e11e12/preflight_api.py --url http://127.0.0.1:18083 \
  --request docs/students/241880585/e11-e12-b3/real-request.json --out "$EVIDENCE/real-api"
```

两个请求均应生成 verification.json，包含五阶段、job_id、trace_id、实际候选镜像 ID 和已核对的文件 SHA256。相同幂等键与输入返回同一任务，修改 target 后应返回 HTTP 409。真实项目的增量阶段应含唯一一条 MD，也就是 main.o 缺少 extra.h。补丁应只为 main.o 增加该依赖。确认最终 recheck 显示 accepted=true、header_change=true 且无 MD。

任一任务失败时先看相应目录的 state.json 和 result.json，原始日志在 work/api-jobs/<job_id>/evidence/。DRAFT 失败先看 draft-build/iter-01 和 iter-02。镜像运行日志位于 image-execution/，每条记录包含 Docker 命令及镜像 ID。重新运行使用新的预跑输出目录。

## 交给四号

```bash
sample_job=$(python3 -c 'import json,sys; print(json.load(open(sys.argv[1]))["job_id"])' "$EVIDENCE/sample-api/verification.json")
real_job=$(python3 -c 'import json,sys; print(json.load(open(sys.argv[1]))["job_id"])' "$EVIDENCE/real-api/verification.json")
mkdir -p "$HOME/devops-submissions/241880585"
archive="$HOME/devops-submissions/241880585/$(basename "$EVIDENCE").tar.gz"
tar -czf "$archive" "$EVIDENCE" "work/api-jobs/$sample_job" "work/api-jobs/$real_job"
sha256sum "$archive" | tee "$archive.sha256"
sha256sum -c "$archive.sha256"
```

交接时附个人分支、实际代码 SHA、启动命令、两份请求、两份 verification.json、归档文件和 SHA256。真实项目报告以此次预跑产物为准。正式 A/B 联调由四号完成。

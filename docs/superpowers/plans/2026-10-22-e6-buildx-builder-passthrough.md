# E6 Buildx Builder Passthrough Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 为 B 轨道 E6/E7 增加可选的宿主机 Buildx 构建器透传，使课程服务器通过既有镜像加速配置完成两轮真实构建，同时保持候选、证据结构和禁网运行验证不变。

**Architecture:** 新建一个只负责 Buildx 参数校验与容器挂载参数生成的模块，由 `lab_cloud.py` 和 `run_e7_b_gate.py` 共用。入口在启动任何服务容器前检查构建器与 `~/.docker/buildx`，随后只向容器传入 `BUILDX_BUILDER` 和只读 Buildx 元数据目录；不传 `--builder` 时返回空参数，保持原行为。

**Tech Stack:** Python 3.10+ 标准库（`argparse`、`pathlib`、`subprocess`、`unittest.mock`）、Docker Engine、Docker Buildx、GitHub Actions YAML

## Global Constraints

- `--builder NAME` 仅允许用于 B 轨道的 `e6` 和 `gate`。
- 不修改 `work/candidate/Dockerfile`、候选 SHA256、`services/draft/draft/autobuild.py` 或两轮构建逻辑。
- 不修改宿主机 Docker daemon 配置，不重启共享 Docker 服务。
- 只读挂载宿主机 `~/.docker/buildx` 到容器 `/tmp/.docker/buildx`；不得挂载 `~/.docker/config.json` 或完整 `~/.docker`。
- 保留现有 Docker socket 挂载、socket 组号和服务容器 `HOME=/tmp`。
- 最终验证继续使用第二轮同一镜像 ID、`--network none`、退出码 0 和输出 `hello E3`。
- 未传 `--builder` 时命令与证据格式保持向后兼容。
- 保留失败证据 `work/e6-own-241880481-01`；成功重跑写入 `work/e6-own-241880481-02`。

---

## File Structure

- Create: `scripts/docker_builder.py` — 校验 builder 使用范围、检查宿主机 builder、生成最小 Docker 容器参数。
- Create: `scripts/tests/__init__.py` — 测试包标记。
- Create: `scripts/tests/test_docker_builder.py` — 覆盖默认兼容、有效挂载、builder 不存在和元数据缺失。
- Create: `scripts/tests/test_lab_cloud_builder.py` — 覆盖阶段限制、E6 命令组装与 E7 参数转发。
- Create: `scripts/tests/test_run_e7_b_gate_builder.py` — 覆盖 E7 门禁服务容器参数组装。
- Modify: `scripts/lab_cloud.py` — 增加 `--builder`，在 E6 中使用并向 gate 转发。
- Modify: `scripts/run_e7_b_gate.py` — 支持直接调用时的 `--builder`。
- Modify: `.github/workflows/e7-quality-gate.yml` — 在构建前运行入口层测试。
- Modify: `README.md` — 记录接口、安全边界和服务器命令。
- Modify: `docs/实验报告.md` — E6 成功后记录首次失败、方案和验收结果。

### Task 1: Buildx 参数解析与最小挂载模块

**Files:**
- Create: `scripts/docker_builder.py`
- Create: `scripts/tests/__init__.py`
- Create: `scripts/tests/test_docker_builder.py`

**Interfaces:**
- Consumes: builder 名称、轨道名、阶段名和可选宿主用户目录。
- Produces: `validate_builder_scope(builder: str | None, track: str, stage: str) -> None`；`resolve_builder_run_args(builder: str | None, home: Path | None = None) -> list[str]`；`BuilderConfigurationError`。

- [ ] **Step 1: 写出失败测试，固定允许范围和最小挂载行为**

```python
# scripts/tests/test_docker_builder.py
import subprocess
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from docker_builder import (
    BuilderConfigurationError,
    resolve_builder_run_args,
    validate_builder_scope,
)


class DockerBuilderTests(unittest.TestCase):
    def test_no_builder_preserves_default_command(self):
        with patch("docker_builder.subprocess.run") as run:
            self.assertEqual(resolve_builder_run_args(None), [])
            run.assert_not_called()

    def test_valid_builder_returns_only_env_and_readonly_buildx_mount(self):
        with tempfile.TemporaryDirectory() as folder:
            home = Path(folder)
            buildx = home / ".docker" / "buildx"
            buildx.mkdir(parents=True)
            completed = subprocess.CompletedProcess([], 0, "", "")
            with patch("docker_builder.subprocess.run", return_value=completed) as run:
                result = resolve_builder_run_args("e5-241880585", home)
            self.assertEqual(result, [
                "-e", "BUILDX_BUILDER=e5-241880585",
                "--mount", f"type=bind,src={buildx.resolve()},dst=/tmp/.docker/buildx,readonly",
            ])
            run.assert_called_once_with(
                ["docker", "buildx", "inspect", "e5-241880585"],
                stdin=subprocess.DEVNULL,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.PIPE,
                text=True,
                timeout=30,
            )

    def test_missing_builder_is_rejected(self):
        with tempfile.TemporaryDirectory() as folder:
            buildx = Path(folder) / ".docker" / "buildx"
            buildx.mkdir(parents=True)
            completed = subprocess.CompletedProcess([], 1, "", "no builder found")
            with patch("docker_builder.subprocess.run", return_value=completed):
                with self.assertRaisesRegex(BuilderConfigurationError, "not available"):
                    resolve_builder_run_args("missing", Path(folder))

    def test_missing_buildx_metadata_is_rejected(self):
        with tempfile.TemporaryDirectory() as folder:
            completed = subprocess.CompletedProcess([], 0, "", "")
            with patch("docker_builder.subprocess.run", return_value=completed):
                with self.assertRaisesRegex(BuilderConfigurationError, "metadata directory"):
                    resolve_builder_run_args("e5-241880585", Path(folder))

    def test_builder_scope_is_limited_to_b_e6_and_gate(self):
        validate_builder_scope("e5-241880585", "B", "e6")
        validate_builder_scope("e5-241880585", "B", "gate")
        with self.assertRaisesRegex(BuilderConfigurationError, "only supported"):
            validate_builder_scope("e5-241880585", "B", "build")
        with self.assertRaisesRegex(BuilderConfigurationError, "only supported"):
            validate_builder_scope("e5-241880585", "A", "e6")


if __name__ == "__main__":
    unittest.main()
```

同时创建空文件 `scripts/tests/__init__.py`。

- [ ] **Step 2: 运行测试并确认因模块缺失而失败**

Run: `python3 -m unittest discover -s scripts/tests -t scripts -p 'test_docker_builder.py' -v`

Expected: FAIL，包含 `ModuleNotFoundError: No module named 'docker_builder'`。

- [ ] **Step 3: 实现最小 helper，不读取或挂载 Registry 凭据**

```python
# scripts/docker_builder.py
"""Validate and expose a named host Buildx instance to service containers."""
import subprocess
from pathlib import Path


class BuilderConfigurationError(ValueError):
    """The requested host Buildx instance cannot be safely passed through."""


def validate_builder_scope(builder, track, stage):
    if builder and (track != "B" or stage not in ("e6", "gate")):
        raise BuilderConfigurationError("--builder is only supported for B track e6/gate")


def resolve_builder_run_args(builder, home=None):
    if not builder:
        return []
    host_home = Path.home() if home is None else Path(home)
    buildx = (host_home / ".docker" / "buildx").resolve()
    try:
        inspected = subprocess.run(
            ["docker", "buildx", "inspect", builder],
            stdin=subprocess.DEVNULL,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.PIPE,
            text=True,
            timeout=30,
        )
    except (OSError, subprocess.TimeoutExpired) as exc:
        raise BuilderConfigurationError(f"Buildx builder {builder!r} is not available: {exc}") from exc
    if inspected.returncode:
        detail = inspected.stderr.strip() or f"exit code {inspected.returncode}"
        raise BuilderConfigurationError(f"Buildx builder {builder!r} is not available: {detail}")
    if not buildx.is_dir():
        raise BuilderConfigurationError(f"Buildx metadata directory is missing: {buildx}")
    return [
        "-e", f"BUILDX_BUILDER={builder}",
        "--mount", f"type=bind,src={buildx},dst=/tmp/.docker/buildx,readonly",
    ]
```

- [ ] **Step 4: 运行 helper 测试并确认全部通过**

Run: `python3 -m unittest discover -s scripts/tests -t scripts -p 'test_docker_builder.py' -v`

Expected: `Ran 5 tests` 和 `OK`。

- [ ] **Step 5: 提交 helper 与测试**

```bash
git add scripts/docker_builder.py scripts/tests/__init__.py scripts/tests/test_docker_builder.py
git commit -m "feat: add safe Buildx builder passthrough"
```

### Task 2: 将 builder 接入 E6 入口并转发给 E7

**Files:**
- Modify: `scripts/lab_cloud.py`
- Create: `scripts/tests/test_lab_cloud_builder.py`

**Interfaces:**
- Consumes: Task 1 的 `validate_builder_scope()` 和 `resolve_builder_run_args()`。
- Produces: `lab_cloud.py --builder NAME`；E6 `docker run` 中的 builder 参数；gate 子进程的 `--builder NAME`。

- [ ] **Step 1: 写出失败入口测试，覆盖非法阶段、E6 组装和 gate 转发**

```python
# scripts/tests/test_lab_cloud_builder.py
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

import lab_cloud


class LabCloudBuilderTests(unittest.TestCase):
    def fresh_out(self, name):
        base = lab_cloud.ROOT / "work"
        base.mkdir(exist_ok=True)
        folder = tempfile.TemporaryDirectory(prefix=f"test-{name}-", dir=base)
        return folder, str(Path(folder.name).relative_to(lab_cloud.ROOT))

    def test_builder_is_rejected_for_build_before_any_command_runs(self):
        with patch.object(lab_cloud.sys, "platform", "linux"), \
             patch("lab_cloud.subprocess.run") as run:
            with self.assertRaises(SystemExit) as raised:
                lab_cloud.main(["build", "--builder", "e5-241880585"])
        self.assertEqual(raised.exception.code, 2)
        run.assert_not_called()

    def test_e6_adds_builder_options_to_service_container(self):
        holder, out = self.fresh_out("e6")
        self.addCleanup(holder.cleanup)
        builder_args = [
            "-e", "BUILDX_BUILDER=e5-241880585",
            "--mount", "type=bind,src=/root/.docker/buildx,dst=/tmp/.docker/buildx,readonly",
        ]
        with patch.object(lab_cloud.sys, "platform", "linux"), \
             patch("lab_cloud.resolve_builder_run_args", return_value=builder_args), \
             patch("lab_cloud.execute", return_value=0) as execute, \
             patch("lab_cloud.os.getuid", return_value=0, create=True), \
             patch("lab_cloud.os.getgid", return_value=0, create=True), \
             patch.object(Path, "stat", return_value=SimpleNamespace(st_gid=999)):
            code = lab_cloud.main([
                "e6", "--builder", "e5-241880585", "--replay",
                "--out", out, "--build-timeout", "600",
            ])
        self.assertEqual(code, 0)
        command = execute.call_args.args[0]
        self.assertIn("BUILDX_BUILDER=e5-241880585", command)
        self.assertIn("type=bind,src=/root/.docker/buildx,dst=/tmp/.docker/buildx,readonly", command)
        self.assertEqual(command.count("/var/run/docker.sock:/var/run/docker.sock"), 1)

    def test_gate_forwards_builder_name(self):
        holder, out = self.fresh_out("gate")
        self.addCleanup(holder.cleanup)
        with patch.object(lab_cloud.sys, "platform", "linux"), \
             patch("lab_cloud.resolve_builder_run_args", return_value=["checked"]), \
             patch("lab_cloud.execute", return_value=0) as execute:
            code = lab_cloud.main([
                "gate", "--builder", "e5-241880585", "--replay", "--out", out,
            ])
        self.assertEqual(code, 0)
        command = execute.call_args.args[0]
        position = command.index("--builder")
        self.assertEqual(command[position + 1], "e5-241880585")


if __name__ == "__main__":
    unittest.main()
```

- [ ] **Step 2: 运行入口测试并确认 `--builder` 尚未定义**

Run: `python3 -m unittest discover -s scripts/tests -t scripts -p 'test_lab_cloud_builder.py' -v`

Expected: FAIL；合法 E6/gate 用例报告 `unrecognized arguments: --builder`。

- [ ] **Step 3: 在 `lab_cloud.py` 解析、校验并记录 builder**

在 import 区加入：

```python
from docker_builder import (
    BuilderConfigurationError,
    resolve_builder_run_args,
    validate_builder_scope,
)
```

在 `--build-timeout` 后加入：

```python
parser.add_argument('--builder', help='B e6/gate: reuse a named host Buildx instance')
```

在平台与超时检查之后、创建输出目录之前加入：

```python
try:
    validate_builder_scope(args.builder, TRACK, args.stage)
    builder_run_args = resolve_builder_run_args(args.builder)
except BuilderConfigurationError as exc:
    parser.error(str(exc))
```

在 `meta` 中加入 `'builder': args.builder`。未传 builder 时 `builder_run_args` 必须是空列表。

- [ ] **Step 4: 将 builder 参数插入 E6 服务容器，并向 gate 转发名称**

在 B 轨道 gate 命令组装处加入：

```python
if args.builder:
    command += ['--builder', args.builder]
```

在 B 轨道 E6 的 `container([...])` 参数中，将 `*builder_run_args` 放在 Docker socket 挂载之后、输入与证据挂载之前：

```python
'-v', '/var/run/docker.sock:/var/run/docker.sock',
*builder_run_args,
'--mount', f'type=bind,src={candidate},dst=/inputs/Dockerfile,readonly',
```

- [ ] **Step 5: 运行 Task 1 与 Task 2 测试**

Run: `python3 -m unittest discover -s scripts/tests -t scripts -p 'test_*builder.py' -v`

Expected: `Ran 8 tests` 和 `OK`，非法阶段测试没有调用 Docker。

- [ ] **Step 6: 提交 E6 入口改动**

```bash
git add scripts/lab_cloud.py scripts/tests/test_lab_cloud_builder.py
git commit -m "feat: pass named Buildx builder into E6"
```

### Task 3: 将相同 builder 配置接入 E7 门禁并纳入 CI

**Files:**
- Modify: `scripts/run_e7_b_gate.py`
- Create: `scripts/tests/test_run_e7_b_gate_builder.py`
- Modify: `.github/workflows/e7-quality-gate.yml`

**Interfaces:**
- Consumes: Task 1 的 `resolve_builder_run_args()`；Task 2 转发的 `--builder NAME`。
- Produces: `service_command(image, source, candidate, evidence, cidfile, expected, build_timeout, verify_timeout, builder_run_args, uid, gid, socket_gid) -> list[str]`。

- [ ] **Step 1: 写出 E7 服务容器命令的失败测试**

```python
# scripts/tests/test_run_e7_b_gate_builder.py
import unittest
from pathlib import Path

from run_e7_b_gate import service_command


class GateBuilderCommandTests(unittest.TestCase):
    def test_service_command_includes_builder_and_preserves_security_options(self):
        builder = [
            "-e", "BUILDX_BUILDER=e5-241880585",
            "--mount", "type=bind,src=/root/.docker/buildx,dst=/tmp/.docker/buildx,readonly",
        ]
        command = service_command(
            "e7-draft:test", Path("/source"), Path("/candidate"), Path("/evidence"),
            Path("/cid"), "hello E3", 600, 30, builder, 0, 0, 999,
        )
        self.assertIn("BUILDX_BUILDER=e5-241880585", command)
        self.assertIn("type=bind,src=/root/.docker/buildx,dst=/tmp/.docker/buildx,readonly", command)
        self.assertIn("/var/run/docker.sock:/var/run/docker.sock", command)
        self.assertEqual(command[command.index("--network") + 1], "bridge")
        self.assertEqual(command[command.index("--expected-output") + 1], "hello E3")

    def test_service_command_without_builder_matches_previous_shape(self):
        command = service_command(
            "e7-draft:test", Path("/source"), Path("/candidate"), Path("/evidence"),
            Path("/cid"), "hello E3", 600, 30, [], 0, 0, 999,
        )
        self.assertFalse(any(item.startswith("BUILDX_BUILDER=") for item in command))
        self.assertFalse(any("/tmp/.docker/buildx" in item for item in command))


if __name__ == "__main__":
    unittest.main()
```

- [ ] **Step 2: 运行测试并确认 `service_command` 缺失**

Run: `python3 -m unittest discover -s scripts/tests -t scripts -p 'test_run_e7_b_gate_builder.py' -v`

Expected: FAIL，包含 `cannot import name 'service_command'`。

- [ ] **Step 3: 在 E7 runner 中实现命令函数并解析 builder**

在 import 区加入：

```python
from docker_builder import BuilderConfigurationError, resolve_builder_run_args
```

在 `main()` 之前加入：

```python
def service_command(image, source, candidate, evidence, cidfile, expected,
                    build_timeout, verify_timeout, builder_run_args,
                    uid, gid, socket_gid):
    return [
        "docker", "run", "--rm", "--network", "bridge",
        "--user", f"{uid}:{gid}", "-e", "HOME=/tmp",
        "--group-add", str(socket_gid),
        "-v", "/var/run/docker.sock:/var/run/docker.sock",
        *builder_run_args,
        "--cidfile", str(cidfile),
        "--mount", f"type=bind,src={source},dst=/fixture,readonly",
        "--mount", f"type=bind,src={candidate},dst=/candidate.Dockerfile,readonly",
        "--mount", f"type=bind,src={evidence},dst=/evidence",
        image, "python3", "-m", "draft", "auto-build",
        "--fixture", "/fixture", "--candidate", "/candidate.Dockerfile",
        "--out", "/evidence", "--expected-output", expected,
        "--timeout", str(build_timeout), "--verify-timeout", str(verify_timeout),
    ]
```

在 parser 中加入：

```python
parser.add_argument("--builder", help="Reuse a named host Buildx instance")
```

在创建输出目录之前加入：

```python
try:
    builder_run_args = resolve_builder_run_args(args.builder)
except BuilderConfigurationError as exc:
    parser.error(str(exc))
```

把循环内的内联命令替换为：

```python
command = service_command(
    args.image, source, path, evidence, case / "service-container-id.txt",
    expected, args.build_timeout, 1 if name == "runtime-timeout" else 30,
    builder_run_args, os.getuid(), os.getgid(),
    Path("/var/run/docker.sock").stat().st_gid,
)
```

单元测试容器继续使用 `--network none`；builder 只用于会执行嵌套构建的工作流容器。

- [ ] **Step 4: 在 CI 的语法检查之后运行入口层测试**

在 `.github/workflows/e7-quality-gate.yml` 加入：

```yaml
      - name: Test cloud entry-point command assembly
        shell: bash
        run: |
          set -euo pipefail
          python3 -m unittest discover -s scripts/tests -t scripts -p 'test_*builder.py' -v 2>&1 | tee work/ci/entry-tests.log
```

CI 不传 `--builder`，继续使用 GitHub runner 默认构建器。

- [ ] **Step 5: 运行全部入口测试和语法检查**

Run: `python3 -m unittest discover -s scripts/tests -t scripts -p 'test_*builder.py' -v`

Expected: `Ran 10 tests` 和 `OK`。

Run: `python3 -m compileall -q services/draft/draft scripts`

Expected: exit code 0，无错误输出。

- [ ] **Step 6: 提交 E7 与 CI 改动**

```bash
git add scripts/run_e7_b_gate.py scripts/tests/test_run_e7_b_gate_builder.py .github/workflows/e7-quality-gate.yml
git commit -m "feat: reuse named Buildx builder in E7 gate"
```

### Task 4: 文档、服务器验证与 E6 证据验收

**Files:**
- Modify: `README.md`
- Modify: `docs/实验报告.md`
- Verify only: `work/build-e6-241880481-03/`
- Preserve: `work/e6-own-241880481-01/`
- Create on server: `work/e6-own-241880481-02/`

**Interfaces:**
- Consumes: Task 2 的 E6 命令、服务器 builder `e5-241880585`、候选 `work/candidate/Dockerfile`。
- Produces: 通过 `verify_e6_b_evidence.py` 的成功证据和可供组员合并的报告说明。

- [ ] **Step 1: 在 README 记录接口和安全边界**

在统一入口说明后加入：

```markdown
课程服务器若已配置命名 Buildx 实例，可在 B 轨道 E6/E7 使用可选的
`--builder NAME`。入口会先执行 `docker buildx inspect NAME`，仅把
`~/.docker/buildx` 只读挂载进服务容器，并设置 `BUILDX_BUILDER`；不会挂载
`~/.docker/config.json`。不传该参数时保持默认 Docker 构建行为。

第 2 人 E6 服务器命令：

    python3 scripts/lab_cloud.py e6 \
      --builder e5-241880585 \
      --candidate work/candidate/Dockerfile \
      --out work/e6-own-241880481-02 \
      --build-timeout 600
```

- [ ] **Step 2: 完成变更审查，再推送个人分支**

Run: `git diff --check`

Expected: 无输出，exit code 0。

Run: `git push -u origin feat/e6-autobuild-241880481`

Expected: 更新同名个人分支；不得向 `main` 直接推送。

- [ ] **Step 3: 在课程服务器更新个人分支并重跑入口测试**

```bash
cd /root/241880481/devops-e5
git fetch origin
git switch feat/e6-autobuild-241880481
git pull --ff-only origin feat/e6-autobuild-241880481
python3 -m unittest discover -s scripts/tests -t scripts -p 'test_*builder.py' -v
```

Expected: 10 项入口测试全部通过。

- [ ] **Step 4: 确认服务镜像和命名 builder 可用**

```bash
docker image inspect course1020-draft:local >/dev/null
docker buildx inspect e5-241880585
```

Expected: 两条命令 exit code 均为 0，builder 状态为 `running`。不要重复构建已在 `work/build-e6-241880481-03` 验证通过的服务镜像。

- [ ] **Step 5: 使用新目录运行正式 E6**

```bash
nohup bash -lc '
cd /root/241880481/devops-e5
python3 scripts/lab_cloud.py e6 \
  --builder e5-241880585 \
  --candidate work/candidate/Dockerfile \
  --out work/e6-own-241880481-02 \
  --build-timeout 600
code=$?
printf "E6_EXIT_CODE=%s\n" "$code"
exit "$code"
' > work/e6-own-241880481-02.launcher.log 2>&1 &
echo $! | tee work/e6-own-241880481-02.pid
```

Expected: 返回后台 PID，SSH 断开不会终止实验。

- [ ] **Step 6: 检查完成状态，不用 `tail -F` 长时间占用终端**

```bash
pid=$(cat work/e6-own-241880481-02.pid)
if ps -p "$pid" >/dev/null; then
  echo "E6_STATUS=RUNNING"
  tail -n 40 work/e6-own-241880481-02/evidence/iter-01/build-stderr.log 2>/dev/null
  tail -n 40 work/e6-own-241880481-02/evidence/iter-02/build-stderr.log 2>/dev/null
else
  echo "E6_STATUS=FINISHED"
  tail -n 120 work/e6-own-241880481-02.launcher.log
fi
```

Expected while running: 日志首行显示 `building with "e5-241880585" instance using docker-container driver`。Expected when finished: launcher 包含 `"status": "SUCCEEDED"` 和 `E6_EXIT_CODE=0`。

- [ ] **Step 7: 运行课程证据校验器并检查关键不变量**

```bash
python3 scripts/verify_e6_b_evidence.py \
  --run-dir work/e6-own-241880481-02/evidence \
  | tee work/e6-own-241880481-02/verification.json
```

Expected: exit code 0，JSON 中 `passed` 为 `true`、`baseline_failure` 为 `MISSING_MAKE`、`verified_output` 为 `hello E3`。随后运行：

```bash
python3 - <<'PY'
import hashlib
import json
from pathlib import Path

run = Path("work/e6-own-241880481-02")
report = json.loads((run / "evidence/result.json").read_text())
candidate_sha = hashlib.sha256(Path("work/candidate/Dockerfile").read_bytes()).hexdigest()
assert report["status"] == "SUCCEEDED"
assert [a["iteration"] for a in report["attempts"]] == [1, 2]
assert report["attempts"][0]["build_exit_code"] != 0
assert report["attempts"][0]["failure_class"] == "MISSING_MAKE"
assert report["attempts"][1]["build_exit_code"] == 0
assert report["candidate_sha256"] == candidate_sha
assert report["verification"]["exit_code"] == 0
assert report["verification"]["actual_output"] == "hello E3\n"
assert report["verification"]["output_matches"] is True
network = report["verification"]["command"].index("--network")
assert report["verification"]["command"][network + 1] == "none"
assert report["verification"]["command"][-1] == report["attempts"][1]["image_id"]
print("E6_INVARIANTS=PASS")
print("TRACE_ID=" + report["trace_id"])
print("IMAGE_ID=" + report["attempts"][1]["image_id"])
print("CANDIDATE_SHA256=" + candidate_sha)
PY
```

Expected: `E6_INVARIANTS=PASS`，并输出 trace ID、完整 image ID 和候选 SHA256。

- [ ] **Step 8: 用真实结果更新实验报告并提交**

在 `docs/实验报告.md` 的 E6 节写入：

```markdown
- 首次运行目录：`work/e6-own-241880481-01`。服务容器使用默认 builder，访问
  `registry-1.docker.io` 超时，第一轮被分类为 `INFRASTRUCTURE`；这次运行不计为
  缺少 make 的复现。
- 修复方式：入口显式选择宿主机已有的 `e5-241880585`，只读透传
  `~/.docker/buildx`；候选 Dockerfile、固定 digest、候选 SHA、自动构建代码和
  禁网验证逻辑均未修改。
- 正式运行目录：`work/e6-own-241880481-02`。第一轮为 `MISSING_MAKE`，第二轮
  构建成功；验证使用第二轮同一 image ID，在 `--network none` 下退出 0 并输出
  `hello E3`，总状态为 `SUCCEEDED`，证据校验器通过。
```

Run: `git diff --check`

Expected: 无输出，exit code 0。

```bash
git add README.md docs/实验报告.md
git commit -m "docs: record E6 Buildx validation"
git push origin feat/e6-autobuild-241880481
```

- [ ] **Step 9: 最终分支验收**

```bash
python3 -m unittest discover -s scripts/tests -t scripts -p 'test_*builder.py' -v
python3 -m compileall -q services/draft/draft scripts
git diff --check origin/main...HEAD
git status --short
git log --oneline origin/main..HEAD
```

Expected: 10 项入口测试通过；语法与 diff 检查通过；工作区为空；提交历史只包含设计、helper、E6、E7/CI 和 E6 文档提交。

## Self-Review Record

- Spec coverage: `--builder` 范围、builder 存在性、只读 Buildx 子目录、E6 组装、E7 转发、默认兼容、失败保留和真实证据验收均有对应任务。
- Security coverage: 计划没有挂载完整 `~/.docker` 或 `config.json`，没有修改 daemon，也没有修改候选或自动构建算法。
- Type consistency: 两个入口统一消费 `resolve_builder_run_args(...) -> list[str]`；E7 命令函数使用同一列表格式。
- Scope control: 不调整 3.5 GiB 内存阈值、不创建 swap、不重建已经通过 24 项测试的服务镜像、不把服务器 builder 名称设为默认值。

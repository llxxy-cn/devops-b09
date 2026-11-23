"""Validate a Makefile repair in an isolated copy before accepting it."""

from __future__ import annotations

import json
import shlex
import shutil
import subprocess
import time
from pathlib import Path

from lab import scan


def compiler_flags(project: Path) -> list[str]:
    result = subprocess.run(
        ['make', '-s', '--eval=__e14_flags: ; @printf "%s\\n" "$(CFLAGS)"',
         '__e14_flags'], cwd=project, capture_output=True, text=True, timeout=30,
    )
    if result.returncode:
        raise ValueError('Cannot read project CFLAGS: ' + result.stderr.strip())
    return shlex.split(result.stdout.strip())


def save(path: Path, data: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def command(argv: list[str], cwd: Path, log: Path, timeout: float = 120) -> str:
    result = subprocess.run(argv, cwd=cwd, capture_output=True, text=True,
                            encoding="utf-8", errors="replace", timeout=timeout)
    log.parent.mkdir(parents=True, exist_ok=True)
    log.write_text(result.stdout + result.stderr, encoding="utf-8")
    if result.returncode:
        raise ValueError(f"{' '.join(argv)} exited {result.returncode}; see {log.name}")
    return result.stdout.strip()


def validate_repair(project: Path, patch: Path, edits: list[dict], evidence: Path,
                    expected_output: str, test_command: list[str] | None = None) -> dict:
    """Return a verdict; never modify project when validation fails."""
    if evidence.exists():
        raise ValueError("Validation output already exists")
    if test_command is not None and (
        not isinstance(test_command, list) or not test_command
        or any(not isinstance(part, str) or not part for part in test_command)
    ):
        raise ValueError("test_command must be a nonempty argv list")
    sandbox = evidence / "sandbox"
    shutil.copytree(project, sandbox, ignore=shutil.ignore_patterns(".git", "*.o", "app"))
    checks: dict[str, bool] = {}
    rebuilds: list[dict] = []
    error = None
    try:
        command(["git", "init", "-b", "main"], sandbox, evidence / "git-init.log")
        command(["git", "add", "."], sandbox, evidence / "git-add.log")
        command(["git", "-c", "user.name=E14", "-c", "user.email=e14@example.invalid",
                 "commit", "-m", "E14 validation input"], sandbox, evidence / "git-commit.log")
        command(["git", "apply", "--check", str(patch.resolve())], sandbox,
                evidence / "apply-check.log")
        command(["git", "apply", str(patch.resolve())], sandbox, evidence / "apply.log")
        checks["patch_applies"] = True
        command(["make", "clean"], sandbox, evidence / "clean.log")
        command(["make", "app"], sandbox, evidence / "build.log")
        checks["build"] = True
        if test_command:
            command(test_command, sandbox, evidence / "test.log")
            checks["test"] = True
        checks["output"] = command(["./app"], sandbox, evidence / "run.log") == expected_output
        if not checks["output"]:
            raise ValueError("Program output differs from expected_output")
        edges = sorted({(edit["target"], edit["dependency"]) for edit in edits})
        if not edges:
            raise ValueError("Repair contains no dependency edges")
        checks["edge_rebuilds"] = True
        for index, (target_name, dependency_name) in enumerate(edges, 1):
            dependency = sandbox / dependency_name
            target = sandbox / target_name
            if not dependency.is_file() or not target.is_file():
                raise ValueError(f"Missing repair edge: {target_name} <- {dependency_name}")
            before = target.stat().st_mtime_ns
            time.sleep(1.05)
            dependency.touch()
            command(["make", "app"], sandbox, evidence / f"rebuild-{index:02d}.log")
            actual = command(["./app"], sandbox, evidence / f"rebuild-{index:02d}-run.log")
            after = target.stat().st_mtime_ns
            passed = after > before and actual == expected_output
            rebuilds.append({"target": target_name, "dependency": dependency_name,
                             "before_mtime_ns": before, "after_mtime_ns": after,
                             "output": actual, "passed": passed})
            save(evidence / "edge-rebuilds.json", rebuilds)
            checks["edge_rebuilds"] = checks["edge_rebuilds"] and passed
            if not passed:
                raise ValueError(f"Dependency did not rebuild correctly: {target_name} <- {dependency_name}")
        recheck = scan(sandbox, compiler_flags=compiler_flags(sandbox))
        save(evidence / "recheck.json", recheck)
        checks["no_missing"] = not any(f["type"] == "MISSING" for f in recheck["findings"])
        if not checks["no_missing"]:
            raise ValueError("Missing dependencies remain after repair")
    except (OSError, ValueError, subprocess.TimeoutExpired, KeyError) as exc:
        error = str(exc)
    accepted = error is None and bool(checks) and all(checks.values())
    verdict = {"accepted": accepted, "checks": checks, "error": error,
               "rollback": not accepted, "source_unchanged": True,
               "edge_rebuilds": rebuilds, "test_command": test_command}
    save(evidence / "validation.json", verdict)
    if accepted:
        (project / "Makefile").write_bytes((sandbox / "Makefile").read_bytes())
        verdict["source_unchanged"] = False
        save(evidence / "validation.json", verdict)
    return verdict

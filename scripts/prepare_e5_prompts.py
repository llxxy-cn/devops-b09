"""Prepare teaching DRAFT prompts from real logs; does not call a model."""
import argparse
import json
from pathlib import Path

KEYWORDS = ["error", "unknown", "missing", "no such file or directory",
            "failed to execute", "execution failed", "file not found",
            "not specified", "unable to locate package",
            "no matching distribution found for"]

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--run-dir", required=True)
    root = Path(parser.parse_args().run_dir).resolve()
    iteration = root / "iter-01"
    dockerfile = (iteration / "Dockerfile").read_text(encoding="utf-8")
    log = (iteration / "build-retry.log").read_text(encoding="utf-8")
    result = json.loads((iteration / "result-retry.json").read_text(encoding="utf-8"))
    readme = (root / "project" / "README.md").read_text(encoding="utf-8")
    if result.get("build_exit_code") in (None, 0, 124) or "make: not found" not in log:
        raise ValueError("Evidence must show the real make-not-found failure, not a network or outer-timeout failure")
    lines = log.splitlines()
    localization = {
        "provenance": "SCRIPT_FROM_ACTUAL_BUILD_LOG",
        "build_exit_code": result["build_exit_code"],
        "build_log": "build-retry.log",
        "keyword_matches": [
            {"line": n, "text": line, "keywords": [k for k in KEYWORDS if k in line.lower()]}
            for n, line in enumerate(lines, 1)
            if any(k in line.lower() for k in KEYWORDS)],
        "root_cause_lines": [
            {"line": n, "text": line} for n, line in enumerate(lines, 1)
            if "/bin/sh:" in line and "make: not found" in line],
        "note": "Root-cause extraction here is a fixture-specific teaching rule. The two prompts are teaching adaptations, not verbatim paper templates."
    }
    instruction = (
        "Repair the failed Dockerfile using the actual build evidence.\n"
        "Preserve the exact pinned FROM image and digest, project files, WORKDIR, "
        "build command and final program command. Install necessary build dependencies.\n"
        "Do not bypass the build, suppress failure, or replace the program with a printed answer.\n"
        "Return only one complete Dockerfile in a fenced Dockerfile code block.\n"
        "The candidate will undergo a real build and program verification.\n")
    inputs = ("\nFailed Dockerfile:\n```dockerfile\n" + dockerfile.rstrip()
              + "\n```\n\nLast up to 50 lines of the actual build log:\n```text\n"
              + "\n".join(lines[-50:]) + "\n```\n")
    outputs = {
        "error-localization.json": json.dumps(localization, ensure_ascii=False, indent=2) + "\n",
        "prompt-error-driven.txt": instruction + inputs,
        "prompt-context-driven.txt": instruction + "\nProject README context:\n```text\n"
        + readme.rstrip() + "\n```\n" + inputs
    }
    for name, content in outputs.items():
        p = iteration / name
        if p.exists() and p.read_text(encoding="utf-8") != content:
            raise ValueError(f"Existing different output preserved: {p}")
    for name, content in outputs.items():
        p = iteration / name
        if not p.exists():
            p.write_text(content, encoding="utf-8")
        print(p)
    print("Model calls: 0. Prompts ready; repair generation and validation remain pending.")

if __name__ == "__main__":
    try:
        main()
    except (OSError, ValueError) as exc:
        raise SystemExit(f"ERROR: {exc}")

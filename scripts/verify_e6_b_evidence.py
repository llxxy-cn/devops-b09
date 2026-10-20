"""Check saved teaching replay reports against their local artifacts."""
import argparse
import hashlib
import json
from pathlib import Path
import re


def verify(directory):
    root = Path(directory).resolve()
    report = json.loads((root / "result.json").read_text(encoding="utf-8"))
    if report["status"] != "SUCCEEDED":
        raise ValueError("Workflow was not successful")
    attempts = report["attempts"]
    if len(attempts) != 2 or [a["iteration"] for a in attempts] != [1, 2]:
        raise ValueError("Expected exactly two ordered attempts")
    if attempts[0]["build_exit_code"] == 0 or attempts[0]["failure_class"] != "MISSING_MAKE":
        raise ValueError("Baseline did not reproduce missing make")
    initial_logs = "\n".join((root / "iter-01" / name).read_text(encoding="utf-8")
                             for name in ("build-stdout.log", "build-stderr.log"))
    if not re.search(r"/bin/sh:.*\bmake: (?:not found|command not found)", initial_logs):
        raise ValueError("Missing-make evidence was not found in saved logs")
    if attempts[1]["build_exit_code"] != 0:
        raise ValueError("Candidate build did not succeed")
    candidate = (root / "iter-02/Dockerfile").read_bytes()
    if hashlib.sha256(candidate).hexdigest() != report["candidate_sha256"]:
        raise ValueError("Candidate hash mismatch")
    image = json.loads((root / "iter-02/image-inspect.json").read_text(encoding="utf-8"))[0]["Id"]
    verification = report["verification"]
    if image != attempts[1]["image_id"] or verification["command"][-1] != image:
        raise ValueError("Built and verified image IDs differ")
    actual = (root / "verify.log").read_text(encoding="utf-8")
    if verification["exit_code"] != 0 or verification["output_matches"] is not True:
        raise ValueError("Program verification failed")
    if actual != verification["actual_output"] or actual.rstrip("\r\n") != "hello E3" or verification["expected_output"] != "hello E3":
        raise ValueError("Unexpected program output")
    project = root / "project"
    if (project / "Dockerfile.reference").exists():
        raise ValueError("Reference answer leaked into build context")
    for name, expected in report["input_sha256"].items():
        path = (project / name).resolve()
        if not path.is_relative_to(project.resolve()):
            raise ValueError("Input path is outside project")
        if hashlib.sha256(path.read_bytes()).hexdigest() != expected:
            raise ValueError(f"Input hash mismatch: {name}")
    return {"passed": True, "trace_id": report["trace_id"], "baseline_failure": "MISSING_MAKE",
            "fixed_build_exit_code": 0, "verify_exit_code": 0, "verified_output": "hello E3",
            "candidate_sha256": report["candidate_sha256"], "image_id": image,
            "scope": "Saved evidence consistency; does not independently rerun builds"}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--run-dir", required=True)
    args = parser.parse_args()
    try:
        result = verify(args.run_dir)
    except (ValueError, OSError, KeyError, TypeError, IndexError) as exc:
        print(json.dumps({"passed": False, "error": str(exc)}, ensure_ascii=False))
        return 1
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

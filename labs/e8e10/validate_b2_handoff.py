import argparse
import csv
import json
import shutil
import sys
from pathlib import Path

from lab import buildchecker, run, save, validate


STYLES = ("direct", "macro", "mixed")


def load_json(path):
    return json.loads(path.read_text())


def verify_inputs(root):
    projects = root / "projects"
    inputs = root / "inputs"

    for style in STYLES:
        project = projects / style
        report_path = inputs / f"{style}-report.json"
        plan_path = inputs / f"{style}-plan.json"
        patch_path = inputs / f"{style}.patch"

        for path in (project / ".git", report_path, plan_path, patch_path):
            if not path.exists():
                raise ValueError(f"MISSING_HANDOFF_INPUT {path}")

        if run(["git", "status", "--porcelain"], project):
            raise ValueError(f"HANDOFF_WORK_COPY_DIRTY {style}")

        report = load_json(report_path)
        head = run(["git", "rev-parse", "HEAD"], project).strip()
        if report["commit"] != head:
            raise ValueError(f"HANDOFF_REPORT_COMMIT_MISMATCH {style}")

        plan = load_json(plan_path)
        if not plan or plan[0]["style"] != style:
            raise ValueError(f"HANDOFF_PLAN_STYLE_MISMATCH {style}")


def accepted_style(root, style, rows):
    project = root / "projects" / style
    patchfile = root / "inputs" / f"{style}.patch"
    results = root / "results"

    result = validate(project, patchfile, results / style / "accept")
    assert result["accepted"] is True
    assert all(result["checks"].values())
    assert result["rollback"] is False
    assert result["source_unchanged"] is False

    report = buildchecker(project, results / style / "buildchecker")
    missing = [
        finding
        for finding in report["findings"]
        if finding["type"] == "MISSING"
    ]
    assert missing == []

    rows.append({"style": style, "case": "accepted", "passed": True})
    print(
        "ACCEPTED",
        style,
        result["checks"],
        "BUILDCHECKER_MISSING=0",
    )


def run_matrix(root):
    verify_inputs(root)

    results = root / "results"
    results.mkdir(exist_ok=True)
    if any(results.iterdir()):
        raise ValueError(f"RESULTS_MUST_BE_EMPTY {results}")

    rows = []
    direct = root / "projects" / "direct"
    direct_patch = root / "inputs" / "direct.patch"
    direct_before = (direct / "Makefile").read_bytes()

    test_reject = validate(
        direct,
        direct_patch,
        results / "direct" / "reject-test",
        fail_test=True,
    )
    assert test_reject["accepted"] is False
    assert test_reject["checks"]["patch_applies"] is True
    assert test_reject["checks"]["build"] is True
    assert test_reject["checks"]["test"] is False
    assert test_reject["rollback"] is True
    assert test_reject["source_unchanged"] is True
    assert (direct / "Makefile").read_bytes() == direct_before
    rows.append({"style": "direct", "case": "test-rejection", "passed": True})
    print("EXPECTED_TEST_REJECTION", test_reject)

    build_fail = root / "projects" / "direct-build-fail"
    if build_fail.exists():
        raise ValueError(f"BUILD_FAILURE_COPY_ALREADY_EXISTS {build_fail}")
    shutil.copytree(direct, build_fail)
    (build_fail / "main.c").write_text("this is invalid C;\n")
    build_fail_before = (build_fail / "Makefile").read_bytes()

    build_reject = validate(
        build_fail,
        direct_patch,
        results / "direct" / "reject-build",
    )
    assert build_reject["checks"]["patch_applies"] is True
    assert build_reject["checks"].get("build", False) is False
    assert "COMMAND_FAILED" in build_reject["error"]
    assert build_reject["accepted"] is False
    assert build_reject["rollback"] is True
    assert build_reject["source_unchanged"] is True
    assert (build_fail / "Makefile").read_bytes() == build_fail_before
    rows.append({"style": "direct", "case": "build-rejection", "passed": True})
    print("EXPECTED_BUILD_REJECTION", build_reject)

    for style in STYLES:
        accepted_style(root, style, rows)

    direct_after_accept = (direct / "Makefile").read_bytes()
    broken = root / "inputs" / "broken.patch"
    broken.write_text("invalid patch\n")
    patch_reject = validate(
        direct,
        broken,
        results / "direct" / "reject-patch",
    )
    assert patch_reject["accepted"] is False
    assert patch_reject["rollback"] is True
    assert patch_reject["source_unchanged"] is True
    assert (direct / "Makefile").read_bytes() == direct_after_accept
    rows.append({"style": "direct", "case": "patch-rejection", "passed": True})
    print("EXPECTED_PATCH_REJECTION", patch_reject)

    with (root / "results.csv").open("w", newline="") as handle:
        writer = csv.DictWriter(
            handle,
            fieldnames=["style", "case", "passed"],
        )
        writer.writeheader()
        writer.writerows(rows)

    save(
        root / "gate.json",
        {
            "track": "B",
            "passed": True,
            "rows": len(rows),
            "accepted_styles": list(STYLES),
            "rejection_cases": [
                "test-rejection",
                "build-rejection",
                "patch-rejection",
            ],
        },
    )
    print("B3_HANDOFF_GATE_PASS", rows)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--run-dir", type=Path, required=True)
    args = parser.parse_args()
    run_matrix(args.run_dir.resolve())


if __name__ == "__main__":
    main()

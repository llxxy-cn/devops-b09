"""Verify an incoming MD report and generate a Makefile patch."""

import argparse
import subprocess
import sys
from pathlib import Path

from pipeline import Failure, check_envelope, load_artifact, patch


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--project", type=Path, required=True)
    parser.add_argument("--report", type=Path, required=True)
    parser.add_argument("--sha256", required=True)
    parser.add_argument("--kind", choices=("fixed-md", "incremental-check"), required=True)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()

    try:
        report = load_artifact(args.report, args.sha256)
        target = subprocess.check_output(
            ["git", "-C", str(args.project), "rev-parse", "HEAD"], text=True
        ).strip()
        check_envelope(report, target, args.kind)
        data = report["data"]
        if data["commit"] != target:
            raise Failure("STALE_REPORT", "Report data belongs to another commit")

        diff, _ = patch(args.project, data)
        if not diff:
            raise Failure("NO_MISSING_DEPENDENCY", "No MD to repair")

        with args.out.open("x", encoding="utf-8") as output:
            output.write(diff)
    except Failure as error:
        print(f"{error.code}: {error}", file=sys.stderr)
        return 1
    except (OSError, ValueError, KeyError, TypeError, subprocess.CalledProcessError) as error:
        print(f"REPAIR_INPUT_ERROR: {error}", file=sys.stderr)
        return 1

    print(f"PATCH_WRITTEN: {args.out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

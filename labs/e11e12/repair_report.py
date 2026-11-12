"""Verify an incoming MD report and generate a Makefile patch."""

import argparse
import subprocess
import sys
from pathlib import Path

from pipeline import Failure, repair_from_artifact


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--project", type=Path, required=True)
    parser.add_argument("--report", type=Path, required=True)
    parser.add_argument("--sha256", required=True)
    parser.add_argument("--kind", choices=("fixed-md", "incremental-check"), required=True)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()

    try:
        repair_from_artifact(args.project, args.report, args.sha256, args.kind, args.out)
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

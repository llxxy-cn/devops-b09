import hashlib
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


SCRIPT = Path(__file__).resolve().with_name("repair_report.py")


class RepairReportTests(unittest.TestCase):
    def setUp(self):
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        self.root = Path(tmp.name)
        self.project = self.root / "project"
        self.project.mkdir()
        subprocess.run(["git", "init", "-q", str(self.project)], check=True)
        subprocess.run(
            [
                "git", "-C", str(self.project),
                "-c", "user.name=B2 Test",
                "-c", "user.email=b2@example.invalid",
                "commit", "--allow-empty", "-qm", "fixture",
            ],
            check=True,
        )
        self.target = subprocess.check_output(
            ["git", "-C", str(self.project), "rev-parse", "HEAD"], text=True
        ).strip()
        (self.project / "Makefile").write_text(
            "MAIN_DEPS = main.c helper.h\n"
            "main.o: $(MAIN_DEPS)\n"
            "\tcc -c main.c\n"
        )
        (self.project / "extra.h").write_text("#define EXTRA 1\n")
        self.report = {
            "schema_version": "e11e12-1",
            "kind": "fixed-md",
            "commit": self.target,
            "status": "SUCCEEDED",
            "data": {
                "commit": self.target,
                "findings": [
                    {"type": "MISSING", "target": "main.o", "dependency": "extra.h"}
                ],
            },
        }

    def run_repair(self, kind="fixed-md", sha256=None):
        report = self.root / "report.json"
        report.write_text(json.dumps(self.report))
        digest = hashlib.sha256(report.read_bytes()).hexdigest()
        output = self.root / f"{kind}.patch"
        result = subprocess.run(
            [
                sys.executable, str(SCRIPT), "--project", str(self.project),
                "--report", str(report), "--sha256", sha256 or digest,
                "--kind", kind, "--out", str(output),
            ],
            capture_output=True,
            text=True,
        )
        return result, output

    def test_macro_repair_for_both_report_types(self):
        for kind in ("fixed-md", "incremental-check"):
            with self.subTest(kind=kind):
                self.report["kind"] = kind
                result, output = self.run_repair(kind)
                self.assertEqual(result.returncode, 0, result.stderr)
                diff = output.read_text()
                self.assertIn("+MAIN_DEPS = main.c helper.h extra.h\n", diff)
                self.assertNotIn("+main.o:", diff)

    def test_stale_report_with_correct_hash_is_rejected(self):
        self.report["commit"] = "0" * 40
        self.report["data"]["commit"] = "0" * 40
        result, output = self.run_repair()
        self.assertEqual(result.returncode, 1)
        self.assertIn("STALE_REPORT", result.stderr)
        self.assertFalse(output.exists())

    def test_wrong_hash_is_rejected(self):
        result, output = self.run_repair(sha256="0" * 64)
        self.assertEqual(result.returncode, 1)
        self.assertIn("ARTIFACT_HASH_MISMATCH", result.stderr)
        self.assertFalse(output.exists())


if __name__ == "__main__":
    unittest.main()

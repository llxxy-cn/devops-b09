import hashlib
import difflib
import json
import os
import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import pipeline


class E13ProjectCompatTests(unittest.TestCase):
    def make_repo(self, root, include_config=True):
        repo = root / "repo"
        repo.mkdir()
        (repo / "main.c").write_text("int main(void){return 0;}\n")
        (repo / "helper.c").write_text("int helper(void){return 0;}\n")
        if include_config:
            (repo / "config.h").write_text("#define VALUE 1\n")
        (repo / "Makefile").write_text(
            "app: main.o helper.o\n\tcc main.o helper.o -o app\n"
            "main.o: main.c\n\tcc -c main.c -o main.o\n"
            "helper.o: helper.c\n\tcc -c helper.c -o helper.o\n"
        )
        subprocess.run(["git", "init", "-b", "main"], cwd=repo, check=True, capture_output=True)
        subprocess.run(["git", "add", "."], cwd=repo, check=True, capture_output=True)
        subprocess.run(
            [
                "git",
                "-c",
                "user.name=E13",
                "-c",
                "user.email=e13@example.invalid",
                "commit",
                "-m",
                "fixture",
            ],
            cwd=repo,
            check=True,
            capture_output=True,
        )
        sha = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=repo, text=True).strip()
        return repo, sha

    def source_report(self):
        return {
            "job_id": "job-source",
            "trace_id": "trace-source",
            "uri": "artifact://job-source/incremental-check.json",
            "sha256": "1" * 64,
            "bytes": 3052,
        }

    def request(self, repo, sha, report, report_sha):
        return {
            "mode": "e11-b",
            "repo": str(repo),
            "base": sha,
            "target": sha,
            "candidate": str(repo / "candidate.Dockerfile"),
            "expected_output": "1",
            "fixed_report": str(report),
            "fixed_report_sha256": report_sha,
            "project_compat": {"layout": "root-make", "make_test": False},
            "expected_source_report": self.source_report(),
        }

    def write_report(self, root, commit):
        report = root / "fixed-md.json"
        report.write_text(
            json.dumps(
                {
                    "schema_version": "e11e12-1",
                    "kind": "fixed-md",
                    "status": "SUCCEEDED",
                    "commit": commit,
                    "data": {"commit": commit, "findings": []},
                    "source_report": self.source_report(),
                }
            )
            + "\n"
        )
        return report

    def assert_rejected_before_candidate(self, output, result, code, auto_build):
        self.assertEqual(result["status"], "FAILED")
        self.assertEqual(result["error"]["code"], code)
        auto_build.assert_not_called()
        self.assertFalse((output / "draft-build").exists())
        self.assertFalse((output / "candidate.patch").exists())
        self.assertFalse((output / "validation" / "sandbox").exists())

    def test_stale_report_is_rejected_before_draft(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            repo, sha = self.make_repo(root)
            report = self.write_report(root, "f" * 40)
            request = self.request(repo, sha, report, hashlib.sha256(report.read_bytes()).hexdigest())
            output = root / "out-stale"
            with patch("draft.autobuild.auto_build", return_value={"status": "FAILED"}) as auto_build:
                result = pipeline.execute(request, output)
            self.assert_rejected_before_candidate(output, result, "STALE_REPORT", auto_build)

    def test_tampered_report_is_rejected_before_draft(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            repo, sha = self.make_repo(root)
            report = self.write_report(root, sha)
            declared_hash = hashlib.sha256(report.read_bytes()).hexdigest()
            report.write_bytes(report.read_bytes() + b"\n")
            request = self.request(repo, sha, report, declared_hash)
            output = root / "out-tampered"
            with patch("draft.autobuild.auto_build", return_value={"status": "FAILED"}) as auto_build:
                result = pipeline.execute(request, output)
            self.assert_rejected_before_candidate(
                output, result, "ARTIFACT_HASH_MISMATCH", auto_build
            )

    def test_root_make_snapshot_does_not_require_config_header(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            repo, sha = self.make_repo(root, include_config=False)
            resolved, project = pipeline.snapshot(
                repo,
                sha,
                root / "snapshot",
                root / "logs",
                project_compat={"layout": "root-make", "make_test": False},
            )
            self.assertEqual(resolved, sha)
            self.assertTrue((project / "Makefile").is_file())

    def test_root_make_validation_skips_make_test_and_checks_every_repaired_edge(self):
        class RecordingRuntime:
            image_id = "sha256:" + "1" * 64

            def __init__(self):
                self.commands = []

            def run(self, argv, project):
                self.commands.append(list(argv))
                if argv == ["make", "clean"]:
                    for name in ("main.o", "helper.o", "app"):
                        (project / name).unlink(missing_ok=True)
                    return ""
                if argv == ["make", "test"]:
                    raise AssertionError("root-make project has no make test target")
                if argv == ["make", "app"]:
                    for name in ("main.o", "helper.o"):
                        (project / name).write_text(str(len(self.commands)))
                    (project / "app").write_text("fixture")
                    return ""
                if argv == ["./app"]:
                    return "1"
                raise AssertionError(argv)

            def scan(self, project, old=None, *, real=False):
                return {
                    "commit": "fixture",
                    "findings": [
                        {"type": "REDUNDANT", "target": "main.o", "dependency": "unused.h"}
                    ],
                }

        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            project = root / "project"
            project.mkdir()
            for name in (
                "calculate.h",
                "config.h",
                "extra.h",
                "add.h",
                "sub.h",
                "unused.h",
            ):
                (project / name).write_text("/* fixture */\n")
            (project / "main.c").write_text("int main(void){return 0;}\n")
            (project / "helper.c").write_text("int helper(void){return 0;}\n")
            original = (
                "app: main.o helper.o\n\tcc main.o helper.o -o app\n"
                "main.o: main.c unused.h\n\tcc -c main.c -o main.o\n"
                "helper.o: helper.c\n\tcc -c helper.c -o helper.o\n"
                "clean:\n\trm -f main.o helper.o app\n"
            )
            changed = original.replace(
                "main.o: main.c unused.h",
                "main.o: main.c unused.h calculate.h config.h extra.h",
            ).replace(
                "helper.o: helper.c",
                "helper.o: helper.c add.h calculate.h sub.h",
            )
            (project / "Makefile").write_text(original)
            patchfile = root / "candidate.patch"
            patchfile.write_text(
                "".join(
                    difflib.unified_diff(
                        original.splitlines(True),
                        changed.splitlines(True),
                        fromfile="a/Makefile",
                        tofile="b/Makefile",
                    )
                )
            )
            edits = [
                {"target": "main.o", "dependency": "calculate.h", "style": "direct"},
                {"target": "main.o", "dependency": "config.h", "style": "direct"},
                {"target": "main.o", "dependency": "extra.h", "style": "direct"},
                {"target": "helper.o", "dependency": "add.h", "style": "direct"},
                {"target": "helper.o", "dependency": "calculate.h", "style": "direct"},
                {"target": "helper.o", "dependency": "sub.h", "style": "direct"},
            ]
            runtime = RecordingRuntime()
            verdict, _ = pipeline.validate_in_draft(
                project,
                patchfile,
                edits,
                root / "validation",
                runtime,
                "1",
                {"layout": "root-make", "make_test": False},
            )
            self.assertTrue(verdict["accepted"])
            self.assertNotIn(["make", "test"], runtime.commands)
            rebuilds = json.loads((root / "validation" / "edge-rebuilds.json").read_text())
            self.assertEqual(len(rebuilds), 6)
            self.assertTrue(all(row["rebuilt"] and row["output_matches"] for row in rebuilds))
            recheck = json.loads((root / "validation" / "recheck.json").read_text())
            self.assertEqual(
                recheck["findings"],
                [{"type": "REDUNDANT", "target": "main.o", "dependency": "unused.h"}],
            )

    def test_valid_root_make_request_uses_candidate_runtime_validation(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            repo, sha = self.make_repo(root)
            source = self.source_report()
            report = root / "fixed-md.json"
            report.write_text(
                json.dumps(
                    {
                        "schema_version": "e11e12-1",
                        "kind": "fixed-md",
                        "status": "SUCCEEDED",
                        "commit": sha,
                        "data": {
                            "commit": sha,
                            "findings": [
                                {
                                    "type": "MISSING",
                                    "target": "main.o",
                                    "dependency": "config.h",
                                }
                            ],
                        },
                        "source_report": source,
                    }
                )
                + "\n"
            )
            request = self.request(
                repo, sha, report, hashlib.sha256(report.read_bytes()).hexdigest()
            )
            output = root / "out-valid"
            image_id = "sha256:" + "2" * 64

            def fake_auto_build(_target, _candidate, draft_out, _expected, timeout):
                draft_out.mkdir(parents=True)
                result = {
                    "status": "SUCCEEDED",
                    "attempts": [{"image_id": image_id}],
                    "timeout": timeout,
                }
                (draft_out / "result.json").write_text(json.dumps(result) + "\n")
                return result

            def fake_validate(target, patchfile, edits, validation_out, runtime, expected, profile):
                sandbox = validation_out / "sandbox"
                shutil.copytree(target, sandbox)
                subprocess.run(
                    ["git", "apply", str(patchfile)], cwd=sandbox, check=True, capture_output=True
                )
                validation_out.mkdir(parents=True, exist_ok=True)
                verdict = {
                    "accepted": True,
                    "checks": {"edge_rebuilds": True, "no_missing": True},
                    "error": None,
                    "rollback": False,
                    "source_unchanged": True,
                    "image_id": runtime.image_id,
                }
                (validation_out / "validation.json").write_text(json.dumps(verdict) + "\n")
                (validation_out / "recheck.json").write_text(
                    json.dumps({"findings": []}) + "\n"
                )
                (validation_out / "edge-rebuilds.json").write_text(
                    json.dumps([{"target": "main.o", "dependency": "config.h", "rebuilt": True}])
                    + "\n"
                )
                self.assertEqual(profile, {"layout": "root-make", "make_test": False})
                self.assertEqual(expected, "1")
                self.assertEqual(len(edits), 1)
                return verdict, sandbox

            def fake_full(_project, full_out):
                full_out.mkdir(parents=True, exist_ok=True)
                findings = [
                    {"type": "REDUNDANT", "target": "main.o", "dependency": "unused.h"}
                ]
                (full_out / "findings.json").write_text(json.dumps(findings) + "\n")
                return {"status": "SUCCEEDED", "findings": findings}

            runtime = type("Runtime", (), {"image_id": image_id})()
            with patch.dict(os.environ, {"COURSE_HOST_ROOT": str(pipeline.ROOT)}), patch(
                "draft.autobuild.auto_build", side_effect=fake_auto_build
            ), patch.object(pipeline, "DraftRuntime", return_value=runtime), patch.object(
                pipeline, "validate_in_draft", side_effect=fake_validate
            ), patch.object(pipeline, "validate", side_effect=AssertionError("host validation used")), patch.object(
                pipeline, "full", side_effect=fake_full
            ):
                result = pipeline.execute(request, output)

            self.assertEqual(result["status"], "SUCCEEDED")
            self.assertEqual(result["image_id"], image_id)
            self.assertTrue((output / "validation" / "edge-rebuilds.json").is_file())


if __name__ == "__main__":
    unittest.main()

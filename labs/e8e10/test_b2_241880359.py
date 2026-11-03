import copy
import tempfile
import unittest
from pathlib import Path

from lab import fixture, scan, patch


class B2PatchTests241880359(unittest.TestCase):
    def test_duplicate_findings_produce_same_patch_as_single_finding(self):
        for style in ("direct", "macro", "mixed"):
            with self.subTest(style=style):
                with tempfile.TemporaryDirectory() as tmp:
                    project = Path(tmp) / "project"
                    fixture(project, style)
                    report = scan(project)
                    before = (project / "Makefile").read_bytes()

                    expected_diff, expected_plan = patch(project, report)

                    duplicated = copy.deepcopy(report)
                    missing = next(
                        item for item in duplicated["findings"]
                        if item["type"] == "MISSING"
                    )
                    duplicated["findings"].append(dict(missing))

                    actual_diff, actual_plan = patch(project, duplicated)

                    self.assertEqual(
                        (project / "Makefile").read_bytes(), before,
                        "生成补丁不能修改源 Makefile",
                    )
                    self.assertEqual(
                        actual_diff, expected_diff,
                        "重复报告不能导致重复添加依赖",
                    )
                    self.assertEqual(
                        actual_plan, expected_plan,
                        "修改计划应只记录一次相同修复",
                    )


if __name__ == "__main__":
    unittest.main()

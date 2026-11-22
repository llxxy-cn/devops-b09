import subprocess
import unittest
from pathlib import Path


class ServerFormalScriptTests(unittest.TestCase):
    @staticmethod
    def script_path():
        root = Path(__file__).resolve().parents[3]
        return root / "docs/students/241880481/e13-e14/run-server-formal-c1-c3.sh"

    def test_help_describes_required_material_directory(self):
        result = subprocess.run(
            ["bash", str(self.script_path()), "--help"], text=True, capture_output=True
        )
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertIn("MATERIAL_DIR", result.stdout)
        self.assertIn("C1", result.stdout)
        self.assertIn("C2", result.stdout)
        self.assertIn("C3", result.stdout)

    def test_fixed_bundle_is_created_from_a_named_ref(self):
        script = self.script_path().read_text(encoding="utf-8")
        self.assertIn("checkout -q -B b09-e13-fixed", script)
        self.assertIn(
            'bundle create "$EVIDENCE_ROOT/deliverables/a09-e13-project-fixed.bundle" b09-e13-fixed',
            script,
        )


if __name__ == "__main__":
    unittest.main()

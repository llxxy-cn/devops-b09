import subprocess
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from docker_builder import (
    BuilderConfigurationError,
    resolve_builder_run_args,
    validate_builder_scope,
    wrap_builder_command,
)

TEST_TMP = Path(__file__).resolve().parents[2] / "work"
TEST_TMP.mkdir(exist_ok=True)


class DockerBuilderTests(unittest.TestCase):
    def test_no_builder_preserves_default_command(self):
        with patch("docker_builder.subprocess.run") as run:
            self.assertEqual(resolve_builder_run_args(None), [])
            run.assert_not_called()

    def test_valid_builder_returns_only_env_and_readonly_buildx_mount(self):
        with tempfile.TemporaryDirectory(dir=TEST_TMP) as folder:
            home = Path(folder)
            buildx = home / ".docker" / "buildx"
            buildx.mkdir(parents=True)
            completed = subprocess.CompletedProcess([], 0, "", "")
            with patch("docker_builder.subprocess.run", return_value=completed) as run:
                result = resolve_builder_run_args("e5-241880585", home)
            self.assertEqual(result, [
                "-e", "BUILDX_BUILDER=e5-241880585",
                "--mount", f"type=bind,src={buildx.resolve()},dst=/tmp/buildx-source,readonly",
            ])
            run.assert_called_once_with(
                ["docker", "buildx", "inspect", "e5-241880585"],
                stdin=subprocess.DEVNULL,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.PIPE,
                text=True,
                timeout=30,
            )

    def test_missing_builder_is_rejected(self):
        with tempfile.TemporaryDirectory(dir=TEST_TMP) as folder:
            buildx = Path(folder) / ".docker" / "buildx"
            buildx.mkdir(parents=True)
            completed = subprocess.CompletedProcess([], 1, "", "no builder found")
            with patch("docker_builder.subprocess.run", return_value=completed):
                with self.assertRaisesRegex(BuilderConfigurationError, "not available"):
                    resolve_builder_run_args("missing", Path(folder))

    def test_missing_buildx_metadata_is_rejected(self):
        with tempfile.TemporaryDirectory(dir=TEST_TMP) as folder:
            completed = subprocess.CompletedProcess([], 0, "", "")
            with patch("docker_builder.subprocess.run", return_value=completed):
                with self.assertRaisesRegex(BuilderConfigurationError, "metadata directory"):
                    resolve_builder_run_args("e5-241880585", Path(folder))

    def test_builder_scope_is_limited_to_b_e6_and_gate(self):
        validate_builder_scope("e5-241880585", "B", "e6")
        validate_builder_scope("e5-241880585", "B", "gate")
        with self.assertRaisesRegex(BuilderConfigurationError, "only supported"):
            validate_builder_scope("e5-241880585", "B", "build")
        with self.assertRaisesRegex(BuilderConfigurationError, "only supported"):
            validate_builder_scope("e5-241880585", "A", "e6")

    def test_builder_command_copies_readonly_metadata_before_execution(self):
        command = wrap_builder_command(["python3", "-m", "draft"], True)
        self.assertEqual(command[:2], ["sh", "-c"])
        self.assertIn('cp -R /tmp/buildx-source "$HOME/.docker/buildx"', command[2])
        self.assertEqual(command[3:], ["buildx-init", "python3", "-m", "draft"])

    def test_default_command_does_not_add_a_shell_wrapper(self):
        self.assertEqual(
            wrap_builder_command(["python3", "-m", "draft"], False),
            ["python3", "-m", "draft"],
        )


if __name__ == "__main__":
    unittest.main()

import unittest
from pathlib import Path

from run_e7_b_gate import service_command


class GateBuilderCommandTests(unittest.TestCase):
    def test_service_command_includes_builder_and_preserves_security_options(self):
        builder = [
            "-e", "BUILDX_BUILDER=e5-241880585",
            "--mount", "type=bind,src=/root/.docker/buildx,dst=/tmp/.docker/buildx,readonly",
        ]
        command = service_command(
            "e7-draft:test", Path("/source"), Path("/candidate"), Path("/evidence"),
            Path("/cid"), "hello E3", 600, 30, builder, 0, 0, 999,
        )
        self.assertIn("BUILDX_BUILDER=e5-241880585", command)
        self.assertIn(
            "type=bind,src=/root/.docker/buildx,dst=/tmp/.docker/buildx,readonly",
            command,
        )
        self.assertIn("/var/run/docker.sock:/var/run/docker.sock", command)
        self.assertEqual(command[command.index("--network") + 1], "bridge")
        self.assertEqual(command[command.index("--expected-output") + 1], "hello E3")

    def test_service_command_without_builder_matches_previous_shape(self):
        command = service_command(
            "e7-draft:test", Path("/source"), Path("/candidate"), Path("/evidence"),
            Path("/cid"), "hello E3", 600, 30, [], 0, 0, 999,
        )
        self.assertFalse(any(item.startswith("BUILDX_BUILDER=") for item in command))
        self.assertFalse(any("/tmp/.docker/buildx" in item for item in command))


if __name__ == "__main__":
    unittest.main()

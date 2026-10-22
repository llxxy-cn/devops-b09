import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

import lab_cloud


class LabCloudBuilderTests(unittest.TestCase):
    def fresh_out(self, name):
        base = lab_cloud.ROOT / "work"
        base.mkdir(exist_ok=True)
        folder = tempfile.TemporaryDirectory(prefix=f"test-{name}-", dir=base)
        return folder, str(Path(folder.name).relative_to(lab_cloud.ROOT))

    def test_builder_is_rejected_for_build_before_any_command_runs(self):
        with patch.object(lab_cloud.sys, "platform", "linux"), \
             patch("lab_cloud.subprocess.run") as run:
            with self.assertRaises(SystemExit) as raised:
                lab_cloud.main(["build", "--builder", "e5-241880585"])
        self.assertEqual(raised.exception.code, 2)
        run.assert_not_called()

    def test_e6_adds_builder_options_to_service_container(self):
        holder, out = self.fresh_out("e6")
        self.addCleanup(holder.cleanup)
        builder_args = [
            "-e", "BUILDX_BUILDER=e5-241880585",
            "--mount", "type=bind,src=/root/.docker/buildx,dst=/tmp/buildx-source,readonly",
        ]
        real_stat = Path.stat

        def stat_with_docker_socket(path, *args, **kwargs):
            if str(path).replace("\\", "/") == "/var/run/docker.sock":
                return SimpleNamespace(st_gid=999)
            return real_stat(path, *args, **kwargs)

        with patch.object(lab_cloud.sys, "platform", "linux"), \
             patch("lab_cloud.resolve_builder_run_args", return_value=builder_args), \
             patch("lab_cloud.execute", return_value=0) as execute, \
             patch("lab_cloud.os.getuid", return_value=0, create=True), \
             patch("lab_cloud.os.getgid", return_value=0, create=True), \
             patch.object(Path, "stat", stat_with_docker_socket):
            code = lab_cloud.main([
                "e6", "--builder", "e5-241880585", "--replay",
                "--out", out, "--build-timeout", "600",
            ])
        self.assertEqual(code, 0)
        command = execute.call_args.args[0]
        self.assertIn("BUILDX_BUILDER=e5-241880585", command)
        self.assertIn(
            "type=bind,src=/root/.docker/buildx,dst=/tmp/buildx-source,readonly",
            command,
        )
        self.assertEqual(command.count("/var/run/docker.sock:/var/run/docker.sock"), 1)
        image = command.index(lab_cloud.IMAGE)
        self.assertEqual(command[image + 1:image + 3], ["sh", "-c"])
        self.assertIn("cp -R /tmp/buildx-source", command[image + 3])

    def test_gate_forwards_builder_name(self):
        holder, out = self.fresh_out("gate")
        self.addCleanup(holder.cleanup)
        with patch.object(lab_cloud.sys, "platform", "linux"), \
             patch("lab_cloud.resolve_builder_run_args", return_value=["checked"]), \
             patch("lab_cloud.execute", return_value=0) as execute:
            code = lab_cloud.main([
                "gate", "--builder", "e5-241880585", "--replay", "--out", out,
            ])
        self.assertEqual(code, 0)
        command = execute.call_args.args[0]
        position = command.index("--builder")
        self.assertEqual(command[position + 1], "e5-241880585")


if __name__ == "__main__":
    unittest.main()

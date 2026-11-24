import unittest
import pipeline


class OfflineBuildTests(unittest.TestCase):
    def test_offline_build_requires_explicit_local_base_and_make_path(self):
        valid = {
            "offline_build": {
                "base_image": "b09-e13-offline-python:3.13-slim",
                "make_path": "/opt/offline-toolchain/make",
            }
        }
        self.assertEqual(pipeline.parse_offline_build(valid, "e11-b"), valid["offline_build"])
        for value in ({}, {"base_image": "python:3.13-slim", "make_path": "/bad"},
                      {"base_image": "python:3.13-slim@sha256:" + "a" * 64,
                       "make_path": "/opt/offline-toolchain/make"}):
            with self.assertRaises(pipeline.Failure):
                pipeline.parse_offline_build({"offline_build": value}, "e11-b")

    def test_legacy_build_has_original_command_shape(self):
        self.assertIsNone(pipeline.parse_offline_build({}, "e11-b"))


if __name__ == "__main__":
    unittest.main()

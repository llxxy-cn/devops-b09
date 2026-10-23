"""Intentional CI rejection fixture for the E7 merge-gate demonstration."""

from draft.cli import main


def test_intentionally_wrong_version_exit_code():
    """Keep this wrong until the failed-pipeline merge block is recorded."""
    assert main(["version"]) == 1

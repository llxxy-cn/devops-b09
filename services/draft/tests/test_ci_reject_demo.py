"""Recovered CI check for the E7 merge-gate demonstration."""

from draft.cli import main


def test_version_returns_success_exit_code():
    """The same MR now records the correct successful version contract."""
    assert main(["version"]) == 0

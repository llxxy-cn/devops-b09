"""E7 preflight checks: reject invalid inputs before invoking Docker."""
from unittest.mock import Mock

import pytest
from draft import autobuild as workflow


BASE = (
    "FROM python:3.13-slim\n"
    "WORKDIR /work\n"
    "COPY main.c Makefile ./\n"
    "RUN make\n"
    'CMD ["./hello"]\n'
)
PIN = "FROM python:3.13-slim@sha256:" + "a" * 64
CANDIDATE = BASE.replace(
    "FROM python:3.13-slim", PIN
).replace(
    "RUN make", "RUN apt-get install -y build-essential\nRUN make"
)


@pytest.fixture
def inputs(tmp_path):
    fixture = tmp_path / "fixture"
    fixture.mkdir()
    (fixture / "Dockerfile.broken").write_text(BASE, encoding="utf-8")
    candidate = tmp_path / "candidate.Dockerfile"
    candidate.write_text(CANDIDATE, encoding="utf-8")
    return fixture, candidate, tmp_path / "output"


def test_existing_evidence_is_preserved(inputs, monkeypatch):
    fixture, candidate, output = inputs
    output.mkdir()
    evidence = output / "result.json"
    original = b'{"status":"SUCCEEDED","trace_id":"previous-run"}\n'
    evidence.write_bytes(original)
    execute = Mock(side_effect=AssertionError("Docker must not run"))
    monkeypatch.setattr(workflow, "execute", execute)

    with pytest.raises(ValueError, match="fresh empty output directory"):
        workflow.auto_build(fixture, candidate, output, "hello E3")

    execute.assert_not_called()
    assert evidence.read_bytes() == original
    assert {p.name for p in output.iterdir()} == {"result.json"}


def test_changed_cmd_is_rejected_before_build(inputs, monkeypatch):
    fixture, candidate, output = inputs
    candidate.write_text(
        CANDIDATE.replace('CMD ["./hello"]', 'CMD ["echo", "hello E3"]'),
        encoding="utf-8",
    )
    execute = Mock(side_effect=AssertionError("Docker must not run"))
    monkeypatch.setattr(workflow, "execute", execute)

    with pytest.raises(ValueError, match="required project/build/runtime"):
        workflow.auto_build(fixture, candidate, output, "hello E3")

    execute.assert_not_called()
    assert not output.exists()

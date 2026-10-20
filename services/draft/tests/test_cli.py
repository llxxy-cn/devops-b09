"""E4 骨架的单元测试。E5/E6 实现方法后，在这里继续添加测试。"""
from draft import __version__
from draft.cli import build_parser, main


def test_version(capsys):
    assert main(["version"]) == 0
    assert capsys.readouterr().out.strip() == f"draft {__version__}"


def test_smoke_defaults():
    args = build_parser().parse_args(["smoke"])
    assert args.fixture == "fixtures/draft"
    assert args.tag == "e4-smoke-broken:latest"


def test_smoke_reports_missing_docker(monkeypatch):
    from draft import smoke
    monkeypatch.setattr(smoke, "run", lambda cmd, timeout=600: (127, "docker: not found"))
    result = smoke.run_smoke("fixtures/draft", "t")
    assert result["passed"] is False
    assert "docker.sock" in result["hint"]

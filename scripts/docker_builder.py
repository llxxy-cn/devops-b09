"""Validate and expose a named host Buildx instance to service containers."""
import subprocess
from pathlib import Path


class BuilderConfigurationError(ValueError):
    """The requested host Buildx instance cannot be safely passed through."""


def validate_builder_scope(builder, track, stage):
    if builder and (track != "B" or stage not in ("e6", "gate")):
        raise BuilderConfigurationError("--builder is only supported for B track e6/gate")


def resolve_builder_run_args(builder, home=None):
    if not builder:
        return []
    host_home = Path.home() if home is None else Path(home)
    buildx = (host_home / ".docker" / "buildx").resolve()
    try:
        inspected = subprocess.run(
            ["docker", "buildx", "inspect", builder],
            stdin=subprocess.DEVNULL,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.PIPE,
            text=True,
            timeout=30,
        )
    except (OSError, subprocess.TimeoutExpired) as exc:
        raise BuilderConfigurationError(
            f"Buildx builder {builder!r} is not available: {exc}"
        ) from exc
    if inspected.returncode:
        detail = inspected.stderr.strip() or f"exit code {inspected.returncode}"
        raise BuilderConfigurationError(
            f"Buildx builder {builder!r} is not available: {detail}"
        )
    if not buildx.is_dir():
        raise BuilderConfigurationError(f"Buildx metadata directory is missing: {buildx}")
    return [
        "-e", f"BUILDX_BUILDER={builder}",
        "--mount", f"type=bind,src={buildx},dst=/tmp/.docker/buildx,readonly",
    ]

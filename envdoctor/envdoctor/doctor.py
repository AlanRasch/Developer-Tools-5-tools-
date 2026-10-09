"""Run every check for a project and collect the results."""

from __future__ import annotations

import json
from pathlib import Path

from .checks import (Result, check_command, check_env_file, check_git_identity,
                     check_port, check_python, check_virtualenv)


def load_config(root: Path) -> dict:
    """Read envdoctor.json if the project has one. It is optional."""
    path = root / "envdoctor.json"
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8"))


def python_requirement(root: Path) -> str | None:
    pyproject = root / "pyproject.toml"
    if not pyproject.exists():
        return None
    for line in pyproject.read_text(encoding="utf-8").splitlines():
        if line.strip().startswith("requires-python"):
            return line.split("=", 1)[1].strip().strip('"').strip("'")
    return None


def run_checks(root: Path) -> list[Result]:
    config = load_config(root)
    results: list[Result] = []
    results.append(check_python(config.get("python") or python_requirement(root)))
    results.append(check_virtualenv())
    for command in config.get("commands", ["git"]):
        results.append(check_command(command))
    results.extend(check_env_file(root))
    for port in config.get("ports", []):
        results.append(check_port(int(port)))
    identity = check_git_identity()
    if identity:
        results.append(identity)
    return results


def summarize(results: list[Result]) -> dict[str, int]:
    return {s: sum(1 for r in results if r.status == s) for s in ("PASS", "WARN", "FAIL")}

"""Read staged changes, commit history and tags from git."""

from __future__ import annotations

import subprocess
from pathlib import Path


def _git(args: list[str], cwd: Path) -> str:
    try:
        result = subprocess.run(["git", "-C", str(cwd), *args], capture_output=True, text=True,
                                timeout=120, check=True)
    except FileNotFoundError as err:
        raise ValueError("git is not installed or not on PATH") from err
    except subprocess.CalledProcessError as err:
        raise ValueError(f"git {' '.join(args[:2])} failed: {err.stderr.strip() or 'is this a git repository?'}") from err
    return result.stdout


def staged_diff(cwd: Path = Path(".")) -> str:
    return _git(["diff", "--cached", "--unified=0"], cwd)


def latest_tag(cwd: Path = Path(".")) -> str | None:
    try:
        return _git(["describe", "--tags", "--abbrev=0"], cwd).strip() or None
    except ValueError:
        return None


def subjects_since(tag: str | None, cwd: Path = Path(".")) -> list[str]:
    """One-line messages of every commit after `tag` (or the whole history if there is no tag)."""
    rev = f"{tag}..HEAD" if tag else "HEAD"
    return [line for line in _git(["log", rev, "--pretty=%s"], cwd).splitlines() if line.strip()]

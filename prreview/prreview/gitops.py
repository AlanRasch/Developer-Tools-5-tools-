"""Get the diff to review from git."""

from __future__ import annotations

import subprocess
from pathlib import Path


def git_diff(base: str, head: str = "HEAD", cwd: Path = Path(".")) -> str:
    """Changes on `head` since it diverged from `base` (the same as a pull request)."""
    try:
        result = subprocess.run(
            ["git", "-C", str(cwd), "diff", f"{base}...{head}"],
            capture_output=True, text=True, timeout=120, check=True,
        )
    except FileNotFoundError as err:
        raise ValueError("git is not installed or not on PATH") from err
    except subprocess.CalledProcessError as err:
        raise ValueError(f"git diff failed: {err.stderr.strip() or 'check the branch names'}") from err
    return result.stdout

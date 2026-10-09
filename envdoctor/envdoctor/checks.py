"""Each check returns a Result: PASS, WARN or FAIL, with a plain-language fix when needed."""

from __future__ import annotations

import os
import platform
import re
import shutil
import socket
import subprocess
import sys
from dataclasses import asdict, dataclass
from pathlib import Path

INSTALL_HINTS = {
    "git": {"macos": "Run: xcode-select --install   (or install from git-scm.com)",
            "windows": "Run: winget install Git.Git",
            "linux": "Run: sudo apt install git"},
    "node": {"macos": "Run: brew install node",
             "windows": "Run: winget install OpenJS.NodeJS.LTS",
             "linux": "Run: sudo apt install nodejs npm"},
    "docker": {"macos": "Install Docker Desktop from docker.com",
               "windows": "Install Docker Desktop from docker.com",
               "linux": "Run: sudo apt install docker.io"},
}


@dataclass
class Result:
    name: str
    status: str        # PASS, WARN or FAIL
    message: str
    fix: str = ""

    def to_dict(self) -> dict:
        return asdict(self)


def current_os() -> str:
    system = platform.system()
    return {"Darwin": "macos", "Windows": "windows"}.get(system, "linux")


def check_python(required: str | None) -> Result:
    have = f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}"
    if not required:
        return Result("Python version", "PASS", f"Python {have} (no requirement set)")
    ok = python_matches(required, sys.version_info[:2])
    if ok:
        return Result("Python version", "PASS", f"Python {have} meets '{required}'")
    return Result("Python version", "FAIL", f"Python {have} does not meet '{required}'",
                  "Install a Python version that matches the project, then create a new virtual environment.")


def python_matches(spec: str, version: tuple[int, int]) -> bool:
    """Understands clauses such as '>=3.10,<4'. Anything else is treated as satisfied."""
    for clause in spec.split(","):
        match = re.match(r"^\s*(>=|<=|==|>|<)\s*(\d+)\.(\d+)", clause)
        if not match:
            continue
        op, wanted = match.group(1), (int(match.group(2)), int(match.group(3)))
        ok = {">=": version >= wanted, "<=": version <= wanted, "==": version == wanted,
              ">": version > wanted, "<": version < wanted}[op]
        if not ok:
            return False
    return True


def check_virtualenv() -> Result:
    in_venv = sys.prefix != getattr(sys, "base_prefix", sys.prefix) or bool(os.getenv("VIRTUAL_ENV"))
    if in_venv:
        return Result("Virtual environment", "PASS", "A virtual environment is active")
    return Result("Virtual environment", "WARN", "No virtual environment is active",
                  "Create one with: python -m venv .venv   then activate it, so packages stay separate per project.")


def check_command(name: str, system: str | None = None) -> Result:
    if shutil.which(name):
        return Result(f"Command: {name}", "PASS", f"'{name}' is on PATH")
    hint = INSTALL_HINTS.get(name, {}).get(system or current_os(), f"Install '{name}' and make sure it is on PATH.")
    return Result(f"Command: {name}", "FAIL", f"'{name}' was not found", hint)


def check_env_file(root: Path) -> list[Result]:
    example = root / ".env.example"
    if not example.exists():
        return []
    results = []
    env_path = root / ".env"
    if not env_path.exists():
        return [Result(".env file", "FAIL", ".env is missing",
                       "Copy .env.example to .env and fill in the values.")]
    results.append(Result(".env file", "PASS", ".env exists"))
    present = parse_env(env_path)
    for key, default in parse_env(example).items():
        if key in present or os.getenv(key):
            continue
        if default:
            continue
        results.append(Result(f"Variable: {key}", "WARN", f"{key} is empty or missing in .env",
                              f"Set {key} in .env (see .env.example for what it is for)."))
    return results


def parse_env(path: Path) -> dict[str, str]:
    values: dict[str, str] = {}
    for raw in path.read_text(encoding="utf-8", errors="replace").splitlines():
        line = raw.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, _, value = line.partition("=")
        values[key.strip()] = value.strip().strip('"').strip("'")
    return values


def check_port(port: int) -> Result:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.settimeout(0.5)
        try:
            sock.bind(("127.0.0.1", port))
        except OSError:
            return Result(f"Port {port}", "WARN", f"port {port} is already in use",
                          f"Stop the other program using port {port}, or change the port in your settings.")
    return Result(f"Port {port}", "PASS", f"port {port} is free")


def check_git_identity() -> Result | None:
    if not shutil.which("git"):
        return None
    try:
        name = subprocess.run(["git", "config", "user.name"], capture_output=True, text=True, timeout=10).stdout.strip()
    except (OSError, subprocess.SubprocessError):
        return None
    if name:
        return Result("Git identity", "PASS", f"git will sign commits as '{name}'")
    return Result("Git identity", "WARN", "git has no user name set",
                  'Run: git config --global user.name "Your Name" and git config --global user.email you@example.com')

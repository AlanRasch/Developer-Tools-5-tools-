"""Read pinned dependencies and find which packages the project actually imports."""

from __future__ import annotations

import ast
import re
from dataclasses import dataclass
from pathlib import Path

PIN_RE = re.compile(r"^\s*([A-Za-z0-9][A-Za-z0-9._-]*)\s*==\s*([A-Za-z0-9.!+_-]+)")
NAME_RE = re.compile(r"^\s*([A-Za-z0-9][A-Za-z0-9._-]*)")
SKIP_DIRS = {".git", ".venv", "venv", "env", "node_modules", "__pycache__", "site-packages", "build", "dist"}

# Packages whose import name differs from the package name.
IMPORT_OVERRIDES = {
    "pyyaml": "yaml", "pillow": "pil", "beautifulsoup4": "bs4", "scikit-learn": "sklearn",
    "python-dotenv": "dotenv", "python-telegram-bot": "telegram", "pyjwt": "jwt",
    "opencv-python": "cv2", "protobuf": "google",
}


@dataclass(frozen=True)
class Dependency:
    name: str
    version: str


def parse_requirements(path: Path) -> tuple[list[Dependency], list[str]]:
    """Return (pinned packages written as name==version, names that are not pinned)."""
    pinned: list[Dependency] = []
    unpinned: list[str] = []
    for raw in path.read_text(encoding="utf-8").splitlines():
        line = raw.split("#", 1)[0].strip()
        if not line or line.startswith("-"):
            continue
        match = PIN_RE.match(line)
        if match:
            pinned.append(Dependency(match.group(1), match.group(2)))
            continue
        name = NAME_RE.match(line)
        if name:
            unpinned.append(name.group(1))
    return pinned, unpinned


def import_name(package: str) -> str:
    key = package.lower()
    return IMPORT_OVERRIDES.get(key, key.replace("-", "_"))


def imported_modules(root: Path) -> set[str]:
    """Top-level module names imported anywhere in the project (lower case)."""
    found: set[str] = set()
    for path in root.rglob("*.py"):
        if any(part in SKIP_DIRS for part in path.relative_to(root).parts[:-1]):
            continue
        try:
            tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        except (SyntaxError, UnicodeDecodeError):
            continue
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                found.update(alias.name.split(".")[0].lower() for alias in node.names)
            elif isinstance(node, ast.ImportFrom) and node.module and node.level == 0:
                found.add(node.module.split(".")[0].lower())
    return found


def is_imported(package: str, modules: set[str]) -> bool:
    return import_name(package) in modules

"""Collect what the code actually defines: names, command-line options and environment variables."""

from __future__ import annotations

import ast
import re
from dataclasses import dataclass, field
from pathlib import Path

SKIP_DIRS = {".git", ".venv", "venv", "env", "node_modules", "__pycache__", "site-packages", "build", "dist"}
OPTION_RE = re.compile(r"""['"](--[a-zA-Z][a-zA-Z0-9-]*)['"]""")
ENV_RE = re.compile(r"""['"]([A-Z][A-Z0-9]*(?:_[A-Z0-9]+)+)['"]""")


@dataclass
class CodeIndex:
    names: set[str] = field(default_factory=set)       # functions, classes, module-level variables
    options: set[str] = field(default_factory=set)     # e.g. --format, quoted in add_argument(...)
    env_vars: set[str] = field(default_factory=set)    # e.g. "DATABASE_URL" quoted in the code
    text: str = ""                                       # all source text, for simple substring checks


def _python_files(root: Path, source_dirs: list[Path]) -> list[Path]:
    files: set[Path] = set()
    for base in source_dirs:
        for path in base.rglob("*.py"):
            if not any(part in SKIP_DIRS for part in path.relative_to(root).parts[:-1]):
                files.add(path)
    return sorted(files)


def build_index(root: Path, source_dirs: list[Path]) -> CodeIndex:
    index = CodeIndex()
    chunks: list[str] = []
    for path in _python_files(root, source_dirs):
        source = path.read_text(encoding="utf-8", errors="replace")
        chunks.append(source)
        index.options.update(OPTION_RE.findall(source))
        index.env_vars.update(ENV_RE.findall(source))
        try:
            tree = ast.parse(source, filename=str(path))
        except SyntaxError:
            continue
        for node in ast.walk(tree):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
                index.names.add(node.name)
            elif isinstance(node, ast.Assign) and isinstance(node, ast.stmt):
                for target in node.targets:
                    if isinstance(target, ast.Name):
                        index.names.add(target.id)
    index.text = "\n".join(chunks)
    return index

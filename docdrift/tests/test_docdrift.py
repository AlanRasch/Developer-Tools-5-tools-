"""Offline tests for docdrift. Each test builds a small project in a temp folder."""

import json
from pathlib import Path

from docdrift.checks import check_document, find_docs
from docdrift.cli import main
from docdrift.code_index import build_index

DEMO = Path(__file__).resolve().parent.parent / "examples" / "demo"

CODE = '''\
import argparse
import os

DEFAULT_FORMAT = "text"


def load_settings():
    return os.getenv("DATABASE_URL")


class Exporter:
    pass


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--format")
'''


def make_project(tmp_path, readme):
    (tmp_path / "src").mkdir(parents=True)
    (tmp_path / "src" / "app.py").write_text(CODE)
    (tmp_path / "README.md").write_text(readme)
    return tmp_path


def issues_for(root):
    index = build_index(root, [root / "src"])
    issues = []
    for doc in find_docs(root, [root / "README.md"]):
        issues.extend(check_document(doc, root, index))
    return issues


def kinds(issues):
    return {(i.kind, i.item) for i in issues}


def test_matching_docs_have_no_issues(tmp_path):
    readme = (
        "# App\n\nRun with `--format` and set `DATABASE_URL`.\n\n"
        "Call `load_settings()` or use the `Exporter` class.\n\n"
        "```bash\npython app.py --format json\n```\n"
    )
    assert issues_for(make_project(tmp_path, readme)) == []


def test_missing_option_in_code_block_is_reported(tmp_path):
    readme = "```bash\npython app.py --output out.txt\n```\n"
    assert ("option", "--output") in kinds(issues_for(make_project(tmp_path, readme)))


def test_help_and_version_options_are_ignored(tmp_path):
    readme = "```\npython app.py --help --version\n```\n"
    assert issues_for(make_project(tmp_path, readme)) == []


def test_renamed_function_is_reported(tmp_path):
    readme = "Call `render_report()` to print the summary.\n"
    assert ("function", "render_report") in kinds(issues_for(make_project(tmp_path, readme)))


def test_removed_class_is_reported(tmp_path):
    readme = "Use the `LegacyParser` class.\n"
    assert ("class", "LegacyParser") in kinds(issues_for(make_project(tmp_path, readme)))


def test_missing_env_var_is_reported(tmp_path):
    readme = "Set `API_TOKEN_SECRET` before running.\n"
    assert ("env var", "API_TOKEN_SECRET") in kinds(issues_for(make_project(tmp_path, readme)))


def test_broken_relative_link_is_reported(tmp_path):
    readme = "See [the design notes](docs/design.md) and [home](https://example.com).\n"
    found = kinds(issues_for(make_project(tmp_path, readme)))
    assert ("broken link", "docs/design.md") in found
    assert not any(item.startswith("https") for _, item in found)


def test_existing_link_is_fine(tmp_path):
    root = make_project(tmp_path, "See [notes](NOTES.md).\n")
    (root / "NOTES.md").write_text("notes")
    assert issues_for(root) == []


def test_each_problem_is_reported_once(tmp_path):
    readme = "Use `ghost()` and `ghost()` again.\n"
    issues = issues_for(make_project(tmp_path, readme))
    assert len([i for i in issues if i.item == "ghost"]) == 1


def test_cli_exit_codes(tmp_path):
    root = make_project(tmp_path, "Call `ghost()`.\n")
    assert main(["check", "--root", str(root)]) == 0
    assert main(["check", "--root", str(root), "--fail-on-issues"]) == 1
    clean = make_project(tmp_path / "clean", "Nothing to see.\n")
    assert main(["check", "--root", str(clean), "--fail-on-issues"]) == 0


def test_cli_json_output(tmp_path):
    root = make_project(tmp_path, "Call `ghost()`.\n")
    out = tmp_path / "report.json"
    main(["check", "--root", str(root), "--format", "json", "-o", str(out)])
    data = json.loads(out.read_text())
    assert data["documents_checked"] == 1 and data["issues"][0]["item"] == "ghost"


def test_demo_project_reports_its_known_drift():
    index = build_index(DEMO, [DEMO / "src"])
    readme = DEMO / "README.md"
    found = {(i.kind, i.item) for i in check_document(readme, DEMO, index)}
    assert ("option", "--verbose") in found
    assert ("function", "render_report") in found
    assert ("class", "LegacyParser") in found
    assert ("broken link", "docs/design.md") in found
    assert ("broken link", "CHANGELOG.md") in found
    assert ("option", "--output") not in found  # --output exists in the code

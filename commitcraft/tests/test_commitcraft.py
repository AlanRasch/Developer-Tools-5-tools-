"""Offline tests. Git is not needed; diffs and commit lists are given directly."""

import subprocess
from datetime import date
from pathlib import Path

import pytest

from commitcraft.changelog import parse_subject, prepend_to_changelog, render_section
from commitcraft.cli import main
from commitcraft.diffstat import FileDiff, parse_diff
from commitcraft.message import MAX_SUBJECT, build_message, check_message, classify

SAMPLE = Path(__file__).resolve().parent.parent / "examples" / "sample.diff"


def file(path, added=(), removed=(), new=False):
    return FileDiff(path=path, added=list(added), removed=list(removed), is_new=new)


def test_parse_diff_reads_files_and_counts():
    files = parse_diff(SAMPLE.read_text())
    assert [f.path for f in files] == ["shop/cart.py", "tests/test_cart.py"]
    assert files[1].is_new and len(files[0].added) == 3


def test_tests_only_is_test_type():
    assert classify([file("tests/test_x.py", added=["assert 1"])]) == "test"


def test_docs_only_is_docs_type():
    assert classify([file("README.md", added=["hello"])]) == "docs"


def test_config_only_is_chore():
    assert classify([file("pyproject.toml", added=["x = 1"])]) == "chore"


def test_new_function_is_feat():
    assert classify([file("app/shop.py", added=["def checkout(cart):", "    return cart"])]) == "feat"


def test_bug_wording_is_fix():
    assert classify([file("app/shop.py", added=["    if x is None:  # fix crash on missing item"],
                          removed=["    if x:"])]) == "fix"


def test_sample_message_format():
    message = build_message(parse_diff(SAMPLE.read_text()))
    subject = message.splitlines()[0]
    assert subject.startswith(("feat(", "feat:", "test(", "fix(", "refactor(", "chore("))
    assert "- shop/cart.py (changed, +3 -0)" in message
    assert "- tests/test_cart.py (new file, +2 -0)" in message
    assert check_message(message) == []


def test_long_subjects_are_shortened():
    files = [file(f"module_{i}/file_{i}_with_long_name.py", added=["def f(): pass"]) for i in range(8)]
    subject = build_message(files).splitlines()[0]
    assert len(subject) <= MAX_SUBJECT


def test_nothing_staged_is_an_error():
    with pytest.raises(ValueError):
        build_message([])


def test_check_message_flags_bad_subject():
    problems = check_message("Updated stuff\n\n- x")
    assert any("type" in p for p in problems)


def test_parse_subject_variants():
    assert parse_subject("feat(api)!: drop v1") == {"type": "feat", "scope": "api", "breaking": True, "text": "drop v1"}
    assert parse_subject("Merge branch 'x'")["type"] == "other"


def test_changelog_groups_commits():
    subjects = ["feat(cart): add remove_item", "fix: handle empty cart", "docs: update readme",
                "feat(api)!: drop v1 endpoints", "Merge branch 'main'"]
    section = render_section("1.2.0", subjects, on=date(2026, 10, 9))
    assert section.startswith("## [1.2.0] - 2026-10-09")
    assert section.index("Breaking changes") < section.index("### Added") < section.index("### Fixed")
    assert "**cart:** add remove_item" in section
    assert "### Other" in section and "Merge branch" in section


def test_prepend_keeps_existing_entries(tmp_path):
    changelog = tmp_path / "CHANGELOG.md"
    changelog.write_text("# Changelog\n\n## [1.0.0] - 2026-01-01\n\n- First release\n")
    assert prepend_to_changelog(changelog, "## [1.1.0] - 2026-10-09\n\n- New thing\n") == "updated"
    text = changelog.read_text()
    assert text.index("1.1.0") < text.index("1.0.0")
    assert text.startswith("# Changelog")


def test_prepend_creates_missing_file(tmp_path):
    target = tmp_path / "CHANGELOG.md"
    assert prepend_to_changelog(target, "## [1.0.0]\n") == "created"
    assert target.read_text().startswith("# Changelog")


def test_cli_message_to_file(tmp_path):
    out = tmp_path / "msg.txt"
    assert main(["message", "--diff-file", str(SAMPLE), "-o", str(out)]) == 0
    assert out.read_text().startswith(("feat", "test", "fix", "refactor", "chore"))


def test_cli_changelog_from_real_git_history(tmp_path):
    if subprocess.run(["git", "--version"], capture_output=True).returncode != 0:
        pytest.skip("git is not installed")

    def git(*args):
        subprocess.run(["git", "-C", str(tmp_path), *args], check=True, capture_output=True,
                       env={"GIT_AUTHOR_NAME": "t", "GIT_AUTHOR_EMAIL": "t@t", "GIT_COMMITTER_NAME": "t",
                            "GIT_COMMITTER_EMAIL": "t@t", "PATH": __import__("os").environ["PATH"]})

    git("init", "-q")
    (tmp_path / "a.py").write_text("x = 1\n")
    git("add", "a.py")
    git("commit", "-qm", "feat: first feature")
    git("tag", "v1.0.0")
    (tmp_path / "a.py").write_text("x = 2\n")
    git("commit", "-qam", "fix: correct value")
    assert main(["changelog", "--repo", str(tmp_path), "--version", "1.0.1", "--write"]) == 0
    text = (tmp_path / "CHANGELOG.md").read_text()
    assert "### Fixed" in text and "correct value" in text
    assert "first feature" not in text  # it was before the tag

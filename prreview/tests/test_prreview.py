"""Offline tests. No git repository or network is needed."""

import json
from pathlib import Path

from prreview.cli import main
from prreview.diffparse import parse_diff
from prreview.report import render_json, render_markdown, render_text
from prreview.rules import review, summarize

SAMPLE = Path(__file__).resolve().parent.parent / "examples" / "sample.diff"


def test_parse_diff_tracks_files_and_line_numbers():
    changes = parse_diff(SAMPLE.read_text())
    assert [c.path for c in changes] == ["app/payments.py", "app/utils.py"]
    payments = changes[0]
    first_added_line, text = payments.added[0]
    assert first_added_line == 10
    assert "API_KEY" in text


def test_new_and_deleted_files_are_detected():
    diff = (
        "diff --git a/new.py b/new.py\nnew file mode 100644\n--- /dev/null\n+++ b/new.py\n@@ -0,0 +1 @@\n+x = 1\n"
        "diff --git a/old.py b/old.py\ndeleted file mode 100644\n--- a/old.py\n+++ /dev/null\n@@ -1 +0,0 @@\n-y = 2\n"
    )
    changes = parse_diff(diff)
    assert changes[0].path == "new.py" and changes[0].is_new
    assert len(changes) == 1  # the deleted file has no new path to report


def test_removed_error_handling_rule_on_its_own():
    diff = (
        "diff --git a/app.py b/app.py\n--- a/app.py\n+++ b/app.py\n@@ -1,4 +1,2 @@\n"
        "-    try:\n-        run()\n-    except ValueError:\n-        pass\n+    run()\n"
    )
    findings = review(parse_diff(diff))
    assert any(f.title == "Error handling removed" for f in findings)


def test_rules_find_security_and_quality_issues():
    findings = review(parse_diff(SAMPLE.read_text()))
    titles = {f.title for f in findings}
    assert {"Possible hard-coded secret", "SQL built from text", "Bare except clause",
            "Debugging leftover", "Use of eval() or exec()", "Unfinished work marker"} <= titles
    assert findings[0].severity == "High"  # most severe first


def test_specific_except_replaced_by_bare_except_is_flagged():
    findings = review(parse_diff(SAMPLE.read_text()))
    assert any(f.title == "Bare except clause" for f in findings)


def test_missing_test_changes_are_flagged():
    findings = review(parse_diff(SAMPLE.read_text()))
    assert any(f.title == "No test changes" for f in findings)


def test_tests_changed_clears_missing_test_warning():
    diff = (
        "diff --git a/app.py b/app.py\n--- a/app.py\n+++ b/app.py\n@@ -1 +1 @@\n-a = 1\n+a = 2\n"
        "diff --git a/tests/test_app.py b/tests/test_app.py\n--- a/tests/test_app.py\n+++ b/tests/test_app.py\n"
        "@@ -1 +1 @@\n-b = 1\n+b = 2\n"
    )
    assert not any(f.title == "No test changes" for f in review(parse_diff(diff)))


def test_summary_counts():
    summary = summarize(parse_diff(SAMPLE.read_text()))
    assert summary["files"] == 2 and summary["added"] > 0 and summary["removed"] > 0
    assert "app" in summary["by_folder"]


def test_renderers():
    changes = parse_diff(SAMPLE.read_text())
    findings, summary = review(changes), summarize(changes)
    assert "| High |" in render_markdown(summary, findings)
    assert "[High]" in render_text(summary, findings)
    assert json.loads(render_json(summary, findings))["summary"]["files"] == 2


def test_cli_diff_file_and_fail_on(capsys):
    assert main(["review", "--diff-file", str(SAMPLE), "--format", "text", "--fail-on", "high"]) == 1
    assert main(["review", "--diff-file", str(SAMPLE), "--format", "text"]) == 0


def test_cli_empty_diff(tmp_path, capsys):
    empty = tmp_path / "empty.diff"
    empty.write_text("")
    assert main(["review", "--diff-file", str(empty)]) == 0
    assert "No changes" in capsys.readouterr().out


def test_cli_writes_markdown_file(tmp_path):
    out = tmp_path / "review.md"
    assert main(["review", "--diff-file", str(SAMPLE), "-o", str(out)]) == 0
    assert out.read_text().startswith("## Pull request review")

"""Offline tests. The network is replaced by a fake lookup function."""

import json
from pathlib import Path

import pytest

from deptriage.cli import main
from deptriage.osv import lowest_fix, severity_of, version_key
from deptriage.parsing import Dependency, import_name, imported_modules, parse_requirements
from deptriage.report import render_json, render_markdown, render_text
from deptriage.triage import priority_for, scan

SAMPLE = Path(__file__).resolve().parent.parent / "examples" / "sample-app"


def fake_vulns(name, version):
    data = {
        "requests": [{"id": "TEST-1", "summary": "Credentials leak on redirect",
                      "database_specific": {"severity": "HIGH"},
                      "affected": [{"ranges": [{"type": "ECOSYSTEM", "events": [
                          {"introduced": "0"}, {"fixed": "2.20.0"}]}]}]}],
        "pyyaml": [{"id": "TEST-2", "summary": "Unsafe loading", "database_specific": {"severity": "MEDIUM"},
                    "affected": [{"ranges": [{"events": [{"fixed": "5.4"}]}]}]}],
        "flask": [{"id": "TEST-3", "summary": "Session issue", "database_specific": {"severity": "HIGH"}}],
    }
    if name == "numpy":
        raise ConnectionError("simulated network error")
    return data.get(name, [])


def test_parse_requirements_pins_and_unpinned(tmp_path):
    req = tmp_path / "requirements.txt"
    req.write_text("# comment\nrequests==2.19.1  # http\n-r other.txt\nnumpy\nflask>=1.0\n")
    pinned, unpinned = parse_requirements(req)
    assert pinned == [Dependency("requests", "2.19.1")]
    assert unpinned == ["numpy", "flask"]


def test_import_names_handle_overrides():
    assert import_name("PyYAML") == "yaml"
    assert import_name("Flask-Cors") == "flask_cors"


def test_imported_modules_ignores_skipped_folders(tmp_path):
    (tmp_path / "app.py").write_text("import requests\nfrom yaml import safe_load\n")
    (tmp_path / ".venv").mkdir()
    (tmp_path / ".venv" / "x.py").write_text("import flask\n")
    assert imported_modules(tmp_path) == {"requests", "yaml"}


def test_priority_uses_usage():
    assert priority_for("HIGH", True) == "High"
    assert priority_for("HIGH", False) == "Medium"
    assert priority_for("MEDIUM", True) == "Medium"
    assert priority_for("LOW", True) == "Low"


def test_version_ordering_and_lowest_fix():
    assert version_key("1.10.0") > version_key("1.9.9")
    vuln = {"affected": [{"ranges": [{"events": [{"fixed": "2.5"}, {"fixed": "2.20.0"}]}]}]}
    assert lowest_fix(vuln, "2.19.1") == "2.20.0"
    assert lowest_fix(vuln, "2.20.0") is None


def test_severity_defaults_to_unknown():
    assert severity_of({}) == "UNKNOWN"
    assert severity_of({"database_specific": {"severity": "critical"}}) == "CRITICAL"


def test_scan_ranks_imported_packages_first():
    deps = [Dependency("requests", "2.19.1"), Dependency("flask", "1.0"), Dependency("pyyaml", "5.3")]
    findings, errors = scan(deps, fake_vulns, modules={"requests", "yaml"})
    assert errors == []
    assert findings[0].package == "requests" and findings[0].priority == "High"
    flask = next(f for f in findings if f.package == "flask")
    assert flask.imported is False and flask.priority == "Medium"
    assert next(f for f in findings if f.package == "requests").fixed_in == "2.20.0"


def test_network_errors_are_collected_not_fatal():
    findings, errors = scan([Dependency("numpy", "1.0")], fake_vulns, modules=set())
    assert findings == [] and len(errors) == 1 and "simulated" in errors[0]


def test_renderers_include_key_facts():
    deps = [Dependency("requests", "2.19.1")]
    findings, errors = scan(deps, fake_vulns, modules={"requests"})
    assert "[High] requests==2.19.1" in render_text(findings, errors, 1, [])
    assert "| High |" in render_markdown(findings, errors, 1, [])
    assert json.loads(render_json(findings, errors, 1, []))["findings"][0]["vuln_id"] == "TEST-1"


def test_cli_fail_on_threshold(tmp_path, monkeypatch):
    (tmp_path / "requirements.txt").write_text("requests==2.19.1\n")
    (tmp_path / "app.py").write_text("import requests\n")
    monkeypatch.setattr("deptriage.cli.query_osv", fake_vulns)
    assert main(["scan", "--path", str(tmp_path), "--fail-on", "high"]) == 1
    assert main(["scan", "--path", str(tmp_path), "--fail-on", "none"]) == 0


def test_cli_missing_requirements_returns_2(tmp_path):
    assert main(["scan", "--path", str(tmp_path)]) == 2


def test_cache_avoids_repeat_queries(tmp_path):
    from deptriage.osv import cached
    calls = []

    def counting(name, version):
        calls.append(name)
        return []

    lookup = cached(counting, tmp_path / "cache.json")
    lookup("requests", "2.19.1")
    lookup("requests", "2.19.1")
    assert calls == ["requests"]


def test_sample_project_runs_offline(monkeypatch, capsys):
    monkeypatch.setattr("deptriage.cli.query_osv", fake_vulns)
    code = main(["scan", "--path", str(SAMPLE), "--fail-on", "none"])
    out = capsys.readouterr().out
    assert code == 0
    assert "numpy" in out  # unpinned package reported

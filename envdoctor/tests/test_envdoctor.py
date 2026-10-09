"""Offline tests. Commands and ports are simulated, so the results do not depend on the computer."""

import json
import socket
from pathlib import Path

import pytest

from envdoctor import checks
from envdoctor.checks import (check_command, check_env_file, check_port, check_python,
                              current_os, parse_env, python_matches)
from envdoctor.cli import main
from envdoctor.doctor import python_requirement, run_checks

SAMPLE = Path(__file__).resolve().parent.parent / "examples" / "sample-project"


def test_python_version_specs():
    assert python_matches(">=3.10", (3, 12))
    assert not python_matches(">=3.11", (3, 10))
    assert python_matches(">=3.10,<4", (3, 13))
    assert not python_matches(">=3.8,<3.10", (3, 10))


def test_python_check_uses_requirement():
    assert check_python(">=3.1").status == "PASS"
    assert check_python(">=99.0").status == "FAIL"
    assert check_python(None).status == "PASS"


def test_missing_command_gets_os_specific_hint(monkeypatch):
    monkeypatch.setattr(checks.shutil, "which", lambda name: None)
    result = check_command("git", system="windows")
    assert result.status == "FAIL" and "winget" in result.fix
    assert "xcode-select" in check_command("git", system="macos").fix
    assert "brew" in check_command("node", system="macos").fix


def test_present_command_passes(monkeypatch):
    monkeypatch.setattr(checks.shutil, "which", lambda name: "/usr/bin/" + name)
    assert check_command("git").status == "PASS"


def test_env_file_missing_and_present(tmp_path):
    (tmp_path / ".env.example").write_text("API_TOKEN=\nDEBUG=false\n")
    assert check_env_file(tmp_path)[0].status == "FAIL"
    (tmp_path / ".env").write_text("API_TOKEN=abc123\n")
    results = check_env_file(tmp_path)
    assert results[0].status == "PASS"
    assert not any("API_TOKEN" in r.name for r in results)


def test_parse_env_handles_quotes_and_comments(tmp_path):
    path = tmp_path / ".env"
    path.write_text('# comment\nNAME="Alan"\nEMPTY=\nURL=sqlite:///a.db\n')
    assert parse_env(path) == {"NAME": "Alan", "EMPTY": "", "URL": "sqlite:///a.db"}


def test_port_in_use_is_warning():
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as blocker:
        blocker.bind(("127.0.0.1", 0))
        blocker.listen(1)
        port = blocker.getsockname()[1]
        assert check_port(port).status == "WARN"


def test_free_port_passes():
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as probe:
        probe.bind(("127.0.0.1", 0))
        port = probe.getsockname()[1]
    assert check_port(port).status == "PASS"


def test_python_requirement_read_from_pyproject(tmp_path):
    (tmp_path / "pyproject.toml").write_text('[project]\nrequires-python = ">=3.11"\n')
    assert python_requirement(tmp_path) == ">=3.11"


def test_run_checks_uses_project_config(monkeypatch):
    monkeypatch.setattr(checks.shutil, "which", lambda name: "/bin/" + name)
    results = run_checks(SAMPLE)
    names = [r.name for r in results]
    assert "Command: git" in names and "Command: node" in names
    assert "Python version" in names


def test_cli_json_and_exit_code(tmp_path, monkeypatch, capsys):
    (tmp_path / "envdoctor.json").write_text(json.dumps({"commands": ["definitely-not-installed-xyz"]}))
    monkeypatch.setattr(checks.shutil, "which", lambda name: None if "xyz" in name else "/bin/x")
    code = main([str(tmp_path), "--json"])
    data = json.loads(capsys.readouterr().out)
    assert code == 1
    assert data["summary"]["FAIL"] >= 1


def test_cli_missing_folder_returns_2(tmp_path):
    assert main([str(tmp_path / "missing")]) == 2


def test_os_detection_returns_known_value():
    assert current_os() in {"macos", "windows", "linux"}

# Local Developer Environment Doctor

Check whether a computer is ready to work on a project, and say exactly how to fix anything that is missing. It runs on Windows, macOS and Linux.

Setting up a project on a new laptop often wastes hours: the wrong Python version, a missing Git, a `.env` file that was never created, or a port already used by another program. This tool finds those problems in a few seconds.

---

## What it checks

| Check | What it looks for |
|---|---|
| Python version | Matches the `requires-python` line in `pyproject.toml`, or the `python` setting in `envdoctor.json` |
| Virtual environment | Whether one is active, so project packages stay separate |
| Commands | Each command in the config (default: `git`) is on your PATH, with an install hint for your system |
| `.env` file | Exists when `.env.example` does, and sets every variable that has no default |
| Ports | Each port listed in the config is free |
| Git identity | Your name is set, so commits are attributed correctly |

Results are PASS, WARN or FAIL. Each problem comes with a plain-language fix.

---

## Installation

You need Python 3.10 or newer.

**Windows (PowerShell)**

```powershell
cd envdoctor
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -e .
```

**macOS and Linux**

```bash
cd envdoctor
python3 -m venv .venv
source .venv/bin/activate
pip install -e .
```

You can also run the tool without installing it: `python -m envdoctor path/to/project`.

---

## Quick start

Check the current folder:

```bash
envdoctor
```

Check another project, and get machine-readable output:

```bash
envdoctor path/to/project
envdoctor path/to/project --json
```

Output for the included sample project, run on a computer without a `.env` file:

```
[PASS] Python version: Python 3.13.16 meets '>=3.10'
[WARN] Virtual environment: No virtual environment is active
       Fix: Create one with: python -m venv .venv   then activate it, so packages stay separate per project.
[PASS] Command: git: 'git' is on PATH
[PASS] Command: node: 'node' is on PATH
[FAIL] .env file: .env is missing
       Fix: Copy .env.example to .env and fill in the values.
[PASS] Port 8000: port 8000 is free

Summary: 5 passed, 1 warning(s), 1 failure(s).
Fix the failures above, then run envdoctor again.
```

---

## Project configuration

Add an `envdoctor.json` file to your project to say what it needs:

```json
{
  "python": ">=3.10",
  "commands": ["git", "node", "docker"],
  "ports": [8000, 5432]
}
```

| Setting | Meaning |
|---|---|
| `python` | Python version requirement, for example `>=3.11` or `>=3.10,<4`. If missing, the tool reads `pyproject.toml`. |
| `commands` | Programs that must be on the PATH. Default: `["git"]`. |
| `ports` | Port numbers that should be free, for example for a web server or database |

Without this file, the tool still checks Python, the virtual environment, Git, and the `.env` file if `.env.example` exists.

---

## Install hints

For common tools, the tool shows the command for your operating system:

| Tool | Windows | macOS | Linux |
|---|---|---|---|
| git | `winget install Git.Git` | `xcode-select --install` | `sudo apt install git` |
| node | `winget install OpenJS.NodeJS.LTS` | `brew install node` | `sudo apt install nodejs npm` |
| docker | Install Docker Desktop | Install Docker Desktop | `sudo apt install docker.io` |

Other tools get a general instruction to install them and make sure they are on the PATH.

---

## Exit codes

| Code | Meaning |
|---|---|
| `0` | No failures (warnings may still be shown) |
| `1` | At least one FAIL result |
| `2` | The folder does not exist |

Warnings do not fail the check, because they usually describe optional improvements.

---

## Privacy

Everything runs on your computer. The tool does not send any information anywhere. It reads the `.env` file to check which variables are set, but it does not print their values.

---

## Limitations

- **Port checks are a snapshot.** A port that is free now may be taken later.
- **Commands are checked, not versions.** The tool confirms that `node` exists, not that it is version 20. Add version checks in `checks.py` if you need them.
- **Some tools are not detected.** A tool installed in a non-standard location that is not on the PATH will be reported as missing.
- **Windows PATH changes need a new terminal.** After installing a tool, open a new terminal window before running the check again.

---

## Project structure

```
envdoctor/
├── envdoctor/
│   ├── checks.py   # each individual check and the install hints
│   ├── cli.py      # command-line output and exit codes
│   └── doctor.py   # runs the checks and reads envdoctor.json
├── examples/sample-project/   # an envdoctor.json and .env.example to try
├── tests/test_envdoctor.py    # 13 offline tests
├── pyproject.toml
└── README.md
```

---

## Running the tests

```bash
pip install -e ".[dev]"
python -m pytest -q
```

The tests do not depend on what is installed on your computer. They simulate commands and check ports on a local address.

---

## Troubleshooting

| Problem | What to try |
|---|---|
| A tool is installed but reported missing | Open a new terminal so the PATH is refreshed, or check that the tool is on the PATH |
| `.env is missing` | Copy `.env.example` to `.env` |
| Port reported in use | Find the other program with a tool such as `lsof -i :8000` (macOS and Linux) or `netstat -ano` (Windows), and stop it |
| Python check fails after an upgrade | Create a new virtual environment with the correct Python version |

---

**Author:** Dr. Firend Alan Rasch · American University of Phnom Penh
**License:** MIT (or your preferred license)

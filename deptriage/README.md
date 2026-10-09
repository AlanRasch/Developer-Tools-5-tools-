# Dependency Security Triage

Find known security vulnerabilities in a Python project's pinned dependencies, and see which ones the project actually uses. Results are ranked so the urgent fixes come first, and each finding shows the smallest published version that fixes it.

Most vulnerability scanners report every problem in every package, including packages the code never imports. This tool ranks a vulnerability higher when the project really imports that package.

---

## What it does

1. Reads `name==version` lines from `requirements.txt`.
2. Checks each pinned version against the free [OSV database](https://osv.dev).
3. Scans the project's Python files to see which packages are imported.
4. Ranks each finding:
   - **High**: a critical or high severity issue in a package the code imports
   - **Medium**: a high severity issue in a package the code does not import, or a medium issue in one it does
   - **Low**: everything else
5. Suggests the lowest fixed version newer than the one you have.
6. Lists packages that are not pinned, because they cannot be checked reliably.

---

## Installation

You need Python 3.10 or newer, and an internet connection for the vulnerability lookups.

**macOS and Linux**

```bash
cd deptriage
python3 -m venv .venv
source .venv/bin/activate
pip install -e .
```

**Windows (PowerShell)**

```powershell
cd deptriage
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -e .
```

This installs the `dep-triage` command. You can also run it as `python -m deptriage`.

---

## Quick start

```bash
dep-triage scan --path path/to/your/project
```

To save time on repeat runs, keep the results in a cache file:

```bash
dep-triage scan --path path/to/your/project --cache .dep-triage-cache.json
```

To produce a Markdown report, for example for a pull request comment:

```bash
dep-triage scan --format markdown -o dependency-report.md --fail-on none
```

---

## Commands and options

| Option | Meaning |
|---|---|
| `--path PATH` | Project folder (default: current folder) |
| `--requirements FILE` | File with the pinned versions (default: `requirements.txt`) |
| `--format text\|markdown\|json` | Output format (default: text) |
| `-o FILE` | Save the report to a file |
| `--fail-on high\|medium\|low\|none` | Exit with code 1 if findings at this level or higher exist (default: `high`) |
| `--cache FILE` | Store lookups in a JSON file to avoid repeat network calls |

**Exit codes:** `0` no blocking findings, `1` blocking findings were found, `2` a problem such as a missing requirements file.

---

## Reading the output

```
[High] requests==2.19.1  OSV-2023-XXXX  (HIGH, imported by this project)
    Credentials can leak when a redirect changes host
    Fix: upgrade to 2.20.0 or newer
```

- **Priority** is the ranking described above.
- **imported by this project** means a Python file in the project imports the package.
- **Fix** is the lowest published fixed version newer than yours. If the line says no fixed version is published yet, the risk remains until the maintainers release a fix. Consider replacing the package or limiting how the code uses it.

---

## Using it in continuous integration

```yaml
- name: Check dependencies
  run: |
    pip install -e path/to/deptriage
    dep-triage scan --format markdown -o dep-report.md --fail-on high
```

Adding `--fail-on high` makes the build fail only for the most urgent problems, so the team can fix the rest at a steady pace.

---

## How the checks work

- **Pinned versions only.** A line such as `requests>=2.0` is listed as not pinned, because the tool cannot know which version you will install. Pin your dependencies with `==` to get reliable results.
- **Usage detection is approximate.** The tool looks at `import` statements. It does not follow dynamic imports, plugins loaded by name, or code that runs only in another folder. A package marked as not imported is probably unused, but check before you remove it.
- **Version comparison is simple.** Versions are compared part by part, so unusual version schemes may choose the wrong upgrade. Check the suggestion before you apply it.
- **The database is only as complete as OSV.** A package with no entry in OSV is not necessarily safe.

---

## Privacy

Each package name and version is sent to the OSV service at `api.osv.dev` to be checked. Your source code is never sent anywhere. The `--cache` file stays on your computer.

---

## Project structure

```
deptriage/
├── deptriage/
│   ├── cli.py        # command-line options and exit codes
│   ├── osv.py        # OSV lookups, version comparison, cache
│   ├── parsing.py    # requirements file and import detection
│   ├── report.py     # text, Markdown and JSON output
│   └── triage.py     # priority rules and scanning
├── examples/sample-app/   # small project with a requirements file to try
├── tests/test_deptriage.py   # 13 offline tests (the network is replaced by a fake)
├── pyproject.toml
└── README.md
```

---

## Running the tests

```bash
pip install -e ".[dev]"
python -m pytest -q
```

The tests do not use the network. They replace the vulnerability lookup with a fake, so they run the same way every time.

Note: the live OSV lookup was not run in the environment where this tool was built, because that environment has no internet access. Run `dep-triage scan` on a machine with internet access to confirm live results.

---

## Troubleshooting

| Problem | What to try |
|---|---|
| `could not reach the OSV database` | Check your internet connection or proxy settings, then run again |
| Nothing is checked | Make sure the requirements file has `name==version` lines |
| Every package says "not imported" | Run the tool from the project folder, or pass `--path` |
| `requirements file not found` | Pass the correct file with `--requirements` |

---

**Author:** Dr. Firend Alan Rasch · American University of Phnom Penh
**License:** MIT (or your preferred license)

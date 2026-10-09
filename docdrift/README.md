# Documentation Drift Detector

Find documentation that no longer matches the code. It checks that the functions, classes, command-line options and environment variables mentioned in your Markdown files still exist in the source, and that links between documents still work.

Outdated documentation is one of the most common complaints from new developers. This tool catches the mismatches before someone else trips over them.

---

## What it checks

| Problem | Example in the docs | What the tool does |
|---|---|---|
| Option that no longer exists | `python app.py --output out.txt` | Checks that `--output` is defined in the code |
| Function that was renamed or removed | `` `render_report()` `` | Checks that a function with that name exists |
| Class that was removed | `` `LegacyParser` `` | Checks that a class with that name exists |
| Environment variable that was removed | `` `API_TOKEN_SECRET` `` | Checks that the variable is used in the code |
| Broken relative link | `[design notes](docs/design.md)` | Checks that the file exists |

Each problem is reported once per document, with the line number. Common help and version options are ignored.

---

## Installation

You need Python 3.10 or newer. No other packages are needed.

**macOS and Linux**

```bash
cd docdrift
python3 -m venv .venv
source .venv/bin/activate
pip install -e .
```

**Windows (PowerShell)**

```powershell
cd docdrift
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -e .
```

---

## Quick start

Check the README and the `docs` folder of your project:

```bash
docdrift check --root path/to/your/project
```

Check specific files and a specific source folder:

```bash
docdrift check --root . --docs README.md --docs guides --source app
```

Produce a Markdown report, and fail the build if any issue is found:

```bash
docdrift check --format markdown -o docs-report.md --fail-on-issues
```

Output from the included demo:

```
Checked 1 document(s).
Found 5 issue(s):

README.md:7  [option]  --verbose appears in the docs but not in the code
README.md:13  [function]  `render_report()` is mentioned but no such function exists
README.md:13  [class]  `LegacyParser` is mentioned but no such class exists
README.md:15  [broken link]  link to 'docs/design.md' points to a file that does not exist
README.md:15  [broken link]  link to 'CHANGELOG.md' points to a file that does not exist
```

Those five problems were planted on purpose in `examples/demo/README.md`, so you can see the tool working before you point it at your own project.

---

## Commands and options

| Option | Meaning |
|---|---|
| `--root PATH` | Project folder (default: current folder) |
| `--docs PATH` | Markdown file or folder to check, relative to `--root`. Repeat for several. Default: `README.md` and `docs/` |
| `--source PATH` | Folder with the code. Repeat for several. Default: `src`, or the whole project if there is no `src` folder |
| `--format text\|markdown\|json` | Output format (default: text) |
| `-o FILE` | Save the report to a file |
| `--fail-on-issues` | Exit with code 1 if any issue is found |

**Exit codes:** `0` no issues (or issues without `--fail-on-issues`), `1` issues found with `--fail-on-issues`, `2` a problem such as a missing folder.

---

## How it reads your project

- **Code:** every `.py` file under the source folder is read. Function, class and top-level variable names are collected with Python's own parser. Options are found where they are quoted in the code (for example `"--output"`), and environment variables are found where they appear as quoted names.
- **Docs:** each Markdown file is read line by line. Code blocks are checked for options and environment variables. Inline code such as `` `name()` `` is checked for function and class names. Links are checked for files that exist.

Inside code blocks, the tool checks options and environment variables only. Function and class names are checked only in inline code, because code blocks often show example output.

---

## Limitations

- **Python only.** Other languages are not checked.
- **Name checks are simple.** A function mentioned as `` `load()` `` is checked by name. If another library has a function with the same name, the tool cannot tell the difference.
- **Some false positives are possible.** For example, a tool name written in capitals with an underscore may look like an environment variable. Treat each issue as a suggestion, and ignore the ones that are correct.
- **Behaviour is not checked.** If a function still exists but now does something different, the tool will not notice.
- **Only Markdown is read.** ReStructuredText and other formats are not checked.

---

## Using it in continuous integration

```yaml
- name: Check documentation
  run: |
    pip install -e path/to/docdrift
    docdrift check --format markdown -o docs-report.md --fail-on-issues
```

Start without `--fail-on-issues` if your documentation already has many issues. Fix them gradually, then turn the check on.

---

## Project structure

```
docdrift/
├── docdrift/
│   ├── checks.py      # the documentation checks
│   ├── cli.py         # command-line options and exit codes
│   ├── code_index.py  # collects names, options and variables from the code
│   └── report.py      # text, Markdown and JSON output
├── examples/demo/     # a tool with planted documentation problems
├── tests/test_docdrift.py   # 12 offline tests
├── pyproject.toml
└── README.md
```

---

## Running the tests

```bash
pip install -e ".[dev]"
python -m pytest -q
```

---

## Troubleshooting

| Problem | What to try |
|---|---|
| `no Markdown documents found` | Check `--docs`, or run the tool from the project folder |
| Too many false positives | Remove the terms that are not code from the docs, or fix the checks in `checks.py` |
| An option that exists is reported | Make sure the option is quoted in the code, for example `"--format"` |

---

**Author:** Dr. Firend Alan Rasch · American University of Phnom Penh
**License:** MIT (or your preferred license)

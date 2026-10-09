# PR Reviewer

Review a pull request's changes before a human reads them. It checks the diff for common risks, such as hard-coded secrets, SQL built from text, `eval()`, bare `except:` clauses, debugging leftovers, and changes to code with no matching test changes. It then writes a short summary you can paste into a pull request comment.

The checks are fast and predictable. They catch common mistakes and make reviews quicker, but they do not replace a human reviewer.

---

## Features

- Works on any git repository, or on a saved diff file, so it runs without network access.
- Findings are ranked High, Medium or Low, and each one shows the file and line.
- Flags source changes that come without test changes.
- Reports large pull requests that would be easier to review if split.
- Output as Markdown for comments, plain text, or JSON.
- Optional plain-language summary written by Claude (needs an API key).
- Can fail a build when High findings exist.

---

## Installation

You need Python 3.10 or newer and git.

**macOS and Linux**

```bash
cd prreview
python3 -m venv .venv
source .venv/bin/activate
pip install -e .
```

**Windows (PowerShell)**

```powershell
cd prreview
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -e .
```

For the optional AI summary, install the extra with `pip install -e ".[claude]"`.

---

## Quick start

Review your current branch against `main`, run from inside the repository:

```bash
prreview review --base main
```

Review a saved diff, which needs no git at all:

```bash
prreview review --diff-file examples/sample.diff
```

Save a Markdown review for a pull request comment:

```bash
prreview review --base main --format markdown -o review.md
```

Add a plain-language summary (set `ANTHROPIC_API_KEY` first):

```bash
prreview review --base main --with-claude
```

Output from the included sample diff:

```
Changes 2 file(s): +10 / -6 lines, mainly in app (2).

[High] Possible hard-coded secret (app/payments.py:10)
    Secrets belong in environment variables or a secret store, not in source code.
[High] SQL built from text (app/payments.py:11)
    Build queries with placeholders (for example ? or %s) and pass values separately.
[High] Use of eval() or exec() (app/utils.py:2)
    Running strings as code is a common route to code injection. Parse the input instead.
[Medium] Bare except clause (app/payments.py:14)
    A bare except hides every error, including KeyboardInterrupt. Name the exception type.
[Medium] Debugging leftover (app/payments.py:17)
    Remove debugging calls before merging.
[Medium] No test changes (app/payments.py, app/utils.py)
    2 source file(s) changed but no test file did. Add or update tests.
[Low] Unfinished work marker (app/payments.py:16)
    Mark unfinished work in the issue tracker, or finish it before merging.
```

---

## Commands and options

| Option | Meaning |
|---|---|
| `--base BRANCH` | Branch to compare with (default: `main`) |
| `--head REF` | Branch or commit to review (default: `HEAD`) |
| `--diff-file FILE` | Review a saved diff instead of running git |
| `--repo PATH` | Repository folder (default: current folder) |
| `--format markdown\|text\|json` | Output format (default: markdown) |
| `-o FILE` | Save the review to a file |
| `--fail-on high\|medium\|low\|none` | Exit with code 1 if findings at this level or higher exist (default: `none`) |
| `--with-claude` | Add a plain-language summary (needs `ANTHROPIC_API_KEY`) |

**Exit codes:** `0` review completed, `1` findings at the `--fail-on` level, `2` a problem such as git not being available.

---

## What the rules check

| Severity | Check | Why |
|---|---|---|
| High | `eval()` or `exec()` | Running text as code can allow code injection |
| High | `shell=True` | Passing text to the shell can allow command injection |
| High | Hard-coded passwords, keys, tokens | Secrets in source code leak through version control |
| High | SQL built with `+`, `{}` or `%` | Text-built queries can allow SQL injection |
| Medium | Bare `except:` | Hides every error, including `KeyboardInterrupt` |
| Medium | Removed `except` blocks | Errors may no longer be handled |
| Medium | Debugging calls (`breakpoint()`, `pdb`, `console.log`) | Should not reach production |
| Medium | Source changed, no test changed | Changes without tests are harder to trust |
| Low | `TODO`, `FIXME`, `XXX` | Unfinished work |
| Low | More than 400 changed lines | Large reviews get less attention |

The rules look only at added and removed lines. They do not understand your architecture, so treat each finding as a prompt to look, not a verdict.

---

## Using it in a pull request workflow

```yaml
- name: Review pull request
  run: |
    pip install -e path/to/prreview
    prreview review --base origin/main --format markdown -o pr-review.md --fail-on high
```

Adjust `--fail-on` to match your team. Starting with `high` blocks only the most serious issues while the team gets used to the tool.

---

## Privacy

Without `--with-claude`, everything stays on your computer. With `--with-claude`, the first 12,000 characters of the diff are sent to the Anthropic API to write the summary. Do not use that option for code you cannot share with that service.

---

## Project structure

```
prreview/
├── prreview/
│   ├── cli.py        # command-line options and the optional AI summary
│   ├── diffparse.py  # reads a unified diff into per-file changes
│   ├── gitops.py     # gets the diff from git
│   ├── report.py     # Markdown, text and JSON output
│   └── rules.py      # review rules and summary counts
├── examples/sample.diff   # a diff with deliberate problems, to try the tool
├── tests/test_prreview.py # 12 offline tests
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
| `No changes found` | Check the branch names with `--base` and `--head`, and make sure the branch has commits |
| `git diff failed` | Run the command from inside the repository, or use `--repo` |
| `--with-claude needs ANTHROPIC_API_KEY` | Set the key in your environment |
| Many "No test changes" findings | Those files may be legitimately untested. Check the list, and add tests where needed |

---

**Author:** Dr. Firend Alan Rasch · American University of Phnom Penh
**License:** MIT (or your preferred license)

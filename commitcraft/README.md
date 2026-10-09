# Commit Writer

Two small helpers for developers who write good commit history without the effort:

1. **`commitcraft message`** reads the changes you have staged, and writes a commit message in the Conventional Commits style: `feat(scope): short description`, followed by one line per changed file.
2. **`commitcraft changelog`** reads the commits since the last release tag, groups them into Added, Fixed, Changed, Documentation and Breaking changes, and adds a new section to your `CHANGELOG.md`.

It works offline. No API key is needed.

---

## Installation

You need Python 3.10 or newer, and git for the commands that read your repository.

**macOS and Linux**

```bash
cd commitcraft
python3 -m venv .venv
source .venv/bin/activate
pip install -e .
```

**Windows (PowerShell)**

```powershell
cd commitcraft
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -e .
```

---

## Writing a commit message

Stage your changes, then run:

```bash
git add .
commitcraft message
```

Example output, from the included sample diff:

```
feat: add cart, test_cart

- shop/cart.py (changed, +3 -0)
- tests/test_cart.py (new file, +2 -0)
```

To use the message directly for your commit:

```bash
commitcraft message -o .git/COMMIT_MSG_DRAFT
git commit -F .git/COMMIT_MSG_DRAFT
```

Read the message before you commit. The tool guesses the type from the kind of change, so correct it when it is wrong.

### How the type is chosen

| Type | Chosen when |
|---|---|
| `test` | Only test files changed |
| `docs` | Only Markdown or text documents changed |
| `chore` | Only configuration files changed |
| `feat` | New files or new functions were added |
| `fix` | Added lines use words such as fix, bug, error, crash or missing |
| `refactor` | Roughly as many lines were added as removed |
| `chore` | Anything else |

### Checks on the message

The tool warns when the subject is longer than 72 characters, or does not start with a recognised type. Subjects are shortened automatically to fit the limit.

---

## Writing a changelog section

```bash
commitcraft changelog --version 1.2.0            # print the section only
commitcraft changelog --version 1.2.0 --write    # add it to CHANGELOG.md
```

By default the tool starts from the latest git tag. To start from a specific tag:

```bash
commitcraft changelog --version 1.2.0 --since v1.1.0 --write
```

Commit messages in the Conventional Commits style become grouped entries:

```markdown
## [1.2.0] - 2026-10-09

### Breaking changes
- **api:** drop v1 endpoints

### Added
- **cart:** add remove_item

### Fixed
- handle empty cart
```

Messages that do not follow the style go under **Other**, so nothing is lost. A line that ends with `!` after the type, such as `feat!:`, is listed under **Breaking changes**.

When `CHANGELOG.md` already exists, the new section is placed below the `# Changelog` heading, so the newest release is at the top.

---

## Commands and options

| Command | Option | Meaning |
|---|---|---|
| `message` | `--repo PATH` | Repository folder (default: current folder) |
| `message` | `--diff-file FILE` | Use a saved diff instead of the staged changes |
| `message` | `-o FILE` | Save the message to a file |
| `changelog` | `--version VERSION` | Version for the new section (required) |
| `changelog` | `--since TAG` | Start from this tag (default: the latest tag) |
| `changelog` | `--write` | Add the section to the changelog file (default: print only) |
| `changelog` | `--file NAME` | Changelog file name (default: `CHANGELOG.md`) |

**Exit codes:** `0` success, `2` a problem such as git not being available or nothing being staged.

---

## Using it with a git hook

To start every commit message with a suggestion, save this as `.git/hooks/prepare-commit-msg` and make it executable (on macOS and Linux). It only fills in an empty message, so it never overwrites what you wrote:

```bash
#!/bin/sh
if [ -z "$(grep -v '^#' "$1" | tr -d '[:space:]')" ]; then
  commitcraft message > "$1" 2>/dev/null || true
fi
```

On Windows, Git runs hooks with its own shell, so the same script works in Git Bash.

---

## Project structure

```
commitcraft/
├── commitcraft/
│   ├── changelog.py  # groups commits and updates CHANGELOG.md
│   ├── cli.py        # the message and changelog commands
│   ├── diffstat.py   # reads a diff into per-file changes
│   ├── gitops.py     # reads staged changes, tags and history from git
│   └── message.py    # chooses the type, scope and subject
├── examples/sample.diff   # a sample diff to try the tool
├── tests/test_commitcraft.py   # 16 offline tests, including a real git history test
├── pyproject.toml
└── README.md
```

---

## Running the tests

```bash
pip install -e ".[dev]"
python -m pytest -q
```

The test that builds a real git history is skipped automatically if git is not installed.

---

## Troubleshooting

| Problem | What to try |
|---|---|
| `nothing is staged` | Run `git add` first, or use `--diff-file` |
| `git describe failed` or no tag found | Create a tag such as `git tag v1.0.0`, or pass `--since` |
| Wrong type chosen | Edit the message before committing; the rules are simple by design |
| Subject is too long | Shorten the description, or edit the message |

---

**Author:** Dr. Firend Alan Rasch · American University of Phnom Penh
**License:** MIT (or your preferred license)

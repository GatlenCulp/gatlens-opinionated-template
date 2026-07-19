---
name: gotem-setup
description: >-
  Install uv and use GOTem (Gatlen's Opinionated Template) to scaffold a brand-new
  Python project repository from scratch, fully unattended, then verify it end-to-end.
  Use when the user wants to create a new project from the GOTem / gatlens-opinionated-template
  cookiecutter, bootstrap a new repo with this template, or test that GOTem generates a
  working project. macOS / Linux only.
---

# GOTem Setup

Bootstrap a **new project repository** with GOTem (Gatlen's Opinionated Template) on a clean
machine. This skill installs `uv` from scratch and runs GOTem **directly from its GitHub source**
(no PyPI, no local checkout of the template required), so it works even when nothing but a shell,
`git`, and `curl` are present.

`gotem` is a thin wrapper around the Cookiecutter CLI whose template and version are pre-pinned, so
**every Cookiecutter flag works** — including `--no-input` and `key=value` overrides, which is what
makes unattended generation possible.

## When to use this

- The user asks to "create a new project with GOTem", "scaffold a repo from gatlens-opinionated-template", or similar.
- You need to generate a project without any interactive prompts (CI, an agent, a script).
- You want to smoke-test that GOTem produces a working project.

## Scope note

This skill is **self-contained and independent** of the GOTem repository it lives in. Do not assume
the template source is on disk. Everything is fetched fresh from GitHub.

---

## Prerequisites

These must exist on the machine (all standard on macOS/Linux dev boxes):

- `curl` — to install `uv`.
- `git` — GOTem's default (`version_control=git (local)`) runs `git init` + an initial commit in the new project.
- `make` — when `environment_manager=uv` (the default), GOTem's post-generation hook runs `make create_environment` and `make requirements` inside the new project.

You do **not** need a pre-installed Python: `uv` provides one on demand.

Set a git identity if the machine has none (the initial commit needs it):

```bash
git config --global user.name  >/dev/null 2>&1 || git config --global user.name  "Automated Setup"
git config --global user.email >/dev/null 2>&1 || git config --global user.email "setup@example.com"
```

---

## Step 1 — Install uv from scratch

```bash
# Installs uv into ~/.local/bin without touching system Python
curl -LsSf https://astral.sh/uv/install.sh | sh

# Make it available in the current shell
export PATH="$HOME/.local/bin:$PATH"
command -v uv >/dev/null || source "$HOME/.local/bin/env"

uv --version   # sanity check
```

If `uv` is already installed, this is a no-op — skip to Step 2.

---

## Step 2 — Generate a new project (unattended)

Run GOTem straight from the GitHub source with `uvx`. `uvx --from git+<url>` installs the tool into a
throwaway environment and runs it; no global install, no local clone.

```bash
# Choose where the new project should be created and what it is called.
OUTPUT_DIR="$HOME/projects"          # parent dir; the project folder is created inside it
PROJECT_NAME="My New Project"        # human-readable; repo/module names are derived from this
mkdir -p "$OUTPUT_DIR"

uvx --from "git+https://github.com/GatlenCulp/gatlens-opinionated-template" gotem \
  --no-input \
  --output-dir "$OUTPUT_DIR" \
  project_name="$PROJECT_NAME" \
  author_name="Your Name" \
  description="A short description of the project." \
  python_version_number="3.12"
```

- `--no-input` — never prompt; take the default for anything you don't override.
- `--output-dir` — where the generated project folder is placed.
- `key=value` args — override any field from `ccds.json` (see the reference below).
- The template itself is pinned to GOTem's released tag by the `gotem` wrapper, so results are reproducible. To pin the **tool** version too, install from a tag: `git+https://github.com/GatlenCulp/gatlens-opinionated-template@v0.5.1`.

The resulting project lands at `"$OUTPUT_DIR/<repo_name>"`, where `<repo_name>` is
`project_name` lowercased with spaces replaced by underscores (e.g. `my_new_project`).

### Keeping it fully offline of GitHub auth

The **defaults are safe for unattended runs**: `version_control` defaults to `git (local)` and both
SSH-key options default to `n`, so **no `gh` login, GitHub API call, or SSH key generation happens**.
Only opt into those by overriding the fields below — and only when the environment is authenticated
(`gh auth login` done) and the user explicitly wants a GitHub repo created.

### Common overrides (from `ccds.json`)

| Field | Default (first option) | Notable choices |
| --- | --- | --- |
| `project_name` | `project_name` | any string (drives `repo_name`, `module_name`) |
| `author_name` | `Your name` | any string |
| `description` | `A short description of the project.` | any string |
| `python_version_number` | `3.12` | `3.10`–`3.13` |
| `dataset_storage` | `none` | `azure`, `s3`, `gcs` |
| `environment_manager` | `virtualenv` | **`uv`** (recommended), `conda`, `pipenv`, `pixi`, `poetry`, `none` |
| `dependency_file` | `requirements.txt` | `pyproject.toml`, `environment.yml`, `Pipfile`, `pixi.toml` |
| `pydata_packages` | `none` | `basic` |
| `testing_framework` | `none` | `pytest`, `unittest` |
| `linting_and_formatting` | `ruff` | `flake8+black+isort` |
| `open_source_license` | `No license file` | `MIT`, `BSD-3-Clause` |
| `docs` | `mkdocs` | `none` |
| `include_code_scaffold` | `Yes` | `No` |
| `version_control` | `git (local)` | `none`, `git (github private)`, `git (github public)` |

> Note: with `--no-input`, `environment_manager` defaults to `virtualenv`, which skips the automatic
> `uv` env build. Pass `environment_manager="uv"` to exercise the full GOTem experience (this triggers
> `make create_environment` + `make requirements` in the new project and needs `make` + network access
> to install dependencies). Pass `environment_manager="none"` for the fastest possible scaffold with no
> dependency install.

Example — a pytest + uv project, ready to test:

```bash
uvx --from "git+https://github.com/GatlenCulp/gatlens-opinionated-template" gotem \
  --no-input --output-dir "$OUTPUT_DIR" \
  project_name="My New Project" \
  author_name="Your Name" \
  description="A short description of the project." \
  environment_manager="uv" \
  testing_framework="pytest"
```

---

## Step 3 — Verify end-to-end

Confirm the generated project is real and usable, then (for a smoke test) clean it up.

```bash
REPO_DIR="$OUTPUT_DIR/my_new_project"   # <OUTPUT_DIR>/<repo_name>
cd "$REPO_DIR"

# 1. Structure exists
test -f pyproject.toml && test -f README.md && echo "OK: project files present"
ls -la

# 2. Git repo was initialized with an initial commit (default version_control=git (local))
git log --oneline -1

# 3. If environment_manager=uv was used, the env was built by the post-gen hook.
#    Otherwise build it now, then run the tests (only if testing_framework was pytest/unittest).
uv sync 2>/dev/null || true
uv run pytest -q 2>/dev/null || echo "No pytest suite (testing_framework was 'none') or tests skipped"
```

A successful run shows: project files present, one initial git commit, and — when a testing framework
was selected — a passing (or at least collectible) test suite.

### Throwaway smoke test + cleanup

To verify GOTem works **without leaving anything behind**, generate into a temp dir and remove it:

```bash
TMP="$(mktemp -d)"
uvx --from "git+https://github.com/GatlenCulp/gatlens-opinionated-template" gotem \
  --no-input --output-dir "$TMP" \
  project_name="Smoke Test" \
  environment_manager="uv" testing_framework="pytest"

cd "$TMP/smoke_test"
git log --oneline -1
uv run pytest -q

cd / && rm -rf "$TMP"   # clean up
echo "GOTem smoke test complete"
```

---

## Troubleshooting

- **`uv: command not found` after install** — the installer added `uv` to `~/.local/bin`; run `export PATH="$HOME/.local/bin:$PATH"` (or `source "$HOME/.local/bin/env"`) in the current shell.
- **Initial commit fails / "Author identity unknown"** — set `git config --global user.name`/`user.email` (see Prerequisites), or pass `version_control="none"` to skip git entirely.
- **Post-gen hangs or errors on dependency install** — `environment_manager="uv"` runs `make create_environment` + `make requirements`, which need `make` and network access. Use `environment_manager="none"` to skip it.
- **A GitHub repo gets created / `gh` errors** — only happens if you pass `version_control="git (github public|private)"`. Leave it at the default `git (local)` for a purely local repo.
- **Want a specific template version** — pin the tool install: `uvx --from "git+https://github.com/GatlenCulp/gatlens-opinionated-template@v0.5.1" gotem ...`.
- **Slow first run** — `uvx` downloads and builds the tool the first time; subsequent runs are cached.

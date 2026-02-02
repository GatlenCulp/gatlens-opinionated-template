<!-- Copied guidance for AI coding agents. Keep concise and actionable. -->
# Copilot instructions for this repository

Purpose: help AI agents be immediately productive editing this Cookiecutter-based Python template.

- **Big picture**: this repo is an opinionated Cookiecutter Data Science template (GOTem). It scaffolds new projects under the generated project root (see the example tree in README.md) and includes docs, CI, pre-commit, and multiple tooling opinionated defaults (FastAPI, Typer, Polars, Loguru, UV/uvx). Primary source files for the template are the root files and the `{{ cookiecutter.repo_name }}` subtree; runtime hooks live in `hooks/`.

- **Key components & boundaries**:
  - Template engine & hooks: `cookiecutter` templates + `hooks/` (`pre_gen_project.py`, `post_gen_project.py`). Changes here affect rendered projects.
  - Documentation: `docs/` (mkdocs). Use `uv run mkdocs serve` locally and `uv run mkdocs gh-deploy --clean` to publish.
  - Tests for the template: `tests/` — these run against generated projects. Use `pytest --test-type=basic|detailed|all` or plain `pytest`.
  - Tooling/config: `pyproject.toml`, `Makefile`, `Taskfile.yml`, `.github/workflows/` (CI). Editing these changes how generated projects behave.

- **Developer workflows (explicit commands)**:
  - Install dev deps: `pip install -r dev-requirements.txt`.
  - Render & test template-only checks: `pytest tests/test_template_rendering.py`.
  - Basic instantiation tests: `pytest --test-type=basic`.
  - Full tests: `pytest --test-type=all` or `pytest`.
  - Run docs locally: `cd docs && uv run mkdocs serve`.
  - Publish docs: `cd docs && uv run mkdocs gh-deploy --clean`.
  - Pre-commit checks: `pre-commit run --all-files` (if hooks modify files, re-add and commit).

- **Project-specific conventions** (do not assume common defaults):
  - Math in markdown uses KaTeX delimiters: inline `\( ... \)` and display `\[ ... \]` (see `.cursor/rules/111_katex-math.mdc`).
  - Style & response guidance for LLMs is collected in `.cursor/rules/*.mdc` (see `100_general-style.mdc` and `103_general-programming.mdc`) — follow those rules (concise answers, avoid deep nesting, prefer explicit errors).
  - This template favors modern, opinionated libs (Polars over pandas, Typer over argparse, FastAPI over Flask). When adding or changing code, prefer consistency with these choices unless instructed otherwise.
  - Tests are configuration-driven using `ccds.json` and `tests/conftest.py`; changes to test behavior may require updating test generators.

- **Integration points & external dependencies**:
  - CI: actions live in `.github/workflows/` and rely on `uv` tool steps to install and test generated projects.
  - Publishing & packaging: `pyproject.toml` and `Makefile`/`Taskfile.yml` contain packaging/publish tasks.
  - Docs publishing relies on GitHub Pages via mkdocs (see `docs/README.md`).

- **When editing generated artifacts**:
  - Do not manually edit the generated site on `gh-pages`; use `uv run mkdocs gh-deploy` to regenerate.
  - Updating template defaults requires updating both `cookiecutter.json` and example files under `{{ cookiecutter.repo_name }}`.

- **Searchable examples to reference**:
  - Template hooks: `hooks/pre_gen_project.py`, `hooks/post_gen_project.py`.
  - LLM/style guidance: `.cursor/rules/100_general-style.mdc`, `.cursor/rules/103_general-programming.mdc`, `.cursor/rules/111_katex-math.mdc`.
  - Tests harness: `tests/conftest.py`, `tests/test_template_rendering.py`.
  - Docs pattern: `docs/README.md` and `mkdocs.yml`.

- **Practical editing rules for AI agents**:
  - When modifying template files, run the instantiation tests locally (see `tests/`) before proposing PRs.
  - Preserve cookiecutter template variables (`{{ cookiecutter.* }}`) and Jinja blocks exactly; do not attempt to render them while editing the template.
  - If changing default dependencies, update `dev-requirements.txt` and `pyproject.toml` consistently.
  - Keep changes minimal and focused: this repo is a template—small, well-scoped patches are preferred.

If anything here is unclear or you want additional details (example workflows, more file references, or CI specifics), tell me which section to expand.

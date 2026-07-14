"""Tests for the publish-example CI helper (``.github/scripts/render_example.py``).

These exercise the logic that the ``publish-example`` workflow depends on:

* ``prune_dangling_symlinks`` removes broken symlinks (and only those), so that
  cookiecutter's temp-dir copy step does not raise on this repo's tracked
  ``.trunk`` runtime symlinks.
* ``render`` produces a clean example project (correct structure, no leftover
  ``.git`` from the post-gen hook, no dangling symlinks) from the template's
  default answers.

The render test copies the template into a temp directory first (with
``symlinks=True`` so dangling symlinks are copied as-is rather than followed),
which both mirrors a fresh CI checkout and keeps the test from mutating the real
working tree when it prunes symlinks.
"""  # noqa: INP001

import importlib.util
import shutil
from pathlib import Path
from types import ModuleType

import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]
SCRIPT_PATH = REPO_ROOT / ".github" / "scripts" / "render_example.py"

# Directories not needed to render the template; skipping them keeps the
# per-test template copy small and fast.
_COPY_IGNORE = shutil.ignore_patterns(
    ".git",
    "__pycache__",
    "*.pyc",
    ".venv",
    "venv",
    ".pytest_cache",
    "node_modules",
    "logs",
)


def _load_render_module() -> ModuleType:
    """Import ``render_example.py`` by path (it lives outside any package)."""
    spec = importlib.util.spec_from_file_location("render_example", SCRIPT_PATH)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


render_example = _load_render_module()


def _dangling_symlinks(root: Path) -> list[Path]:
    return [p for p in root.rglob("*") if p.is_symlink() and not p.exists()]


def test_prune_dangling_symlinks_removes_only_broken_links(tmp_path: Path) -> None:
    """Only broken symlinks are removed; real files and valid links survive."""
    real_file = tmp_path / "real.txt"
    real_file.write_text("hello")

    good_link = tmp_path / "good_link"
    good_link.symlink_to(real_file)

    bad_link = tmp_path / "bad_link"
    bad_link.symlink_to(tmp_path / "does_not_exist")

    removed = render_example.prune_dangling_symlinks(tmp_path)

    assert removed == [bad_link]
    assert not bad_link.exists()
    assert not bad_link.is_symlink()
    # Valid symlink and real file are untouched.
    assert good_link.is_symlink()
    assert real_file.read_text() == "hello"


def test_render_produces_clean_example_project(tmp_path: Path) -> None:
    """Render the real template and assert the example is clean and complete."""
    # Copy the template into an isolated dir so pruning does not touch the repo.
    template_copy = tmp_path / "template"
    shutil.copytree(REPO_ROOT, template_copy, symlinks=True, ignore=_COPY_IGNORE)

    # Inject a broken symlink like the tracked .trunk ones that dangle on a
    # fresh checkout, so the render path genuinely relies on pruning it. Without
    # pruning, cookiecutter's temp-dir copy would raise on this.
    (template_copy / "dangling_link").symlink_to(template_copy / "does_not_exist")

    output_dir = tmp_path / "out"
    project_dir = render_example.render(str(template_copy), str(output_dir))

    # The generated project exists and is inside the requested output dir.
    assert project_dir.is_dir()
    assert output_dir in project_dir.parents

    # The post-gen hook's local git repo must be stripped before publishing.
    assert not (project_dir / ".git").exists()

    # Core scaffold and the workflow files that force the PAT `workflow` scope.
    assert (project_dir / "pyproject.toml").is_file()
    workflows = project_dir / ".github" / "workflows"
    assert workflows.is_dir()
    assert list(workflows.glob("*.yml")), "rendered example should ship workflows"

    # A clean example must not carry broken symlinks into the published repo.
    assert _dangling_symlinks(project_dir) == []


def test_render_overwrites_existing_output(tmp_path: Path) -> None:
    """A pre-existing output directory is cleared, not merged, before rendering."""
    template_copy = tmp_path / "template"
    shutil.copytree(REPO_ROOT, template_copy, symlinks=True, ignore=_COPY_IGNORE)

    output_dir = tmp_path / "out"
    output_dir.mkdir()
    # Stale content from a previous run should be cleared, not merged.
    (output_dir / "stale.txt").write_text("old")

    project_dir = render_example.render(str(template_copy), str(output_dir))

    assert not (output_dir / "stale.txt").exists()
    assert project_dir.is_dir()


if __name__ == "__main__":
    raise SystemExit(pytest.main([__file__, "-v"]))

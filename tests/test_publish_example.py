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
from cookiecutter.exceptions import RepositoryNotFound

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


@pytest.fixture
def template_copy(tmp_path: Path) -> Path:
    """Copy the repo into an isolated dir so pruning/rendering never touches the real tree.

    ``symlinks=True`` copies symlinks verbatim (rather than following them), so
    the tracked dangling ``.trunk`` links come along without raising and the copy
    faithfully mirrors a fresh CI checkout.
    """
    dest = tmp_path / "template"
    shutil.copytree(REPO_ROOT, dest, symlinks=True, ignore=_COPY_IGNORE)
    return dest


def test_prune_dangling_symlinks_removes_only_broken_links(tmp_path: Path) -> None:
    """Under .trunk, broken symlinks (incl. nested) are removed; valid ones survive."""
    trunk = tmp_path / ".trunk"
    trunk.mkdir()

    real_file = trunk / "real.txt"
    real_file.write_text("hello")

    good_link = trunk / "good_link"
    good_link.symlink_to(real_file)

    bad_link = trunk / "bad_link"
    bad_link.symlink_to(trunk / "does_not_exist")

    # A broken symlink nested in a subdirectory must also be pruned (rglob walks
    # recursively), since real .trunk links live under nested paths.
    nested_dir = trunk / "plugins" / "trunk"
    nested_dir.mkdir(parents=True)
    nested_bad = nested_dir / "nested_bad"
    nested_bad.symlink_to(trunk / "also_missing")

    removed = render_example.prune_dangling_symlinks(tmp_path)

    assert set(removed) == {bad_link, nested_bad}
    assert not bad_link.is_symlink()
    assert not nested_bad.is_symlink()
    # Valid symlink and real file are untouched.
    assert good_link.is_symlink()
    assert real_file.read_text() == "hello"


def test_prune_dangling_symlinks_ignores_paths_outside_trunk(tmp_path: Path) -> None:
    """Broken symlinks outside .trunk are left alone (scoped to .trunk only)."""
    (tmp_path / ".trunk").mkdir()

    outside = tmp_path / "elsewhere_broken"
    outside.symlink_to(tmp_path / "missing")
    git_broken = tmp_path / ".git"
    git_broken.mkdir()
    (git_broken / "broken").symlink_to(tmp_path / "missing")

    removed = render_example.prune_dangling_symlinks(tmp_path)

    assert removed == []
    assert outside.is_symlink()
    assert (git_broken / "broken").is_symlink()


def test_prune_dangling_symlinks_without_trunk_is_noop(tmp_path: Path) -> None:
    """A template root with no .trunk directory prunes nothing and does not error."""
    assert render_example.prune_dangling_symlinks(tmp_path) == []


def test_render_produces_clean_example_project(tmp_path: Path, template_copy: Path) -> None:
    """Render the real template and assert the example is clean and complete."""
    # Inject a broken symlink under .trunk like the tracked runtime symlinks
    # that dangle on a fresh checkout, so the render path genuinely relies on
    # pruning it. Without pruning, cookiecutter's temp-dir copy would raise.
    trunk_dir = template_copy / ".trunk"
    trunk_dir.mkdir(exist_ok=True)
    (trunk_dir / "dangling_link").symlink_to(trunk_dir / "does_not_exist")

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


def test_render_overwrites_existing_output(tmp_path: Path, template_copy: Path) -> None:
    """A pre-existing output directory is cleared, not merged, before rendering."""
    output_dir = tmp_path / "out"
    output_dir.mkdir()
    # Stale content from a previous run should be cleared, not merged.
    (output_dir / "stale.txt").write_text("old")

    project_dir = render_example.render(str(template_copy), str(output_dir))

    assert not (output_dir / "stale.txt").exists()
    assert project_dir.is_dir()


def test_render_fails_on_missing_template(tmp_path: Path) -> None:
    """Rendering a non-existent template path raises rather than silently succeeding."""
    missing = tmp_path / "no_such_template"
    with pytest.raises(RepositoryNotFound):
        render_example.render(str(missing), str(tmp_path / "out"))


if __name__ == "__main__":
    raise SystemExit(pytest.main([__file__, "-v"]))

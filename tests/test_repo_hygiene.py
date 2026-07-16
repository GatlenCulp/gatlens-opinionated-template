# mypy: ignore-errors
# ruff: noqa
"""Repo-hygiene guards for the template itself (not generated projects).

These protect against regressions that break a clean checkout/render — most
notably the dangling `.trunk` runtime symlinks that previously pointed at the
author's local machine and broke cookiecutter's copy step on a fresh clone.
"""
import subprocess
from pathlib import Path

import pytest

from conftest import CCDS_ROOT


def _tracked_symlinks(root: Path) -> list[str]:
    """Return repo-relative paths of all git-tracked symlinks (git mode 120000)."""
    out = subprocess.check_output(
        ["git", "ls-files", "-s"], cwd=str(root), text=True
    )
    paths = []
    for line in out.splitlines():
        meta, _, path = line.partition("\t")
        if meta.split(" ", 1)[0] == "120000":
            paths.append(path)
    return paths


@pytest.mark.basic
def test_no_dangling_tracked_symlinks():
    """No git-tracked symlink may point at a missing target.

    Dangling symlinks (e.g. the `.trunk/{actions,logs,notifications,out,tools,
    plugins/trunk}` runtime dirs) break a fresh clone and template render.
    """
    dangling = [p for p in _tracked_symlinks(CCDS_ROOT) if not (CCDS_ROOT / p).exists()]
    assert not dangling, (
        "Dangling git-tracked symlinks found (they break a clean render): "
        f"{dangling}. These are runtime paths that should not be committed; "
        "remove them with `git rm` and let `.trunk/.gitignore` keep them out."
    )

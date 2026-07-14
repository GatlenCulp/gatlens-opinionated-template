"""Render the GOTem / CCDS template with default answers into an output directory.

Used by the ``publish-example`` GitHub Actions workflow to generate a browsable
example instance of this template that is then published to a public repository.

Importing :mod:`ccds.__main__` applies the monkey-patches that make cookiecutter
read ``ccds.json`` (instead of the deprecated ``cookiecutter.json``) and tolerate
the template's optional sub-options, exactly as the test-suite does.
"""  # noqa: INP001

from __future__ import annotations

import argparse
import shutil
import sys
from pathlib import Path

from ccds.__main__ import api_main


def prune_dangling_symlinks(root: Path) -> list[Path]:
    """Remove broken symlinks under ``root/.trunk`` and return what was removed.

    Cookiecutter copies the whole template directory into a temp dir before
    running the pre-prompt hook; ``shutil.copytree`` raises on dangling symlinks.
    This repo tracks a handful of ``.trunk`` runtime symlinks that point at the
    template author's local machine, so they are always broken on a fresh
    checkout. They are runtime caches with no bearing on the rendered project,
    so pruning them is safe and lets the render proceed anywhere.

    The walk is scoped to ``.trunk`` so that running this script against a real
    working tree (the ``--template .`` default) never deletes unrelated broken
    symlinks elsewhere in the tree, including anything under ``.git``.
    """
    trunk = root / ".trunk"
    removed: list[Path] = []
    if not trunk.is_dir():
        return removed
    for path in trunk.rglob("*"):
        if path.is_symlink() and not path.exists():
            path.unlink()
            removed.append(path)
    return removed


def render(template: str, output_dir: str) -> Path:
    """Render ``template`` into ``output_dir`` with the template's defaults.

    Returns the path to the generated project directory. Any git repository that
    the post-generation hook may create is removed so the publish step can manage
    its own history for the target repository.
    """
    for link in prune_dangling_symlinks(Path(template).resolve()):
        print(f"pruned dangling symlink: {link}", file=sys.stderr)  # noqa: T201

    out = Path(output_dir).resolve()
    if out.exists():
        shutil.rmtree(out)
    out.mkdir(parents=True)

    project_dir = Path(
        api_main.cookiecutter(
            template,
            no_input=True,
            output_dir=str(out),
            overwrite_if_exists=True,
        ),
    )

    git_dir = project_dir / ".git"
    if git_dir.is_dir():
        shutil.rmtree(git_dir)

    return project_dir


def main(argv: list[str] | None = None) -> int:
    """Parse CLI arguments, render the template, and print the project path."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--template",
        default=".",
        help="Path to the template root (default: current directory).",
    )
    parser.add_argument(
        "--output-dir",
        default="_rendered",
        help="Directory to render the project into (default: ./_rendered).",
    )
    args = parser.parse_args(argv)

    project_dir = render(args.template, args.output_dir)

    # The generated project path is the only thing written to stdout so the
    # workflow can capture it; all other output goes to stderr via loguru.
    print(project_dir)  # noqa: T201
    return 0


if __name__ == "__main__":
    sys.exit(main())

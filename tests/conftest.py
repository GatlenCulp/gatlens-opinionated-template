# type: ignore
# ruff: noqa
from collections.abc import Generator
from contextlib import contextmanager
from itertools import cycle, product
import json
from pathlib import Path
import shutil
import sys
import tempfile

import pytest

from ccds.__main__ import api_main

CCDS_ROOT = Path(__file__).parents[1].resolve()

default_args: dict[str, str] = {
    "project_name": "my_test_project",
    "repo_name": "my-test-repo",
    "module_name": "project_module",
    "author_name": "DrivenData",
    "description": "A test project",
}

### GATLEN'S TEST ###


def pytest_collection_modifyitems(config: pytest.Config, items: list[pytest.Item]) -> None:
    """Filter test items based on their timeout marker value.

    This pytest hook modifies the test collection by removing tests whose timeout
    value exceeds the maximum specified timeout, as well as tests without any
    timeout marker. The maximum timeout can be set using the --max-timeout command
    line option. If --max-timeout is not provided, all tests will run regardless
    of their timeout value.

    Args:
        config: The pytest configuration object containing test session information
        items: List of collected test items to be filtered

    Note:
        Tests are marked with @pytest.mark.timeout(value) decorator. If a test's
        timeout value is greater than max_timeout or if it has no timeout marker,
        it will be deselected.
    """
    max_timeout = config.getoption("--max-timeout")
    if max_timeout is None:
        return

    all_items = set(items)
    deselected_tests = {
        item
        for item in items
        if not item.get_closest_marker("timeout")  # Remove tests without timeout marker
        or item.get_closest_marker("timeout").args[0]
        > max_timeout  # Remove tests exceeding max_timeout
    }

    if deselected_tests:
        config.hook.pytest_deselected(items=list(deselected_tests))
        items[:] = list(all_items - deselected_tests)


def pytest_addoption(parser: pytest.Parser) -> None:
    """Add custom command line options to pytest.

    This function registers two custom command line options:
    - --max-timeout: Set maximum allowed timeout for tests (default: None, run all tests)
    - --fast (-F): Control test execution speed by skipping certain validations

    Args:
        parser: The pytest command line parser to which options will be added

    Example:
        Run tests with a maximum timeout of 10 seconds:
        pytest --max-timeout=10

        Run all tests regardless of timeout:
        pytest  # without --max-timeout option

        Run tests in fast mode:
        pytest --fast or pytest -F
    """
    parser.addoption(
        "--max-timeout",
        action="store",
        default=None,
        type=int,
        help="Only run tests with timeout less than this value. If not provided, run all tests.",
    )
    parser.addoption(
        "--fast",
        "-F",
        action="count",
        default=0,
        help="Speed up tests by skipping configs and/or Makefile validation",
    )


### GATLEN'S TEST ###


def config_generator(fast: int | bool = False) -> Generator[dict[str, str], None, None]:
    """Generate test configurations based on cookiecutter.json options.

    Args:
        fast: Speed control flag for test execution

    Yields:
        Dictionary of configuration options for each test case
    """
    cookiecutter_json: dict[str, list[str]] = json.load(
        (CCDS_ROOT / "ccds.json").open("r"),
    )

    running_py_version: str = f"{sys.version_info.major}.{sys.version_info.minor}"
    py_version: list[tuple[str, str]] = [("python_version_number", v) for v in [running_py_version]]

    filtered_configs = list(
        product(
            py_version,
            [("environment_manager", opt) for opt in cookiecutter_json["environment_manager"]],
            [("dependency_file", opt) for opt in cookiecutter_json["dependency_file"]],
            [("pydata_packages", opt) for opt in cookiecutter_json["pydata_packages"]],
            [("version_control", opt) for opt in ("none", "git (local)")],
            # TODO: Tests for "version_control": "git (github)"
        ),
    )

    def _is_valid(config) -> bool:
        config_dict: dict[str, str] = dict(config)
        if (config_dict["dependency_file"] == "none") and (
            config_dict["environment_manager"] != "uv"
        ):
            return False
        if (config_dict["environment_manager"] == "pipenv") ^ (
            config_dict["dependency_file"] == "Pipfile"
        ):
            return False
        # conda is the only valid env manager for environment.yml
        if (config_dict["dependency_file"] == "environment.yml") and (
            config_dict["environment_manager"] != "conda"
        ):
            return False
        return True

    # remove invalid configs
    filtered_configs = [c for c in filtered_configs if _is_valid(c)]

    cycle_fields: list[str] = [
        "dataset_storage",
        "open_source_license",
        "include_code_scaffold",
        "docs",
    ]
    cyclers = {k: cycle(cookiecutter_json[k]) for k in cycle_fields}

    for ind, c in enumerate(filtered_configs):
        config = dict(c)
        config.update(default_args)
        # Alternate including the code scaffold
        for field, cycler in cyclers.items():
            config[field] = next(cycler)
        config["repo_name"] += f"-{ind}"
        yield config

        # just do a single config if fast passed once or three times
        if fast == 1 or fast >= 3:
            break


@pytest.fixture
def fast(request):
    return request.config.getoption("--fast")


def pytest_generate_tests(metafunc: pytest.Metafunc) -> None:  # type: ignore[misc]
    """Generate test configurations."""

    def make_test_id(config: dict[str, str]) -> str:
        # Map full names to shorter versions
        abbreviations = {
            "environment_manager": {
                "none": "no-env",
                "virtualenv": "venv",
                "conda": "con",
                "pipenv": "penv",
                "uv": "uv",
            },
            "dependency_file": {
                "requirements.txt": "req.txt",
                "environment.yml": "env.yml",
                "Pipfile": "pfile",
            },
            "docs": {"mkdocs": "mkdocs", "none": "no-doc"},
            "version_control": {
                "none": "no-vc",
                "git (local)": "git",
                "git (github private)": "gh-prv",
                "git (github public)": "gh-pub",
            },
            "pydata_packages": {"none": "no-pkg", "basic": "pkg"},
        }

        # Define column widths
        cols = [
            ("env", 6),  # environment_manager
            ("dep", 6),  # dependency_file
            ("doc", 6),  # docs
            ("vc", 6),  # version_control
            ("pkg", 6),  # pydata_packages
        ]

        # Format each component with fixed width
        components = []
        for (prefix, width), key in zip(
            cols,
            [
                "environment_manager",
                "dependency_file",
                "docs",
                "version_control",
                "pydata_packages",
            ],
            strict=False,
        ):
            value = abbreviations[key][config[key]]
            # Ensure exact width by padding or truncating
            formatted = f"{value:<{width}}"[:width]
            components.append(formatted)

        return " ".join(components)

    if "config" in metafunc.fixturenames:
        configs = list(config_generator(metafunc.config.getoption("fast")))
        parametrize_args = [
            (
                pytest.param(config, marks=pytest.mark.xfail)
                if config["environment_manager"] == "conda"
                else config
            )
            for config in configs
        ]
        metafunc.parametrize(
            "config",
            parametrize_args,
            ids=make_test_id,
        )


@contextmanager
def bake_project(config: dict[str, str]) -> Generator[Path, None, None]:
    """Creates a temporary cookiecutter project for testing purposes.

    This context manager creates a temporary directory, bakes a cookiecutter project
    using the provided configuration, and cleans up afterwards.

    Args:
        config: Dictionary containing cookiecutter template configuration values.
            Must include a 'repo_name' key.

    Yields:
        Path: Path to the generated project directory.

    Example:
        >>> config = {"repo_name": "test-project", ...}
        >>> with bake_project(config) as project_path:
        ...     # work with generated project
        ...     pass
        >>> # Directory is automatically cleaned up after context exits
    """
    temp = Path(tempfile.mkdtemp(suffix="data-project")).resolve()

    api_main.cookiecutter(
        str(CCDS_ROOT),
        no_input=True,
        extra_context=config,
        output_dir=temp,
        overwrite_if_exists=True,
    )

    yield temp / config["repo_name"]

    # cleanup after
    shutil.rmtree(temp)

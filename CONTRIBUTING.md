# Contributing

This is a very small project. If you have large Pull Requests to make, I recommend making them over with the upstream at [CookieCutter Data Science (CCDS)](https://github.com/drivendataorg/cookiecutter-data-science). If you have recommendations/changes/particular issues with my implementation, feel free to leave an issue but I'm not sure if I will be able to get around to it.

## Dev Instructions

### Installing Requirements

It is recommended to use [UV](https://github.com/astral-sh/uv) for installations.

Create virtual environment and install dependencies

```bash
uv sync --extra dev
```

### Running the tests

```bash
pytest
```

_Note: Some of the configs require conda to be installed. MiniConda or MiniForge are lightly recommended._

<!-- Conda-forge may be better -->

```bash
brew install --cask miniconda
```

## Contributing to CookieCutter Data Science (CCDS)

> The Cookiecutter Data Science project is opinionated, but not afraid to be wrong. Best practices change, tools evolve, and lessons are learned. **The goal of this project is to make it easier to start, structure, and share an analysis.** [Pull requests](https://github.com/drivendataorg/cookiecutter-data-science/pulls) and [filing issues](https://github.com/drivendataorg/cookiecutter-data-science/issues) is encouraged. We'd love to hear what works for you, and what doesn't.
>
> If you use the Cookiecutter Data Science project, link back to this page or [give us a holler](https://twitter.com/drivendataorg) and [let us know](mailto:info@drivendata.org)!

<!-- TODO: Perhaps use this: https://cookiecutter.readthedocs.io/en/stable/advanced/human_readable_prompts.html -->

## Possible Future Features

- [ ] Use `{{ cookiecutter.project_emoji }}` to create an automatic folder icon `{{ cookiecuttter.module_name }}.icns`. I personally find this very useful for organizing my projects

## TODO
- [ ] Perhaps add mise-en-place as a task/package manager
- [ ] Add typst to options for LaTeX
- [ ] `ignore` folder. Literally just has `.gitignore` with
    ```bash
    # Ignore all files in this directory
    *
    # Except for this .gitignore file
    !.gitignore
    ```
- [ ] Compare devenv vs envrc vs mise-en-place vs a straight up flake for better package management
- [X] Pull the latest changes from CookieCutter Data Science
- [ ] Allow selection between Typst and LaTeX
- [ ] Test that [COOKIECUTTER_CONFIG works](https://cookiecutter.readthedocs.io/en/stable/advanced/user_config.html) and add to documentation.
- [ ] Fix LICENSE bug (not showing up when selected?)
- [ ] Switch to using [this](https://cookiecutter.readthedocs.io/en/stable/advanced/nested_config_files.html) instead of manual scaffold deletion

### Docs to add about COOKIECUTTER_CONFIG

```bash
export COOKIECUTTER_CONFIG="/home/audreyr/my-custom-config.yaml"
# or if currently set `unset COOKIECUTTER_CONFIG`
```

Example context:
```yaml
default_context:
    author_name: "Gatlen Culp"
    python_version_number: "3.12"
    dataset_storage: "none"
    environment_manager: "uv"
    dependency_file: "pyproject.toml"
    pydata_packages: "none"
    testing_framework: "pytest"
    linting_and_formatting: "ruff"
    open_source_license: "MIT"
    docs: "mkdocs"
    _author_email: "GatlenCulp@gmail.com"
    _github_username: "GatlenCulp"
    _custom_domain": "gatlen.me"
    _use_conventional_commits": "y"
    _generate_personal_ssh_keys": "n"
    _generate_and_upload_gh_deploy_keys": "n"
    _project_emoji": ""
    _qa_tool": "trunk"
    _qa_level": "basic"
    _task_manager": "taskfile"
    _typesetting_tool": "typst"
    _readme_modern_header": "y"
    _readme_include_logo": "y"
    _readme_include_screenshots": "y"
    _readme_use_github_discussions": "n"
    _readme_include_badges": "y"
    _readme_include_toc": "n"
    _readme_include_project_assistance": "y"
    _readme_include_authors": "y"
    _readme_include_security": "y"
    _readme_include_acknowledgements": "y"
    _readme_table_in_about": "y"
    
abbreviations:
    gh: https://github.com/{0}.git
    bb: https://bitbucket.org/{0}
```

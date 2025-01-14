"""File to be run after template initialization by cookiecutter."""  # noqa: INP001

from copy import copy
import os
from pathlib import Path
import shutil
import subprocess

from ccds.hook_utils.configure_vcs import configure_github_repo, init_local_git_repo

# https://github.com/cookiecutter/cookiecutter/issues/824
#   our workaround is to include these utility functions in the CCDS package
from ccds.hook_utils.custom_config import write_custom_config
from ccds.hook_utils.dependencies import basic, packages, scaffold, write_dependencies

#
#  TEMPLATIZED VARIABLES FILLED IN BY COOKIECUTTER
#
packages_to_install = copy(packages)

# {% if cookiecutter.dataset_storage.s3 %}
packages_to_install += ["awscli"]
# {% endif %} #

# {% if cookiecutter.include_code_scaffold != "No" %}
packages_to_install += scaffold
# {% endif %}

# {% if cookiecutter.pydata_packages == "basic" %}
packages_to_install += basic
# {% endif %}

# track packages that are not available through conda
pip_only_packages = [
    "awscli",
    "python-dotenv",
]

# Use the selected documentation package specified in the config,
# or none if none selected
docs_path = Path("docs")
# {% if cookiecutter.docs != "none" %}
packages_to_install += ["{{ cookiecutter.docs }}"]
pip_only_packages += ["{{ cookiecutter.docs }}"]
docs_subpath = docs_path / "{{ cookiecutter.docs }}"
for obj in docs_subpath.iterdir():
    shutil.move(str(obj), str(docs_path))
# {% endif %}

# Remove all remaining docs templates
for docs_template in docs_path.iterdir():
    if docs_template.is_dir() and docs_template.name != "docs":
        shutil.rmtree(docs_template)

#
#  POST-GENERATION FUNCTIONS
#
write_dependencies(
    "{{ cookiecutter.dependency_file }}",
    packages_to_install,
    pip_only_packages,
    repo_name="{{ cookiecutter.repo_name }}",
    module_name="{{ cookiecutter.module_name }}",
    python_version="{{ cookiecutter.python_version_number }}",
)

write_custom_config("{{ cookiecutter.custom_config }}")

# Remove LICENSE if "No license file"
if "{{ cookiecutter.open_source_license }}" == "No license file":  # noqa: PLR0133
    Path("LICENSE").unlink()

# Make single quotes prettier
# Jinja tojson escapes single-quotes with \u0027 since it's meant for HTML/JS
pyproject_text = Path("pyproject.toml").read_text()
Path("pyproject.toml").write_text(pyproject_text.replace(r"\u0027", "'"))

# {% if cookiecutter.include_code_scaffold == "No" %}
# remove everything except __init__.py so result is an empty package
for generated_path in Path("{{ cookiecutter.module_name }}").iterdir():
    if generated_path.is_dir():
        shutil.rmtree(generated_path)
    elif generated_path.name != "__init__.py":
        generated_path.unlink()
    elif generated_path.name == "__init__.py":
        # remove any content in __init__.py since it won't be available
        generated_path.write_text(
            '"""{{ cookiecutter.module_name }}: {{ cookiecutter.project_short_description }}."""\n',
        )
# {# TODO(Gatlen Culp): Fix below #}
# {% elif cookiecutter.include_code_scaffold == "data" %}
# {% elif cookiecutter.include_code_scaffold == "paper" %}
# {% elif cookiecutter.include_code_scaffold == "app" %}
# {% elif cookiecutter.include_code_scaffold == "ml" %}
# {% elif cookiecutter.include_code_scaffold == "lib" %}
# {% elif cookiecutter.include_code_scaffold == "course" %}
# {% endif %}

#
#  GATLEN'S UPLOAD TO GITHUB REPO CODE
#

# Install the virtual environment (uv only for now)
# {% if cookiecutter.environment_manager == "uv" %}
os.chdir(Path.cwd())
subprocess.run(["make", "create_environment"], check=False)  # noqa: S603, S607
subprocess.run(["make", "requirements"], check=False)  # noqa: S603, S607
# {% endif %}

#
#  VERSION CONTROL
#

# {% if cookiecutter.version_control == "git (local)" %}
init_local_git_repo(directory=Path.cwd())
# {% elif cookiecutter.version_control == "git (github private)" %}
configure_github_repo(
    directory=Path.cwd(),
    repo_name="{{ cookiecutter.repo_name }}",
    visibility="private",
)
# {% elif cookiecutter.version_control == "git (github public)" %}
configure_github_repo(
    directory=Path.cwd(),
    repo_name="{{ cookiecutter.repo_name }}",
    visibility="public",
)
# {% endif %}

# {% if cookiecutter.environment_manager == "uv" %}
os.chdir(Path.cwd())
subprocess.run(["pre-commit", "install"], check=False)  # noqa: S603, S607
# {% endif %}

"""Defines Pydantic models to represent cookiecutter arguments."""

import json
import os
from pathlib import Path
from typing import Literal, Union, Optional, List, Dict, Any, ClassVar

from loguru import logger
from pydantic import BaseModel, Field


class FieldHelp(BaseModel):
    """Model for field help information."""
    description: str
    more_information: str = ""


class ChoiceHelp(BaseModel):
    """Model for individual choice help information."""
    description: str
    more_information: str = ""


class Subfield(BaseModel):
    """Model for subfield information."""
    field: str
    help: FieldHelp


class Choice(BaseModel):
    """Model for field choice information."""
    choice: str
    help: ChoiceHelp
    subfields: Optional[List[Subfield]] = None


class FieldHelpExport(BaseModel):
    """Model for exporting field help information."""
    field: str
    help: FieldHelp
    choices: Optional[List[Choice]] = None


# Storage options
class AzureStorage(BaseModel):
    """Azure Blob Storage container configuration."""
    container: str = Field(
        default="container-name",
        description="Name of the container on blob storage.",
        more_information="[Docs](https://learn.microsoft.com/en-us/azure/storage/blobs/blob-containers-portal)"
    )


class S3Storage(BaseModel):
    """Amazon S3 storage configuration."""
    bucket: str = Field(
        default="bucket-name",
        description="The name of the bucket to store data in; can also be a longer S3 path.",
        more_information="[Docs](https://docs.aws.amazon.com/AmazonS3/latest/userguide/Welcome.html#BasicsBucket)"
    )
    aws_profile: str = Field(
        default="default",
        description="The name of the profile to use for the aws CLI.",
        more_information="[Docs](https://docs.aws.amazon.com/cli/latest/userguide/cli-configure-files.html)"
    )


class GCSStorage(BaseModel):
    """Google Cloud Storage configuration."""
    bucket: str = Field(
        default="bucket-name",
        description="The name of the bucket to store data in.",
        more_information="[Docs](https://cloud.google.com/storage/docs/buckets)"
    )


# Main cookiecutter arguments model
class GotemArgs(BaseModel):
    """Pydantic model representing all cookiecutter arguments."""

    # Basic project information
    project_name: str = Field(
        default="project_name",
        description="A name for the project, for example 'My Project'."
    )
    repo_name: str = Field(
        default="",
        description="Default generated by altering the `project_name`. Used for folder and repo name for the project."
    )
    module_name: str = Field(
        default="",
        description="Default generated by altering the `project_name` to be a compatible Python module name."
    )
    author_name: str = Field(
        default="Your name, organization, or team",
        description="Name of the individual or organization that created the project."
    )
    description: str = Field(
        default="A short description of the project.",
        description="A short description that appears in the README.md file by default."
    )
    python_version_number: str = Field(
        default="3.12",
        description="The version of Python that the project will use.",
        more_information="[Python version status](https://devguide.python.org/versions/)"
    )
    
    # Dataset storage options
    dataset_storage: Union[
        Dict[Literal["none"], str],
        Dict[Literal["azure"], AzureStorage],
        Dict[Literal["s3"], S3Storage],
        Dict[Literal["gcs"], GCSStorage]
    ] = Field(
        default={"none": "none"},
        description="A cloud storage location for where data should be stored; controls `sync_data_up` and `sync_data_down` Makefile commands."
    )
    
    # Environment and dependency management
    environment_manager: Literal["uv", "none", "virtualenv", "conda", "pipenv"] = Field(
        default="uv",
        description="Tool for managing creating Python environments. Controls `make create_environment` Makefile command.",
        more_information="[About virtual environments](https://www.dataquest.io/blog/a-complete-guide-to-python-virtual-environments/)"
    )
    dependency_file: Literal["requirements.txt", "environment.yml", "Pipfile"] = Field(
        default="requirements.txt",
        description="Where to track project-specific dependencies; often paired with specific environment manager."
    )
    pydata_packages: Literal["basic", "none"] = Field(
        default="basic",
        description="Packages automatically added to your requirements file."
    )
    
    # License and documentation
    open_source_license: Literal["MIT", "No license file", "BSD-3-Clause"] = Field(
        default="MIT",
        description="Whether to include a license file and which one to use."
    )
    docs: Literal["mkdocs", "none"] = Field(
        default="mkdocs",
        description="Whether to include a `docs` folder and documentation tools."
    )
    
    # Code scaffold options
    include_code_scaffold: Literal["data", "No", "paper", "app", "ml", "lib", "course"] = Field(
        default="data",
        description="Whether to include some basic boilerplate code in the Python module."
    )
    
    # Version control options
    version_control: Literal["git (local)", "none", "git (github private)", "git (github public)"] = Field(
        default="git (local)",
        description="What kind of version control system (vcs) and repository host to use."
    )
    
    # Hidden/private options (prefixed with _)
    author_email: str = Field(default="")
    github_username: str = Field(default="")
    custom_domain: str = Field(default="")
    use_conventional_commits: Literal["y", "n"] = Field(default="y")
    generate_personal_ssh_keys: Literal["y", "n"] = Field(default="n")
    generate_and_upload_gh_deploy_keys: Literal["y", "n"] = Field(default="n")
    project_emoji: str = Field(default="🍪")
    qa_tool: Literal["trunk", "pre-commit", None] = Field(default="trunk")
    qa_level: str = Field(default="basic")
    
    # README options
    readme_modern_header: Literal["y", "n"] = Field(
        default="y",
        description="Whether to include a license file and which one to use.",
        json_schema_extra={"alias": "_readme_modern_header"},
        serialization_alias="_readme_modern_header"
    )
    readme_include_logo: Literal["y", "n"] = Field(
        default="y",
        description="Whether to include a logo in the README.",
        json_schema_extra={"alias": "_readme_include_logo"},
        serialization_alias="_readme_include_logo"
    )
    readme_include_screenshots: Literal["y", "n"] = Field(
        default="y",
        description="Whether to include screenshots in the README.",
        json_schema_extra={"alias": "_readme_include_screenshots"},
        serialization_alias="_readme_include_screenshots"
    )
    readme_use_github_discussions: Literal["y", "n"] = Field(
        default="n",
        description="Whether to use GitHub Discussions for the project.",
        json_schema_extra={"alias": "_readme_use_github_discussions"},
        serialization_alias="_readme_use_github_discussions"
    )
    readme_include_badges: Literal["y", "n"] = Field(
        default="y",
        description="Whether to include badges in the README.",
        json_schema_extra={"alias": "_readme_include_badges"},
        serialization_alias="_readme_include_badges"
    )
    readme_include_toc: Literal["y", "n"] = Field(
        default="n",
        description="Whether to include a table of contents in the README.",
        json_schema_extra={"alias": "_readme_include_toc"},
        serialization_alias="_readme_include_toc"
    )
    readme_include_project_assistance: Literal["y", "n"] = Field(
        default="y",
        description="Whether to include project assistance information in the README.",
        json_schema_extra={"alias": "_readme_include_project_assistance"},
        serialization_alias="_readme_include_project_assistance"
    )
    readme_include_authors: Literal["y", "n"] = Field(
        default="y",
        description="Whether to include author information in the README.",
        json_schema_extra={"alias": "_readme_include_authors"},
        serialization_alias="_readme_include_authors"
    )
    readme_include_security: Literal["y", "n"] = Field(
        default="y",
        description="Whether to include security information in the README.",
        json_schema_extra={"alias": "_readme_include_security"},
        serialization_alias="_readme_include_security"
    )
    readme_include_acknowledgements: Literal["y", "n"] = Field(
        default="y",
        description="Whether to include acknowledgements in the README.",
        json_schema_extra={"alias": "_readme_include_acknowledgements"},
        serialization_alias="_readme_include_acknowledgements"
    )
    readme_table_in_about: Literal["y", "n"] = Field(
        default="y",
        description="Whether to include a table in the about section of the README.",
        json_schema_extra={"alias": "_readme_table_in_about"},
        serialization_alias="_readme_table_in_about"
    )
    
    # Templating options
    copy_without_render: List[str] = Field(default_factory=list)

if __name__ == "__main__":
    cookiecutter_args = GotemArgs()
    logger.info(str(cookiecutter_args))
# Pre-commit Hooks Collection

<!-- TODO: This https://www.notion.so/gatlen/Ruff-Styling-Config-and-Python-Packages-158803bca419800fa4abc97864e25a7b?pvs=4 -->

## What is pre-commit and why would I want to use it?
![pre-commit logo](https://avatars.githubusercontent.com/u/6943086?s=280&v=4)

[Pre-commit](https://pre-commit.com/) is a framework for managing and maintaining multi-language pre-commit [Git hooks](https://git-scm.com/book/en/v2/Customizing-Git-Git-Hooks), which are essentially pieces of code that are run right before you commit on your local machine and can even prevent you from committing if rules are not met. This is a feature of Git itself, and Pre-commit builds on it, simplifies it, and makes these hooks more reusable. (And despite its name, pre-commit can set up hooks at (any?) stage in the git pipeline, prior to commit tends to be the most common however.)

<!-- One might use a pre-push hook as a slightly more time-intensive pre-commit. -->

![Git Hooks](https://d8it4huxumps7.cloudfront.net/uploads/images/652f8091f32cc_git_hooks_06.jpg?d=2000x2000)

These are very easy to set up and there is a large ecosystem of ready-to-go hooks. They're a nice low-code way of maintaining quality and enforcing standards, especially on small, quickly moving projects. They tend to be fast and light-weight as opposed to CI/CD testing with something like [GitHub Actions](https://github.com/features/actions) which might take minutes. It's common to include these same pre-commit tests in GitHub Actions with [pre-commit ci](https://pre-commit.ci/) on top of the more expensive tests.

Pre-commit can be as nitpicky as you want it to be depending on quality-time tradeoff you're making on your project. But it can be helpful for a number of cases, of which might make sense to issue on a commit-level rather than a pull-request level:
1. Linting/formatting code and data files (json, etc.)
2. Re-building code or documentation.
3. Making database migrations
4. Preventing secrets or large files from being committed
5. Requiring commit messages to follow a standard (Like [Commitizen](https://commitizen-tools.github.io/commitizen/))
6. More

It's also nice because you can run a bunch of QA tools your research team doesn't care or know much about without them having to learn the tool.

Pre-commit, by default, only operates on STAGED files.

This page describes the collection of pre-commit hooks selected for this project.

<details>
<summary>
Alternatives (Husky)
</summary>
[Husky](https://typicode.github.io/husky/) is an alternative to pre-commit. My understanding of the differences is that it is mainly geared towards the NodeJS community while pre-commit is multi-language, a bit simpler, a bit more popular, and tends to be the go-to for the Python community, hency why I chose it.
</details>

## Install
The repository should already be configured with a `.pre-commit-config.yaml` file and can be installed with `pre-commit install`. That's basically it, then whenever you commit you should see something like:

![Pre-commit Example](./pre-commit_example.png)

Every time you change the config file, you will have to reinstall. Without installing, you can also test a new configuration with: `pre-commit run --all-files`

Fun fact: `pre-commit autoupdate` will use the newest found versions of the precommits and insert a version if none was provided.

## Hooks

I tried selecting hooks that do not duplicate what another tool already does. For example, for python linting I use ruff and only ruff rather than [the common out-of-the-box pre-commit hooks](https://github.com/pre-commit/pre-commit-hooks). Same for JSON, YAML, TOML, etc. Same for security features. I aim to have only the best tooling.

### 01 Security

[GitLeaks](https://github.com/gitleaks/gitleaks) prevents passwords, api keys, or other secrets from entering your GitHub repo.

```yaml
  - repo: https://github.com/gitleaks/gitleaks
    rev: v8.22.0
    hooks:
      - id: gitleaks
```
<details>
<summary>
Alternatives to GitLeaks (TruffleHog)
</summary>
[TruffleHog](https://github.com/trufflesecurity/trufflehog) is an alternative to GitLeaks that is a bit more powerful, offering continuous scanning of a variety of platforms, not just files. And has a cute pig for their logo (crucial knowledge). However, it is a bit heavier and takes more time to set up. If you're handling particularly important information, I might recommend using it over GitLeaks.
</details>


<!-- TODO: Read this, https://kislyuk.github.io/argcomplete/ -->

### 02 Formatting

Local `make-lint` (commented out and using the remote hooks to avoid needing particular dependencies and to make the config more portable.)
```yaml
- repo: local
hooks:
    - id: make-lint
    name: Run 'make lint'
    entry: make
    args: ["lint"]
    language: system
```

**JS[X], TS[X], JSON[C], CSS, GraphQL**

[Biome](https://biomejs.dev/internals/language-support/) is a super fast formatter/linter/LS (hEy gUys iTs in rUsT) for JS[X], TS[X], JSON[C], CSS, and GraphQL with more coming soon. I think it generally has some better defaults and errors than something like ESLint. There's also a [VSCode Extension](https://marketplace.visualstudio.com/items?itemName=biomejs.biome) to use instead of ESLint

```yaml
repos:
-   repo: https://github.com/biomejs/pre-commit
    rev: "1.4.1"
    hooks:
    -   id: biome-ci
        additional_dependencies: ["@biomejs/biome@1.4.1"]
```

**JSON, YAML, TOML**

For [JSON Schema](https://json-schema.org/specification) (or YAML or TOML schema), [check-jsonschema](https://check-jsonschema.readthedocs.io/en/stable/precommit_usage.html) is helpful (despite having a confusing name). It also comes as a [CLI](https://check-jsonschema.readthedocs.io/en/stable/install.html). I've also included here a [TaskFile.yml](https://taskfile.dev/) checker.

```yaml
- repo: https://github.com/python-jsonschema/check-jsonschema
  rev: 0.30.0
  hooks:
    - id: check-github-workflows
      args: ["--verbose"]
    - id: check-taskfile
```

While check-jsonschema supports TOML files, [validate-pyproject](https://validate-pyproject.readthedocs.io/en/stable/readme.html) has a pre-commit hook as well. An official TOML schema seems to be in the works and when that comes out I think pyproject.toml will be one of the first. Perhaps I will instead use , I could steal the [JSON Schema](https://validate-pyproject.readthedocs.io/en/stable/json-schemas.html) posted by the creator of the project or the one from [Schema Store](https://json.schemastore.org/pyproject.json)

```yaml
  - repo: https://github.com/abravalheri/validate-pyproject
    rev: v0.23
    hooks:
        - id: validate-pyproject
          # Optional extra validations from SchemaStore:
          additional_dependencies: ["validate-pyproject-schema-store[all]"]
```


<details>
<summary>
Alternatives to Biome (ESLint & Prettier)
</summary>
Biome is meant to be a replacement for [ESLint](https://eslint.org/) (the most popular JavaScript Linter) and [Prettier](https://prettier.io/) (A code formatter with an insane number of supported files, notoriously slow). People seem quite excited about the project but it definitely doesn't have the wide scale adoption that Prettier and ESlint have and because of that -- a lack of plugins. Since this is a python-focused project template, the JS code won't be that advanced, and because it is speedy -- I've included it in this pre-commit. I'm also generally annoyed with the way Prettier does things. If you need those extensions, I wouldn't hesitate to use ESLint and Prettier.
</details>


**Python**

[ruff](https://docs.astral.sh/ruff/) formatter and linter (Super fast Python linter and code formatter that is increasingly becoming the standard over Black, Flake8, isort, pyupgrade, pydocstyle, mccabe complexity, pydoclint, [Bandit](https://bandit.readthedocs.io/en/latest/), and more.) It's incredible. It's hasn't fully replaced everything, but it is close enough to make it the only element on this list.

```yaml
- repo: https://github.com/astral-sh/ruff-pre-commit
rev: v0.8.4
hooks:
    # Run the linter.
    - id: ruff
    args: [ --fix ]
    # Run the formatter.
    - id: ruff-format
```

[MyPy](https://mypy-lang.org/) for Python type checking. I would prefer to use the [faster and more featureful](https://github.com/microsoft/pyright/blob/main/docs/mypy-comparison.md) Microsoft [Pyright](https://microsoft.github.io/pyright/#/) since it is  but there's currently not a good existing pre-commit hook for this. 
_(Will likely either make my own, adapt their [Git hook](https://github.com/microsoft/pyright/blob/main/docs/ci-integration.md), or just call it locally)_

```yaml
  - repo: https://github.com/pre-commit/mirrors-mypy
    hooks:
      - id: mypy
```

<!-- TODO: Add Pyright, no pre-existing hook available. [![Checked with pyright](https://microsoft.github.io/pyright/img/pyright_badge.svg)](https://microsoft.github.io/pyright/) -->

**Markdown**

I'm playing with [mdformat](https://mdformat.readthedocs.io/en/stable/) for the time being. I may switch back to using [Prettier](https://prettier.io/) but I'm still not super into it.

```yaml
- id: mdformat
  name: mdformat
  description: "CommonMark compliant Markdown formatter"
  entry: mdformat
  language: python
  types: [markdown]
  minimum_pre_commit_version: '1.0.0'
```

**Jupyter Notebooks**

[nbQA](https://nbqa.readthedocs.io/en/latest/index.html) is generally the go-to tool for notebook quality assurance. It allows you to use all the normal formatting tools with notebooks.

Here I have the tools listed previously but now run on a Notebook:

```yaml
- repo: https://github.com/nbQA-dev/nbQA
  rev: 1.9.1
  hooks:
    - id: nbqa-ruff-check
    - id: nbqa-ruff-format
    - id: nbqa-mypy
```


**YAML, HTML, Everything else not listed above**
<!-- HTML Hint for linting? https://htmlhint.com/ -->

[Prettier](https://prettier.io/) is an opinionated code formatter that I'm honestly not a huge fan of. It takes quite a while to run and I've personally run into issues with it breaking things. BUT it is pretty standard. I might try swapping out Prettier with better but smaller-scoped linters, but this might be overkill and require too many downloads.

<!-- TODO: Replace with prettier -->
```yaml
- repo: local
hooks:
    - id: make-lint
    name: Run 'make lint'
    entry: make
    args: ["lint"]
    language: system
```

If you're using [uv](https://docs.astral.sh/uv/), they [also have pre-commits](https://github.com/astral-sh/uv-pre-commit)

<!-- CZ git https://cz-git.qbb.sh/cli/why -->

### 03 Project and Files

`check-added-large-files` - Prevent giant files from being committed.

`check-case-conflict` - Check for files with names that would conflict on a case-insensitive filesystem like MacOS HFS+ or Windows FAT.

`check-illegal-windows-names` - Check for files that cannot be created on Windows.

`check-symlinks` - Checks for symlinks which do not point to anything.

`destroyed-symlinks` - Detects symlinks which are changed to regular files with a content of a path which that symlink was pointing to.

### 04 Git

[commitizen](https://commitizen.github.io/cz-cli/) - Enforces the usage of the Commitizen commit message format for consistent and standardized commits. Can also autogenerate changelog :D

_You should use the CLI too! I recommend the [czg](https://cz-git.qbb.sh/) implementation bc it's slightly faster and a bit more featureful._

`commitizen-branch` - Performs commit message validation. With the argument below it works specifically for branch pushes, but other options are available.

```yaml
- repo: https://github.com/commitizen-tools/commitizen
    rev: v2.35.0
    hooks:
    - id: commitizen
    - id: commitizen-branch
        stages: [push]
```

<details>
<summary>
Alternatives to Commitizen (Commitlint)
</summary>
[commitlint](https://github.com/conventional-changelog/commitlint) is a similar project to commitizen. Many articles claim that the difference between the two are that commitizen is more of a tool to generate these fancy commits while commitlint is meant to lint the commits. However, considering `cz check` is a thing, I'm confused what the difference is. More work to be done. The tools can be used together. Seems like commitizen has better python support than commitlint. Projects equally popular. More research to be done on the differences!
</details>

<!-- TODO: Look into the differences above. Oop. -->

<!-- TODO: Also look into running pre-commit before cz even pops up, it's annoying to write things and then have it fail the pre-commit and have to rewrite. -->

<!-- TODO: Look at https://github.com/conventional-changelog/conventional-changelog but commitizen may already deal with that. -->

<!-- TODO: Look into [gitmoji](https://gitmoji.dev/). I think it is just a standardization and commitizen could do that automatically potentially. -->

`check-merge-conflict` - Check for files that contain merge conflict strings.

`forbid-new-submodules` - Prevent addition of new git submodules. (I'm mixed on this one.)

`no-commit-to-branch` - Protect specific branches from direct checkins.


### 05 Testing

TODO: Finish implementing `tests/` boilerplate and include a precommit hook to run the fastest tests.

<!-- Also maybe add profiling? -->


Some inspo from [this article](https://medium.com/marvelous-mlops/welcome-to-pre-commit-heaven-5b622bb8ebce)
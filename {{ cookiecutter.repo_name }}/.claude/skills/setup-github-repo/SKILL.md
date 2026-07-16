---
name: setup-github-repo
description: >-
  Publish this GOTem-generated project as a brand-new GitHub repository. Use
  when the user wants to create the remote repo, push the first commit, and wire
  up repo settings (description, topics, homepage), branch protection, issue
  labels, GitHub Actions, and GitHub Pages docs. Triggers on requests like
  "set up GitHub", "create the repo on GitHub", "publish this project",
  "configure branch protection", or "put this on GitHub".
---

# Set up a GOTem project as a new GitHub repository

This skill turns the current GOTem (Gatlen's Opinionated Template) project into a
fully configured GitHub repository: it creates the remote, pushes your history,
and applies the repo settings, protections, labels, and Pages/docs that GOTem
ships templates for.

It is **idempotent** — safe to re-run. Each step checks current state before
changing anything, so you can run it again after fixing a prerequisite.

## When to use

- The project was generated from GOTem and only exists locally (no GitHub remote yet).
- The user asks to "create the repo", "publish to GitHub", "set up branch
  protection", "apply the labels", or "turn on Pages".

Do **not** use this to work on the GOTem template repository itself — it is for
*generated* projects. If `cookiecutter.json`, `ccds.json`, or a
`{{ cookiecutter.repo_name }}` directory exists at the project root, you are in
the template, not a generated project — stop and tell the user.

## Prerequisites (check these first, report clearly if missing)

1. **git** installed: `git --version`.
2. **A way to talk to GitHub**, in preference order:
   - **GitHub CLI** — `gh --version` and `gh auth status`. This is GOTem's
     primary path. If unauthenticated, tell the user to run `gh auth login`.
     For deploy keys, branch protection, and labels the token needs the `repo`
     scope (plus `admin:org` when creating under an organization). Check with
     `gh auth status` and refresh scopes via
     `gh auth refresh -s repo,admin:org` if needed.
   - **GitHub MCP tools** (`mcp__github__create_repository`,
     `mcp__github__create_or_update_file`, etc.) — use these only if `gh` is
     unavailable. They can create the repo and push files but cannot set classic
     branch protection or rulesets; note that limitation to the user.
3. Confirm the intended **repo name**, **visibility** (private/public), **owner**
   (personal vs. an org), and **description** before creating anything. Derive
   sensible defaults, then confirm:
   - repo name → the project directory name (or `repo_name` in `pyproject.toml`).
   - description → `project.description` in `pyproject.toml`.
   - visibility → ask; default to **private**.

## Fast path

For the common case, run the bundled helper, which performs every deterministic
step idempotently:

```bash
bash .claude/skills/setup-github-repo/scripts/setup_github_repo.sh \
  --name "<repo-name>" \
  --visibility private \
  --description "<one-line description>"
```

Useful flags: `--org <org>` (create under an organization), `--public`,
`--default-branch main`, `--no-protect` (skip branch protection), `--no-labels`,
`--no-pages`, `--homepage <url>`, `--dry-run` (print actions without executing).
Run with `--help` for the full list.

Read the script's output and relay a concise summary. If a step is skipped
(e.g. protection needs a plan the account doesn't have), say so explicitly
rather than reporting blanket success.

## What the setup does, step by step

Follow these in order. The helper script automates 1–7; do the rest with
judgment or when the user asks.

1. **Local git** — `git init -b main` if there's no `.git`; stage and make an
   initial commit if the tree is dirty or has no commits. GOTem's post-gen hook
   may already have done this — don't duplicate commits.
2. **Create the remote** — if `origin` doesn't already point at an existing
   GitHub repo:
   - `gh`: `gh repo create <owner>/<name> --private|--public --source=. --remote=origin --description "<desc>"`
   - MCP: `mcp__github__create_repository`, then add the remote locally.
   If the repo already exists, set `origin` to it instead of failing.
3. **Push** — `git push -u origin main` and `git push --tags`. Push a `dev`
   branch too if the project uses one.
4. **Repo settings** — `gh repo edit <owner>/<name> --description "<desc>"
   --homepage "<url>" --add-topic python,gotem,<extras>`. Enable/disable
   features to match the project (issues on; wiki/discussions per the user).
5. **Branch protection** — protect `main` (and `dev` if present). Prefer a
   **repository ruleset** (works on private repos on all plans) over classic
   branch protection (private-repo protection needs GitHub Pro/Team). Require a
   PR before merging and require the CI status checks from
   `.github/workflows/main.yml` to pass. If the plan can't enforce it, warn the
   user instead of silently skipping.
6. **Issue labels** — apply `.github/labels.yml` so the ISSUE_TEMPLATE labels
   resolve. Create/update each label with `gh label create <name>
   --color <hex> --description "<desc>" --force`.
7. **GitHub Actions** — the workflows in `.github/workflows/` run automatically
   once pushed. Tell the user which optional secrets unlock full functionality:
   `CODECOV_TOKEN` (coverage upload in `main.yml`) and, for publishing releases,
   a PyPI token / trusted publisher. Add with `gh secret set <NAME>`.
8. **GitHub Pages / docs** (only if the project uses mkdocs — check for
   `docs/mkdocs.yml`) — docs deploy via `on-release-main.yml` on release using
   `mkdocs gh-deploy`. Ensure Pages serves from the `gh-pages` branch
   (`gh api -X POST repos/<owner>/<name>/pages -f source[branch]=gh-pages
   -f source[path]=/` after the first deploy). If a `CNAME` file with a custom
   domain is present, set the Pages custom domain to match.
9. **Deploy keys (optional)** — GOTem can generate SSH deploy keys under
   `secrets/`. If the user wants CI/CD deploy access, upload the public key with
   `gh repo deploy-key add <path-to>.pub --title "<repo>-deploy"` (add
   `--allow-write` only if pushes are needed). Never commit or print private keys.

## Verify

After running, confirm the result and report it back:

- `gh repo view <owner>/<name> --json name,visibility,url,defaultBranchRef` and
  share the URL.
- `git remote -v` shows `origin` → the new repo.
- `git status` is clean and `main` is pushed (`git log origin/main -1`).
- If protection was requested, confirm the ruleset/protection exists on `main`.

## Notes & troubleshooting

- **Already on GitHub**: if `origin` already exists, don't recreate — reconcile
  the remote and push. Ask before force-pushing anything.
- **Org vs. personal**: creating under an org requires membership and the
  `admin:org` (or repo-creation) permission; surface the exact `gh` error if it
  fails rather than guessing.
- **Private-repo protection**: classic branch protection on private repos needs
  a paid plan; rulesets do not — prefer rulesets.
- **Git LFS**: GOTem configures `.gitattributes` for LFS. If the first push
  errors on LFS, see the "Known Issues" note in the GOTem README
  (`git lfs install --skip-smudge`).
- Keep everything in `secrets/` out of git; it is git-ignored by design.

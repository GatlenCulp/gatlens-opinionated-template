# GOTem v1.0 Release Plan & Roadmap

_Status: draft • Target: first stable `v1.0.0` of `gatlens-opinionated-template` (GOTem)_

This document defines what "v1.0" means for GOTem, the roadmap to get there, the
distribution strategy on PyPI, the changes needed in the day-to-day development
pattern, and how to run parallel **stable (`master`)** and **bleeding-edge
(`dev`)** versions of the template.

The guiding constraint from the maintainer: **v1.0 should remove fluff, change
as little as possible from the upstream CCDS fork, and above all be _stable_.**
v1.0 is a *hardening and pruning* release, not a feature release.

---

## 1. Where GOTem is today (0.5.1)

GOTem is a fork of [CookieCutter Data Science (CCDS) v2](https://cookiecutter-data-science.drivendata.org/).
It ships as a PyPI package `gatlens-opinionated-template` whose module is `ccds`
and whose CLI entry point is `gotem`. The CLI monkey-patches cookiecutter to read
`ccds.json` and, per `ccds/__main__.py`, **pins the rendered template to the git
tag `v{__version__}`** — i.e. the installed PyPI version decides which tag of this
repo is used to generate a project. This pinning is the mechanism the whole
distribution/branching strategy is built on (see §6–7).

### What's solid
- Working `ccds`-derived CLI, sub-option prompting, and scaffold cleaner.
- Multi-environment test harnesses (uv, conda, pixi, poetry, pipenv, virtualenv).
- CI is green again after the recent fixes (PRs #17/#18).
- A real, opinionated, modern stack (uv, Ruff, Typer, Pydantic, Loguru, Polars).

### What blocks a credible "1.0 / stable"
| Issue | Evidence | Why it matters for 1.0 |
| --- | --- | --- |
| README says **"Not yet ready for production…may fail to work between versions"** | `README.md:9-10` | Directly contradicts a v1.0 "stable" claim. Must be resolved. |
| Classifier already says `Production/Stable` while version is 0.5.1 | `pyproject.toml:22` | Mixed signals about maturity. |
| `.trunk/` contains **6 committed dangling symlinks** pointing at the author's machine | `find . -xtype l` → `.trunk/{actions,out,logs,tools,notifications,plugins/trunk}` | Breaks a clean render (confirmed by PR #19's workaround). And `_qa_tool` **defaults to `trunk`**. Stability bug in the default path. |
| Experimental features shipped as defaults | `ccds.json`: `_qa_tool: trunk`, `_typesetting_tool: typst`, plus `.obsidian`, `flake.nix`/`default.nix`, `homebrew`, `install.sh`, `_backend`/`_frontend` in the template | The 0.4.x/0.5.0 changelog literally calls these "experimental / probably should not be used." Defaults must be things that reliably work. |
| Version metadata is inconsistent | classifiers list Python 3.9 but `requires-python = ">=3.10,<4"`; `.python-version` = 3.10.16; `ccds.json` default = 3.12 | Pick one story and make it true everywhere. |
| Two changelogs | `HISTORY.md` (upstream CCDS) + `CHANGELOG.md` (commitizen) | Confusing provenance; decide the canonical one. |
| Maintainer scratch files committed | `temp.md`, `welcome.txt`, `docs/unpublished/` | Fluff; remove or relocate. |
| Release workflow uses deprecated mechanics | `release.yml`: username/password PyPI auth, `::set-output`, `actions/checkout@v3`, `pypi-publish@v1.3.0` | Should move to Trusted Publishing (OIDC) before we call releases "stable." |

---

## 2. Principles for v1.0

1. **Prune, don't rebuild.** Stay close to upstream CCDS so future syncs stay cheap.
   Every deletion should reduce surface area, not change generated-project behavior
   for the features we keep.
2. **Defaults must never be experimental.** If a feature isn't reliable enough to be
   the default, it becomes an opt-in (or is deferred to post-1.0), not the default.
3. **A clean render must always succeed.** `gotem` with default answers, on a fresh
   machine, must produce a project whose CI passes out of the box. This is the single
   most important acceptance test for 1.0.
4. **One honest maturity story.** The README, the classifier, and the version number
   must agree.
5. **Semver means something after 1.0.** Breaking template changes → major bump.

---

## 3. v1.0 scope

### 3.1 Remove / relocate (the "fluff")

Template *machinery* (root of this repo — safe to remove, does not affect kept features):
- `temp.md` — maintainer scratch notes. **Delete.**
- `welcome.txt` — stale, references master-branch URL. **Delete or fold into CLI output.**
- `docs/unpublished/` — **Delete or move out of the published docs tree.**
- `devenv.nix` / `devenv.yaml` / `devenv.lock` — experimental dev-shell. **Delete** (or move to a `experimental/` branch) unless actively used.
- `.trunk/` at repo root — **Delete the committed runtime symlinks**; keep only the tracked config (`.trunk/trunk.yaml`, linter configs) if Trunk is retained at all. The dangling symlinks must go regardless.
- `cookiecutter.json` deprecation stub — **Keep** (tiny, guides legacy users).
- Consolidate to **one changelog**. Recommended: keep `CHANGELOG.md` (commitizen-managed) as canonical for GOTem; rename `HISTORY.md` → `docs/UPSTREAM_HISTORY.md` for provenance.

Generated-project *content* — demote from default to opt-in, or drop for 1.0:
- `_qa_tool`: default **`trunk` → `pre-commit`** (pre-commit is the more universally reliable default; keep trunk as an opt-in). This also sidesteps the dangling-symlink class of problems.
- `_typesetting_tool: typst`, `.obsidian/`, `flake.nix`/`default.nix`, `homebrew/`, `install.sh`, `_backend`/`_frontend` scaffolds — gate all behind explicit opt-in options that default to "none/no". They can stay in the tree; they just must not be produced by the default render.

> Rule of thumb: nothing the 0.4/0.5 changelog described as "experimental" or
> "skeleton code" ships **on** by default in 1.0.

### 3.2 Fix (stability)

- **Delete the dangling `.trunk` symlinks** and add a test/CI guard (`find . -xtype l` must return nothing) so they can't come back.
- **Make the default render pass CI end-to-end.** Add a CI job that renders the template with default answers and runs the generated project's own lint + tests (PR #19 already builds most of this machinery — reuse it as a *gate*, not just a mirror-publisher).
- **Reconcile Python versions.** Drop the 3.9 classifier (or lower `requires-python`), and align `.python-version`, `ccds.json` default, and the classifier list.
- **Rewrite the README maturity banner** to match reality at release time (remove the "not ready / may break between versions" warning for the 1.0 tag).
- **Modernize `release.yml`** (see §6).

### 3.3 Keep (unchanged)

The core value proposition stays: uv, Ruff, the modern library defaults, the CLI,
the scaffold cleaner, docs via mkdocs, and the multi-env test harnesses. v1.0 does
**not** touch these beyond making their defaults reliable.

---

## 4. Roadmap / milestones

Small, verifiable steps. Each milestone ends in a tagged pre-release so the
distribution path itself gets exercised before 1.0.

| Milestone | Version | Theme | Exit criteria |
| --- | --- | --- | --- |
| **M0 – Baseline** | 0.5.x | Freeze scope | This ROADMAP merged; issues filed for each item in §3. |
| **M1 – Prune** | `0.6.0` | Remove fluff (§3.1) | Repo builds; no scratch files; one changelog; `find . -xtype l` clean. |
| **M2 – Safe defaults** | `0.7.0` | Demote experimental defaults (§3.1) | Default answers use only reliable features; `ccds.json` defaults updated. |
| **M3 – Green render gate** | `0.8.0` | CI renders default project + runs *its* CI (§3.2) | New CI gate passes on Linux + macOS. |
| **M4 – Metadata & docs honesty** | `0.9.0` | Python/version reconciliation, README banner, modern `release.yml` | Metadata consistent; Trusted Publishing live on TestPyPI. |
| **M5 – Release candidate** | `1.0.0rc1` | Dogfood via `--pre` | Published to PyPI as pre-release; a from-scratch `pip install --pre` + `gotem` works. |
| **M6 – Stable** | `1.0.0` | Tag + release | GitHub Release `v1.0.0`; PyPI stable; README/classifier say stable and mean it. |

Each `0.x` milestone is publishable as a normal release (or pre-release); you do not
have to hold everything for one big drop.

---

## 5. v1.0 release checklist (M6)

Adapted from `RELEASING.md`, corrected for GOTem's tooling:

- [ ] All M1–M5 exit criteria met; `main`/`master` green.
- [ ] `version = "1.0.0"` in `pyproject.toml` (single source of truth; `ccds.__version__` reads it).
- [ ] `CHANGELOG.md` updated (via `cz bump` or by hand) with the `1.0.0` section and date.
- [ ] README maturity banner rewritten; classifier `Development Status :: 5 - Production/Stable` now truthful.
- [ ] Default-render CI gate passing on Linux + macOS.
- [ ] Create GitHub Release with tag **`v1.0.0`** (the leading `v` is required — the CLI resolves `--checkout v{version}`).
- [ ] `release.yml` publishes to TestPyPI, smoke-test `pip install -i test.pypi ... && gotem`, then Prod PyPI.
- [ ] Verify a clean `uvx --from gatlens-opinionated-template gotem` on a fresh machine renders `v1.0.0`.
- [ ] Announce; open the `dev` line for 1.1 work.

---

## 6. Distributing on PyPI

**Current state:** `release.yml` fires on GitHub Release publish, asserts the tag
equals `v{ccds.__version__}`, builds, and pushes to TestPyPI then Prod PyPI using
**username/password secrets**. `make publish` does an ad-hoc `uv build && uv publish`.

**Recommended target state for 1.0:**

1. **Trusted Publishing (OIDC), not passwords.** Configure PyPI + TestPyPI "trusted
   publisher" for this repo's `release` workflow and drop the `PYPI_*` username/password
   secrets. Update `pypa/gh-action-pypi-publish` to a current major and remove the
   deprecated `::set-output` line. This is the single biggest "make releases stable
   and safe" change.
2. **Tag-driven, single source of version truth.** Keep `version` in `pyproject.toml`
   as the only place; the tag `v{version}` gate in `release.yml` already enforces
   consistency — keep it.
3. **Always TestPyPI first.** Keep the TestPyPI step with `skip_existing: true`, and
   add an install-smoke-test step against TestPyPI before the Prod publish. This
   catches broken sdists/wheels before they hit users.
4. **Retire `make publish` for real releases.** Manual `uv publish` bypasses the tag
   check and TestPyPI. Keep it only for local scratch/TestPyPI experiments; releases
   go through the workflow.
5. **Semver + pre-releases.** After 1.0: patch = fixes, minor = additive template
   features, major = breaking generated-project changes. Use PEP 440 pre-release
   suffixes (`1.1.0rc1`, `1.1.0.dev0`) for anything on the `dev` line (see §7).
6. **Because the CLI pins `--checkout v{version}`,** a released version can *only*
   render its own tag by default. So the PyPI version you ship **is** the template
   version users get — there is no drift. Keep it that way; it's a feature.

---

## 7. Can you have `dev` **and** `master` versions? — Yes.

You already have a `dev` branch and a protected `master`. The tag-pinning in
`ccds/__main__.py` (`--checkout` defaults to `v{__version__}`) is exactly what makes
two parallel channels clean. There are three complementary ways to expose a
"dev version," from lightest to most formal:

### Option A — Branch checkout (no PyPI needed) — **recommended default**
Cookiecutter/`gotem` accept `--checkout`. So:

```bash
# Stable (what a normal PyPI install pins to): renders tag v{installed version}
uvx --from gatlens-opinionated-template gotem

# Bleeding edge from the dev branch, straight from GitHub:
uvx --from gatlens-opinionated-template gotem --checkout dev

# A specific released line:
uvx --from gatlens-opinionated-template gotem --checkout v1.0.0
```

- **`master`** = stable, only ever holds tagged releases.
- **`dev`** = integration branch; feature branches merge here first.
- Users opt into `dev` explicitly with `--checkout dev`. Zero extra release
  machinery. This is the cheapest and most flexible split and should be the
  documented "try the unstable version" path.

### Option B — Pre-release versions on PyPI (opt-in via `--pre`)
When `dev` reaches a testable point, publish a **pre-release** from it:

```bash
# tag v1.1.0rc1 on dev → release.yml publishes 1.1.0rc1 to PyPI
pip install --pre gatlens-opinionated-template   # installs the rc
gotem                                             # renders v1.1.0rc1 (pinned)
```

Normal `pip install` ignores pre-releases, so stable users are unaffected; testers
opt in with `--pre`. This gives the `dev` line a real, versioned PyPI presence
without a second package.

### Option C — A second PyPI package (only if you truly need it) — **not recommended for now**
Publish `gatlens-opinionated-template-dev` from `dev`. Highest maintenance
(duplicate metadata, users install a different name). Reach for this only if
pre-releases prove insufficient. For a solo/small project, Options A + B cover it.

### Recommended model
- **`master`**: protected, release-only. Each release = tag `vX.Y.Z` → PyPI stable.
- **`dev`**: default integration target for all feature work. Exposed to adventurous
  users via `gotem --checkout dev` (Option A), and periodically via
  `vX.Y.Zrc/.devN` pre-releases (Option B).
- Document both paths in the README ("Stable" vs "Try the dev version").

---

## 8. Changes to your development pattern

1. **Branch discipline.** Make `dev` the base branch for all feature/fix work; PR into
   `dev`; fast-forward/merge `dev` → `master` only at release time. Keep `master`
   protected (it already is) and release-only. This is what gives you clean §7 channels.
2. **Conventional commits + commitizen for versioning.** You already have commitizen
   configured (`tool.commitizen`, `cz-conventional-gitmoji`). Use `cz bump` to move the
   version and update `CHANGELOG.md` in one step instead of hand-editing — it removes the
   version-mismatch failure mode the release workflow guards against.
3. **"Experimental" lives behind a flag, never in defaults.** New ideas ship as opt-in
   `ccds.json` options defaulting to off, or on a branch — not as the default render.
   This is the discipline that keeps the template stable release-to-release.
4. **The render gate is the definition of done.** A change isn't done until the
   default-answer render still produces a project whose own CI passes. Wire this into CI
   (M3) so it's automatic, not a manual check.
5. **One changelog, one version source.** `pyproject.toml` version + `CHANGELOG.md`
   only. Stop maintaining two changelog files.
6. **Stay synced with upstream, cheaply.** Keep the `upstream-base` branch you already
   have; periodically merge CCDS and resolve. The more fluff you remove now, the smaller
   each future merge conflict surface.
7. **Releases go through the workflow, not `make publish`.** Reserve manual publishing
   for TestPyPI experiments.

---

## 9. After 1.0 (not blocking)

- Consider migrating from CCDS-style tag pinning to `cruft` for update propagation to
  already-generated projects (a recurring TODO in `CONTRIBUTING.md`).
- Trim `.vscode/extensions` recommendations (noted as annoying in `CONTRIBUTING.md`).
- Re-introduce demoted experimental features (typst, obsidian, nix, homebrew) as
  polished opt-in options, one per minor release, each behind the render gate.
- Windows CI (currently disabled) once the default render is stable on Linux/macOS.

---

### TL;DR
v1.0 = **delete the scratch/experimental fluff, make the default render pass CI,
tell one honest maturity story, and modernize PyPI publishing to Trusted Publishing.**
Keep `master` release-only and `dev` as the integration line; expose `dev` to users via
`gotem --checkout dev` and `--pre` pre-releases. Ship it as `0.6 → 0.9` pruning/hardening
milestones, a `1.0.0rc1`, then `1.0.0`.

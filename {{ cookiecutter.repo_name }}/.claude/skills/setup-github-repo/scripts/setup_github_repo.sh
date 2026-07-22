#!/usr/bin/env bash
#
# setup_github_repo.sh — configure a GOTem-generated project as a new GitHub repo.
#
# Idempotent: every step checks current state before acting, so re-running is safe.
# Requires: git, and the GitHub CLI (`gh`) authenticated via `gh auth login`.
#
# Usage:
#   bash setup_github_repo.sh --name my-project --visibility private \
#        --description "A short description"
#
# See --help for all options.

set -euo pipefail

# ---------------------------------------------------------------------------- #
#                                   Defaults                                    #
# ---------------------------------------------------------------------------- #
REPO_NAME=""
VISIBILITY="private"        # private | public
OWNER=""                    # empty => authenticated user; otherwise an org/user
DESCRIPTION=""
HOMEPAGE=""
DEFAULT_BRANCH="main"
REQUIRE_CHECKS=""           # comma-separated status-check contexts to require (opt-in)
DO_PROTECT=1
DO_LABELS=1
DO_PAGES=1
DRY_RUN=0

# ---------------------------------------------------------------------------- #
#                                   Helpers                                     #
# ---------------------------------------------------------------------------- #
c_reset=$'\033[0m'; c_blue=$'\033[34m'; c_green=$'\033[32m'; c_yellow=$'\033[33m'; c_red=$'\033[31m'
info()  { printf '%s==>%s %s\n' "$c_blue"  "$c_reset" "$*"; }
ok()    { printf '%s ok %s %s\n' "$c_green" "$c_reset" "$*"; }
warn()  { printf '%swarn%s %s\n' "$c_yellow" "$c_reset" "$*" >&2; }
die()   { printf '%serr %s %s\n' "$c_red"   "$c_reset" "$*" >&2; exit 1; }

# Guard value-taking options: with `set -u`, a flag without a value would either
# crash on an unbound $2 or silently swallow the next option token.
require_value() { [[ "$2" -ge 2 ]] || die "Option $1 requires a value"; }

run() {
  # Echo the command; execute unless --dry-run.
  printf '    %s$%s %s\n' "$c_blue" "$c_reset" "$*"
  if [[ "$DRY_RUN" -eq 0 ]]; then
    "$@"
  fi
}

usage() {
  sed -n '2,20p' "$0" | sed 's/^# \{0,1\}//'
  cat <<'EOF'

Options:
  --name NAME            Repository name (default: current directory name)
  --description TEXT     Repo description (default: [project].description from pyproject.toml)
  --visibility V         private | public (default: private)
  --public              Shorthand for --visibility public
  --org ORG             Create under an organization instead of your user
  --homepage URL        Repo homepage/website
  --default-branch B    Default branch name (default: main)
  --require-checks LIST  Comma-separated CI status-check contexts to require in the
                        ruleset (opt-in). Matrix jobs are version-suffixed, e.g.
                        "quality,tests-and-type-check (3.12),check-docs". Off by
                        default because requiring a not-yet-existing check blocks merges.
  --no-protect          Skip branch protection / ruleset
  --no-labels           Skip applying .github/labels.yml
  --no-pages            Skip GitHub Pages docs configuration
  --dry-run             Print the actions without executing them
  -h, --help            Show this help
EOF
}

# ---------------------------------------------------------------------------- #
#                                 Parse args                                    #
# ---------------------------------------------------------------------------- #
while [[ $# -gt 0 ]]; do
  case "$1" in
    --name)           require_value "$1" "$#"; REPO_NAME="$2"; shift 2 ;;
    --description)    require_value "$1" "$#"; DESCRIPTION="$2"; shift 2 ;;
    --visibility)     require_value "$1" "$#"; VISIBILITY="$2"; shift 2 ;;
    --public)         VISIBILITY="public"; shift ;;
    --org)            require_value "$1" "$#"; OWNER="$2"; shift 2 ;;
    --homepage)       require_value "$1" "$#"; HOMEPAGE="$2"; shift 2 ;;
    --default-branch) require_value "$1" "$#"; DEFAULT_BRANCH="$2"; shift 2 ;;
    --require-checks) require_value "$1" "$#"; REQUIRE_CHECKS="$2"; shift 2 ;;
    --no-protect)     DO_PROTECT=0; shift ;;
    --no-labels)      DO_LABELS=0; shift ;;
    --no-pages)       DO_PAGES=0; shift ;;
    --dry-run)        DRY_RUN=1; shift ;;
    -h|--help)        usage; exit 0 ;;
    *)                die "Unknown argument: $1 (see --help)" ;;
  esac
done

[[ "$VISIBILITY" == "private" || "$VISIBILITY" == "public" ]] \
  || die "--visibility must be 'private' or 'public'"

# ---------------------------------------------------------------------------- #
#                              Prerequisite checks                             #
# ---------------------------------------------------------------------------- #
info "Checking prerequisites"
command -v git >/dev/null 2>&1 || die "git is not installed."
command -v gh  >/dev/null 2>&1 || die "GitHub CLI (gh) is not installed. See https://cli.github.com/"
gh auth status >/dev/null 2>&1 || die "gh is not authenticated. Run: gh auth login"
ok "git and gh are ready"

# Guard: refuse to run inside the GOTem template itself.
if [[ -f cookiecutter.json || -d "{{ cookiecutter.repo_name }}" ]]; then
  die "This looks like the GOTem template, not a generated project. Aborting."
fi

# ---------------------------------------------------------------------------- #
#                              Derive configuration                            #
# ---------------------------------------------------------------------------- #
if [[ -z "$REPO_NAME" ]]; then
  REPO_NAME="$(basename "$(pwd)")"
fi

if [[ -z "$DESCRIPTION" && -f pyproject.toml ]]; then
  DESCRIPTION="$(grep -m1 -E '^\s*description\s*=' pyproject.toml \
    | sed -E 's/^[^=]*=\s*"?([^"]*)"?\s*$/\1/' || true)"
fi

GH_USER="$(gh api user -q .login)"
FULL_NAME="${OWNER:-$GH_USER}/$REPO_NAME"

# Resolve the remote URL honoring the user's configured Git transport (ssh/https),
# so `origin` matches how `gh auth login` was set up and pushes don't fail.
remote_url_for() {
  local proto
  proto="$(gh config get git_protocol --host github.com 2>/dev/null || echo https)"
  if [[ "$proto" == "ssh" ]]; then
    gh repo view "$FULL_NAME" --json sshUrl -q .sshUrl
  else
    gh repo view "$FULL_NAME" --json url -q .url
  fi
}

info "Configuration"
printf '    repo:        %s\n' "$FULL_NAME"
printf '    visibility:  %s\n' "$VISIBILITY"
printf '    description: %s\n' "${DESCRIPTION:-<none>}"
printf '    branch:      %s\n' "$DEFAULT_BRANCH"
[[ "$DRY_RUN" -eq 1 ]] && warn "DRY RUN — no changes will be made"

# ---------------------------------------------------------------------------- #
#                          1. Local git initialization                         #
# ---------------------------------------------------------------------------- #
info "Ensuring local git repository"
if [[ "$DRY_RUN" -eq 1 ]]; then
  if [[ -d .git ]]; then
    ok ".git present (dry-run: would commit any pending changes)"
  else
    printf '    (dry-run) would run: git init -b %s && git add -A && git commit\n' "$DEFAULT_BRANCH"
  fi
else
  if [[ ! -d .git ]]; then
    run git init -b "$DEFAULT_BRANCH"
  else
    ok ".git already present"
  fi

  # Make sure the default branch is named correctly.
  current_branch="$(git symbolic-ref --quiet --short HEAD 2>/dev/null || echo "")"
  if [[ -n "$current_branch" && "$current_branch" != "$DEFAULT_BRANCH" ]]; then
    run git branch -M "$DEFAULT_BRANCH"
  fi

  # Initial commit if there is nothing committed yet, or commit a dirty tree.
  if ! git rev-parse HEAD >/dev/null 2>&1; then
    run git add -A
    run git commit -m "Initial commit"
  elif [[ -n "$(git status --porcelain)" ]]; then
    warn "Uncommitted changes present — committing them"
    run git add -A
    run git commit -m "Configure project"
  else
    ok "Working tree is committed"
  fi
fi

# ---------------------------------------------------------------------------- #
#                           2. Create the GitHub repo                          #
# ---------------------------------------------------------------------------- #
info "Creating GitHub repository (if needed)"
if gh repo view "$FULL_NAME" >/dev/null 2>&1; then
  warn "Repo $FULL_NAME already exists — reusing it"
  if [[ "$DRY_RUN" -eq 0 ]]; then
    remote_url="$(remote_url_for)"
    if git remote get-url origin >/dev/null 2>&1; then
      run git remote set-url origin "$remote_url"
    else
      run git remote add origin "$remote_url"
    fi
  else
    printf '    (dry-run) would point origin at the existing repo\n'
  fi
else
  create_args=(repo create "$FULL_NAME" "--$VISIBILITY" --source=. --remote=origin)
  [[ -n "$DESCRIPTION" ]] && create_args+=(--description "$DESCRIPTION")
  run gh "${create_args[@]}"
  ok "Created $FULL_NAME"
fi

# ---------------------------------------------------------------------------- #
#                                3. Push history                               #
# ---------------------------------------------------------------------------- #
info "Pushing to origin"
run git push -u origin "$DEFAULT_BRANCH"
if [[ "$DRY_RUN" -eq 0 ]]; then
  git tag | grep -q . && run git push --tags
  git show-ref --verify --quiet refs/heads/dev && run git push -u origin dev
else
  printf '    (dry-run) would push tags and any dev branch\n'
fi

# ---------------------------------------------------------------------------- #
#                              4. Repository settings                          #
# ---------------------------------------------------------------------------- #
info "Applying repository settings"
edit_args=(repo edit "$FULL_NAME" --add-topic python --add-topic gotem)
[[ -n "$DESCRIPTION" ]] && edit_args+=(--description "$DESCRIPTION")
[[ -n "$HOMEPAGE" ]]    && edit_args+=(--homepage "$HOMEPAGE")
run gh "${edit_args[@]}" || warn "Some repo settings could not be applied"

# ---------------------------------------------------------------------------- #
#                             5. Branch protection                             #
# ---------------------------------------------------------------------------- #
# NOTE on plans: branch protection and rulesets are available for PUBLIC repos on
# every plan, but for PRIVATE repos they require GitHub Team or Enterprise. On the
# Free plan a private repo cannot enforce this — the API call below fails and we
# warn rather than pretending protection was applied.
if [[ "$DO_PROTECT" -eq 1 ]]; then
  info "Configuring a branch ruleset for '$DEFAULT_BRANCH'"

  # Optionally require CI status checks. Off by default: matrix jobs report
  # version-suffixed contexts (e.g. "tests-and-type-check (3.12)") and requiring a
  # context that never appears would block every merge. Pass --require-checks once
  # you know the exact contexts (see them under the PR's checks after the first run).
  checks_rule=""
  if [[ -n "$REQUIRE_CHECKS" ]]; then
    contexts=""
    IFS=',' read -ra _ctx <<< "$REQUIRE_CHECKS"
    for c in "${_ctx[@]}"; do
      c="$(printf '%s' "$c" | sed -E 's/^[[:space:]]+|[[:space:]]+$//g')"
      [[ -z "$c" ]] && continue
      contexts+="${contexts:+,}{\"context\":\"$c\"}"
    done
    [[ -n "$contexts" ]] && checks_rule=",
    { \"type\": \"required_status_checks\",
      \"parameters\": { \"strict_required_status_checks_policy\": true,
                        \"required_status_checks\": [ $contexts ] } }"
  fi

  ruleset_json="$(cat <<JSON
{
  "name": "protect-$DEFAULT_BRANCH",
  "target": "branch",
  "enforcement": "active",
  "conditions": { "ref_name": { "include": ["refs/heads/$DEFAULT_BRANCH"], "exclude": [] } },
  "rules": [
    { "type": "pull_request",
      "parameters": {
        "required_approving_review_count": 0,
        "dismiss_stale_reviews_on_push": false,
        "require_code_owner_review": false,
        "require_last_push_approval": false,
        "required_review_thread_resolution": false
      }
    },
    { "type": "deletion" },
    { "type": "non_fast_forward" }$checks_rule
  ]
}
JSON
)"

  if [[ "$DRY_RUN" -eq 1 ]]; then
    printf '    (dry-run) would create/update ruleset protect-%s%s\n' \
      "$DEFAULT_BRANCH" "${REQUIRE_CHECKS:+ (required checks: $REQUIRE_CHECKS)}"
  else
    # Idempotent reconcile: update the existing named ruleset by id if present,
    # otherwise create it — so repeated runs don't stack duplicate rulesets.
    existing_id="$(gh api "repos/$FULL_NAME/rulesets" \
      --jq ".[] | select(.name==\"protect-$DEFAULT_BRANCH\") | .id" 2>/dev/null | head -n1 || true)"
    if [[ -n "$existing_id" ]]; then
      if printf '%s' "$ruleset_json" | gh api -X PUT "repos/$FULL_NAME/rulesets/$existing_id" --input - >/dev/null 2>&1; then
        ok "Ruleset updated for '$DEFAULT_BRANCH'"
      else
        warn "Could not update existing ruleset (permissions/plan?). Left unchanged."
      fi
    elif printf '%s' "$ruleset_json" | gh api -X POST "repos/$FULL_NAME/rulesets" --input - >/dev/null 2>&1; then
      ok "Ruleset created for '$DEFAULT_BRANCH'"
    else
      warn "Could not create ruleset. Private repos need GitHub Team/Enterprise for"
      warn "rulesets & branch protection (public repos work on all plans). Left unprotected."
    fi
  fi
else
  warn "Skipping branch protection (--no-protect)"
fi

# ---------------------------------------------------------------------------- #
#                                 6. Issue labels                              #
# ---------------------------------------------------------------------------- #
if [[ "$DO_LABELS" -eq 1 && -f .github/labels.yml ]]; then
  info "Applying labels from .github/labels.yml"
  # Minimal YAML reader for the fixed GOTem label schema (name/color/description).
  name=""; color=""; desc=""
  flush_label() {
    if [[ -n "$name" ]]; then
      if [[ "$DRY_RUN" -eq 0 ]]; then
        gh label create "$name" --color "${color:-cccccc}" --description "${desc:-}" --force \
          >/dev/null 2>&1 && printf '    + %s\n' "$name" \
          || warn "label '$name' could not be created"
      else
        printf '    (dry-run) label %s (#%s)\n' "$name" "${color:-cccccc}"
      fi
    fi
    name=""; color=""; desc=""
  }
  while IFS= read -r line; do
    case "$line" in
      *"- name:"*)  flush_label; name="$(sed -E 's/.*- name:\s*"?([^"]*)"?.*/\1/' <<<"$line")" ;;
      *"color:"*)   color="$(sed -E 's/.*color:\s*"?([^"]*)"?.*/\1/' <<<"$line")" ;;
      *"description:"*) desc="$(sed -E 's/.*description:\s*"?([^"]*)"?.*/\1/' <<<"$line")" ;;
    esac
  done < .github/labels.yml
  flush_label
  ok "Labels applied"
else
  [[ "$DO_LABELS" -eq 1 ]] && warn "No .github/labels.yml found — skipping labels"
fi

# ---------------------------------------------------------------------------- #
#                            7. GitHub Pages (docs)                            #
# ---------------------------------------------------------------------------- #
# Docs deploy on release via .github/workflows/on-release-main.yml (mkdocs gh-deploy),
# which creates the 'gh-pages' branch. We can only turn on Pages once that branch
# exists, so configure it when present and defer with guidance otherwise.
if [[ "$DO_PAGES" -eq 1 && -f docs/mkdocs.yml ]]; then
  info "Configuring GitHub Pages for mkdocs docs"
  if [[ "$DRY_RUN" -eq 1 ]]; then
    printf '    (dry-run) would enable Pages from gh-pages once that branch exists\n'
  elif gh api "repos/$FULL_NAME/branches/gh-pages" >/dev/null 2>&1; then
    if gh api "repos/$FULL_NAME/pages" >/dev/null 2>&1; then
      ok "GitHub Pages already configured"
    elif gh api -X POST "repos/$FULL_NAME/pages" \
           -f "source[branch]=gh-pages" -f "source[path]=/" >/dev/null 2>&1; then
      ok "GitHub Pages enabled from gh-pages"
    else
      warn "Could not enable Pages automatically — enable it in repo Settings > Pages."
    fi
    if [[ -f CNAME ]]; then
      domain="$(head -n1 CNAME | tr -d '[:space:]')"
      if [[ -n "$domain" ]]; then
        gh api -X PUT "repos/$FULL_NAME/pages" -f "cname=$domain" >/dev/null 2>&1 \
          && ok "Pages custom domain set to $domain" \
          || warn "Could not set Pages custom domain ($domain)"
      fi
    fi
  else
    warn "No 'gh-pages' branch yet — docs deploy on release via on-release-main.yml."
    warn "After the first release creates gh-pages, re-run this script to enable Pages."
  fi
else
  [[ "$DO_PAGES" -eq 1 ]] && warn "No docs/mkdocs.yml — skipping Pages configuration"
fi

# ---------------------------------------------------------------------------- #
#                                    Summary                                    #
# ---------------------------------------------------------------------------- #
info "Done"
if [[ "$DRY_RUN" -eq 0 ]]; then
  url="$(gh repo view "$FULL_NAME" --json url -q .url 2>/dev/null || echo "https://github.com/$FULL_NAME")"
  ok "Repository ready: $url"
  echo
  echo "Next steps you may want to take:"
  echo "  - Add optional secrets:  gh secret set CODECOV_TOKEN"
  echo "  - Review Actions runs:   gh run list"
  echo "  - Require CI checks:     re-run with --require-checks after the first CI run"
  echo "  - Upload a deploy key:   gh repo deploy-key add secrets/<name>.pub --title \"$REPO_NAME-deploy\""
else
  ok "Dry run complete — re-run without --dry-run to apply."
fi

#!/usr/bin/env bash
# deploy_policy.sh — OPERATOR-ONLY control-plane deploy of the fleet-policy
# plugin (v1.2.38, card t_e393b6e8, RECOVERY-PROGRAM RR-3).
#
# WHO RUNS THIS: the company OPERATOR session (interactive, non-worker).
# A dispatcher worker attempting this deploy is denied by the policy gate
# itself (deploy_external_runtime / policy_control_plane_mutation) — that is
# intentional. The worker-side contract is: prepare bundle+runbook, then
# block the card with [continues: company].
#
# WHAT IT DOES (tag-only, never edit-in-place — PROGRAM rule 5):
#   1. resolves the tag in --repo, verifies it exists and prints its version;
#   2. materializes a detached worktree at the tag;
#   3. runs the full test suite + release-bundle build/verify in the worktree
#      (skippable with --skip-tests for a hotfix rerun of an already-proven tag);
#   4. refuses to touch a LIVE plugin clone whose tracked tree has drifted
#      from the target tag UNLESS the drift is content-identical to the tag
#      (the RR-1 capture case) or --force is given;
#   5. checks out the tag detached in the live plugin clone (.state/ is
#      gitignored and survives), audits profile symlinks, prints a JSON
#      manifest with prev/new SHAs for the deploy record.
#
# ROLLBACK: git -C "$PLUGIN_DIR" checkout --detach <prev_sha from manifest>.
# Runbook: docs/fleet-ops/fleet-policy-deploy-runbook.md
set -euo pipefail

REPO=""
TAG=""
PLUGIN_DIR="${LOCALAPPDATA:-$HOME/AppData/Local}/hermes/profiles/company/plugins/fleet-policy"
PROFILES_ROOT="${LOCALAPPDATA:-$HOME/AppData/Local}/hermes/profiles"
SKIP_TESTS=0
DRY_RUN=0
FORCE=0

usage() {
  cat <<'USAGE'
usage: deploy_policy.sh --repo <path> --tag <tag> [--plugin-dir <path>]
                        [--profiles-root <path>] [--skip-tests] [--dry-run] [--force]

  --repo           local clone of maximalang/ventures containing the tag
  --tag            release tag to deploy, e.g. v1.2.38 (deploy is tag-only)
  --plugin-dir     live plugin clone (default: profiles/company/plugins/fleet-policy)
  --profiles-root  hermes profiles root for the symlink audit
  --skip-tests     skip worktree test/bundle proof (tag already proven)
  --dry-run        stop after all checks, print the manifest without deploying
  --force          allow deploy over a live tree that differs from the tag
USAGE
}

while [ $# -gt 0 ]; do
  case "$1" in
    --repo) REPO="$2"; shift 2 ;;
    --tag) TAG="$2"; shift 2 ;;
    --plugin-dir) PLUGIN_DIR="$2"; shift 2 ;;
    --profiles-root) PROFILES_ROOT="$2"; shift 2 ;;
    --skip-tests) SKIP_TESTS=1; shift ;;
    --dry-run) DRY_RUN=1; shift ;;
    --force) FORCE=1; shift ;;
    -h|--help) usage; exit 0 ;;
    *) echo "unknown argument: $1" >&2; usage >&2; exit 2 ;;
  esac
done

[ -n "$REPO" ] && [ -n "$TAG" ] || { usage >&2; exit 2; }
command -v git >/dev/null || { echo "git is required" >&2; exit 1; }

# Native Windows git/uv do not understand MSYS /c/... paths; normalize every
# path handed to an external program to the C:/... form (no-op on POSIX).
w() {
  if command -v cygpath >/dev/null 2>&1; then cygpath -m "$1"; else printf '%s' "$1"; fi
}

REPO="$(cd "$REPO" && pwd)"
TAG_SHA="$(git -C "$(w "$REPO")" rev-list -n1 "refs/tags/$TAG^{commit}" 2>/dev/null || true)"
if [ -z "$TAG_SHA" ]; then
  echo "tag $TAG not found in $REPO (fetch it first: git -C $REPO fetch origin tag $TAG)" >&2
  exit 1
fi
TAG_VERSION="$(git -C "$(w "$REPO")" show "$TAG:plugin.yaml" | sed -n 's/^version:[[:space:]]*"\{0,1\}\([^"]*\)"\{0,1\}$/\1/p' | head -1)"
echo "== tag $TAG -> $TAG_SHA (plugin version ${TAG_VERSION:-unknown})"

# ---------------------------------------------------------------- worktree proof
WORKTREE="$(mktemp -d "${TMPDIR:-/tmp}/fleet-policy-deploy.XXXXXX")"
cleanup() { git -C "$(w "$REPO")" worktree remove --force "$(w "$WORKTREE")" >/dev/null 2>&1 || rm -rf "$WORKTREE"; }
trap cleanup EXIT

git -C "$(w "$REPO")" worktree add --detach "$(w "$WORKTREE")" "$TAG_SHA" >/dev/null
BUNDLE_OK=false
if [ "$SKIP_TESTS" -eq 0 ]; then
  command -v uv >/dev/null || { echo "uv is required for the tag proof (or pass --skip-tests)" >&2; exit 1; }
  ( cd "$WORKTREE" && uv sync --frozen --all-groups >/dev/null )
  ( cd "$WORKTREE" && uv run --frozen python -m pytest tests/ -q | tail -2 )
  ( cd "$WORKTREE" && uv run --frozen fleet-policy --root . build-bundle --output "$(w "$WORKTREE")/.deploy-bundle" >/dev/null )
  ( cd "$WORKTREE" && uv run --frozen fleet-policy verify-bundle --bundle "$(w "$WORKTREE")/.deploy-bundle" )
  BUNDLE_OK=true
fi

# ---------------------------------------------------------------- live clone checks
if [ ! -d "$PLUGIN_DIR/.git" ]; then
  echo "plugin dir is not a git clone: $PLUGIN_DIR" >&2
  echo "this script deploys ONLY into the existing clone shape (symlink farm root)." >&2
  exit 1
fi
LIVE_PREV="$(git -C "$(w "$PLUGIN_DIR")" rev-parse HEAD 2>/dev/null || echo none)"
PLUGIN_DIR="$(cd "$PLUGIN_DIR" && pwd)"
echo "== live plugin clone: $PLUGIN_DIR @ $LIVE_PREV"

git -C "$(w "$PLUGIN_DIR")" fetch --no-tags "$(w "$REPO")" "refs/tags/$TAG:refs/tags/$TAG" >/dev/null 2>&1 \
  || git -C "$(w "$PLUGIN_DIR")" fetch --no-tags "$(w "$REPO")" "refs/tags/$TAG" >/dev/null

DRIFT_NOTE="clean"
if [ -n "$(git -C "$(w "$PLUGIN_DIR")" status --porcelain --untracked-files=no)" ]; then
  # RR-1: a dirty live tree must have been captured into the repo already.
  # If its CONTENT equals the target tag, the checkout below is lossless;
  # otherwise refuse without --force.
  if git -C "$(w "$PLUGIN_DIR")" diff --quiet "$TAG_SHA" -- 2>/dev/null; then
    DRIFT_NOTE="dirty-but-content-identical-to-tag (RR-1 capture already in repo)"
    CHECKOUT_FLAGS="--force"
  else
    if [ "$FORCE" -eq 1 ]; then
      DRIFT_NOTE="DIRTY and different from tag — deployed with --force (capture the diff first!)"
      CHECKOUT_FLAGS="--force"
    else
      echo "ABORT: live tracked tree differs from $TAG and is dirty (RR-1)." >&2
      echo "Capture/merge the live diff into the repo and re-tag, or pass --force knowingly." >&2
      git -C "$(w "$PLUGIN_DIR")" status --porcelain --untracked-files=no >&2
      exit 1
    fi
  fi
else
  CHECKOUT_FLAGS=""
fi

# ---------------------------------------------------------------- symlink audit
SYMLINK_REPORT="[]"
if [ -d "$PROFILES_ROOT" ]; then
  REPORT_TMP="$(mktemp)"
  echo "[" > "$REPORT_TMP"
  FIRST=1
  for profile_plugins in "$PROFILES_ROOT"/*/plugins/fleet-policy; do
    [ -e "$profile_plugins" ] || continue
    case "$profile_plugins" in "$PLUGIN_DIR") continue ;; esac
    if [ -L "$profile_plugins" ]; then
      KIND="symlink"
    else
      KIND="REAL_DIR_NEEDS_MANUAL_SYNC"
    fi
    [ "$FIRST" -eq 0 ] && echo "," >> "$REPORT_TMP"
    FIRST=0
    printf '  {"profile_path": "%s", "kind": "%s"}' "$(w "$profile_plugins")" "$KIND" >> "$REPORT_TMP"
  done
  echo "" >> "$REPORT_TMP"
  echo "]" >> "$REPORT_TMP"
  SYMLINK_REPORT="$(tr -d '\n' < "$REPORT_TMP")"
  rm -f "$REPORT_TMP"
fi

if [ "$DRY_RUN" -eq 1 ]; then
  echo "== dry-run: no changes applied"
else
  # shellcheck disable=SC2086
  git -C "$(w "$PLUGIN_DIR")" checkout --detach $CHECKOUT_FLAGS "$TAG_SHA" >/dev/null
  LIVE_NEW="$(git -C "$(w "$PLUGIN_DIR")" rev-parse HEAD)"
  [ "$LIVE_NEW" = "$TAG_SHA" ] || { echo "checkout verification failed: $LIVE_NEW != $TAG_SHA" >&2; exit 1; }
  echo "== deployed: $LIVE_PREV -> $LIVE_NEW"
fi

LIVE_VERSION="$(sed -n 's/^version:[[:space:]]*"\{0,1\}\([^"]*\)"\{0,1\}$/\1/p' "$PLUGIN_DIR/plugin.yaml" | head -1)"
STATE_PRESENT=false
[ -e "$PLUGIN_DIR/.state" ] && STATE_PRESENT=true

cat <<MANIFEST
{"ok": true, "tag": "$TAG", "tag_sha": "$TAG_SHA", "tag_version": "${TAG_VERSION:-}",
 "plugin_dir": "$(w "$PLUGIN_DIR")", "live_prev_sha": "$LIVE_PREV",
 "live_new_sha": "$(git -C "$(w "$PLUGIN_DIR")" rev-parse HEAD)", "live_version": "${LIVE_VERSION:-}",
 "drift": "$DRIFT_NOTE", "bundle_verified": $BUNDLE_OK, "dry_run": $([ "$DRY_RUN" -eq 1 ] && echo true || echo false),
 "state_dir_present": $STATE_PRESENT,
 "rollback": "git -C \\"$(w "$PLUGIN_DIR")\\" checkout --detach $LIVE_PREV",
 "profiles": $SYMLINK_REPORT}
MANIFEST

echo "== post-deploy: restart/refresh gateway sessions so hooks reload the new version;"
echo "   then observe: fleet-policy events --since <today> --decision deny (shadow window)."

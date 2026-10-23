#!/usr/bin/env bash
# Prepare a minimal php-src PR from the ForgeBlue-validated GH-24492 patch.
# Default mode does NOT create a fork, push, or publish a PR.
set -Eeuo pipefail

LAB_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
MODE="prepare-only"
WORKDIR=""
BRANCH="fix/gh-24492-base64-soft-oom"
REQUIRED_BASE_SHA="fc05c9bf2486d3d66593501bf78c1d83c32ecbc5"
ACTOR="forgeblueai"
PATCH="$LAB_ROOT/patches/base64-fallible.patch"
PHPT_SOURCE="$LAB_ROOT/upstream/ext/standard/tests/url/gh24492_base64_encode_oom.phpt"
PHPT_DEST="ext/standard/tests/url/gh24492_base64_encode_oom.phpt"

usage() {
  cat <<'USAGE'
Usage:
  bash scripts/submit_upstream_base64.sh [--prepare-only|--submit-draft] [--workdir PATH]

Modes:
  --prepare-only   (default) Clone current PHP-8.4 and stage exactly three files.
                   Does NOT create a fork, push a branch, or open a PR.
  --submit-draft   Requires authenticated GitHub CLI and configured git identity.
                   Creates fork if missing, pushes an upstream topic branch, and
                   creates a PUBLIC DRAFT pull request against php/php-src:PHP-8.4.
                   Refuses submission if source SHA differs from tested baseline.

Example:
  bash scripts/submit_upstream_base64.sh --prepare-only
  bash scripts/submit_upstream_base64.sh --submit-draft
USAGE
}

while (( $# > 0 )); do
  case "$1" in
    --prepare-only) MODE="prepare-only"; shift ;;
    --submit-draft) MODE="submit-draft"; shift ;;
    --workdir)
      if (( $# < 2 )); then echo "Missing --workdir value" >&2; exit 2; fi
      WORKDIR="$2"; shift 2 ;;
    -h|--help) usage; exit 0 ;;
    *) echo "Unknown option: $1" >&2; usage >&2; exit 2 ;;
  esac
done

for cmd in git python3; do
  command -v "$cmd" >/dev/null 2>&1 || {
    echo "Required command not found: $cmd" >&2; exit 1;
  }
done
[[ -s "$PATCH" && -s "$PHPT_SOURCE" ]] || {
  echo "Patch or PHPT missing from ForgeBlue lab checkout" >&2; exit 1;
}
if [[ "$MODE" == "submit-draft" ]]; then
  command -v gh >/dev/null 2>&1 || {
    echo "GitHub CLI missing; install 'gh' first" >&2; exit 1;
  }
  gh auth status >/dev/null
  login="$(gh api user --jq .login)"
  if [[ "${login,,}" != "$ACTOR" ]]; then
    echo "Expected GitHub account $ACTOR; authenticated as $login" >&2
    exit 1
  fi
fi

if [[ -z "$WORKDIR" ]]; then
  WORKDIR="$HOME/php-src-gh24492-$(date +%Y%m%d-%H%M%S)"
fi
if [[ -e "$WORKDIR" ]]; then
  echo "Destination already exists; refusing to overwrite: $WORKDIR" >&2
  exit 1
fi
mkdir -p "$(dirname "$WORKDIR")"
git clone --depth=1 --single-branch --branch PHP-8.4 \
  https://github.com/php/php-src.git "$WORKDIR"
SOURCE_SHA="$(git -C "$WORKDIR" rev-parse HEAD)"
echo "Upstream PHP-8.4 HEAD: $SOURCE_SHA"

if [[ "$MODE" == "submit-draft" && "$SOURCE_SHA" != "$REQUIRED_BASE_SHA" ]]; then
  echo "Refusing publication: branch advanced since final NTS/ZTS CI evidence." >&2
  echo "Tested SHA: $REQUIRED_BASE_SHA; current SHA: $SOURCE_SHA" >&2
  echo "Re-run the ForgeBlue current-head CI on this new SHA first." >&2
  exit 1
fi

git -C "$WORKDIR" switch -c "$BRANCH"
git -C "$WORKDIR" apply --check "$PATCH"
git -C "$WORKDIR" apply "$PATCH"
cp "$PHPT_SOURCE" "$WORKDIR/$PHPT_DEST"

git -C "$WORKDIR" add -- \
  ext/standard/base64.c \
  ext/standard/base64.h \
  "$PHPT_DEST"
git -C "$WORKDIR" diff --cached --check

# Protect against accidentally sending lab files or unrelated PHP changes.
expected="$(printf '%s\n' \
  ext/standard/base64.c \
  ext/standard/base64.h \
  "$PHPT_DEST" | LC_ALL=C sort)"
actual="$(git -C "$WORKDIR" diff --cached --name-only | LC_ALL=C sort)"
if [[ "$actual" != "$expected" ]]; then
  echo "Unexpected staged file list:" >&2
  printf '%s\n' "$actual" >&2
  exit 1
fi

printf '\nProposed upstream change (exactly three files):\n'
git -C "$WORKDIR" diff --cached --stat
echo "Working directory: $WORKDIR"
echo "Source SHA: $SOURCE_SHA"
echo "Branch: $BRANCH"

if [[ "$MODE" == "prepare-only" ]]; then
  echo "PREPARE-ONLY complete. No GitHub write action performed."
  echo "Review with: git -C '$WORKDIR' diff --cached"
  exit 0
fi

# Public writes below are explicitly enabled only by --submit-draft.
if ! gh repo view "$ACTOR/php-src" --json nameWithOwner --jq .nameWithOwner >/dev/null 2>&1; then
  gh repo fork php/php-src --clone=false
fi
if ! gh repo view "$ACTOR/php-src" --json nameWithOwner --jq .nameWithOwner >/dev/null 2>&1; then
  echo "Fork is not accessible yet. Retry after GitHub finishes creating it." >&2
  exit 1
fi

git -C "$WORKDIR" config user.name >/dev/null || {
  echo "Please configure git user.name before publishing" >&2; exit 1;
}
git -C "$WORKDIR" config user.email >/dev/null || {
  echo "Please configure git user.email before publishing" >&2; exit 1;
}
git -C "$WORKDIR" commit -m "Fix GH-24492: make userland base64_encode allocation fallible"
git -C "$WORKDIR" remote add fork "git@github.com:$ACTOR/php-src.git"
git -C "$WORKDIR" push -u fork "HEAD:refs/heads/$BRANCH"

gh pr create \
  --repo php/php-src \
  --base PHP-8.4 \
  --head "$ACTOR:$BRANCH" \
  --title "Fix GH-24492: handle base64_encode() soft OOM" \
  --body-file "$LAB_ROOT/docs/upstream/PR_BODY.md" \
  --draft

echo "A draft php/php-src PR was requested. Verify its URL and checks on GitHub."

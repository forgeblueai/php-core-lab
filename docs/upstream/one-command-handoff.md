# One-command PHP upstream draft-PR handoff

As of 2026-10-23, the connected GitHub app cannot create forks and `forgeblueai/php-src` has **not yet been found**. This kit allows the repository owner to perform the GitHub-authenticated steps from their own machine.

**Prerequisites:** Git, an authenticated GitHub CLI (`gh auth status`), configured Git author name/email and GitHub SSH authentication. Use the `forgeblueai` GitHub account. GitHub CLI documentation: https://cli.github.com/manual/gh_repo_fork and https://cli.github.com/manual/gh_pr_create.

## 1. Local verification only (does not publish)

```bash
gh repo clone forgeblueai/php-core-lab
cd php-core-lab
bash scripts/submit_upstream_base64.sh --prepare-only
```

This clones the current `php/php-src:PHP-8.4` HEAD, applies the previously validated patch, stages only the modified C implementation and upstream PHPT, and checks `git diff --cached --check`. The script *never modifies* the working copy of the existing PHP lab project. It does not create a fork, commit, push or open a PR in this mode.

## 2. Publish a draft PR (explicit public action)

```bash
bash scripts/submit_upstream_base64.sh --submit-draft
```

This command checks that GitHub CLI is authenticated as `forgeblueai`, ensures the current PHP-8.4 SHA still matches the fully tested `fc05c9bf2486d3d66593501bf78c1d83c32ecbc5`, uses the existing fork (or creates it if absent), commits and pushes the two-file patch to `forgeblueai/php-src`, and creates a **public Draft PR** against `php/php-src:PHP-8.4`. If PHP-8.4 advanced, it **refuses publication** until new-head tests are run; this prevents citing tests for a different SHA.

The complete draft PR body is kept at [PR_BODY.md](PR_BODY.md).

## What is not covered yet

This is a narrow, upstream-ready candidate, **not** a claim of PHP-project acceptance or a new CVE. Broad test-suite review, non-x86 CPU dispatch, external extension ABI and maintainers' review remain open. The ForgeBlue public laboratory is **not** the actual php-src fork.

The CI workflow `.github/workflows/upstream-kit.yml` invokes only `--prepare-only` and never publishes on behalf of a GitHub runner.

The upstream draft PR has now been created: https://github.com/php/php-src/pull/24618. Do not rerun `--submit-draft` for that already-open branch. This kit is primarily useful for subsequent checked revisions and reproducible dry runs.

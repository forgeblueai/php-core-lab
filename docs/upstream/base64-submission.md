# Upstream submission gate: PHP Base64 OOM regression

Prepared 2026-10-23. Related upstream issue: [php/php-src#24492](https://github.com/php/php-src/issues/24492).

## Branch policy

According to the official PHP [supported versions page](https://www.php.net/supported-versions.php), PHP **8.4** is the lowest branch still receiving regular bug fixes in October 2026. PHP 8.2 and 8.3 receive only security fixes. A public OOM behavior regression is not automatically classed as a security-fix-only backport, so propose the fix on `PHP-8.4` first, then request guidance for older maintenance branches.

**Do not base the upstream PR on release tags** such as `php-8.4.27`. Rebase on the latest active `PHP-8.4` branch, record its exact SHA, and use that as the PR base. The disposable GitHub Actions job `current-branch` checks patch application against the current branch head.

## Patch contract

The prototype [`patches/base64-fallible.patch`](../../patches/base64-fallible.patch) modifies only `ext/standard/base64.c` and `ext/standard/base64.h`:

- `PHP_FUNCTION(base64_encode)` passes a new internal `PHP_BASE64_FALLIBLE` flag.
- Five allocation sites including generic and SIMD implementations propagate a NULL on allocation failure.
- `RETURN_OOM()` is used only at the PHP userland entry point.
- Existing native C callers invoking flags zero or `PHP_BASE64_NO_PADDING` retain non-fallible allocation semantics; changing the exported helper's contract universally is **not** part of this fix.

## Evidence recorded

Original before/after tests on two pinned patched releases: [run 39996126737](https://github.com/forgeblueai/php-core-lab/actions/runs/39996126737).

- Before: 13 MiB input reaches Base64, hard-limit exit 137, no shutdown handler.
- After: normal fatal memory-limit error, exit 255, shutdown handler runs.
- Six upstream Base64 tests and two additional tests passed in both non-ZTS debug builds.
- Eleven selected PHPT tests passed in the patched PHP 8.5.12 ASan/UBSan build. No sanitizer finding in this limited test set; no full security guarantee.

The `upstream-readiness.yml` workflow extends validation to ZTS builds for PHP 8.4.27 and 8.5.12 with SOAP, OpenSSL and iconv enabled, and runs a separate offline integration test for native Base64 consumers. Its results must be checked **before** changing any readiness status.

## Remaining limitations

- Ubuntu x86-64 CI has not demonstrated runtime execution of every SIMD variant, nor ARM64 NEON.
- Only targeted PHPTs, not the full PHP core/extension suite, have been run.
- The full external-extension ABI compatibility contract has not been exhaustively verified.
- The existing upstream PRs [#24548](https://github.com/php/php-src/pull/24548) and [#24596](https://github.com/php/php-src/pull/24596) currently target other paths; check again before submission.

## How to submit after ZTS checks pass

1. Create a personal fork with GitHub's [Fork php/php-src](https://github.com/php/php-src/fork) action. Verify the fork is `forgeblueai/php-src`.
2. Create a **branch from current upstream PHP-8.4**, never directly edit `PHP-8.4`.
3. Apply `patches/base64-fallible.patch` to that branch.
4. Copy `tests/regressions/base64_oom.phpt` to `ext/standard/tests/url/gh24492_base64_encode_oom.phpt`, adapting its expected output to upstream test conventions.
5. Run a debug ZTS and non-ZTS build and relevant PHP tests on the exact upstream branch head.
6. Commit the two C files and focused PHPT. Do not include ForgeBlue lab CI scripts, build artifacts, or unrelated files in the upstream PR.
7. Open an upstream PR against `php/php-src:PHP-8.4`, link GH-24492 and explain that this is deliberately a *partial* fix that retains default C helper semantics.
8. Seek maintainer review before considering wider backports.

The ForgeBlue lab repository is not the PHP upstream repository. An accepted or merged contribution is confirmed only by action in `php/php-src`.

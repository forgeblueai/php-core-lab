# Proposed upstream PHP change: GH-24492 Base64 OOM

**Status:** candidate patch tested on release tags; current PHP-8.4 head test pending at the time this document was authored. This is a fix for a **known publicly discussed OOM regression**, not a new security vulnerability report.

## Target repository

- Upstream: https://github.com/php/php-src
- Base branch: `PHP-8.4` (lowest normal bugfix-maintained branch as of October 2026)
- Related issue: https://github.com/php/php-src/issues/24492
- Adjacent partial fixes: https://github.com/php/php-src/pull/24548 (string allocators) and https://github.com/php/php-src/pull/24596 (URL encode). Both omit Base64.
- Experimental patch: [`patches/base64-fallible.patch`](../../patches/base64-fallible.patch)

## Proposed PR title

`Fix GH-24492: handle base64_encode() soft OOM without changing native helper contracts`

## Proposed description

`base64_encode()` allocates its output through the exported `php_base64_encode_ex()` helper using a non-fallible allocator. When the requested output crosses the soft `memory_limit`, PHP can hit the hard memory limit and terminate the process with exit 137, skipping registered shutdown handlers.

Add `PHP_BASE64_FALLIBLE` as an internal flag set **only** by the PHP userland wrapper. All five generic / SIMD allocation sites use `zend_string_safe_falloc()` and return `NULL` before touching the buffer if allocation fails. The wrapper calls `RETURN_OOM()`. Existing callers passing flags zero or `PHP_BASE64_NO_PADDING` retain non-fallible allocation semantics; this deliberately avoids expanding a nullable C API contract without a full caller audit.

Include `ext/standard/tests/url/gh24492_base64_encode_oom.phpt`, which proves that the input was prepared before the Base64 call, a soft-limit fatal is issued, and the shutdown function executes.

### Previous evidence

- Before/after on pinned PHP 8.4.27 and 8.5.12: https://github.com/forgeblueai/php-core-lab/actions/runs/39996126737
- Debug builds: 8/8 focused tests pass on both versions.
- Clang ASan+UBSan: 11/11 focused tests pass for PHP 8.5.12 (not proof of general memory safety).
- ZTS build and native caller smoke test: https://github.com/forgeblueai/php-core-lab/actions/runs/39999223589 (9/9 on both versions).
- Current-head CI: link to be added **only after a successful run**.

### Remaining review concerns

- Broader extension / PHP test suites and all SIMD CPU runtime variants are not yet exhaustively tested.
- ARM64 NEON is not covered by these x86-64 CI runners.
- Existing external C consumers still assume the non-fallible default result.
- Upstream maintainer review is required for naming and visibility of the new flag.

## Source files to send upstream

1. `ext/standard/base64.c`
2. `ext/standard/tests/url/gh24492_base64_encode_oom.phpt`

No ForgeBlue CI scripts, runner artifacts, or unrelated source files belong in the upstream PR.

## Fork and branch

The fork `forgeblueai/php-src` and draft upstream PR [#24618](https://github.com/php/php-src/pull/24618) now exist. The initial submitted revision still touched `base64.h`; this refinement moves the private flag to `base64.c` and will require an additional reviewed commit on the existing topic branch. Do not open a duplicate PR.

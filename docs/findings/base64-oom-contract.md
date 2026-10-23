# Base64 OOM allocation contract — focused upstream audit

Research snapshot: 2026-10-23. Scope: **observational**; related to already-public [php/php-src#24492](https://github.com/php/php-src/issues/24492).

## Code-path evidence

Source revision: [PHP 8.5.12](https://github.com/php/php-src/tree/136e049ac10b032c83018e65b63b6df858943750).

1. The PHP boundary at [`ext/standard/base64.c` (PHP_FUNCTION(base64_encode))](https://github.com/php/php-src/blob/136e049ac10b032c83018e65b63b6df858943750/ext/standard/base64.c#L1231-L1243) calls `php_base64_encode()` and returns the result without an OOM-specific branch.
2. [Generic `php_base64_encode_ex()`](https://github.com/php/php-src/blob/136e049ac10b032c83018e65b63b6df858943750/ext/standard/base64.c#L1187-L1202) allocates with `zend_string_safe_alloc(..., false)`. The SIMD variants also allocate through `zend_string_safe_alloc`, so a fix must account for CPU-selected paths.
3. [`zend_string_safe_alloc()`](https://github.com/php/php-src/blob/136e049ac10b032c83018e65b63b6df858943750/Zend/zend_string.h) routes to `zend_string_safe_falloc` with `fallible=false`.
4. The exported [C header](https://github.com/php/php-src/blob/136e049ac10b032c83018e65b63b6df858943750/ext/standard/base64.h) establishes a shared helper contract. Consumers include, among others, `ext/standard/password.c`, `ext/soap/php_http.c`, `ext/iconv/iconv.c`, `ext/openssl/openssl_backend_common.c`, and `ext/standard/http_fopen_wrapper.c`. Some immediately dereference the result. A global change to a nullable result **without auditing all callers** is unsafe.

## Relation to existing work

- Upstream [#24548](https://github.com/php/php-src/pull/24548) explicitly excludes Base64 because of internal C caller contracts.
- Upstream [#24596](https://github.com/php/php-src/pull/24596) addresses only user-facing URL encode paths while preserving C helper behavior.
- We are **not** claiming a new PHP vulnerability or proposing a duplicate upstream patch.

## Experiment

`oom_cases/base64_encode_growth.php`: allocate a 14 MiB PHP string and request Base64 output at 16 MiB soft memory limit and 32 MiB hard limit. The runner enforces a 512 MiB process address-space cap and 12-second timeout, records both exit code and shutdown marker, and stores output tails. It runs in the **normal debug build**, not in an ASan build using `USE_ZEND_ALLOC=0`.

Expected pre-run: result **unknown**. Do not infer outcome from code without an independent run. After running, compare exact SHA, exit code, diagnostic text and shutdown behavior on PHP 8.4.27 and PHP 8.5.12.

## Candidate upstream contribution criteria

Only propose an upstream PHPT/patch after verifying the result and confirming no existing PR covers the same function. Any C-level fix must specify whether the public helper preserves non-NULL guarantees; otherwise every call site must be adjusted. If a distinct, undisclosed security issue emerges, stop public reproduction and use PHP's private security reporting channel.

# Base64 fallible-allocation patch candidate

**Status: experimental pending CI.** Targets publicly reported PHP regression [GH-24492](https://github.com/php/php-src/issues/24492); it is not a report of a new vulnerability.

## Candidate design

Existing extension helpers `php_base64_encode()` / `php_base64_encode_ex()` preserve non-fallible allocation semantics with flags 0 (default) and `PHP_BASE64_NO_PADDING` (1).

A new translation-unit-private bit `PHP_BASE64_FALLIBLE` (2) is passed only by `PHP_FUNCTION(base64_encode)`. All five optimized and generic encoding implementations use `zend_string_safe_falloc(..., fallible)` and return NULL if the allocation fails; the userland wrapper then calls `RETURN_OOM()`. The original shared C helper defaults remain unchanged, so existing internal callers are not newly exposed to NULL returns for their normal flags.

The patch covers generic, AVX512-VBMI, AVX512, AVX2/SSSE3, and SSSE3 code paths through five allocation sites; it is important that even CPU-dispatched implementations propagate NULL before dereferencing.

## Verification plan

The `base64-patch.yml` GitHub Actions workflow builds unmodified source at an exact pinned SHA, records seven public OOM probes, applies `patches/base64-fallible.patch`, rebuilds the changed translation units, and records the same probes. The check asserts:
- before: Base64 13 MiB input reaches its encoding call, then hits PHP hard limit (exit 137, no shutdown);
- after: same input reaches encoding call, then reports normal soft OOM (exit 255, shutdown occurs);
- control and four unrelated OOM probes remain unchanged.

A separate patched ASan/UBSan job verifies Base64 correctness on small and binary inputs. It intentionally does not run the OOM comparison under `USE_ZEND_ALLOC=0`.

Do not claim success until the actual CI logs verify all of these conditions. The upstream change is not to be submitted without reviewing whether another PR superseded it.

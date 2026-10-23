## Problem

`base64_encode()` currently uses the non-fallible `php_base64_encode_ex()` allocation contract. A userland call requiring a large output can hit PHP's hard memory limit, terminate with exit 137, and skip the registered shutdown handler. This is part of the previously reported [GH-24492](https://github.com/php/php-src/issues/24492) behavior.

## Fix

Add an implementation-private `PHP_BASE64_FALLIBLE` option (defined in `base64.c`, not the exported header) used **only** by the PHP `base64_encode()` entry point. Make the five generic and x86 SIMD encoding allocation sites honor that option through `zend_string_safe_falloc()`; return `NULL` before dereferencing the failed allocation. The PHP entry point calls `RETURN_OOM()`.

Native C helpers called without the new flag (including existing callers using `PHP_BASE64_NO_PADDING`) preserve their non-fallible behavior, avoiding a breaking change to the exported helper contract.

## Reproduction and tests

The accompanying `ext/standard/tests/url/gh24492_base64_encode_oom.phpt` confirms that the input is constructed before invoking Base64, that memory exhaustion is reported through the soft memory-limit fatal path, and that shutdown handlers run.

Verified experiments from [ForgeBlue PHP Core Lab](https://github.com/forgeblueai/php-core-lab):

- [Pinned PHP 8.4.27 and 8.5.12](https://github.com/forgeblueai/php-core-lab/actions/runs/39996126737): before patch exit 137 without shutdown, after patch exit 255 with soft-OOM message and shutdown.
- [ZTS/extension caller tests](https://github.com/forgeblueai/php-core-lab/actions/runs/39999223589): 9/9 focused PHPTs on both 8.4.27 and 8.5.12, including representative OpenSSL, iconv and SOAP consumers.
- [Current PHP-8.4 HEAD NTS and ZTS](https://github.com/forgeblueai/php-core-lab/actions/runs/40000337560): 9/9 focused PHPTs in each configuration, with before/after OOM verification, based on source SHA `fc05c9bf2486d3d66593501bf78c1d83c32ecbc5`.
- [Patched 8.5.12 sanitizer baseline](https://github.com/forgeblueai/php-core-lab/actions/runs/39996126737): targeted ASan/UBSan tests passed; this is not full memory-safety validation.

This is deliberately a **partial fix**. Existing [#24548](https://github.com/php/php-src/pull/24548) and [#24596](https://github.com/php/php-src/pull/24596) address other allocation paths.

## Limits and review notes

Broader PHP test suites, all CPU-selected SIMD implementations, and ARM64-specific validation remain appropriate follow-up work. This patch does not claim a new security vulnerability or CVE.

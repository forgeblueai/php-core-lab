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

## First CI observation: one result is inconclusive

Initial run [39992715191](https://github.com/forgeblueai/php-core-lab/actions/runs/39992715191) built both pinned releases successfully and recorded `base64_encode_growth` exit code **255** on each; however, the original probe did not print a marker after allocating the 14 MiB input. This means the observation does **not** establish that `base64_encode()` was entered, and does not establish a Base64-specific OOM regression. The comparison job initially failed on a stale test assertion of 10 rows after adding the sixth case; the expected row count is now derived dynamically.

A follow-up experiment introduces `FB_INPUT_READY` before the Base64 call, preserves the original 14 MiB probe, and adds a smaller 13 MiB input case. `scripts/probe.py` records the input-ready marker; the comparison includes it. Do not claim Base64-specific behavior until those markers and diagnostics are evaluated on a completed CI run.

## Verified evidence: second run

CI runs (all jobs passed):
- [Pinned 8.4.27 / 8.5.12 debug builds and evidence comparison, 39993301060](https://github.com/forgeblueai/php-core-lab/actions/runs/39993301060)
- [8.5.12 ASan/UBSan smoke tests, 39993301061](https://github.com/forgeblueai/php-core-lab/actions/runs/39993301061)

Evidence extracted from the actual `oom-results.json` artifacts, not merely workflow exit status:

| Pinned PHP source | Input size | Ready marker | Exit | Shutdown marker | Diagnostic |
| --- | --- | --- | --- | --- | --- |
| 8.4.27 (`00d8bae80154`) | 14 MiB | no | 255 | yes | soft OOM during input construction; tried 14,684,160 bytes |
| 8.4.27 (`00d8bae80154`) | 13 MiB | yes | 137 | no | PHP hard-limit diagnostic; tried 18,178,048 bytes |
| 8.5.12 (`136e049ac10b`) | 14 MiB | no | 255 | yes | soft OOM during input construction; tried 14,684,160 bytes |
| 8.5.12 (`136e049ac10b`) | 13 MiB | yes | 137 | no | PHP hard-limit diagnostic; tried 18,178,048 bytes |

The 13 MiB case prints `FB_INPUT_READY` immediately before calling `base64_encode()`. Thus the **Base64 result allocation**, not source construction, is the failing stage; the output buffer would require about 17.33 MiB before overhead. The 14 MiB case is a control for a *different* failure stage and must not be misclassified as a Base64 allocation result.

The comparison artifact holds **14 rows** across seven bounded cases (including the control). No differences were observed between the two patched release baselines. These observations reproduce behavior linked to **already-public upstream #24492**. They do not establish a new memory corruption or RCE vulnerability, and do not test an upstream patch.

### Caller-contract evidence

| Exported C API caller (8.5.12) | Non-null assumption |
| --- | --- |
| `ext/standard/password.c:56–57` | Immediately reads `ZSTR_LEN(buffer)` |
| `ext/iconv/iconv.c:1112–1114` | Immediately reads `ZSTR_LEN(encoded)` |
| `ext/soap/php_http.c:45–49` | Appends result with `smart_str_append()` |
| `ext/standard/http_fopen_wrapper.c:831–835` | Appends result with `smart_str_append()` |
| `ext/openssl/openssl_backend_common.c:1910–1913` | Replaces owned output buffer with the returned string |

A focused future upstream fix should either preserve the existing non-null C helper contract while adding a separately fallible PHP userland path, or update and verify *every* applicable C caller. The implementation also needs SIMD-aware coverage. These are **design constraints**, not evidence of a newly exploited null-pointer bug.

### Decision

- Confirmed: PHP 8.4.27 and 8.5.12 produce hard-limit process termination in the 13 MiB Base64 case, with no shutdown callback execution.
- Not confirmed: new vulnerability, exploitability, or a PHP core patch that fixes the behavior.
- Action: preserve this evidence in ForgeBlue's research lab and coordinate around the already-open #24492/#24548 work rather than submit a competing unreviewed C patch.

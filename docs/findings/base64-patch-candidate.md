# Base64 fallible-allocation patch — upstream submission status

**Status (2026-11-28): submitted upstream; Ready for Review; awaiting maintainer review.** The authoritative contribution is [php/php-src#24618](https://github.com/php/php-src/pull/24618), addressing the already-public [GH-24492](https://github.com/php/php-src/issues/24492). The PR is open and unmerged. This is not a report of a new vulnerability or CVE.

## Current upstream state

| Field | Value |
|---|---|
| PR | [php/php-src#24618](https://github.com/php/php-src/pull/24618) |
| State | Open; Ready for Review; not merged |
| Base | `PHP-8.4` — `9af71942c6610852dd6350cf19e278628c8b5b60` |
| Head | `fix/gh-24492-base64-soft-oom` — `a9fa71ced100966ef1e3e7c1cc116a06cb5717c2` |
| Changed files | `ext/standard/base64.c`; `ext/standard/tests/url/gh24492_base64_encode_oom.phpt` |
| Requested reviewer | `bukka` |
| Latest retrieved upstream CI run | [45127944786](https://github.com/php/php-src/actions/runs/45127944786) — completed successfully |
| Maintainer acceptance | Not observed; do not infer from CI |

The current upstream run's retrieved job snapshot contained 9 successful jobs and 7 skipped jobs. Some matrix jobs build successfully while their general test steps are skipped; a skipped test job is not test coverage.

## Candidate design now submitted upstream

The submitted patch:

1. Defines `PHP_BASE64_FALLIBLE` privately in `ext/standard/base64.c`.
2. Passes that option only from the PHP userland `PHP_FUNCTION(base64_encode)` entry point.
3. Makes five generic/x86 SIMD allocation sites use `zend_string_safe_falloc(..., fallible)`.
4. Checks for `NULL` before dereferencing the result.
5. Routes failure at the userland boundary through `RETURN_OOM()`.
6. Leaves the public `ext/standard/base64.h` unchanged, preserving the existing exported C helper contract for callers that do not pass the internal flag.

The authoritative implementation and exact diff are in the [upstream PR](https://github.com/php/php-src/pull/24618). Do not treat this lab note as a substitute for the PR diff or current upstream review.

## Original reproduction and control

The pinned research baselines are PHP 8.4.27 (`00d8bae801541db0d95a698e108bb4b1b273fe6e`) and PHP 8.5.12 (`136e049ac10b032c83018e65b63b6df858943750`).

| Probe | Input-ready marker | Observed original-baseline outcome | Meaning |
|---|---:|---|---|
| `base64_encode_growth`, 14 MiB | No | Exit 255; shutdown handler runs; soft memory-limit diagnostic | Input construction fails before Base64; control case |
| `base64_encode_13m`, 13 MiB | Yes | Exit 137; shutdown handler does not run; hard memory-limit diagnostic | Failure occurs after entering Base64 |

The machine-readable original observations are in [base64-oom-observations.json](base64-oom-observations.json). The probe records source SHA, build configuration, return code, input/shutdown markers, hard/soft diagnostic booleans, and bounded stdout/stderr tails. Its limits are 16 MiB PHP memory, 200% hard-limit setting, 512 MiB address-space limit and 12 seconds.

## Verification evidence

### ForgeBlue lab evidence

- [Pinned PHP 8.4.27 / 8.5.12 before-after evidence](https://github.com/forgeblueai/php-core-lab/actions/runs/39996126737): linked in the upstream PR description for the original pinned-baseline behavior.
- [ZTS and selected extension-caller tests](https://github.com/forgeblueai/php-core-lab/actions/runs/39999223589): the PR description records 9/9 focused PHPTs on both pinned versions.
- [PHP-8.4 current-head NTS/ZTS focused PHPT tests](https://github.com/forgeblueai/php-core-lab/actions/runs/40000337560): historical run on the source SHA stated in the PR description at that time.
- [Cross-version comparison/report-generator milestone](https://github.com/forgeblueai/php-core-lab/actions/runs/39993947421) and [ASan/UBSan baseline](https://github.com/forgeblueai/php-core-lab/actions/runs/39993947158).

### Upstream CI

- [Current PR-head CI run 45127944786](https://github.com/php/php-src/actions/runs/45127944786) is associated with the exact PR head `a9fa71ced100966ef1e3e7c1cc116a06cb5717c2` and completed successfully.
- Retrieved job metadata showed 9 successful jobs and 7 skipped jobs. The matrix included Linux x64 release NTS, Linux x32 debug ZTS, Windows x64 ZTS, FreeBSD NTS, macOS ARM64 debug NTS, Alpine x64 ASan debug ZTS and benchmarking. The general PHPT test step was skipped in some jobs, including the macOS ARM64 and Linux ASan entries.
- CI success is not maintainer approval or merge.

### Evidence boundaries

- Earlier local validation recorded full `ext/standard/tests` runs on NTS and ZTS at the then-current PHP-8.4 source revision. Those are historical local results, not tests rerun on 2026-11-28.
- AVX2 runtime was confirmed in the recorded local research. AVX-512 runtime remains unverified.
- The upstream ARM64 job's general test step was skipped; ARM64 runtime test coverage is not established.
- Targeted ASan/UBSan is not exhaustive memory-safety validation. The separate sanitizer baseline uses `USE_ZEND_ALLOC=0`, so it is not directly comparable to the normal Zend allocator OOM path.
- Broader optional-extension and third-party ABI/platform coverage remain limited.
- The current evidence manifest is [base64-soft-oom-pr-24618-2026-11-28.json](../evidence/base64-soft-oom-pr-24618-2026-11-28.json). It uses the exact PR head SHA as the patch-revision identifier; a standalone patch SHA-256 has not been calculated.

## Review and next actions

- Wait for maintainer review on the same PR.
- Respond to any requested changes on PR #24618; do not open a duplicate.
- Extend SIMD, ARM64 or extension-caller validation only when it answers a concrete reviewer or research question.
- Keep the lab issue open until upstream acceptance/merge or an explicit alternative disposition.
- Do not describe this work as a new CVE, an accepted PHP core fix, or a fully comprehensive cross-platform validation.

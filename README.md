# ForgeBlue PHP Core Lab

Reproducible, evidence-first experiments for improving upstream [PHP](https://github.com/php/php-src), focused initially on memory-exhaustion behavior after the October 2026 hardening.

## Scope

- **Upstream source only:** fetch exact Git commit SHAs; never vendor PHP or publish binaries.
- **Safe public baseline:** currently PHP 8.5.12 and PHP 8.4.27, both patched releases.
- **Observation, not exploit validation:** a signal, exit 137, or ASan diagnostic is not automatically a security vulnerability.
- **Responsible disclosure:** keep previously unknown vulnerabilities and exploit details private; see [SECURITY.md](SECURITY.md).

## Run CI

1. Review `.github/workflows/baseline.yml`.
2. Open a pull request from this branch. The pull-request workflow builds two pinned releases on separate **standard** Ubuntu runners.
3. Inspect checks and download the `php-baseline-...` artifacts (build log, PHPT output, machine-readable probe results).
4. After merging to `main`, optionally start **Actions → PHP Core Baseline → Run workflow**.

Each job is capped at 45 minutes, and independent OOM probes have a 12-second timeout and an address-space limit. Artifacts are retained for seven days. CI never pushes commits and has only `contents: read` permissions.

## Source pins

`configs/refs.lock.json` lists the expected SHA for each tested release. The workflow checks the actual `git rev-parse HEAD` against this file before compilation. The tag names are informational; the fetch operation uses an immutable commit SHA.

## Interpreting the evidence

The `tests/*.phpt` files are ordinary functional smoke tests. The `oom_cases/*.php` scripts record how the engine behaves when an allocation request exceeds its memory limits. `scripts/probe.py` records raw exit codes and whether a registered shutdown function executed. Only the non-OOM control case is a pass/fail gate. The other results are **observations**, not CI failures or confirmed bugs.

The workflow deliberately does **not** run unpublished exploit proofs, historical vulnerable PHP versions, or third-party pull-request code with privileged credentials. The separate sanitizer workflow builds the patched PHP 8.5.12 with Clang ASan+UBSan and runs selected PHPT smoke tests using `--asan` and `USE_ZEND_ALLOC=0`. It deliberately does **not** run OOM probes under ASan: ASan reserves large virtual address ranges, invalidating normal RLIMIT_AS constraints. Historical unpatched comparisons remain a separate future stage.

## Provenance

Project: ForgeBlue AI research lab, not affiliated with the PHP Group. Changes intended for PHP itself should be contributed upstream via a focused PHPT or patch after reproducing the issue and checking for duplicate work.

## Evidence comparison and sanitizer CI

- [`baseline.yml`](.github/workflows/baseline.yml) creates two pinned debug artifacts and, only after both pass, downloads them into a third job. `scripts/compare.py` validates the embedded upstream source SHAs and control cases before publishing Markdown, CSV, and JSON.
- [`sanitizers.yml`](.github/workflows/sanitizers.yml) separately compiles PHP 8.5.12 with Clang AddressSanitizer and UndefinedBehaviorSanitizer. It uses `--asan` with system allocation for independent instrumentation; memory-exhaustion behavior here is **not directly comparable** with the normal Zend allocator.
- A green CI run validates only the selected PHPT tests. It does not prove absence of other security bugs. Any potential new security issue follows the private reporting policy.

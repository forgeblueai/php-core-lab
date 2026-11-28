# ForgeBlue PHP Core Lab

Evidence-first, reproducible experiments for PHP internals and upstream PHP contributions. The current focused case study investigates the allocation contract of `base64_encode()` under memory exhaustion, in connection with the already-public [PHP issue GH-24492](https://github.com/php/php-src/issues/24492).

This is an independent research lab and is **not affiliated with the PHP Group**.

## Current status — 2026-11-28

- **Research result:** the Base64 allocation behavior was reproduced on pinned PHP 8.4.27 and 8.5.12 source revisions. The 13 MiB input reaches the Base64 call and then triggers a hard-limit exit; the 14 MiB case is a distinct control that fails while constructing the input, before Base64 is called.
- **Upstream contribution:** [php/php-src#24618 — Fix GH-24492: handle base64_encode() soft OOM](https://github.com/php/php-src/pull/24618) is **open, Ready for Review, and unmerged**.
- **Current PR base:** `PHP-8.4` at `9af71942c6610852dd6350cf19e278628c8b5b60`.
- **Current PR head:** `a9fa71ced100966ef1e3e7c1cc116a06cb5717c2`.
- **Latest retrieved upstream CI run:** [45127944786](https://github.com/php/php-src/actions/runs/45127944786) completed successfully on the PR head. Its retrieved job snapshot contained 9 successful jobs and 7 skipped jobs. A successful CI run is not maintainer approval or merge.
- **Requested reviewer:** `bukka`. No maintainer acceptance or merge is claimed.

The proposed fix keeps `PHP_BASE64_FALLIBLE` private to `ext/standard/base64.c`, makes the five generic/x86 SIMD allocation sites propagate allocation failure, and returns PHP's soft OOM path from the userland `base64_encode()` entry point. The public `base64.h` is unchanged. See the [upstream PR](https://github.com/php/php-src/pull/24618) for the authoritative patch and review state.

## Scope and safety

- **Upstream source only:** fetch exact Git commit SHAs; do not vendor PHP or publish binaries.
- **Pinned research baselines:** PHP 8.4.27 and PHP 8.5.12 are the versions recorded in `configs/refs.lock.json`. They are reproducible research snapshots, not a claim that this is a complete current PHP support matrix.
- **Observation, not exploit validation:** exit 137, memory exhaustion, or an ASan diagnostic is not automatically a security vulnerability.
- **Responsible disclosure:** keep previously unknown vulnerabilities and exploit details private; see [SECURITY.md](SECURITY.md).
- **No unreviewed public claims:** this work concerns the already-public GH-24492 behavior and does not claim a new CVE.

## Evidence and reproducibility

- [Base64 OOM allocation contract](docs/findings/base64-oom-contract.md) — source-call analysis, caller contract, experiment design and observed behavior.
- [Machine-readable observations](docs/findings/base64-oom-observations.json) — compact, pinned evidence for the original 14 MiB and 13 MiB probes.
- [Base64 fallible-allocation patch status](docs/findings/base64-patch-candidate.md) — current upstream submission state and limitations.
- [Evidence manifest — 2026-11-28](docs/evidence/base64-soft-oom-pr-24618-2026-11-28.json) — exact PR refs, pinned baseline SHAs, linked CI evidence, known limits and unverified fields.

### Important distinction between the two OOM probes

| Probe | Input reaches Base64? | Observed outcome on the original pinned baselines | Interpretation |
|---|---:|---|---|
| `base64_encode_growth` (14 MiB) | No | Exit 255; shutdown runs; soft memory-limit diagnostic | Input-construction OOM control |
| `base64_encode_13m` (13 MiB) | Yes | Exit 137; shutdown does not run; hard memory-limit diagnostic | Failure occurs after entering Base64 |

The `FB_INPUT_READY` marker is essential: without it, a failed process does not prove that the Base64 allocation was reached.

### Evidence workflow

The baseline workflow verifies the exact PHP source SHA from `configs/refs.lock.json`, builds a debug CLI, runs focused PHPT smoke tests, and executes bounded probes. The probe records source SHA, build configuration, process return code, shutdown/input markers, hard/soft diagnostics and bounded stdout/stderr tails. Its policy includes a 16 MiB PHP memory limit, a 200% hard-limit setting, a 512 MiB address-space cap and a 12-second timeout.

The comparison generator validates pinned source SHAs and the full expected case set, then produces Markdown, CSV and JSON outputs. Four unit tests cover report generation, wrong SHA rejection, missing-snapshot rejection and control-case failure. Workflow artifacts are retained for seven days; the committed observations file and evidence manifest preserve the key durable facts, but they do not replace the original full logs.

The separate sanitizer workflow builds PHP 8.5.12 with Clang ASan+UBSan. It uses `USE_ZEND_ALLOC=0`; therefore its sanitizer smoke tests are **not** a direct reproduction of normal Zend allocator OOM behavior.

## Upstream contribution evidence

The following historical ForgeBlue lab runs are linked from the upstream PR description:

- [Pinned PHP 8.4.27 / 8.5.12 before/after evidence](https://github.com/forgeblueai/php-core-lab/actions/runs/39996126737).
- [ZTS and representative extension-caller tests](https://github.com/forgeblueai/php-core-lab/actions/runs/39999223589).
- [PHP-8.4 current-head NTS/ZTS focused PHPT tests at the then-tested source revision](https://github.com/forgeblueai/php-core-lab/actions/runs/40000337560).
- [Current upstream PR CI run on head `a9fa71c`](https://github.com/php/php-src/actions/runs/45127944786).

The original cross-version report-generation and sanitizer milestone is also recorded in [lab CI run 39993947421](https://github.com/forgeblueai/php-core-lab/actions/runs/39993947421) and [sanitizer run 39993947158](https://github.com/forgeblueai/php-core-lab/actions/runs/39993947158).

## Run CI

1. Review the relevant workflow under `.github/workflows/`.
2. Open a pull request from the branch to run its path-filtered checks, or use **Actions → Run workflow** when an authorized manual run is intended.
3. Inspect the exact source SHA, build configuration, test summary and artifacts for that run.
4. Treat skipped jobs as untested; do not infer runtime coverage from a successful build-only job.

The baseline and sanitizer workflows use read-only `contents` permissions and disable checkout credential persistence. Artifacts are retained for seven days.

## Current limitations

- The upstream PR is not merged and maintainer acceptance remains pending.
- The pinned lab matrix contains PHP 8.4.27 and 8.5.12; PHP 8.6 is not yet a pinned baseline in `configs/refs.lock.json`.
- AVX2 execution was confirmed in the recorded local research; AVX-512 runtime behavior remains unverified.
- The latest upstream matrix includes an ARM64 build job, but its general PHPT test step was skipped; do not describe that as ARM64 runtime test coverage.
- The evidence does not establish exhaustive optional-extension, third-party ABI, operating-system, CPU-dispatch or memory-safety coverage.
- No patch SHA-256 is recorded in the current manifest; the exact upstream head SHA is used as the immutable patch-revision identifier.

## Contribution and review policy

Changes intended for PHP itself belong in a focused upstream PR after reproducing the behavior, checking related work and reviewing all relevant C callers. Continue review on [php/php-src#24618](https://github.com/php/php-src/pull/24618); do not create a duplicate PR. Update public status only when upstream metadata changes.

A green CI result validates only the checks that actually ran. It does not prove absence of other defects, maintainer approval, or upstream acceptance.

# Contributing

Please propose a narrowly scoped, reproducible PHP core observation or regression test.

Before opening a PR, pin a PHP source revision, identify the upstream issue/PR if any, include expected and observed behavior, and distinguish runtime exit codes from memory-safety evidence.

No unpublished vulnerability details in public PRs. Prefer PHPT for upstream-relevant tests. Keep `GITHUB_TOKEN` read-only; never introduce `pull_request_target` for running untrusted code.

This repo contains original experiment scripts; upstream PHP retains its own license and contribution requirements.

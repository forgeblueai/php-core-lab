# Security policy

This is a **public reproducibility harness**, not a place to report undisclosed PHP vulnerabilities.

- For a newly discovered PHP security issue, follow the upstream PHP project’s private security-reporting process: https://github.com/php/php-src/security/advisories/new
- Do not upload weaponized payloads, credentials, non-public exploit traces, or unpatched security PoCs to this repository, pull requests, or CI artifacts.
- Do not test third-party infrastructure. Experiments run only on disposable, isolated GitHub-hosted runners.
- Existing GH-24492 behavior probes are bounded, use fixed inputs, and do not accept external input.
- Public discussions of already disclosed behavior are not a substitute for coordinated disclosure of a new root cause.

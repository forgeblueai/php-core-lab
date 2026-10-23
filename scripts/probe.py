#!/usr/bin/env python3
"""Bounded observations of public PHP OOM regressions, not exploit tests."""
import argparse
import datetime
import json
import re
import resource
import subprocess
from pathlib import Path

CASES = (
    "control",
    "sprintf_width",
    "pack_pad",
    "bin2hex_growth",
    "base64_encode_growth",
    "base64_encode_13m",
    "urlencode_growth",
)
AS_LIMIT = 512 * 1024 * 1024
TIMEOUT = 12


def restrict_address_space():
    resource.setrlimit(resource.RLIMIT_AS, (AS_LIMIT, AS_LIMIT))
    resource.setrlimit(resource.RLIMIT_CORE, (0, 0))


def observe(binary: Path, script: Path):
    command = [
        str(binary), "-n",
        "-d", "memory_limit=16M",
        "-d", "memory_hard_limit_percent=200",
        str(script),
    ]
    try:
        result = subprocess.run(
            command,
            capture_output=True,
            text=True,
            errors="replace",
            timeout=TIMEOUT,
            preexec_fn=restrict_address_space,
        )
        text = result.stdout + "\n" + result.stderr
        return {
            "returncode": result.returncode,
            "begin_seen": "FB_BEGIN" in result.stdout,
            "input_ready_seen": "FB_INPUT_READY" in result.stdout,
            "shutdown_seen": "FB_SHUTDOWN" in result.stdout,
            "hard_limit_message": "Hard memory limit" in text,
            "soft_limit_message": "Allowed memory size" in text,
            "stdout_tail": result.stdout[-1500:],
            "stderr_tail": result.stderr[-1500:],
            "classification": (
                "HARD_LIMIT_EXIT" if result.returncode == 137 and "Hard memory limit" in text
                else "NORMAL_COMPLETION" if result.returncode == 0
                else "SIGNAL" if result.returncode < 0
                else "OTHER_NONZERO_EXIT"
            ),
        }
    except subprocess.TimeoutExpired as error:
        return {
            "returncode": None,
            "classification": "TIMEOUT",
            "timeout_seconds": TIMEOUT,
            "stdout_tail": str(error.stdout or b"")[-1500:],
            "stderr_tail": str(error.stderr or b"")[-1500:],
        }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--php", required=True, type=Path)
    parser.add_argument("--cases", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--snapshot", required=True)
    parser.add_argument("--source-sha-file", required=True, type=Path)
    parser.add_argument("--build-config", required=True)
    args = parser.parse_args()
    sha = args.source_sha_file.read_text(encoding="utf-8").strip()
    if not re.fullmatch(r"[0-9a-f]{40}", sha):
        parser.error("invalid pinned source SHA")
    results = {}
    for case in CASES:
        script = args.cases / (case + ".php")
        if not script.is_file():
            parser.error("missing probe: " + str(script))
        results[case] = observe(args.php.resolve(), script.resolve())
        print(case, results[case]["classification"], "exit", results[case].get("returncode"))

    payload = {
        "schema": 1,
        "timestamp_utc": datetime.datetime.now(datetime.timezone.utc).isoformat(),
        "snapshot": args.snapshot,
        "source_sha": sha,
        "build_config": args.build_config,
        "php_binary": str(args.php),
        "policy": {"memory_limit": "16M", "hard_limit_percent": 200,
                   "address_space_limit_bytes": AS_LIMIT, "timeout_seconds": TIMEOUT},
        "results": results,
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    control = results["control"]
    if control.get("returncode") != 0 or not control.get("shutdown_seen"):
        raise SystemExit("Control probe failed; OOM observations cannot be trusted.")
    print("Control passed; OOM classifications are observational, not vulnerability claims.")


if __name__ == "__main__":
    main()

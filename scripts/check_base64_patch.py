#!/usr/bin/env python3
"""Gate a proposed fix against observed pre/post behavior, not mere process exit."""
import argparse
import json
from pathlib import Path


def check(before, after):
    if before["source_sha"] != after["source_sha"]:
        raise AssertionError("source SHA changed between runs")
    if before["snapshot"] != after["snapshot"]:
        raise AssertionError("PHP snapshot changed between runs")
    name = "base64_encode_13m"
    old = before["results"][name]
    new = after["results"][name]
    if not (old.get("returncode") == 137
            and old.get("classification") == "HARD_LIMIT_EXIT"
            and old.get("hard_limit_message") is True
            and old.get("input_ready_seen") is True
            and old.get("shutdown_seen") is False):
        raise AssertionError(f"baseline does not reproduce existing hard-limit behavior: {old}")
    if not (new.get("returncode") == 255
            and new.get("soft_limit_message") is True
            and new.get("input_ready_seen") is True
            and new.get("shutdown_seen") is True
            and new.get("hard_limit_message") is False):
        raise AssertionError(f"patched Base64 OOM path not restored to normal fatal/shutdown: {new}")
    for case in ("control", "sprintf_width", "pack_pad", "bin2hex_growth", "urlencode_growth"):
        original = before["results"][case]
        patched = after["results"][case]
        if any(original.get(field) != patched.get(field)
               for field in ("classification", "returncode", "shutdown_seen")):
            raise AssertionError(f"unrelated OOM probe changed: {case}")
    return {
        "result": "PASS", "snapshot": before["snapshot"],
        "source_sha": before["source_sha"], "case": name,
        "before": {"exit": old["returncode"], "shutdown": old["shutdown_seen"]},
        "after": {"exit": new["returncode"], "shutdown": new["shutdown_seen"]},
        "limits": before["policy"],
    }


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--before", type=Path, required=True)
    p.add_argument("--after", type=Path, required=True)
    p.add_argument("--output", type=Path, required=True)
    args = p.parse_args()
    a = json.loads(args.before.read_text(encoding="utf-8"))
    b = json.loads(args.after.read_text(encoding="utf-8"))
    result = check(a, b)
    args.output.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print("Verified Base64 allocation boundary:", json.dumps(result))


if __name__ == "__main__":
    main()

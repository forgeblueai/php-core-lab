#!/usr/bin/env python3
"""Produce a traceable comparison of *observed* OOM behavior, not vulnerability claims."""
import argparse
import csv
import json
from pathlib import Path

CASES = ("control", "sprintf_width", "pack_pad", "bin2hex_growth", "urlencode_growth")
HEADERS = ("snapshot", "source_sha", "build_config", "case", "classification",
           "returncode", "shutdown_seen", "hard_limit_message", "soft_limit_message")


def build_report(input_dir: Path, lock_path: Path, output_dir: Path) -> dict:
    lock = json.loads(lock_path.read_text(encoding="utf-8"))
    expected = lock["entries"]
    records = {}
    for file in sorted(input_dir.glob("*/oom-results.json")):
        entry = json.loads(file.read_text(encoding="utf-8"))
        snapshot = entry["snapshot"]
        if snapshot not in expected:
            raise ValueError(f"unknown snapshot {snapshot}")
        if snapshot in records:
            raise ValueError(f"duplicate evidence for {snapshot}")
        if entry.get("source_sha") != expected[snapshot]:
            raise ValueError(f"SHA mismatch for {snapshot}: {entry.get('source_sha')}")
        if entry.get("build_config") != "debug":
            raise ValueError(f"unexpected build config for {snapshot}")
        if not all(c in entry["results"] for c in CASES):
            raise ValueError(f"incomplete case set for {snapshot}")
        ctl = entry["results"]["control"]
        if ctl.get("returncode") != 0 or not ctl.get("shutdown_seen"):
            raise ValueError(f"invalid control case for {snapshot}")
        records[snapshot] = entry
    if set(records) != set(expected):
        raise ValueError(f"missing snapshots: {sorted(set(expected) - set(records))}")

    snapshots = list(expected)
    rows = []
    for snapshot in snapshots:
        entry = records[snapshot]
        for case in CASES:
            test = entry["results"][case]
            row = {"snapshot": snapshot, "source_sha": entry["source_sha"],
                   "build_config": entry["build_config"], "case": case,
                   "classification": test.get("classification"),
                   "returncode": test.get("returncode"),
                   "shutdown_seen": test.get("shutdown_seen"),
                   "hard_limit_message": test.get("hard_limit_message"),
                   "soft_limit_message": test.get("soft_limit_message")}
            rows.append(row)

    output_dir.mkdir(parents=True, exist_ok=True)
    with (output_dir / "oom-comparison.csv").open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=HEADERS)
        writer.writeheader()
        writer.writerows(rows)

    differences = []
    matrix = []
    for case in CASES:
        values = [(records[s]["results"][case].get("classification"),
                   records[s]["results"][case].get("returncode"),
                   records[s]["results"][case].get("shutdown_seen")) for s in snapshots]
        matrix.append((case, values))
        if len(set(values)) > 1:
            differences.append(case)
    summary = {"schema": 1, "snapshots": {s: expected[s] for s in snapshots},
               "differences": differences, "rows": rows,
               "interpretation": "observations only; no vulnerability claim"}
    (output_dir / "oom-comparison.json").write_text(
        json.dumps(summary, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

    markdown = [
        "# Pinned PHP OOM observation comparison",
        "",
        "**These measurements are not proof of a newly discovered vulnerability.**",
        "",
        "Versions and exact source SHAs:",
        *[f"- `{s}`: `{expected[s]}`" for s in snapshots],
        "",
        "| Probe | " + " | ".join(snapshots) + " |",
        "| --- | " + " | ".join(["---"] * len(snapshots)) + " |",
    ]
    for case, values in matrix:
        cells = [f"{c} (exit {code}; shutdown {shutdown})" for c, code, shutdown in values]
        markdown.append("| " + case + " | " + " | ".join(cells) + " |")
    markdown += ["", f"Behavioral differences: {', '.join(differences) if differences else 'none observed'}",
                 "", "For each case, 'exit 137' means hard limit only when the corresponding",
                 "JSON evidence also contains a PHP hard-limit diagnostic.",
                 "No historical unpatched release or candidate upstream patch is included.",
                 ""]
    (output_dir / "oom-comparison.md").write_text("\n".join(markdown), encoding="utf-8")
    return summary


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--input-dir", required=True, type=Path)
    p.add_argument("--lock", required=True, type=Path)
    p.add_argument("--output-dir", required=True, type=Path)
    args = p.parse_args()
    summary = build_report(args.input_dir, args.lock, args.output_dir)
    print("Validated", ", ".join(summary["snapshots"]),
          "| changed cases:", summary["differences"])


if __name__ == "__main__":
    main()

#!/usr/bin/env bash
# report.sh — Aggregate benchmark results and generate a Markdown report.
#
# Usage:
#   ./report.sh --input ./results --output benchmark-report.md
#
# Requires python3 with stdlib only (statistics module).

set -euo pipefail

INPUT_DIR="./results"
OUTPUT_FILE="benchmark-report.md"

while [[ $# -gt 0 ]]; do
  case $1 in
    --input)  INPUT_DIR="$2";   shift 2 ;;
    --output) OUTPUT_FILE="$2"; shift 2 ;;
    *) echo "Unknown argument: $1" >&2; exit 1 ;;
  esac
done

if [[ ! -d "${INPUT_DIR}" ]]; then
  echo "ERROR: Input directory '${INPUT_DIR}' not found." >&2
  exit 1
fi

echo "==> Generating report from '${INPUT_DIR}' -> '${OUTPUT_FILE}'..."

export INPUT_DIR OUTPUT_FILE
python3 - <<'EOF'
import os, json, statistics
from pathlib import Path
from datetime import datetime, timezone

input_dir = os.environ["INPUT_DIR"]
output_file = os.environ["OUTPUT_FILE"]

# Collect all JSONL data
cold_starts = {}   # runtime -> [ms, ...]
task_latencies = {}  # (runtime, task) -> [ms, ...]
task_errors = {}   # (runtime, task) -> count

for round_dir in sorted(Path(input_dir).glob("round-*")):
    for runtime_dir in sorted(round_dir.iterdir()):
        if not runtime_dir.is_dir():
            continue
        runtime = runtime_dir.name
        cold_starts.setdefault(runtime, [])
        # Cold start
        cs_file = runtime_dir / "cold-start.jsonl"
        if cs_file.exists():
            for line in cs_file.read_text().splitlines():
                if line.strip():
                    d = json.loads(line)
                    cold_starts[runtime].append(d["cold_start_ms"])
        # Tasks
        tasks_file = runtime_dir / "tasks.jsonl"
        if tasks_file.exists():
            for line in tasks_file.read_text().splitlines():
                if line.strip():
                    d = json.loads(line)
                    key = (runtime, d["task"])
                    task_latencies.setdefault(key, []).append(d["latency_ms"])
                    if d.get("exit_code", 0) != 0:
                        task_errors[key] = task_errors.get(key, 0) + 1


def pct(data, p):
    if not data:
        return "N/A"
    return int(statistics.quantiles(sorted(data), n=100)[p - 1])


runtimes = list(cold_starts.keys())
tasks = sorted({t for (_, t) in task_latencies})

lines = []
lines.append("# Agent Sandbox Runtime Benchmark Report")
ts = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
lines.append(f"\nGenerated: {ts}\n")
lines.append(f"Input: `{input_dir}`  \n")

# Cold start table
lines.append("\n## Cold-Start Latency\n")
lines.append("| Runtime | P50 (ms) | P95 (ms) | P99 (ms) | Samples |")
lines.append("| --- | --- | --- | --- | --- |")
for rt in runtimes:
    data = cold_starts.get(rt, [])
    lines.append(
        f"| {rt} | {pct(data, 50)} | {pct(data, 95)} | {pct(data, 99)} | {len(data)} |"
    )

# Task latency tables
for task in tasks:
    lines.append(f"\n## Task: `{task}`\n")
    lines.append("| Runtime | P50 (ms) | P95 (ms) | P99 (ms) | Errors | Samples |")
    lines.append("| --- | --- | --- | --- | --- | --- |")
    for rt in runtimes:
        key = (rt, task)
        data = task_latencies.get(key, [])
        errs = task_errors.get(key, 0)
        total = len(data)
        err_rate = f"{errs}/{total} ({100*errs/max(total,1):.1f}%)" if total else "N/A"
        lines.append(
            f"| {rt} | {pct(data, 50)} | {pct(data, 95)} | {pct(data, 99)}"
            f" | {err_rate} | {total} |"
        )

# Write output
Path(output_file).write_text("\n".join(lines) + "\n")
print(f"Report written to: {output_file}")
EOF

echo "==> Done."

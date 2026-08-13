#!/usr/bin/env python3
"""Aggregate and verify #285 JSONL output without cluster access."""

from __future__ import annotations

import argparse
import datetime as dt
import json
import math
import pathlib
import statistics
import sys
from typing import Any


FAILURES = {
    "quota-insufficient",
    "no-matching-slice",
    "admitted-unschedulable",
    "wait-for-pods-ready",
}
RATIOS = {"short": 60, "long": 10, "inference": 10, "mixed": 20}
LIFECYCLE_INTERVALS = {
    "queue_wait": ("created_at", "quota_reserved_at"),
    "admission": ("created_at", "admitted_at"),
    "claim_create": ("admitted_at", "claim_created_at"),
    "claim_allocate": ("claim_created_at", "claim_allocated_at"),
    "pod_schedule": ("claim_reserved_at", "pod_scheduled_at"),
    "simulated_ready": ("pod_scheduled_at", "ready_at"),
    "claim_reclaim": ("ended_at", "claim_deleted_at"),
}


def timestamp(value: str | None) -> dt.datetime | None:
    return dt.datetime.fromisoformat(value.replace("Z", "+00:00")) if value else None


def duration(record: dict[str, Any], start: str, end: str) -> float | None:
    first = timestamp(record.get(start))
    last = timestamp(record.get(end))
    if not first or not last:
        return None
    return max((last - first).total_seconds(), 0.0)


def percentile(values: list[float], quantile: float) -> float | None:
    if not values:
        return None
    ordered = sorted(values)
    position = (len(ordered) - 1) * quantile
    lower = math.floor(position)
    upper = math.ceil(position)
    if lower == upper:
        return ordered[lower]
    return ordered[lower] + (ordered[upper] - ordered[lower]) * (position - lower)


def distribution(values: list[float]) -> dict[str, float | int | None]:
    return {
        "count": len(values),
        "p50_seconds": percentile(values, 0.50),
        "p95_seconds": percentile(values, 0.95),
        "p99_seconds": percentile(values, 0.99),
    }


def read_jsonl(path: pathlib.Path) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    records = []
    for line_number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
        if not line.strip():
            continue
        try:
            records.append(json.loads(line))
        except json.JSONDecodeError as error:
            raise ValueError(f"{path}:{line_number}: {error}") from error
    return records


def cv(values: list[float]) -> float | None:
    if not values:
        return None
    average = statistics.fmean(values)
    if average == 0:
        return 0.0
    return statistics.pstdev(values) / average


def sample_idle_fraction(samples: list[dict[str, Any]]) -> float:
    backlog = [
        float(sample["idle_fraction_while_admitted_pending"])
        for sample in samples
        if int(sample.get("admitted_pending", 0)) > 0
    ]
    return statistics.fmean(backlog) if backlog else 0.0


def event_time(item: dict[str, Any]) -> dt.datetime | None:
    metadata = item.get("metadata", {})
    return timestamp(
        item.get("eventTime")
        or item.get("deprecatedLastTimestamp")
        or metadata.get("creationTimestamp")
    )


def mixed_reclaim_events(path: pathlib.Path, records: list[dict[str, Any]]) -> int:
    if not path.exists():
        return 0
    payload = json.loads(path.read_text(encoding="utf-8") or "{}")
    windows = [
        (timestamp(record.get("created_at")), timestamp(record.get("ended_at")))
        for record in records
        if record.get("scenario") == "mixed"
    ]
    count = 0
    for item in payload.get("items", []):
        involved = item.get("involvedObject") or item.get("regarding") or {}
        observed = event_time(item)
        if (
            item.get("reason") in {"Preempted", "EvictedDueToPreempted"}
            and involved.get("kind") == "Workload"
            and involved.get("namespace") == "dra-kueue-tenant-a"
            and "mixed-low" in involved.get("name", "")
            and observed
            and any(start and end and start <= observed <= end for start, end in windows)
        ):
            count += 1
    return count


def finite_percent(value: float | None) -> str:
    return "n/a" if value is None else f"{value:.2%}"


def finite_seconds(value: float | None) -> str:
    return "n/a" if value is None else f"{value:.3f}s"


def profile_summary(root: pathlib.Path, profile: str, rounds: int, expected: int) -> tuple[dict[str, Any], list[str]]:
    failures: list[str] = []
    round_summaries: list[dict[str, Any]] = []
    all_records: list[dict[str, Any]] = []
    critical_p95s: dict[str, list[float]] = {
        "kueue_end_to_end": [],
        **{name: [] for name in LIFECYCLE_INTERVALS},
    }
    for round_number in range(1, rounds + 1):
        round_dir = root / "runs" / profile / f"round-{round_number}"
        records = read_jsonl(round_dir / "workloads.jsonl")
        samples = read_jsonl(round_dir / "samples.jsonl")
        if not records:
            failures.append(f"{profile} round {round_number}: no workload records")
            continue
        all_records.extend(records)
        main = [record for record in records if record.get("path") == "kueue" and record.get("scenario") in RATIOS]
        direct = [record for record in records if record.get("path") == "direct" and record.get("scenario") == "short"]
        failure_records = [record for record in records if record.get("scenario") in FAILURES]
        smoke = [record for record in records if record.get("scenario") == "extended-smoke"]

        if len(main) != expected:
            failures.append(f"{profile} round {round_number}: expected {expected} main workloads, observed {len(main)}")
        for scenario, ratio in RATIOS.items():
            observed = sum(record.get("scenario") == scenario for record in main)
            wanted = expected * ratio // 100
            if observed != wanted:
                failures.append(f"{profile} round {round_number}: {scenario} expected {wanted}, observed {observed}")
        expected_direct = expected * RATIOS["short"] // 100
        if len(direct) != expected_direct:
            failures.append(f"{profile} round {round_number}: direct baseline expected {expected_direct}, observed {len(direct)}")
        direct_required = (
            "created_at",
            "claim_created_at",
            "claim_allocated_at",
            "claim_reserved_at",
            "pod_scheduled_at",
            "ready_at",
            "ended_at",
            "claim_deleted_at",
        )
        for record in direct:
            missing = [field for field in direct_required if not record.get(field)]
            if record.get("result") != "success" or missing:
                failures.append(
                    f"{profile} round {round_number}: direct {record.get('workload')} incomplete lifecycle "
                    f"({', '.join(missing)})"
                )
        if len(smoke) != 1 or smoke[0].get("result") != "success":
            failures.append(f"{profile} round {round_number}: extended-resource smoke did not succeed exactly once")
        observed_failure_names = {record.get("scenario") for record in failure_records}
        if observed_failure_names != FAILURES:
            failures.append(
                f"{profile} round {round_number}: failure suite mismatch: {sorted(observed_failure_names)}"
            )
        for record in failure_records:
            if record.get("result") != "expected_failure" or not record.get("quota_released_at"):
                failures.append(
                    f"{profile} round {round_number}: failure {record.get('scenario')} lacks expected reason/requeue/quota release"
                )
            scenario = record.get("scenario")
            if scenario == "quota-insufficient" and record.get("quota_reserved_at"):
                failures.append(f"{profile} round {round_number}: quota-insufficient was unexpectedly admitted")
            if scenario in {"no-matching-slice", "admitted-unschedulable", "wait-for-pods-ready"}:
                if (
                    not record.get("admitted_at")
                    or int(record.get("evictions", 0)) < 1
                    or int(record.get("requeues", 0)) < 1
                ):
                    failures.append(
                        f"{profile} round {round_number}: failure {scenario} lacks admission and requeue evidence"
                    )
            if scenario == "wait-for-pods-ready" and int(record.get("requeues", 0)) < 2:
                failures.append(
                    f"{profile} round {round_number}: wait-for-pods-ready observed fewer than two requeues"
                )

        for record in main:
            required = (
                "created_at",
                "quota_reserved_at",
                "admitted_at",
                "claim_created_at",
                "claim_allocated_at",
                "claim_reserved_at",
                "pod_scheduled_at",
                "ready_at",
                "ended_at",
                "claim_deleted_at",
                "quota_released_at",
            )
            missing = [field for field in required if not record.get(field)]
            if record.get("result") != "success" or missing:
                failures.append(
                    f"{profile} round {round_number}: {record.get('workload')} incomplete lifecycle ({', '.join(missing)})"
                )

        direct_latency = [value for record in direct if (value := duration(record, "created_at", "ready_at")) is not None]
        kueue_short = [record for record in main if record.get("scenario") == "short"]
        kueue_latency = [value for record in kueue_short if (value := duration(record, "created_at", "ready_at")) is not None]
        lifecycle = {
            name: distribution(
                [
                    value
                    for record in main
                    if (value := duration(record, start, end)) is not None
                ]
            )
            for name, (start, end) in LIFECYCLE_INTERVALS.items()
        }
        direct_p95 = percentile(direct_latency, 0.95)
        kueue_p95 = percentile(kueue_latency, 0.95)
        overhead_limit = max((direct_p95 or 0.0) * 0.25, 3.0)
        overhead = None if direct_p95 is None or kueue_p95 is None else kueue_p95 - direct_p95
        if overhead is None or overhead > overhead_limit:
            failures.append(
                f"{profile} round {round_number}: Kueue P95 overhead {overhead} exceeds {overhead_limit:.3f}s"
            )
        idle_fraction = sample_idle_fraction(samples)
        if idle_fraction > 0.15:
            failures.append(
                f"{profile} round {round_number}: idle device fraction {idle_fraction:.3%} exceeds 15%"
            )
        sampled_preemptions = sum(
            bool(record.get("preempted")) for record in main if record.get("scenario") == "mixed"
        )
        durable_preemptions = mixed_reclaim_events(round_dir / "kubernetes-events.json", main)
        preemptions = max(sampled_preemptions, durable_preemptions)
        if preemptions == 0:
            failures.append(f"{profile} round {round_number}: mixed suite did not observe owner reclaim/preemption")

        if kueue_p95 is not None:
            critical_p95s["kueue_end_to_end"].append(kueue_p95)
        for name, item in lifecycle.items():
            value = item["p95_seconds"]
            if value is not None:
                critical_p95s[name].append(float(value))
        failure_reasons = {
            str(record.get("scenario")): record.get("reason")
            for record in failure_records
        }
        weighted_share_max: dict[str, float] = {}
        for sample in samples:
            for queue, share in (sample.get("weighted_shares") or {}).items():
                if share is not None:
                    weighted_share_max[queue] = max(weighted_share_max.get(queue, 0.0), float(share))
        round_summaries.append(
            {
                "round": round_number,
                "main_count": len(main),
                "success_rate": sum(record.get("result") == "success" for record in main) / len(main) if main else 0.0,
                "direct_end_to_end": distribution(direct_latency),
                "kueue_end_to_end": distribution(kueue_latency),
                "lifecycle": lifecycle,
                "p95_overhead_seconds": overhead,
                "p95_overhead_limit_seconds": overhead_limit,
                "idle_fraction_while_admitted_pending": idle_fraction,
                "preemptions": preemptions,
                "evictions": sum(int(record.get("evictions", 0)) for record in main),
                "requeues": sum(int(record.get("requeues", 0)) for record in main),
                "failure_reasons": failure_reasons,
                "weighted_share_max": weighted_share_max,
            }
        )

    critical_cv = {f"{name}_p95": cv(values) for name, values in critical_p95s.items()}
    acceptance_cv = {
        name: critical_cv[name]
        for name in ("kueue_end_to_end_p95", "admission_p95")
    }
    for name, value in acceptance_cv.items():
        if value is None or value > 0.30:
            failures.append(f"{profile}: {name} CV {value} exceeds 30% or is unavailable")
    return (
        {
            "profile": profile,
            "expected_workloads_per_round": expected,
            "rounds": round_summaries,
            "critical_cv": critical_cv,
            "acceptance_cv": acceptance_cv,
            "records": len(all_records),
            "passed": not failures,
        },
        failures,
    )


def markdown(summary: dict[str, Any]) -> str:
    lines = [
        "# DRA + Kueue KWOK-only results",
        "",
        f"Generated at `{summary['generated_at']}` by `poc.sh collect`.",
        "",
        "> These measurements represent KWOK control-plane behavior only. They do not",
        "> measure real GPU initialization, DRA node plugins, CDI, DCGM, or workload performance.",
        "",
        f"Overall acceptance: **{'PASS' if summary['passed'] else 'FAIL'}**",
        "",
        "| Profile | Round | Main success | Direct P95 | Kueue P95 | Increment | Idle with admitted pending | Preemptions |",
        "| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |",
    ]
    for profile in summary["profiles"]:
        for item in profile["rounds"]:
            direct = item["direct_end_to_end"]["p95_seconds"]
            kueue = item["kueue_end_to_end"]["p95_seconds"]
            overhead = item["p95_overhead_seconds"]
            lines.append(
                f"| {profile['profile']} | {item['round']} | {item['success_rate']:.2%} | "
                f"{finite_seconds(direct)} | {finite_seconds(kueue)} | {finite_seconds(overhead)} | "
                f"{item['idle_fraction_while_admitted_pending']:.2%} | {item['preemptions']} |"
            )
        lines.extend(
            [
                "",
                "| Round | Lifecycle interval | P50 | P95 | P99 | Samples |",
                "| ---: | --- | ---: | ---: | ---: | ---: |",
            ]
        )
        for item in profile["rounds"]:
            for name, values in item["lifecycle"].items():
                lines.append(
                    f"| {item['round']} | `{name}` | {finite_seconds(values['p50_seconds'])} | "
                    f"{finite_seconds(values['p95_seconds'])} | {finite_seconds(values['p99_seconds'])} | "
                    f"{values['count']} |"
                )
        lines.extend(
            [
                "",
                f"## {profile['profile']} P95 CVs",
                "",
            ]
        )
        lines.extend(
            f"- `{name}`: {finite_percent(value)}"
            for name, value in profile["critical_cv"].items()
        )
        lines.append("")
    if summary["failures"]:
        lines.extend(["## Failed assertions", ""] + [f"- {item}" for item in summary["failures"]] + [""])
    lines.extend(
        [
            "## Consumer boundary for #363",
            "",
            "Issue #363 may consume queue, quota, requeue, scale, and pending-reason baselines.",
            "It must not use this report as evidence that real devices are prepared across clusters.",
            "",
        ]
    )
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", required=True, type=pathlib.Path)
    parser.add_argument("--rounds", default=3, type=int)
    parser.add_argument("--profiles", nargs="+", default=["functional", "scale"])
    parser.add_argument("--summary", required=True, type=pathlib.Path)
    parser.add_argument("--report", type=pathlib.Path)
    parser.add_argument("--verify", action="store_true")
    args = parser.parse_args()
    expected = {"functional": 100, "scale": 1000}
    profiles = []
    failures: list[str] = []
    for profile in args.profiles:
        if profile not in expected:
            raise ValueError(f"unknown profile: {profile}")
        result, profile_failures = profile_summary(args.input, profile, args.rounds, expected[profile])
        profiles.append(result)
        failures.extend(profile_failures)
    result = {
        "schema": "dra-kueue-kwok-summary/v1",
        "generated_at": dt.datetime.now(dt.timezone.utc).isoformat().replace("+00:00", "Z"),
        "profiles": profiles,
        "failures": failures,
        "passed": not failures,
    }
    args.summary.parent.mkdir(parents=True, exist_ok=True)
    args.summary.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    if args.report:
        args.report.parent.mkdir(parents=True, exist_ok=True)
        args.report.write_text(markdown(result), encoding="utf-8")
    if failures:
        for failure in failures:
            print(f"FAIL: {failure}", file=sys.stderr)
    else:
        print("PASS: all requested profiles and rounds satisfy #285 acceptance")
    return 1 if args.verify and failures else 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (OSError, ValueError) as error:
        print(f"analyze.py: {error}", file=sys.stderr)
        raise SystemExit(1)

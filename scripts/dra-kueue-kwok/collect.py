#!/usr/bin/env python3
"""Observe #285 objects and emit append-only JSONL lifecycle records."""

from __future__ import annotations

import argparse
import datetime as dt
import json
import pathlib
import subprocess
import sys
import time
from typing import Any


LABEL_PREFIX = "benchmark.aiinfra.dev/"
KINDS = (
    ("jobs.batch", "job", True),
    ("deployments.apps", "deployment", True),
    ("workloads.kueue.x-k8s.io", "workload", True),
    ("pods", "pod", True),
    # Generated claims don't inherit labels from their owning Pod. Fetch all
    # claims in the four isolated test namespaces and join them by Pod UID.
    ("resourceclaims.resource.k8s.io", "claim", False),
    ("clusterqueues.kueue.x-k8s.io", "queue", False),
)


def utc_now() -> str:
    return dt.datetime.now(dt.timezone.utc).isoformat().replace("+00:00", "Z")


def parse_timestamp(value: str | None) -> dt.datetime | None:
    if not value:
        return None
    return dt.datetime.fromisoformat(value.replace("Z", "+00:00"))


def earlier(old: str | None, new: str | None) -> str | None:
    if not old:
        return new
    if not new:
        return old
    return min(old, new, key=lambda value: parse_timestamp(value) or dt.datetime.max.replace(tzinfo=dt.timezone.utc))


def labels_for(item: dict[str, Any]) -> dict[str, str]:
    return item.get("metadata", {}).get("labels", {}) or {}


def logical_key(item: dict[str, Any]) -> tuple[str, str] | None:
    labels = labels_for(item)
    workload = labels.get(LABEL_PREFIX + "workload")
    run = labels.get(LABEL_PREFIX + "run")
    return (run, workload) if run and workload else None


def condition(item: dict[str, Any], condition_type: str, status: str = "True") -> dict[str, Any] | None:
    for candidate in item.get("status", {}).get("conditions", []) or []:
        if candidate.get("type") == condition_type and candidate.get("status") == status:
            return candidate
    return None


class Observer:
    def __init__(self, run: str, profile: str, round_number: int, total_devices: int, output: pathlib.Path):
        self.run = run
        self.profile = profile
        self.round = round_number
        self.total_devices = total_devices
        self.output = output
        self.output.mkdir(parents=True, exist_ok=True)
        self.records: dict[tuple[str, str], dict[str, Any]] = {}
        self.present: dict[tuple[str, str], set[str]] = {}
        self.seen_types: dict[tuple[str, str], set[str]] = {}
        self.samples = (output / "samples.jsonl").open("a", encoding="utf-8")
        self.events = (output / "events.jsonl").open("a", encoding="utf-8")

    def initial_record(self, item: dict[str, Any]) -> dict[str, Any]:
        labels = labels_for(item)
        return {
            "schema": "dra-kueue-kwok/v1",
            "run": self.run,
            "profile": self.profile,
            "round": self.round,
            "scenario": labels.get(LABEL_PREFIX + "scenario", "unknown"),
            "path": labels.get(LABEL_PREFIX + "path", "unknown"),
            "workload": labels.get(LABEL_PREFIX + "workload", "unknown"),
            "namespace": item.get("metadata", {}).get("namespace"),
            "expected_pods": None,
            "expected_workloads": None,
            "created_at": None,
            "quota_reserved_at": None,
            "admitted_at": None,
            "claim_created_at": None,
            "claim_allocated_at": None,
            "claim_reserved_at": None,
            "pod_scheduled_at": None,
            "ready_at": None,
            "ended_at": None,
            "claim_deleted_at": None,
            "quota_released_at": None,
            "evictions": 0,
            "requeues": 0,
            "preempted": False,
            "reason": None,
            "result": "incomplete",
        }

    def merge_labels(self, record: dict[str, Any], item: dict[str, Any]) -> None:
        labels = labels_for(item)
        for field in ("scenario", "path", "workload"):
            value = labels.get(LABEL_PREFIX + field)
            if value and record.get(field) in (None, "unknown"):
                record[field] = value
        if not record.get("namespace"):
            record["namespace"] = item.get("metadata", {}).get("namespace")

    def event(self, record: dict[str, Any], event_type: str, observed_at: str, source: str, detail: str | None = None) -> None:
        payload = {
            "run": self.run,
            "profile": self.profile,
            "round": self.round,
            "scenario": record["scenario"],
            "workload": record["workload"],
            "event": event_type,
            "observed_at": observed_at,
            "source": source,
        }
        if detail:
            payload["detail"] = detail
        self.events.write(json.dumps(payload, sort_keys=True) + "\n")
        self.events.flush()

    def mark(self, record: dict[str, Any], field: str, value: str | None, source: str, detail: str | None = None) -> None:
        if value and not record.get(field):
            record[field] = value
            self.event(record, field.removesuffix("_at"), utc_now(), source, detail)

    def observe_item(self, item: dict[str, Any], object_type: str, observed_at: str) -> None:
        key = logical_key(item)
        if not key or key[0] != self.run:
            return
        record = self.records.setdefault(key, self.initial_record(item))
        self.merge_labels(record, item)
        identity = f"{object_type}/{item.get('metadata', {}).get('namespace', '')}/{item['metadata']['name']}"
        self.present.setdefault(key, set()).add(identity)
        self.seen_types.setdefault(key, set()).add(object_type)
        creation = item.get("metadata", {}).get("creationTimestamp")
        if object_type in {"job", "deployment"}:
            record["created_at"] = earlier(record.get("created_at"), creation)
            spec = item.get("spec", {})
            record["expected_pods"] = max(
                int(record.get("expected_pods") or 0),
                int(spec.get("parallelism") or spec.get("replicas") or 1),
            )
            record["expected_workloads"] = max(
                int(record.get("expected_workloads") or 0),
                int(spec.get("replicas") or 1) if object_type == "deployment" else 1,
            )
            if condition(item, "Complete"):
                self.mark(record, "ended_at", condition(item, "Complete").get("lastTransitionTime"), identity)
        elif object_type == "workload":
            for selected in item.get("status", {}).get("conditions", []) or []:
                reason = selected.get("reason", "")
                message = selected.get("message", "")
                if reason or message:
                    record["reason"] = ": ".join(part for part in (reason, message) if part)
                if selected.get("type") == "Evicted" and selected.get("status") == "True":
                    transition = selected.get("lastTransitionTime") or observed_at
                    marker = f"eviction/{transition}"
                    if marker not in self.present[key]:
                        self.present[key].add(marker)
                        record["evictions"] += 1
                        record["preempted"] = record["preempted"] or reason == "Preempted"
                        self.event(record, "evicted", observed_at, identity, reason)
                if selected.get("type") == "Requeued" and selected.get("status") == "True":
                    transition = selected.get("lastTransitionTime") or observed_at
                    marker = f"requeue/{transition}"
                    if marker not in self.present[key]:
                        self.present[key].add(marker)
                        record["requeues"] += 1
                        self.event(record, "requeued", observed_at, identity, reason)
                if selected.get("type") == "QuotaReserved" and selected.get("status") == "True":
                    transition = selected.get("lastTransitionTime") or observed_at
                    marker = f"reservation/{identity}/{transition}"
                    if marker not in self.present[key]:
                        self.present[key].add(marker)
                        # Kueue does not keep a long-lived Requeued=True condition.
                        # A new reservation after an eviction is durable evidence
                        # that the workload completed a requeue cycle.
                        if record.get("quota_reserved_at") and record["evictions"] > record["requeues"]:
                            record["requeues"] += 1
                            self.event(record, "requeued", observed_at, identity, "QuotaReservedAfterEviction")
        elif object_type == "claim":
            # Aggregate timestamps are set after all expected claims have
            # reached the respective lifecycle point.
            pass
        elif object_type == "pod":
            unscheduled = condition(item, "PodScheduled", "False")
            if unscheduled:
                record["reason"] = ": ".join(
                    part for part in (unscheduled.get("reason"), unscheduled.get("message")) if part
                )

    def snapshot(self, payloads: dict[str, list[dict[str, Any]]], observed_at: str) -> None:
        previous_present = self.present
        self.present = {
            key: {
                value
                for value in values
                if value.startswith(("eviction/", "requeue/", "reservation/"))
            }
            for key, values in previous_present.items()
        }
        pod_labels_by_uid = {
            item.get("metadata", {}).get("uid"): labels_for(item)
            for item in payloads.get("pod", [])
            if logical_key(item)
        }
        for claim in payloads.get("claim", []):
            references = claim.get("metadata", {}).get("ownerReferences", []) or []
            references += claim.get("status", {}).get("reservedFor", []) or []
            for reference in references:
                inherited = pod_labels_by_uid.get(reference.get("uid"))
                if inherited:
                    claim.setdefault("metadata", {})["labels"] = inherited
                    break
        for object_type, items in payloads.items():
            for item in items:
                self.observe_item(item, object_type, observed_at)

        items_by_key: dict[str, dict[tuple[str, str], list[dict[str, Any]]]] = {}
        for object_type in ("pod", "claim", "workload"):
            grouped: dict[tuple[str, str], list[dict[str, Any]]] = {}
            for item in payloads.get(object_type, []):
                key = logical_key(item)
                if key and key[0] == self.run:
                    grouped.setdefault(key, []).append(item)
            items_by_key[object_type] = grouped
        for key, record in self.records.items():
            expected = int(record.get("expected_pods") or 1)
            expected_workloads = int(record.get("expected_workloads") or 1)
            workloads = items_by_key["workload"].get(key, [])
            if len(workloads) >= expected_workloads:
                for condition_type, field in (("QuotaReserved", "quota_reserved_at"), ("Admitted", "admitted_at")):
                    selected_conditions = [
                        condition(item, condition_type) for item in workloads if condition(item, condition_type)
                    ]
                    if len(selected_conditions) >= expected_workloads:
                        selected = max(
                            (item.get("lastTransitionTime") or observed_at for item in selected_conditions),
                            key=lambda value: parse_timestamp(value) or dt.datetime.min.replace(tzinfo=dt.timezone.utc),
                        )
                        self.mark(record, field, selected, "collector")
            pods = items_by_key["pod"].get(key, [])
            scheduled = [condition(item, "PodScheduled") for item in pods if condition(item, "PodScheduled")]
            ready = [condition(item, "Ready") for item in pods if condition(item, "Ready")]
            if len(scheduled) >= expected:
                selected = max(
                    (item.get("lastTransitionTime") or observed_at for item in scheduled),
                    key=lambda value: parse_timestamp(value) or dt.datetime.min.replace(tzinfo=dt.timezone.utc),
                )
                self.mark(record, "pod_scheduled_at", selected, "collector")
            if len(ready) >= expected:
                selected = max(
                    (item.get("lastTransitionTime") or observed_at for item in ready),
                    key=lambda value: parse_timestamp(value) or dt.datetime.min.replace(tzinfo=dt.timezone.utc),
                )
                self.mark(record, "ready_at", selected, "collector")
            claims = items_by_key["claim"].get(key, [])
            if len(claims) >= expected:
                selected = max(
                    (item.get("metadata", {}).get("creationTimestamp") or observed_at for item in claims),
                    key=lambda value: parse_timestamp(value) or dt.datetime.min.replace(tzinfo=dt.timezone.utc),
                )
                self.mark(record, "claim_created_at", selected, "collector")
                if all(item.get("status", {}).get("allocation") for item in claims):
                    self.mark(record, "claim_allocated_at", observed_at, "collector")
                if all(item.get("status", {}).get("reservedFor") for item in claims):
                    self.mark(record, "claim_reserved_at", observed_at, "collector")

        allocated_claims = 0
        admitted_pending = 0
        admitted_pending_devices = 0
        for item in payloads.get("claim", []):
            if item.get("status", {}).get("allocation"):
                allocated_claims += 1
        ready_keys = {logical_key(item) for item in payloads.get("pod", []) if condition(item, "Ready")}
        for item in payloads.get("workload", []):
            if condition(item, "Admitted") and logical_key(item) not in ready_keys:
                admitted_pending += 1
                admitted_pending_devices += sum(
                    int(pod_set.get("count", 1))
                    for pod_set in item.get("spec", {}).get("podSets", []) or []
                )
        idle_devices = min(
            max(self.total_devices - allocated_claims, 0),
            admitted_pending_devices,
        )
        idle_fraction = idle_devices / self.total_devices if admitted_pending else 0.0
        self.samples.write(
            json.dumps(
                {
                    "run": self.run,
                    "profile": self.profile,
                    "round": self.round,
                    "observed_at": observed_at,
                    "allocated_claims": allocated_claims,
                    "total_devices": self.total_devices,
                    "admitted_pending": admitted_pending,
                    "admitted_pending_devices": admitted_pending_devices,
                    "idle_devices_with_admitted_pending": idle_devices,
                    "idle_fraction_while_admitted_pending": idle_fraction,
                    "weighted_shares": {
                        item.get("metadata", {}).get("name"): item.get("status", {})
                        .get("fairSharing", {})
                        .get("weightedShare")
                        for item in payloads.get("queue", [])
                        if item.get("metadata", {}).get("name", "").startswith("dra-kueue-tenant-")
                    },
                },
                sort_keys=True,
            )
            + "\n"
        )
        self.samples.flush()

        for key, seen in self.seen_types.items():
            now = self.present.get(key, set())
            record = self.records[key]
            if "claim" in seen and not any(value.startswith("claim/") for value in now):
                self.mark(record, "claim_deleted_at", observed_at, "collector")
            if seen.intersection({"job", "deployment"}) and not any(
                value.startswith(("job/", "deployment/")) for value in now
            ):
                self.mark(record, "ended_at", observed_at, "collector")
            if "workload" in seen and not any(value.startswith("workload/") for value in now):
                self.mark(record, "quota_released_at", observed_at, "collector")

    def finish(self) -> None:
        self.samples.close()
        self.events.close()
        final_path = self.output / "workloads.jsonl"
        with final_path.open("w", encoding="utf-8") as stream:
            for record in sorted(self.records.values(), key=lambda item: item["workload"]):
                failure = record["scenario"] in {
                    "quota-insufficient",
                    "no-matching-slice",
                    "admitted-unschedulable",
                    "wait-for-pods-ready",
                }
                if failure and record["reason"] and record["quota_released_at"]:
                    record["result"] = "expected_failure"
                elif record["scenario"] == "extended-smoke":
                    if record["ready_at"] and record["ended_at"] and record["quota_released_at"]:
                        record["result"] = "success"
                elif record["ready_at"] and record["ended_at"]:
                    if (
                        record["claim_allocated_at"]
                        and record["claim_deleted_at"]
                        and (record["path"] == "direct" or record["quota_released_at"])
                    ):
                        record["result"] = "success"
                stream.write(json.dumps(record, sort_keys=True) + "\n")


def kubectl_json(kubectl: str, resource: str, selector: str | None) -> list[dict[str, Any]]:
    command = [kubectl, "get", resource, "-A"]
    if selector:
        command.extend(["-l", selector])
    command.extend(["-o", "json", "--ignore-not-found"])
    result = subprocess.run(command, check=False, capture_output=True, text=True)
    if result.returncode:
        raise RuntimeError(f"{' '.join(command)}: {result.stderr.strip()}")
    return json.loads(result.stdout or "{}").get("items", [])


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--run", required=True)
    parser.add_argument("--profile", required=True)
    parser.add_argument("--round", required=True, type=int)
    parser.add_argument("--devices", required=True, type=int)
    parser.add_argument("--output", required=True, type=pathlib.Path)
    parser.add_argument("--stop-file", required=True, type=pathlib.Path)
    parser.add_argument("--kubectl", default="kubectl")
    parser.add_argument("--interval", default=0.5, type=float)
    args = parser.parse_args()
    observer = Observer(args.run, args.profile, args.round, args.devices, args.output)
    selector = f"{LABEL_PREFIX}run={args.run}"
    try:
        while not args.stop_file.exists():
            observed_at = utc_now()
            payloads: dict[str, list[dict[str, Any]]] = {}
            for resource, object_type, select in KINDS:
                payloads.setdefault(object_type, []).extend(
                    kubectl_json(args.kubectl, resource, selector if select else None)
                )
            observer.snapshot(payloads, observed_at)
            time.sleep(args.interval)
        # One last observation catches deletions immediately preceding stop.
        payloads = {}
        for resource, object_type, select in KINDS:
            payloads.setdefault(object_type, []).extend(
                kubectl_json(args.kubectl, resource, selector if select else None)
            )
        observer.snapshot(payloads, utc_now())
    finally:
        observer.finish()
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (OSError, RuntimeError, json.JSONDecodeError) as error:
        print(f"collect.py: {error}", file=sys.stderr)
        raise SystemExit(1)

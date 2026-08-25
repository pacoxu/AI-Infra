#!/usr/bin/env python3

from __future__ import annotations

import datetime as dt
import importlib.util
import json
import pathlib
import subprocess
import tempfile
import unittest


ROOT = pathlib.Path(__file__).resolve().parents[1]


def load(name: str, path: pathlib.Path):
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


generate = load("generate", ROOT / "generate.py")
analyze = load("analyze", ROOT / "analyze.py")
collect = load("collect", ROOT / "collect.py")


class GeneratorTest(unittest.TestCase):
    def test_profiles_are_deterministic_and_use_current_apis(self) -> None:
        for profile, total in (("functional", 100), ("scale", 1000)):
            phases = {
                phase: generate.workload_documents("fixture", profile, 1, total, phase)
                for phase in ("short", "steady", "mixed-low", "mixed-high")
            }
            self.assertEqual(len(phases["short"]), total * 60 // 100)
            self.assertEqual(len(phases["steady"]), total * 20 // 100)
            self.assertEqual(len(phases["mixed-low"]), total * 10 // 100)
            self.assertEqual(len(phases["mixed-high"]), total * 10 // 100)
            self.assertTrue(all(item["kind"] == "Deployment" for item in phases["mixed-low"] + phases["mixed-high"]))
            with tempfile.TemporaryDirectory() as directory:
                output = pathlib.Path(directory) / "objects.yaml"
                generate.dump_documents(sum(phases.values(), []), output)
                text = output.read_text(encoding="utf-8")
                self.assertNotIn("resource.k8s.io/v1beta", text)
                self.assertNotIn("kueue.x-k8s.io/v1beta1", text)
                self.assertIn('benchmark.aiinfra.dev/round: "1"', text)
            claim = generate.claim_template()
            request = claim["spec"]["spec"]["devices"]["requests"][0]["exactly"]
            self.assertEqual(request["allocationMode"], "ExactCount")

    def test_short_phase_can_be_generated_in_deterministic_waves(self) -> None:
        first = generate.workload_documents("fixture", "scale", 1, 1000, "short", 0, 20)
        second = generate.workload_documents("fixture", "scale", 1, 1000, "short", 20, 20)
        self.assertEqual(len(first), 20)
        self.assertEqual(len(second), 20)
        self.assertEqual(first[0]["metadata"]["name"], "kueue-short-000000")
        self.assertEqual(second[0]["metadata"]["name"], "kueue-short-000020")
        self.assertFalse({item["metadata"]["name"] for item in first} & {item["metadata"]["name"] for item in second})

    def test_resource_slice_count_and_devices(self) -> None:
        documents = generate.slice_documents([f"node-{index:06d}" for index in range(100)])
        self.assertEqual(len(documents), 100)
        self.assertTrue(all(doc["apiVersion"] == "resource.k8s.io/v1" for doc in documents))
        self.assertTrue(all(len(doc["spec"]["devices"]) == 8 for doc in documents))
        names = {device["name"] for doc in documents for device in doc["spec"]["devices"]}
        self.assertEqual(names, {f"gpu-{index}" for index in range(8)})

    def test_queue_model(self) -> None:
        queues = [doc for doc in generate.queue_documents(10) if doc["kind"] == "ClusterQueue"]
        self.assertEqual(len(queues), 2)
        for queue in queues:
            self.assertEqual(queue["apiVersion"], "kueue.x-k8s.io/v1beta2")
            self.assertEqual(queue["spec"]["cohortName"], "dra-kueue-kwok")
            self.assertEqual(queue["spec"]["fairSharing"]["weight"], "1")
            self.assertEqual(queue["spec"]["preemption"]["withinClusterQueue"], "LowerPriority")
            self.assertEqual(queue["spec"]["preemption"]["reclaimWithinCohort"], "Any")
            resource_groups = queue["spec"]["resourceGroups"]
            self.assertEqual(len(resource_groups), 1)
            gpu_quota = next(
                item for item in resource_groups[0]["flavors"][0]["resources"]
                if item["name"] == generate.GPU_RESOURCE
            )
            self.assertEqual(gpu_quota["nominalQuota"], 40)

    def test_borrower_priority_is_lower_than_default(self) -> None:
        base = (ROOT / "manifests" / "base.yaml").read_text(encoding="utf-8")
        low = base.split("name: dra-kueue-low", 1)[1].split("---", 1)[0]
        self.assertIn("value: -100", low)

    def test_extended_smoke_does_not_reference_template(self) -> None:
        [smoke] = generate.workload_documents("fixture", "functional", 1, 100, "extended-smoke")
        pod = smoke["spec"]["template"]["spec"]
        self.assertNotIn("resourceClaims", pod)
        self.assertEqual(
            pod["containers"][0]["resources"]["requests"][generate.EXTENDED_GPU_RESOURCE],
            1,
        )
        self.assertEqual(
            pod["containers"][0]["resources"]["limits"][generate.EXTENDED_GPU_RESOURCE],
            1,
        )

    def test_deployment_uses_always_restart_policy(self) -> None:
        [deployment] = generate.workload_documents("fixture", "functional", 1, 10, "steady")[1:2]
        self.assertEqual(deployment["kind"], "Deployment")
        self.assertEqual(deployment["spec"]["template"]["spec"]["restartPolicy"], "Always")

    def test_failure_suite_is_not_counted_in_main_total(self) -> None:
        for case in (
            "quota-insufficient",
            "no-matching-slice",
            "admitted-unschedulable",
            "wait-for-pods-ready",
        ):
            documents = generate.failure_document("fixture", "functional", 1, case, 80)
            job = documents[-1]
            self.assertEqual(job["metadata"]["labels"]["benchmark.aiinfra.dev/scenario"], case)

    def test_kwok_local_manifest_is_wrapped_as_kustomization(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = pathlib.Path(directory)
            manifest_dir = root / "kueue"
            manifest_dir.mkdir()
            (manifest_dir / "manifests.yaml").write_text("apiVersion: v1\nkind: List\n", encoding="utf-8")
            template = root / "template.yaml"
            template.write_text("manifests:\n- __KUEUE_MANIFEST__\n", encoding="utf-8")
            output = root / "kwokctl.yaml"
            args = type("Args", (), {"template": template, "manifest": manifest_dir, "output": output})
            content = args.template.read_text(encoding="utf-8")
            marker = "__KUEUE_MANIFEST__"
            resources = sorted(
                path.name for path in args.manifest.glob("*.yaml") if path.name != "kustomization.yaml"
            )
            (args.manifest / "kustomization.yaml").write_text(
                "apiVersion: kustomize.config.k8s.io/v1beta1\nkind: Kustomization\nresources:\n"
                + "".join(f"- {resource}\n" for resource in resources),
                encoding="utf-8",
            )
            args.output.write_text(content.replace(marker, str(args.manifest.resolve())), encoding="utf-8")
            self.assertIn("- manifests.yaml", (manifest_dir / "kustomization.yaml").read_text(encoding="utf-8"))

    def test_kwok_config_exposes_metrics_ports(self) -> None:
        config = (ROOT / "config" / "kwokctl.yaml").read_text(encoding="utf-8")
        self.assertIn("kubeSchedulerPort: 10259", config)
        manager_config = (ROOT / "config" / "kueue-manager-config.yaml").read_text(encoding="utf-8")
        self.assertIn("bindAddress: :8443", manager_config)

    def test_kueue_scale_defaults_are_preserved(self) -> None:
        manager_config = (ROOT / "config" / "kueue-manager-config.yaml").read_text(encoding="utf-8")
        self.assertIn("Workload.kueue.x-k8s.io: 10", manager_config)
        self.assertIn("Job.batch: 5", manager_config)
        self.assertIn("qps: 300", manager_config)
        self.assertIn("burst: 500", manager_config)


def iso(seconds: float) -> str:
    origin = dt.datetime(2026, 8, 12, tzinfo=dt.timezone.utc)
    return (origin + dt.timedelta(seconds=seconds)).isoformat().replace("+00:00", "Z")


def successful_record(profile: str, round_number: int, scenario: str, index: int, path: str = "kueue") -> dict:
    base = {
        "run": f"{profile}-r{round_number}",
        "profile": profile,
        "round": round_number,
        "scenario": scenario,
        "path": path,
        "workload": f"{path}-{scenario}-{index:06d}",
        "created_at": iso(0),
        "quota_reserved_at": iso(0.2) if path == "kueue" else None,
        "admitted_at": iso(0.3) if path == "kueue" else None,
        "claim_created_at": iso(0.4),
        "claim_allocated_at": iso(0.5),
        "claim_reserved_at": iso(0.6),
        "pod_scheduled_at": iso(0.7),
        "ready_at": iso(1.0 if path == "direct" else 1.5),
        "ended_at": iso(2.0),
        "claim_deleted_at": iso(2.1),
        "quota_released_at": iso(2.2) if path == "kueue" else None,
        "evictions": 1 if scenario == "mixed" and index == 0 else 0,
        "requeues": 1 if scenario == "mixed" and index == 0 else 0,
        "preempted": scenario == "mixed" and index == 0,
        "reason": "Preempted" if scenario == "mixed" and index == 0 else None,
        "result": "success",
    }
    return base


class AnalyzerTest(unittest.TestCase):
    def write_fixture(self, root: pathlib.Path, incomplete: bool = False) -> None:
        total = 100
        for round_number in range(1, 4):
            directory = root / "runs" / "functional" / f"round-{round_number}"
            directory.mkdir(parents=True)
            records = []
            for scenario, ratio in analyze.RATIOS.items():
                for index in range(total * ratio // 100):
                    records.append(successful_record("functional", round_number, scenario, index))
            for index in range(60):
                records.append(successful_record("functional", round_number, "short", index, "direct"))
            records.append(successful_record("functional", round_number, "extended-smoke", 0))
            for case in sorted(analyze.FAILURES):
                record = successful_record("functional", round_number, case, 0)
                record.update(
                    {
                        "ready_at": None,
                        "claim_allocated_at": None,
                        "result": "expected_failure",
                        "reason": "expected test reason",
                        "requeues": 2 if case == "wait-for-pods-ready" else 1,
                        "evictions": 2 if case == "wait-for-pods-ready" else 1,
                    }
                )
                if case == "quota-insufficient":
                    record["quota_reserved_at"] = None
                    record["admitted_at"] = None
                    record["requeues"] = 0
                    record["evictions"] = 0
                records.append(record)
            if incomplete and round_number == 1:
                records[0]["claim_deleted_at"] = None
                records[0]["result"] = "incomplete"
            with (directory / "workloads.jsonl").open("w", encoding="utf-8") as stream:
                for record in records:
                    stream.write(json.dumps(record) + "\n")
            samples = [
                {
                    "admitted_pending": 1,
                    "idle_fraction_while_admitted_pending": 0.1,
                },
                {
                    "admitted_pending": 0,
                    "idle_fraction_while_admitted_pending": 0.0,
                },
            ]
            with (directory / "samples.jsonl").open("w", encoding="utf-8") as stream:
                for sample in samples:
                    stream.write(json.dumps(sample) + "\n")

    def test_fixture_passes(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = pathlib.Path(directory)
            self.write_fixture(root)
            summary, failures = analyze.profile_summary(root, "functional", 3, 100)
            self.assertFalse(failures, failures)
            self.assertTrue(summary["passed"])
            self.assertEqual(len(summary["rounds"]), 3)

    def test_missing_claim_deletion_fails(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = pathlib.Path(directory)
            self.write_fixture(root, incomplete=True)
            _, failures = analyze.profile_summary(root, "functional", 3, 100)
            self.assertTrue(any("claim_deleted_at" in failure for failure in failures))

    def test_near_zero_subinterval_cv_is_reported_but_not_a_gate(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = pathlib.Path(directory)
            self.write_fixture(root)
            path = root / "runs" / "functional" / "round-2" / "workloads.jsonl"
            records = analyze.read_jsonl(path)
            for record in records:
                if record.get("path") == "kueue" and record.get("scenario") in analyze.RATIOS:
                    record["claim_reserved_at"] = iso(0.6)
                    record["pod_scheduled_at"] = iso(0.601)
            with path.open("w", encoding="utf-8") as stream:
                for record in records:
                    stream.write(json.dumps(record) + "\n")
            summary, failures = analyze.profile_summary(root, "functional", 3, 100)
            self.assertFalse(failures, failures)
            self.assertGreater(summary["critical_cv"]["pod_schedule_p95"], 0.30)
            self.assertNotIn("pod_schedule_p95", summary["acceptance_cv"])

    def test_durable_preemption_event_covers_transient_condition(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = pathlib.Path(directory)
            self.write_fixture(root)
            round_dir = root / "runs" / "functional" / "round-3"
            workloads = analyze.read_jsonl(round_dir / "workloads.jsonl")
            for record in workloads:
                if record.get("scenario") == "mixed":
                    record["preempted"] = False
                    record["evictions"] = 0
            with (round_dir / "workloads.jsonl").open("w", encoding="utf-8") as stream:
                for record in workloads:
                    stream.write(json.dumps(record) + "\n")
            event = {
                "reason": "Preempted",
                "eventTime": iso(1.0),
                "involvedObject": {
                    "kind": "Workload",
                    "namespace": "dra-kueue-tenant-a",
                    "name": "pod-kueue-mixed-low-000000-fixture",
                },
            }
            (round_dir / "kubernetes-events.json").write_text(
                json.dumps({"items": [event]}), encoding="utf-8"
            )
            summary, failures = analyze.profile_summary(root, "functional", 3, 100)
            self.assertFalse(failures, failures)
            self.assertEqual(summary["rounds"][2]["preemptions"], 1)


class CollectorTest(unittest.TestCase):
    def test_job_owner_is_not_overwritten_and_requeue_is_inferred(self) -> None:
        labels = {
            "benchmark.aiinfra.dev/run": "fixture",
            "benchmark.aiinfra.dev/profile": "functional",
            "benchmark.aiinfra.dev/round": "1",
            "benchmark.aiinfra.dev/scenario": "wait-for-pods-ready",
            "benchmark.aiinfra.dev/workload": "failure-wait-for-pods-ready",
            "benchmark.aiinfra.dev/path": "kueue",
        }
        job = {
            "kind": "Job",
            "metadata": {
                "name": "failure-wait-for-pods-ready",
                "namespace": "dra-kueue-failures",
                "labels": labels,
                "creationTimestamp": iso(0),
            },
            "spec": {"parallelism": 1},
        }

        def workload(transition: float, evicted: bool = False) -> dict:
            conditions = [
                {
                    "type": "QuotaReserved",
                    "status": "False" if evicted else "True",
                    "reason": "Pending" if evicted else "QuotaReserved",
                    "lastTransitionTime": iso(transition),
                }
            ]
            if evicted:
                conditions.append(
                    {
                        "type": "Evicted",
                        "status": "True",
                        "reason": "PodsReadyTimeout",
                        "lastTransitionTime": iso(transition),
                    }
                )
            return {
                "kind": "Workload",
                "metadata": {
                    "name": "job-failure-wait-for-pods-ready-fixture",
                    "namespace": "dra-kueue-failures",
                    "labels": labels,
                },
                "status": {"conditions": conditions},
            }

        with tempfile.TemporaryDirectory() as directory:
            observer = collect.Observer("fixture", "functional", 1, 80, pathlib.Path(directory))
            observer.snapshot({"job": [job], "deployment": [], "workload": [workload(1)]}, iso(1))
            observer.snapshot({"job": [job], "deployment": [], "workload": [workload(61, True)]}, iso(61))
            observer.snapshot({"job": [job], "deployment": [], "workload": [workload(66)]}, iso(66))
            record = observer.records[("fixture", "failure-wait-for-pods-ready")]
            self.assertEqual(record["path"], "kueue")
            self.assertEqual(record["created_at"], iso(0))
            self.assertEqual(record["expected_pods"], 1)
            self.assertEqual(record["evictions"], 1)
            self.assertEqual(record["requeues"], 1)
            observer.finish()


class ContractTest(unittest.TestCase):
    def test_shell_entrypoint_contract(self) -> None:
        script = (ROOT / "poc.sh").read_text(encoding="utf-8")
        for action in ("setup", "run", "collect", "verify", "cleanup"):
            self.assertIn(action, script)
        for value in ("--profile", "--rounds", "--output"):
            self.assertIn(value, script)
        subprocess.run(["bash", "-n", str(ROOT / "poc.sh"), str(ROOT / "lib.sh")], check=True)


if __name__ == "__main__":
    unittest.main()

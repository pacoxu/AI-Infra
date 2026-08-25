#!/usr/bin/env python3
"""Generate deterministic manifests for the #285 KWOK-only PoC.

Only the Python standard library is used so the PoC does not acquire a hidden
PyYAML dependency.  The emitted documents deliberately use the GA DRA API and
the Kueue v0.19 API.
"""

from __future__ import annotations

import argparse
import json
import pathlib
import re
import sys
from typing import Any, Iterable


DRIVER = "gpu.kwok.aiinfra.dev"
DEVICE_CLASS = "gpu.kwok.aiinfra.dev"
EMPTY_DEVICE_CLASS = "empty-gpu.kwok.aiinfra.dev"
GPU_RESOURCE = "kwok.aiinfra.dev/gpu"
EMPTY_GPU_RESOURCE = "kwok.aiinfra.dev/empty-gpu"
EXTENDED_GPU_RESOURCE = "kwok.aiinfra.dev/extended-gpu"
COHORT = "dra-kueue-kwok"
TENANTS = ("a", "b")


def scalar(value: Any) -> str:
    if value is None:
        return "null"
    if value is True:
        return "true"
    if value is False:
        return "false"
    if isinstance(value, (int, float)):
        return str(value)
    text = str(value)
    if re.fullmatch(r"[-+]?(?:[0-9]+(?:\.[0-9]*)?|\.[0-9]+)(?:[eE][-+]?[0-9]+)?", text):
        return json.dumps(text)
    if not text or any(c in text for c in ":#{}[],&*!|>'\"%@`\n") or text.strip() != text:
        return json.dumps(text)
    if text.lower() in {"null", "true", "false", "yes", "no"}:
        return json.dumps(text)
    return text


def yaml_lines(value: Any, indent: int = 0) -> list[str]:
    pad = " " * indent
    if isinstance(value, dict):
        lines: list[str] = []
        for key, item in value.items():
            if isinstance(item, (dict, list)):
                if item:
                    lines.append(f"{pad}{key}:")
                    lines.extend(yaml_lines(item, indent + 2))
                else:
                    lines.append(f"{pad}{key}: {'{}' if isinstance(item, dict) else '[]'}")
            else:
                lines.append(f"{pad}{key}: {scalar(item)}")
        return lines
    if isinstance(value, list):
        lines = []
        for item in value:
            if isinstance(item, dict):
                first, *rest = yaml_lines(item, indent + 2)
                lines.append(f"{pad}- {first.strip()}")
                lines.extend(rest)
            elif isinstance(item, list):
                lines.append(f"{pad}-")
                lines.extend(yaml_lines(item, indent + 2))
            else:
                lines.append(f"{pad}- {scalar(item)}")
        return lines
    return [f"{pad}{scalar(value)}"]


def dump_documents(documents: Iterable[dict[str, Any]], destination: pathlib.Path) -> None:
    destination.parent.mkdir(parents=True, exist_ok=True)
    text = "\n---\n".join("\n".join(yaml_lines(doc)) for doc in documents)
    destination.write_text(text + "\n", encoding="utf-8")


def labels(run: str, profile: str, round_number: int, scenario: str, workload: str, path: str) -> dict[str, str]:
    return {
        "benchmark.aiinfra.dev/run": run,
        "benchmark.aiinfra.dev/profile": profile,
        "benchmark.aiinfra.dev/round": str(round_number),
        "benchmark.aiinfra.dev/scenario": scenario,
        "benchmark.aiinfra.dev/workload": workload,
        "benchmark.aiinfra.dev/path": path,
    }


def namespaces() -> list[dict[str, Any]]:
    docs = []
    for name, tenant in (
        ("dra-kueue-direct", "direct"),
        ("dra-kueue-tenant-a", "a"),
        ("dra-kueue-tenant-b", "b"),
        ("dra-kueue-failures", "b"),
    ):
        docs.append(
            {
                "apiVersion": "v1",
                "kind": "Namespace",
                "metadata": {
                    "name": name,
                    "labels": {
                        "benchmark.aiinfra.dev/tenant": tenant,
                        "benchmark.aiinfra.dev/suite": "failures" if name == "dra-kueue-failures" else "main",
                    },
                },
            }
        )
    return docs


def queue_documents(nodes: int) -> list[dict[str, Any]]:
    total_gpu = nodes * 8
    nominal_gpu = total_gpu // 2
    docs: list[dict[str, Any]] = []
    for tenant in TENANTS:
        docs.append(
            {
                "apiVersion": "kueue.x-k8s.io/v1beta2",
                "kind": "ClusterQueue",
                "metadata": {
                    "name": f"dra-kueue-tenant-{tenant}",
                    "labels": {"benchmark.aiinfra.dev/suite": "dra-kueue-kwok"},
                },
                "spec": {
                    "cohortName": COHORT,
                    "namespaceSelector": {
                        "matchLabels": {"benchmark.aiinfra.dev/tenant": tenant}
                    },
                    "resourceGroups": [
                        {
                            "coveredResources": [
                                "cpu",
                                "memory",
                                GPU_RESOURCE,
                                EMPTY_GPU_RESOURCE,
                                EXTENDED_GPU_RESOURCE,
                            ],
                            "flavors": [
                                {
                                    "name": "kwok-gpu",
                                    "resources": [
                                        {"name": "cpu", "nominalQuota": nodes * 32},
                                        {"name": "memory", "nominalQuota": f"{nodes * 256}Gi"},
                                        {"name": GPU_RESOURCE, "nominalQuota": nominal_gpu},
                                        {"name": EMPTY_GPU_RESOURCE, "nominalQuota": total_gpu},
                                        {"name": EXTENDED_GPU_RESOURCE, "nominalQuota": nominal_gpu},
                                    ],
                                }
                            ],
                        }
                    ],
                    "preemption": {
                        "withinClusterQueue": "LowerPriority",
                        "reclaimWithinCohort": "Any",
                    },
                    "fairSharing": {"weight": "1"},
                },
            }
        )
        docs.append(
            {
                "apiVersion": "kueue.x-k8s.io/v1beta2",
                "kind": "LocalQueue",
                "metadata": {
                    "name": "gpu",
                    "namespace": f"dra-kueue-tenant-{tenant}",
                },
                "spec": {"clusterQueue": f"dra-kueue-tenant-{tenant}"},
            }
        )
    # Failure cases use tenant B's ClusterQueue.  This avoids a third share in
    # the cohort and makes quota release assertions unambiguous.
    docs.append(
        {
            "apiVersion": "kueue.x-k8s.io/v1beta2",
            "kind": "LocalQueue",
            "metadata": {"name": "gpu", "namespace": "dra-kueue-failures"},
            "spec": {"clusterQueue": "dra-kueue-tenant-b"},
        }
    )
    return docs


def slice_documents(node_names: list[str]) -> list[dict[str, Any]]:
    docs = []
    for node in sorted(node_names):
        docs.append(
            {
                "apiVersion": "resource.k8s.io/v1",
                "kind": "ResourceSlice",
                "metadata": {
                    "name": f"{node}-gpu",
                    "labels": {"benchmark.aiinfra.dev/suite": "dra-kueue-kwok"},
                },
                "spec": {
                    "driver": DRIVER,
                    "nodeName": node,
                    "pool": {"name": node, "generation": 1, "resourceSliceCount": 1},
                    "devices": [
                        {
                            "name": f"gpu-{index}",
                            "attributes": {
                                "model": {"string": "KWOK-GPU"},
                                "node": {"string": node},
                            },
                            "capacity": {"memory": {"value": "80Gi"}},
                        }
                        for index in range(8)
                    ],
                },
            }
        )
    return docs


def claim_template(name: str = "kwok-gpu", device_class: str = DEVICE_CLASS, count: int = 1) -> dict[str, Any]:
    return {
        "apiVersion": "resource.k8s.io/v1",
        "kind": "ResourceClaimTemplate",
        "metadata": {"name": name},
        "spec": {
            "spec": {
                "devices": {
                    "requests": [
                        {
                            "name": "gpu",
                            "exactly": {
                                "deviceClassName": device_class,
                                "allocationMode": "ExactCount",
                                "count": count,
                            },
                        }
                    ]
                }
            }
        },
    }


def pod_spec(
    template_name: str = "kwok-gpu",
    priority: str | None = None,
    impossible_node: bool = False,
    extended: bool = False,
    restart_policy: str = "Never",
) -> dict[str, Any]:
    requests: dict[str, Any] = {"cpu": "100m", "memory": "64Mi"}
    resources: dict[str, Any] = {"requests": requests}
    spec: dict[str, Any] = {
        "restartPolicy": restart_policy,
        "terminationGracePeriodSeconds": 0,
        "containers": [
            {
                "name": "workload",
                "image": "registry.k8s.io/pause:3.10.1",
                "resources": resources,
            }
        ],
    }
    if extended:
        requests[EXTENDED_GPU_RESOURCE] = 1
        resources["limits"] = {EXTENDED_GPU_RESOURCE: 1}
    else:
        spec["resourceClaims"] = [
            {"name": "gpu", "resourceClaimTemplateName": template_name}
        ]
        resources["claims"] = [{"name": "gpu"}]
    if priority:
        spec["priorityClassName"] = priority
    if impossible_node:
        spec["nodeSelector"] = {"benchmark.aiinfra.dev/nonexistent": "true"}
    return spec


def job(
    *,
    name: str,
    namespace: str,
    item_labels: dict[str, str],
    parallelism: int = 1,
    managed: bool = True,
    priority: str | None = None,
    template_name: str = "kwok-gpu",
    impossible_node: bool = False,
    extended: bool = False,
) -> dict[str, Any]:
    object_labels = dict(item_labels)
    pod_labels = dict(item_labels)
    if managed:
        object_labels["kueue.x-k8s.io/queue-name"] = "gpu"
        pod_labels["kueue.x-k8s.io/queue-name"] = "gpu"
    return {
        "apiVersion": "batch/v1",
        "kind": "Job",
        "metadata": {"name": name, "namespace": namespace, "labels": object_labels},
        "spec": {
            "suspend": managed,
            "parallelism": parallelism,
            "completions": parallelism,
            "backoffLimit": 0,
            "template": {
                "metadata": {"labels": pod_labels},
                "spec": pod_spec(template_name, priority, impossible_node, extended),
            },
        },
    }


def deployment(
    *, name: str, namespace: str, item_labels: dict[str, str], priority: str | None = None
) -> dict[str, Any]:
    object_labels = dict(item_labels)
    object_labels["kueue.x-k8s.io/queue-name"] = "gpu"
    pod_labels = dict(object_labels)
    selector_labels = {"benchmark.aiinfra.dev/workload": item_labels["benchmark.aiinfra.dev/workload"]}
    pod_labels.update(selector_labels)
    return {
        "apiVersion": "apps/v1",
        "kind": "Deployment",
        "metadata": {"name": name, "namespace": namespace, "labels": object_labels},
        "spec": {
            "replicas": 2,
            "selector": {"matchLabels": selector_labels},
            "template": {
                "metadata": {"labels": pod_labels},
                "spec": pod_spec(priority=priority, restart_policy="Always"),
            },
        },
    }


def tenant_for(index: int) -> str:
    return TENANTS[index % 2]


def workload_documents(
    run: str,
    profile: str,
    round_number: int,
    total: int,
    phase: str,
    start: int = 0,
    count: int | None = None,
) -> list[dict[str, Any]]:
    docs: list[dict[str, Any]] = []
    counts = {
        "short": total * 60 // 100,
        "long": total * 10 // 100,
        "inference": total * 10 // 100,
        "mixed": total * 20 // 100,
    }
    if sum(counts.values()) != total:
        raise ValueError("workload total must be divisible into 60/10/10/20 without rounding")

    if phase in {"direct", "short"}:
        phase_count = counts["short"]
        selected_count = phase_count - start if count is None else count
        if start < 0 or selected_count < 0 or start + selected_count > phase_count:
            raise ValueError(
                f"short workload range [{start}, {start + selected_count}) exceeds [0, {phase_count})"
            )
        for index in range(start, start + selected_count):
            direct = phase == "direct"
            path = "direct" if direct else "kueue"
            tenant = "direct" if direct else tenant_for(index)
            workload = f"{path}-short-{index:06d}"
            item_labels = labels(run, profile, round_number, "short", workload, path)
            docs.append(
                job(
                    name=workload,
                    namespace="dra-kueue-direct" if direct else f"dra-kueue-tenant-{tenant}",
                    item_labels=item_labels,
                    managed=not direct,
                )
            )
        return docs

    if phase == "steady":
        for scenario in ("long", "inference"):
            for index in range(counts[scenario]):
                tenant = tenant_for(index)
                workload = f"kueue-{scenario}-{index:06d}"
                item_labels = labels(run, profile, round_number, scenario, workload, "kueue")
                if scenario == "long":
                    docs.append(
                        job(
                            name=workload,
                            namespace=f"dra-kueue-tenant-{tenant}",
                            item_labels=item_labels,
                            parallelism=4,
                        )
                    )
                else:
                    docs.append(
                        deployment(
                            name=workload,
                            namespace=f"dra-kueue-tenant-{tenant}",
                            item_labels=item_labels,
                        )
                    )
        return docs

    if phase in {"mixed-low", "mixed-high"}:
        half = counts["mixed"] // 2
        low = phase == "mixed-low"
        tenant = "a" if low else "b"
        priority = "dra-kueue-low" if low else "dra-kueue-high"
        offset = 0 if low else half
        for index in range(half):
            logical_index = index + offset
            workload = f"kueue-mixed-{'low' if low else 'high'}-{logical_index:06d}"
            item_labels = labels(run, profile, round_number, "mixed", workload, "kueue")
            docs.append(
                deployment(
                    name=workload,
                    namespace=f"dra-kueue-tenant-{tenant}",
                    item_labels=item_labels,
                    priority=priority,
                )
            )
        return docs

    if phase == "extended-smoke":
        workload = "kueue-extended-smoke"
        item_labels = labels(run, profile, round_number, "extended-smoke", workload, "kueue")
        docs.append(
            job(
                name=workload,
                namespace="dra-kueue-tenant-a",
                item_labels=item_labels,
                extended=True,
            )
        )
        return docs

    raise ValueError(f"unknown phase: {phase}")


def failure_document(run: str, profile: str, round_number: int, case: str, total_gpu: int) -> list[dict[str, Any]]:
    workload = f"failure-{case}"
    item_labels = labels(run, profile, round_number, case, workload, "kueue")
    kwargs: dict[str, Any] = {
        "name": workload,
        "namespace": "dra-kueue-failures",
        "item_labels": item_labels,
    }
    docs: list[dict[str, Any]] = []
    if case == "quota-insufficient":
        docs.append(claim_template("too-many-gpus", DEVICE_CLASS, total_gpu + 1))
        docs[-1]["metadata"]["namespace"] = "dra-kueue-failures"
        kwargs["template_name"] = "too-many-gpus"
    elif case == "no-matching-slice":
        kwargs["template_name"] = "empty-gpu"
    elif case in {"admitted-unschedulable", "wait-for-pods-ready"}:
        kwargs["impossible_node"] = True
    else:
        raise ValueError(f"unknown failure case: {case}")
    docs.append(job(**kwargs))
    return docs


def patch_kueue_manifest(source: pathlib.Path, config: pathlib.Path, destination: pathlib.Path) -> None:
    """Replace the embedded Kueue configuration without parsing all YAML.

    The released manifest contains one literal block named
    ``controller_manager_config.yaml``.  Preserving the rest byte-for-byte is
    safer than round-tripping a very large CRD bundle through a YAML library.
    """

    lines = source.read_text(encoding="utf-8").splitlines()
    config_lines = config.read_text(encoding="utf-8").rstrip().splitlines()
    marker_index = next(
        (index for index, line in enumerate(lines) if line.lstrip().startswith("controller_manager_config.yaml: |")),
        None,
    )
    if marker_index is None:
        raise ValueError("Kueue release manifest does not contain controller_manager_config.yaml literal block")
    marker_indent = len(lines[marker_index]) - len(lines[marker_index].lstrip())
    block_indent = marker_indent + 2
    end = marker_index + 1
    while end < len(lines):
        line = lines[end]
        if line.strip() and len(line) - len(line.lstrip()) <= marker_indent:
            break
        end += 1
    replacement = [" " * block_indent + line if line else "" for line in config_lines]
    output = lines[: marker_index + 1] + replacement + lines[end:]
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text("\n".join(output) + "\n", encoding="utf-8")


def read_nodes(path: pathlib.Path) -> list[str]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    items = payload.get("items", [])
    return [item["metadata"]["name"] for item in items]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    subparsers = parser.add_subparsers(dest="command", required=True)

    common = argparse.ArgumentParser(add_help=False)
    common.add_argument("--output", required=True, type=pathlib.Path)

    setup = subparsers.add_parser("setup", parents=[common])
    setup.add_argument("--nodes", required=True, type=int)
    setup.add_argument("--nodes-json", type=pathlib.Path)

    workloads = subparsers.add_parser("workloads", parents=[common])
    workloads.add_argument("--run", required=True)
    workloads.add_argument("--profile", required=True, choices=("functional", "scale"))
    workloads.add_argument("--round", required=True, type=int)
    workloads.add_argument("--total", required=True, type=int)
    workloads.add_argument("--start", type=int, default=0)
    workloads.add_argument("--count", type=int)
    workloads.add_argument(
        "--phase",
        required=True,
        choices=("direct", "short", "steady", "mixed-low", "mixed-high", "extended-smoke"),
    )

    failure = subparsers.add_parser("failure", parents=[common])
    failure.add_argument("--run", required=True)
    failure.add_argument("--profile", required=True, choices=("functional", "scale"))
    failure.add_argument("--round", required=True, type=int)
    failure.add_argument("--total-gpu", required=True, type=int)
    failure.add_argument(
        "--case",
        required=True,
        choices=("quota-insufficient", "no-matching-slice", "admitted-unschedulable", "wait-for-pods-ready"),
    )

    patch = subparsers.add_parser("patch-kueue-manifest")
    patch.add_argument("--source", required=True, type=pathlib.Path)
    patch.add_argument("--config", required=True, type=pathlib.Path)
    patch.add_argument("--output", required=True, type=pathlib.Path)
    kwok_config = subparsers.add_parser("kwok-config")
    kwok_config.add_argument("--template", required=True, type=pathlib.Path)
    kwok_config.add_argument("--manifest", required=True, type=pathlib.Path)
    kwok_config.add_argument("--output", required=True, type=pathlib.Path)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    if args.command == "setup":
        dump_documents(namespaces(), args.output / "namespaces.yaml")
        dump_documents(queue_documents(args.nodes), args.output / "queues.yaml")
        if args.nodes_json:
            node_names = read_nodes(args.nodes_json)
        else:
            node_names = [f"node-{index:06d}" for index in range(args.nodes)]
        if len(node_names) != args.nodes:
            raise ValueError(f"expected {args.nodes} node names, received {len(node_names)}")
        dump_documents(slice_documents(node_names), args.output / "resource-slices.yaml")
    elif args.command == "workloads":
        dump_documents(
            workload_documents(
                args.run,
                args.profile,
                args.round,
                args.total,
                args.phase,
                args.start,
                args.count,
            ),
            args.output,
        )
    elif args.command == "failure":
        dump_documents(
            failure_document(args.run, args.profile, args.round, args.case, args.total_gpu),
            args.output,
        )
    elif args.command == "patch-kueue-manifest":
        patch_kueue_manifest(args.source, args.config, args.output)
    elif args.command == "kwok-config":
        content = args.template.read_text(encoding="utf-8")
        marker = "__KUEUE_MANIFEST__"
        if content.count(marker) != 1:
            raise ValueError(f"kwokctl configuration must contain exactly one {marker} placeholder")
        if args.manifest.is_dir():
            resources = sorted(
                path.name
                for path in args.manifest.glob("*.yaml")
                if path.name != "kustomization.yaml"
            )
            if not resources:
                raise ValueError(f"Kueue Kustomize directory has no YAML resources: {args.manifest}")
            (args.manifest / "kustomization.yaml").write_text(
                "apiVersion: kustomize.config.k8s.io/v1beta1\n"
                "kind: Kustomization\n"
                "resources:\n"
                + "".join(f"- {resource}\n" for resource in resources),
                encoding="utf-8",
            )
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(content.replace(marker, str(args.manifest.resolve())), encoding="utf-8")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (OSError, ValueError, KeyError, json.JSONDecodeError) as error:
        print(f"generate.py: {error}", file=sys.stderr)
        raise SystemExit(1)

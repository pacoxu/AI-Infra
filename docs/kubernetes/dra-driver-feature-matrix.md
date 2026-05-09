---
status: Active
maintainer: pacoxu
last_updated: 2026-05-09
tags: kubernetes, dra, drivers, ecosystem, feature-matrix
canonical_path: docs/kubernetes/dra-driver-feature-matrix.md
source_urls: |-
  https://kubernetes.io/docs/concepts/scheduling-eviction/dynamic-resource-allocation/
  https://kubernetes.io/blog/2026/05/07/kubernetes-v1-36-dra-136-updates/
  https://github.com/kubernetes-sigs/dra-driver-nvidia-gpu
  https://github.com/ROCm/k8s-gpu-dra-driver
  https://github.com/kubernetes-sigs/dra-driver-cpu
  https://github.com/kubernetes-sigs/dra-driver-google-tpu
  https://github.com/Project-HAMi/k8s-dra-driver
  https://github.com/Project-HAMi/enflame-dra-driver
  https://github.com/kubernetes-sigs/cni-dra-driver
  https://github.com/kubernetes-sigs/dranet
  https://github.com/k8snetworkplumbingwg/dra-driver-sriov
  https://github.com/IBM/power-dra-driver
  https://github.com/ibm-aiu/dra-driver-spyre
  https://github.com/RBLN-SW/rbln-k8s-dra-driver
  https://github.com/kubevirt/dra-pci-driver
  https://github.com/DiamondLightSource/dra-usbip-driver
  https://github.com/ffromani/dra-driver-memory
  https://github.com/ffromani/dra-driver-cpumem
  https://github.com/fabiendupont/dra-driver-hugepages
  https://github.com/fabiendupont/k8s-dra-driver-time-share
  https://github.com/justin-oleary/cxl-dra-driver
  https://github.com/abhinavdahiya/k8s-dra-driver-trace-collector
  https://github.com/mewz-project/waiot-dra-driver
---

# Public Kubernetes DRA Driver Feature Matrix

This note maps **public GitHub DRA implementations** to a small set of
**higher-signal DRA features**. The goal is not to restate that each project is
"a DRA driver", but to answer a more practical question:

**Which drivers publicly show evidence that they already use specific DRA
features, which ones are still in progress, and where there is no visible
issue/PR signal yet?**

## Scope

As of **May 9, 2026**, this matrix only audits the user's **confirmed public
implementations** list. The more experimental / sparse-description repos are
listed separately at the end and are intentionally not scored in the main
matrix.

## Tracked Features

This page focuses on Beta / GA features and one older but operationally
important Beta feature:

- `PL`: Prioritized List (`v1.36`, Stable)
- `ER`: Extended Resource Support (`v1.36`, Beta)
- `PD`: Partitionable Devices (`v1.36`, Beta)
- `DT`: Device Taints and Tolerations (`v1.36`, Beta)
- `BC`: Device Binding Conditions (`v1.36`, Beta)
- `RHS`: Resource Health Status (`v1.36`, Beta)
- `CC`: Consumable Capacity (`v1.34+`, Beta, but important for sharing)

Alpha features such as workload-level claims, node allocatable resources,
resource pool visibility, device metadata, and deterministic device selection
are not part of the main scoring table here.

## Reading Guide

- `Supported`: explicit public repo signal in code, README, demo, test, or a
  clearly landed PR.
- `WIP`: explicit open issue or PR, or only weak partial signal without a clear
  landed example.
- `No visible issue/PR`: among the tracked features above, I did not find a
  strong public signal in that repo.

Important caveat:

- For some scheduler-side features like `PL`, a driver may be
  **theoretically compatible** without needing much driver-specific code.
  "No visible signal" here means **no explicit public repo evidence found**,
  not "impossible to use".

## Matrix: Confirmed Drivers With Explicit Signals

| Repo | Resource Type | Supported | WIP | No visible issue/PR yet | Example evidence |
| --- | --- | --- | --- | --- | --- |
| `kubernetes-sigs/dra-driver-nvidia-gpu` | NVIDIA GPU | `ER`, `PD`, `DT`, `RHS` | `BC` | `PL`, `CC` | `demo/specs/extended-resources/*`; `cmd/gpu-kubelet-plugin/partitions.go`; PR `#983`; PR `#689`; PR `#855` |
| `ROCm/k8s-gpu-dra-driver` | AMD GPU | `PD` | none | `PL`, `ER`, `DT`, `BC`, `RHS`, `CC` | PR `#33` mentions non-partitionable GPUs |
| `kubernetes-sigs/dra-driver-cpu` | CPU | `CC` | none | `PL`, `ER`, `PD`, `DT`, `BC`, `RHS` | `README.md`; `pkg/driver/dra_hooks.go`; PR `#16` |
| `Project-HAMi/k8s-dra-driver` | HAMi GPU | `ER`, `PD`, `CC` | none | `PL`, `DT`, `BC`, `RHS` | `templates/deviceclass-hami-gpu.yaml`; `cmd/hami-kubelet-plugin/partitions.go`; `cmd/hami-kubelet-plugin/hami_core.go` |
| `kubernetes-sigs/cni-dra-driver` | CNI-oriented network DRA | `CC` | none | `PL`, `ER`, `PD`, `DT`, `BC`, `RHS` | `pkg/discovery/resources.go`; `docs/demo/readme.md` |
| `k8snetworkplumbingwg/dra-driver-sriov` | SR-IOV network | `ER` | none | `PL`, `PD`, `DT`, `BC`, `RHS`, `CC` | `demo/extended-resource/*`; PR `#75` |
| `RBLN-SW/rbln-k8s-dra-driver` | Rebellions NPU | `ER` | none | `PL`, `PD`, `DT`, `BC`, `RHS`, `CC` | `templates/deviceclass-npu.yaml` |
| `DiamondLightSource/dra-usbip-driver` | USB/IP remote USB | `PL` | none | `ER`, `PD`, `DT`, `BC`, `RHS`, `CC` | `docs/tutorials/quick-start.md` contains `firstAvailable` |
| `ffromani/dra-driver-memory` | memory / hugepages | `CC` | none | `PL`, `ER`, `PD`, `DT`, `BC`, `RHS` | `pkg/sysinfo/rslice.go`; `discover_amd64_test.go` |
| `IBM/power-dra-driver` | IBM Power features | none | `PD` | `PL`, `ER`, `DT`, `BC`, `RHS`, `CC` | closed issue `#26 Support DRAPartitionableDevices` but no strong demo/example signal yet |

## Matrix: Confirmed Drivers With No High-Signal Match In Tracked Features

These repos may still be useful DRA implementations, but I did not find strong
public evidence for the tracked Beta / GA feature set above.

| Repo | Resource Type | Current read |
| --- | --- | --- |
| `kubernetes-sigs/dra-driver-google-tpu` | Google TPU | No strong public signal for `PL/ER/PD/DT/BC/RHS/CC` in this pass. |
| `Project-HAMi/enflame-dra-driver` | Enflame | Sparse public feature signal in tracked set. |
| `kubernetes-sigs/dranet` | network DRA | Strong topology/network positioning, but no high-confidence explicit match in the tracked feature set from this pass. |
| `ibm-aiu/dra-driver-spyre` | IBM AIU Spyre | Sparse public feature signal in tracked set. |
| `kubevirt/dra-pci-driver` | PCI passthrough | No high-signal public evidence yet for the tracked set. |
| `ffromani/dra-driver-cpumem` | combined CPU/memory/hugepages | Likely feature-adjacent to `CC`, but I did not find a strong explicit signal in this pass. |
| `fabiendupont/dra-driver-hugepages` | hugepages | Sparse public feature signal in tracked set. |
| `fabiendupont/k8s-dra-driver-time-share` | CPU time-sharing | Conceptually close to `CC`, but no strong explicit `allowMultipleAllocations`-style signal found in this pass. |
| `justin-oleary/cxl-dra-driver` | CXL pooled memory | Sparse public feature signal in tracked set. |
| `abhinavdahiya/k8s-dra-driver-trace-collector` | trace-processing capacity | DRA lifecycle signal exists, but no strong explicit match to the tracked Beta / GA feature list in this pass. |
| `mewz-project/waiot-dra-driver` | Waiot | Sparse public feature signal in tracked set. |

## Patterns Worth Calling Out

### 1. `ER` is the clearest migration signal today

Among public repos, the cleanest and most repeatable signal is
**Extended Resource Support**:

- `nvidia-gpu`
- `sriov`
- `HAMi`
- `RBLN`

This aligns with the operational need to let existing
`vendor.com/device: N` workloads move toward DRA gradually.

### 2. `PD` is concentrated in GPU-class drivers

The strongest public `PD` signals are still in GPU-oriented repos:

- `nvidia-gpu`
- `ROCm`
- `HAMi`

`IBM/power-dra-driver` has a public feature issue for partitionable devices,
but its public landing signal is weaker than NVIDIA/HAMi/ROCm.

### 3. `CC` is strongest in CPU / memory / sharing-oriented drivers

The clearest public `CC` signals came from:

- `dra-driver-cpu`
- `dra-driver-memory`
- `HAMi`
- `cni-dra-driver`

This is consistent with where DRA sharing semantics are most natural today:
CPU pools, memory slices, bandwidth-like resources, and fine-grained
multi-tenant shares.

### 4. `DT`, `BC`, and `RHS` are still sparse across public repos

The only repo with strong public signals across all three operational features
is `kubernetes-sigs/dra-driver-nvidia-gpu`:

- `DT`: merged PR `#983`
- `RHS`: merged PR `#689`
- `BC`: open PR `#855`

That does **not** mean other drivers cannot adopt these features. It means the
public repo evidence is still uneven.

## Experimental / Sparse-Description Repos Not Scored Here

I did not include the following repos in the scored matrix because the user
already separated them as likely experimental / sparse-description repos, and
their public metadata would need a deeper manual audit:

- `CoHDI/composable-dra-driver`
- `converged-computing/fluxbind-dra-driver`
- `lengrongfu/dra-device-driver`
- `xrwang8/ascend-dra-driver`
- `johnahull/dra-driver-nvme`
- `TheRealSibasishBehera/kubevirt-dra-driver`
- `pravk03/simple-cpu-dra-driver`
- `Tal-or/dra-cpu-driver`
- `gke-labs/dra-drivers`
- `ndbaker1/runtime-spec-dra-driver`
- `rotatingvio/cni-dra-driver`
- `toVersus/fake-dra-driver`
- `nojnhuh/dra-noop-driver`
- `nojnhuh/dra-driver-sandbox`
- `13567436138/k8s-dra-driver`

## Method Notes

This page is intentionally conservative:

- I preferred **public repo evidence** over inference.
- I treated **README/demo/test/code hits** as stronger than generic issue body
  matches.
- I treated a **closed issue without an obvious example/PR** as weaker than a
  landed demo or merged implementation PR.
- I hit GitHub Search API rate limits during the scan, so the matrix should be
  read as a **high-signal public snapshot**, not a mathematically exhaustive
  proof.

If you want to extend this page later, the next useful pass would be:

1. Add a per-repo `last updated` column.
2. Add a separate Alpha-feature appendix.
3. Re-check the sparse repos after they grow examples or design docs.

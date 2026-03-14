---
status: Active
maintainer: pacoxu
date: 2026-01-28
tags: kubernetes, pod, startup, optimization, gpu, ai, cold-start, dra
canonical_path: docs/blog/2026-01-28/gpu-pod-startup-ai.md
---

# Kubernetes Pod Startup Speed Optimization Guide: AI Edition

[中文版本](./gpu-pod-startup-ai_zh.md)

## Background: Why AI Pod Cold Start Is Fundamentally Harder

For general workloads, slow Pod startup is usually attributed to "slow image pulls,"
"heavy init logic," or "misconfigured probes." But when the workload is AI — especially
GPU inference or online training services — the situation changes entirely. "Pod started"
does not mean "business ready." You still face a chain of AI-specific initialization steps:
GPU driver and runtime initialization, preparation of model weights and tokenizer artifacts,
first-execution compilation and kernel cache building, and inference service warmup. Stacked
together, these make AI Pod cold start far more complex than typical applications.

More critically, the end-to-end critical path of AI cold start is often dominated by
node-side scaling rather than Pod creation itself. When no idle GPU nodes exist, the node
autoscaler must provision new nodes first; even after a node becomes ready, the accelerator
device plugin needs time to report GPU resources to the control plane, during which the Pod
can only sit in Pending state. In some environments, this waiting phase is measured in
minutes.

Therefore, the right perspective for an AI startup optimization guide is not "listing tips"
but "shortening the critical path" — decompose AI Pod startup into measurable stages, then
find the highest-leverage optimization for each stage.

## Defining the AI Pod Startup Timeline

The first step of optimization is not "tweaking configs" but defining what you are actually
measuring.

Kubernetes standardizes Pod lifecycle states and conditions. Phase and Conditions provide
sufficiently granular milestones — the Pending phase explicitly includes "waiting for
scheduling + image download" time. A suitable end-to-end startup timeline for AI (from
control plane Pod creation to business-ready) can be defined as follows:

First, capacity becomes available — either a node already exists, or node scaling completes.
Without a node, the Pod stays unschedulable, waiting for the node autoscaler. Second,
scheduling completes, corresponding to the Pod condition `PodScheduled=True`. Third, the
sandbox and network become ready, corresponding to `PodReadyToStartContainers=True` (beta,
enabled by default), meaning the Pod sandbox is created and networking is configured.
Fourth, init containers complete, corresponding to `Initialized=True`. Fifth, containers
and Pod become ready — `ContainersReady=True` and `Ready=True` — at which point the Pod
enters the Service load balancer pool.

For AI Pods, however, a traditional readinessProbe declaring Ready is often insufficient —
the model may not be fully loaded, warmup may not have run, and exposing such an instance
to traffic would cause first-request latency spikes. Kubernetes provides the
`readinessGates` mechanism: a Pod is considered Ready only when "all containers are ready"
AND "all readinessGates-specified custom conditions are True."

```yaml
spec:
  readinessGates:
  - conditionType: ai.example.com/ModelLoaded
  - conditionType: ai.example.com/WarmupDone
```

This lets you move warmup off the "live traffic critical path" and use readinessGates to
guarantee that the first request never hits a cold instance — the single most important
engineering practice for AI startup optimization.

## Segmented Profiling and Observability: Turning "Slow" into Optimizable Metrics

AI Pod cold start easily devolves into vague discussions of "it feels slow," ending with
"we changed a bunch of parameters but don't know if they helped." A more robust approach:
first use segmented timing to pin the bottleneck to a specific stage, then discuss
optimizations. Kubernetes provides rich enough signals through Phase, Conditions, and
events — you just need to stitch them into a timeline.

Here is a recommended set of "AI cold start segmented metrics":

`T_node_wait` is the time waiting for node scaling and accelerator capability readiness. In
GPU scenarios, the accelerator device plugin may need several minutes to report resources to
the cluster, meaning even after a node starts, the Pod still cannot schedule there — and may
even trigger duplicate scaling events.

`T_schedule` is the time from Pod creation to `PodScheduled=True`. When topology-awareness,
affinity rules, and multi-GPU constraints increase, this segment grows significantly.

`T_image` is the time for images and dependencies to reach the node (including decompression).
The larger the image layers, the higher the concurrency, and the more congested the node disk
and network, the more likely this becomes the primary bottleneck. Kubernetes provides parallel
image pull switches (serializeImagePulls and maxParallelImagePulls).

`T_model_artifact` is the time for model artifacts to reach a locally readable path — whether
downloaded from object storage, pulled from a model registry, or mounted and unpacked from an
OCI artifact. KServe documentation explicitly states: traditional S3/URI model pulls work for
small models but become a bottleneck for large models, significantly slowing startup under
autoscaling.

`T_runtime_init` covers GPU driver and runtime initialization, framework library loading, and
first-time CUDA-related overhead.

`T_warmup_compile` covers first inference, first graph compilation, first TensorRT engine
build, and other one-time costs. Without cache reuse, these costs recur with every Pod
rebuild.

Binding these segments to Kubernetes observability signals is key: `PodScheduled`,
`Initialized`, `Ready`, and other conditions all carry timestamps. For AI-specific
milestones like `ModelLoaded` and `WarmupDone`, custom conditions written back to PodStatus
make "AI business readiness" visible, monitorable, and alertable at the orchestration layer.

## Scheduling and Hardware Locality: GPUs Are Not Just a Number

Many "GPU Pod cold start" articles reduce scheduling to a single sentence: "just request
nvidia.com/gpu." This holds for single-GPU inference, but once you enter multi-GPU
inference/training, MIG partitioning, NUMA alignment, or GPU sharing, two categories of
issues directly impact startup speed: more complex scheduling paths, and post-scheduling
failures and retries on the node side.

First, understand the Kubernetes device plugin framework. Vendors report hardware as extended
resources to kubelet, which updates NodeStatus accordingly. But "hardware locality" does not
automatically equal "node-level availability." Take NUMA as an example: the Topology Manager
aims to align CPU, devices, and other resources to the same NUMA domain. However, the
scheduler lacks topology awareness, which can lead to "Pod scheduled to a node, but ultimately
fails at the node side due to Topology Manager" scenarios. Such failures cause retries and
startup time jitter.

At the cluster level, to avoid startup jitter from node-side AdmissionErrors, some platforms
report NUMA/GPU topology information to the scheduling layer for scoring or constraints.
Alibaba Cloud ACK's practice shows that relying solely on kubelet CPU policy and NUMA
topology policy leads to "scheduler unaware whether remaining CPU/GPU within a NUMA domain
satisfies QoS" problems, causing many Pods to enter AdmissionError after scheduling. After
enabling NUMA topology-aware scheduling, model loading time in certain scenarios dropped from
approximately 15.9s to approximately 5.4s (results vary by environment).

Next is DRA (Dynamic Resource Allocation). DRA's value extends beyond being "yet another way
to request GPUs." It introduces "device classes + selectors + claims" into scheduling and
allocation. Kubernetes documentation defines DRA as a mechanism for requesting and sharing
device resources (commonly hardware accelerators) between Pods: device drivers and
administrators define device classes, Kubernetes allocates matching devices to claims, and
places Pods on nodes that can access those devices. DRA elevates "topology/model/capacity"
constraints from "node label assembly + manual affinity" to "declarative device selection."

Additionally, GPU sharing strategies affect startup and stability. Taking NVIDIA GPU
Operator's time-slicing as an example, it achieves oversubscription by turning a single
physical GPU into multiple "replicas" for Pods to claim, but this sharing lacks MIG's
hardware memory and fault isolation capabilities. These facts influence how you define "Ready"
and implement warmup and isolation strategies, indirectly affecting cold start experience.

## Image and Model Distribution: Moving Large Files Off the Critical Path

AI Pod "downloads" typically have two layers: container images and model artifacts. Both are
often large and both can sit on the critical path. The optimization principle can be
summarized in one sentence: pre-place what you can, cache what you can, load on-demand what
you must.

At the container image level, Kubernetes provides parallel pull strategies: setting kubelet's
`serializeImagePulls` to false enables cross-Pod parallel image pulling, with
`maxParallelImagePulls` limiting concurrency to prevent image pulls from saturating network
or disk I/O. Note that kubelet does not pull images in parallel for multiple containers
within the same Pod.

A more aggressive approach is lazy pulling / remote snapshots. The stargz snapshotter
directly mounts rootfs layers from the remote registry instead of downloading and unpacking
everything — allowing containers to start even before image content fully lands on disk,
fetching actually accessed content on demand. The nydus-snapshotter takes a similar approach:
containers can run even with only partial image availability, fetching necessary data blocks
on demand. For multi-GB AI images, this optimization can reduce image pull time from minutes
to seconds.

At the model artifact level, KServe defines "storage initializer as init container to
download models to local directory" as the standard pattern. In the OCI modelcar approach,
KServe v0.14 made a key optimization: early modelcar as sidecar could not guarantee model
container started first; it was later reconfigured as an init container to ensure model images
are prefetched before the main container starts. It also introduced "Model Cache" using node
local storage to cache large models, shortening LLM Pod startup time.

Without KServe, you can take Kubernetes-native routes. First, package models as OCI artifacts,
letting models be distributed and cached "like images," benefiting from node-local image
caching and layer reuse. Second, directly mount OCI artifacts as volumes — Kubernetes image
volumes (v1.35 beta, enabled by default) allow mounting OCI registry content into the
container filesystem as a volume. For scenarios needing large read-only weight files, this
provides an earlier, more controllable loading point than "download after application starts."

For model repositories and caching, if you use the Hugging Face Hub ecosystem, the
most-overlooked startup cost is often "repeated downloads and decompression."
huggingface_hub defaults its cache to `~/.cache/huggingface/hub`, configurable via `HF_HOME`
or `HF_HUB_CACHE` environment variables to faster paths (like node-local NVMe or a shared
read-only cache volume).

Finally, model format itself matters. Safetensors is positioned as "safe (relative to pickle)
and fast (zero-copy)" tensor storage, supporting partial tensor loading (especially meaningful
for multi-GPU/sharded loading). In contrast, PyTorch's torch.save uses Python pickle for
serialization, and torch.load uses pickle deserialization; pickle's executable deserialization
risk has been repeatedly highlighted by supply chain security research — loading untrusted
model files can lead to arbitrary code execution. For ultimate "weight-to-GPU speed," vLLM
documentation mentions fastsafetensors can leverage GPU Direct Storage to load weights
directly into GPU memory, bypassing the CPU.

## Runtime Initialization and Compilation Caching: Reducing First-Time Penalties

Another "hidden heavyweight" of AI Pod cold start is one-time initialization cost. It is not
a single slow point but multiple "first times" stacking: first GPU initialization trigger,
first CUDA JIT trigger, first framework compilation trigger, first inference engine graph
optimization and kernel generation.

For GPU initialization, NVIDIA's Driver Persistence documentation describes a specific and
actionable fact: in Linux headless/short-job scenarios, GPUs may initialize on each job start
and de-initialize after; applications triggering GPU initialization may incur approximately
1-3 seconds of startup cost per GPU (attributed to ECC scrubbing in the documentation), with
persistence mode / persistence daemon provided to maintain GPU initialization state. In
nvidia-smi, persistence mode is defined as "keeping the driver loaded even without active
clients, thereby minimizing driver load latency."

For CUDA JIT, the compute cache mechanism caches binaries generated from JIT-compiled PTX to
avoid recompilation. Environment variables `CUDA_CACHE_PATH` and `CUDA_CACHE_MAXSIZE`
control cache location and size. There is a cold-start-specific pitfall: if the default
cache directory sits on a slow network home directory, it can cause extremely long application
startup times — in such cases, set `CUDA_CACHE_PATH` to a faster filesystem.

For framework compilation, PyTorch's torch.compile cache writes to
`TORCHINDUCTOR_CACHE_DIR` (defaulting to something like `/tmp/torchinductor_<user>`). For
containerized deployments, the default cache easily vanishes with the Pod. If you mount it to
a persistent volume or node-local persistent path and reuse it across rolling upgrades and
elastic scaling, you can reduce "compile on every cold start" to "compile once per
hardware/model version combination."

For inference engines, TensorRT's architecture documentation provides a direct initialization
acceleration option: CUDA lazy loading (`CUDA_MODULE_LOADING=LAZY`) can significantly reduce
TensorRT's peak GPU/host memory usage and accelerate initialization, with negligible
performance impact (approximately <1%). If using ONNX Runtime + TensorRT EP, documentation
highlights "cache" as a first-class capability: TensorRT EP cache can reduce session creation
time from minutes to seconds; TensorRT RTX EP further provides runtime cache, caching
JIT-compiled CUDA kernels per engine for deserialization on subsequent loads to reduce session
load time.

This section distills into one engineering principle: externalize one-time costs (driver init
/ JIT / compile / engine build) as reusable cache assets, and ensure they keep hitting across
Pod rebuilds and scaling events.

## Pre-warming and Elasticity: Pod Pools, Model Warmup, and Cost Tradeoffs

After addressing the "download surface" and "first-time initialization surface," you arrive
at the final question: how to enable "second-scale expansion" under traffic bursts without
exploding costs. Think of this as a triangle: latency, cost, complexity — each pre-warming
approach occupies a different position.

From "moving first-request latency off the critical path," inference service built-in warmup
is the most straightforward approach. Taking Triton as an example, its ModelWarmup mechanism
allows the server to execute a series of warmup inference requests before serving external
traffic. Only after a model instance successfully completes warmup does it begin serving.
Some backends delay initialization until the first inference (such as TF-TRT optimization);
ModelWarmup moves these unpredictable latencies away from the client side.

Aligning warmup with Kubernetes Ready semantics is the single most important pattern for AI
startup optimization: use readinessGates or readinessProbe to keep Pods out of the load
balancer pool until warmup completes, mechanistically guaranteeing that first requests never
hit cold instances.

From "moving scaling wait off the critical path," node/capacity reservation is another
high-leverage tool. Kubernetes documentation defines node overprovisioning as using
negative-priority placeholder Pods to pre-reserve compute resources, reducing the time new
Pods spend in Pending during scaling events. AWS EKS best practices documentation notes:
Cluster Autoscaler conserves costs by making Pods wait for node scaling, but nodes may need
minutes to become available; overprovisioning trades cost for latency.

GPU scenarios introduce an additional special waiting item: accelerator device plugins during
scaling may need minutes to report resources, meaning Pods cannot immediately schedule to new
nodes even after they appear — potentially triggering duplicate scaling events. This means AI
"pre-warming" should not focus only on in-Pod warmup but also on node-side GPU stack
readiness — drivers, container runtime, device plugin, and resource reporting across the
entire chain.

From "moving model distribution off the critical path," KServe's evolution provides a
systematic case study: modelcars reuse image distribution and caching through OCI model
artifacts; to solve sidecar startup ordering uncertainty, OCI model containers were
reconfigured as init containers for prefetching; local model caching was then introduced to
further shorten LLM Pod startup. This abstracts into a general conclusion: AI pre-warming is
not just "sending a few empty requests" but "building reusable distribution and caching layers
around model artifacts."

GKE's Agent Sandbox approaches pre-warming from another dimension. It combines gVisor security
sandboxes with container snapshot technology, creating gVisor snapshots of fully configured
containers (including dependency libraries, runtime state, and pre-loaded models) during
initialization. When new requests arrive, new instances can be restored from snapshots in
hundreds of milliseconds. Compared to traditional cold starts, Agent Sandbox achieves up to
90% startup time improvement while maintaining gVisor sandbox-level security isolation. This
is especially valuable for LLM Agents, Serverless AI, and multi-tenant AI services requiring
both fast startup and strong isolation.

## Conclusion: Three Often-Overlooked Critical Levers

To summarize, beyond the commonly discussed "scheduling / model loading / warmup" trio, at
least three categories of levers often have greater impact on end-to-end cold start:

First is capacity provisioning and node-side accelerator stack readiness. Node scaling can
take minutes, device plugin reporting can take minutes, and stacked together, Pod Pending time
far exceeds expectations.

Second is critical-path removal for image/model distribution. Parallel pulls, lazy pulling,
OCI artifactification, node-local caching — the core idea is "don't make the user's first
request wait for file IO."

Third is one-time initialization and compilation cache reuse. Driver persistence, CUDA/JIT
cache, torch.compile cache, inference engine cache — transforming "first-time" costs into
reusable assets.

Combining these three lever categories with conventional scheduling optimization, model format
optimization, and service warmup constitutes the complete critical path for AI Pod cold start
optimization.

---

## Related Resources

<a href="https://kubernetes.io/docs/concepts/workloads/pods/pod-lifecycle/">
Kubernetes Pod Lifecycle</a>

<a href="https://kubernetes.io/docs/concepts/scheduling-eviction/dynamic-resource-allocation/">
Dynamic Resource Allocation (DRA)</a>

<a href="https://kubernetes.io/docs/tasks/manage-gpus/scheduling-gpus/">
Scheduling GPUs</a>

<a href="https://docs.nvidia.com/deploy/driver-persistence/index.html">
NVIDIA Driver Persistence</a>

<a href="https://docs.nvidia.com/cuda/cuda-c-best-practices-guide/">
CUDA Best Practices Guide</a>

<a href="https://pytorch.org/docs/stable/torch.compiler_faq.html">
PyTorch torch.compile FAQ</a>

<a href="https://huggingface.co/docs/safetensors/index">Safetensors</a>

<a href="https://onnxruntime.ai/docs/execution-providers/TensorRT-ExecutionProvider.html">
ONNX Runtime TensorRT EP</a>

<a href="https://docs.nvidia.com/deeplearning/triton-inference-server/user-guide/docs/user_guide/model_configuration.html">
Triton Model Configuration (ModelWarmup)</a>

<a href="https://kserve.github.io/website/latest/">KServe Documentation</a>

<a href="https://github.com/containerd/stargz-snapshotter">
Stargz Snapshotter</a>

<a href="https://github.com/containerd/nydus-snapshotter">
Nydus Snapshotter</a>

<a href="https://cloud.google.com/blog/products/containers-kubernetes/agentic-ai-on-kubernetes-and-gke">
GKE Agent Sandbox</a>

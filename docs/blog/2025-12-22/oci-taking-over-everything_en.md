---
status: Active
maintainer: pacoxu
last_updated: 2025-12-22
tags: oci, kubernetes, ai-infrastructure, docker, modelpack, harbor
---

# OCI Is Quietly Taking Over Everything: A Single Distribution Backbone for Images, Charts, AI Models, and WASM

**Note:** Some content was generated with AI assistance. Please verify before
using in production.

## Table of Contents

- [Hook: A KubeCon Atlanta takeaway that says the quiet part out loud](#hook-a-kubecon-atlanta-takeaway-that-says-the-quiet-part-out-loud)
- [Why the AI era amplifies the need for OCI](#why-the-ai-era-amplifies-the-need-for-oci)
- [Kubernetes: OCI Image Volumes are enabled by default in v1.35 (still Beta)](#kubernetes-oci-image-volumes-are-enabled-by-default-in-v135-still-beta)
- [ModelPack: making models first-class OCI citizens](#modelpack-making-models-first-class-oci-citizens)
- [Harbor: from image/chart registry to model-aware artifact hub](#harbor-from-imagechart-registry-to-model-aware-artifact-hub)
- [Docker Model Runner: unifying inference engines and OCI distribution](#docker-model-runner-unifying-inference-engines-and-oci-distribution)
- [ORAS: the Swiss Army knife for OCI artifacts](#oras-the-swiss-army-knife-for-oci-artifacts)
- [Ollama and similar specs: standardize distribution first, format later](#ollama-and-similar-specs-standardize-distribution-first-format-later)
- [WASM artifact registries: the next OCI unification puzzle piece](#wasm-artifact-registries-the-next-oci-unification-puzzle-piece)
- [Market signals: Bitnami policy changes and Docker DHI](#market-signals-bitnami-policy-changes-and-docker-dhi)
- [Performance and what's next](#performance-and-whats-next)
- [A practical adoption roadmap](#a-practical-adoption-roadmap)
- [References](#references)

## Hook: A KubeCon Atlanta takeaway that says the quiet part out loud

A KubeCon North America (Atlanta) recap distilled a major shift into one
sentence: **OCI is quietly taking over everything**. It is no longer "just the
container image format." Helm charts, WASM modules, and now AI models are
increasingly distributed via **OCI registries**.

Reference link:
https://metalbear.com/blog/kubecon-atlanta-takeaways/

This is not a branding story; it is an operational one. Organizations already
standardized on registries for auth, policy, scanning, and provenance.
Extending that same backbone to "non-image artifacts" is the most pragmatic
path.

Reference link:
https://www.docker.com/blog/oci-artifacts-for-ai-model-packaging/

## Why the AI era amplifies the need for OCI

AI changes the distribution problem in three ways:

- **Size**: models and GPU stacks routinely hit tens of GiB; resumable and
  parallelized pulls become critical.

Reference link:
https://fuweid.com/post/2025-containerd-220-rebase-snapshot/

- **Governance**: SBOMs, signatures, attestations, and audit-ready metadata
  need to travel with the artifact.

Reference link:
https://www.docker.com/blog/docker-hardened-images-for-every-developer/

- **Unification**: enterprises do not want separate platforms for container
  images, charts, models, plugins, and WASM components.

Docker's rationale for choosing **OCI artifacts** for model packaging makes
this explicit: reuse existing registry workflows and unlock deeper integration
with containerd/Kubernetes over time.

Reference link:
https://www.docker.com/blog/oci-artifacts-for-ai-model-packaging/

Additionally, CNCF published a blog post discussing how OCI Artifacts will
drive future AI use cases:

Reference link:
https://www.cncf.io/blog/2025/08/27/how-oci-artifacts-will-drive-future-ai-use-cases/

## Kubernetes: OCI Image Volumes are enabled by default in v1.35 (still Beta)

Kubernetes is steadily turning OCI registries into a first-class delivery path
for "runtime payloads" beyond container images:

- v1.31 introduced **read-only volumes based on OCI artifacts** (Alpha).

Reference link:
https://kubernetes.io/blog/2024/08/16/kubernetes-1-31-image-volume-source/

- The feature reached **Beta** (v1.33+).

Reference link:
https://kubernetes.io/docs/tasks/configure-pod-container/image-volumes/

- In v1.35, the Beta capability is **enabled by default**, with runtime
  requirements (e.g., containerd v2.1+).

Reference link:
https://kubernetes.io/blog/2025/12/17/kubernetes-v1-35-release/

This enables a cleaner pattern: keep your runtime image lean, and mount
models/config/plugins from the same OCI registry infrastructure you already
govern.

### What problem does it solve?

Traditional approaches for delivering models/config/binaries to Pods:

- Bundle into application image (results in huge images, frequent changes)
- Download via initContainer at startup (slow, unstable, not auditable)

ImageVolume's value: **Decouple "runtime image" from "runtime artifacts
(models, config, WASM)"**, and unify the distribution path to OCI Registry.

Reference link:
https://kubernetes.io/blog/2024/08/16/kubernetes-1-31-image-volume-source/

Official Kubernetes blog links:

https://kubernetes.io/blog/2024/08/16/kubernetes-1-31-image-volume-source/
https://kubernetes.io/blog/2025/12/17/kubernetes-v1-35-release/

## ModelPack: making models first-class OCI citizens

ModelPack's model-spec frames the "AI model-centric infrastructure age" and
proposes a model packaging approach compatible with OCI image spec and artifact
guidelines, explicitly calling out Kubernetes OCI volume sources as a target
integration point.

Reference link:
https://github.com/modelpack/model-spec

In narrative terms:

> Kubernetes provides the **mount point** (ImageVolume).
> ModelPack provides the **model packaging semantics** that can live inside OCI
> registries.

Reference link:
https://github.com/modelpack/model-spec

ModelPack workflow visualization:

![ModelPack Flow](https://github.com/user-attachments/assets/184db2f5-a6b5-4011-8167-be9310e7fffd)

(Diagram: ModelPack packages AI models → OCI Artifact provides distribution
standard across registries → Image Volume enables end users to consume directly
from Kubernetes API)

## Harbor: from image/chart registry to model-aware artifact hub

Harbor v2.14.0 release notes highlight **Enhanced CNAI Model integration**,
including support for **raw CNAI model format** referenced by the model spec.

Reference link:
https://github.com/goharbor/harbor/releases

That is a strong signal: the registry layer is evolving to manage models with
the same enterprise-grade lifecycle controls as other artifacts.

Reference link:
https://github.com/goharbor/harbor/releases

Harbor community proposal details:
https://github.com/goharbor/community/blob/main/proposals/new/AI-model-processor.md

Related GitHub issue:
https://github.com/goharbor/harbor/issues/21229

## Docker Model Runner: unifying inference engines and OCI distribution

Docker is pushing two aligned moves:

1. **OCI artifacts for model packaging** (why OCI, how it works, what it
   unlocks).

Reference link:
https://www.docker.com/blog/oci-artifacts-for-ai-model-packaging/

2. **A single inference entry point** that supports multiple engines:

   - GGUF → llama.cpp
   - safetensors → vLLM

   and both can be pushed/pulled as OCI images to any OCI registry.

Reference link:
https://www.docker.com/blog/docker-model-runner-integrates-vllm/

Docker also integrated Model Runner into Hugging Face's local apps workflow,
making "discover → pull → run" feel as frictionless as pulling a container
image.

Reference link:
https://www.docker.com/blog/docker-model-runner-on-hugging-face/

## ORAS: the Swiss Army knife for OCI artifacts

ORAS positions itself as the de facto tooling for OCI artifacts—treating media
types as first-class, not assuming everything is a container image, and
providing CLI plus client libraries.

Reference link:
https://oras.land/

This is exactly what you want once models/WASM/SBOMs/policies are stored
side-by-side in registries.

Reference link:
https://oras.land/

## Ollama and similar specs: standardize distribution first, format later

Ollama's success proves:

- Developers need an end-to-end experience from "acquire model" to "run model"
- Natural conventions emerge around model organization and metadata

From an enterprise/cloud-native perspective, **consensus often starts with
"distribution protocol and registry compatibility (OCI Distribution/Registry)"
first**, then converges on "model format and metadata specs" later. ModelPack
explicitly lists Ollama as a potential integration target.

Reference link:
https://github.com/modelpack/model-spec

## WASM artifact registries: the next OCI unification puzzle piece

WASM module/component distribution mirrors AI model distribution needs: smaller
but more diverse, fast iteration, strong supply-chain requirements.

The industry increasingly uses OCI registries for WASM artifacts:

- CNCF TAG Runtime guidance on mapping WASM to OCI artifacts.

Reference link:
https://github.com/modelpack

- Microsoft's perspective on distributing WASM components via OCI registries.

Reference link:
https://wasmcloud.com/docs/deployment/netconf/registries/

- wasmCloud and Spin workflows built around registries.

Reference link:
https://github.com/goharbor/harbor/issues/21229

## Market signals: Bitnami policy changes and Docker DHI

### Bitnami: Free image/chart distribution policy adjustment (effective Aug 28, 2025)

Bitnami/charts announcement provides clear timeline and changes:

- Effective Aug 28, 2025: public catalog changes; massive content migration to
  legacy; community free tier reduced to "development use, mostly latest"; with
  brownout schedule and migration guidance.

Reference link:
https://github.com/bitnami/charts/issues/35164

This type of event is perfect for illustrating "why you need a controlled
distribution backbone": production systems should not bet entirely on the
long-term stability of a single public catalog.

### Docker DHI: Making "more secure base images" the default option

Docker's Dec 17, 2025 announcement emphasizes: Docker Hardened Images (DHI)
catalog (based on Debian/Alpine) will be opened under Apache 2.0, with
"verifiable provenance, reproducible builds, attestations" as part of the
default security baseline.

Reference links:
https://docs.docker.com/dhi/
https://www.docker.com/press-release/docker-makes-hardened-images-free-open-and-transparent-for-everyone/

## Performance and what's next

As models and "super-large images" become normal, the ecosystem is addressing
gaps in runtime and spec layers:

- containerd v2.2's Rebase Snapshot is expected to significantly improve large
  image download efficiency, leveraging OCI Distribution's resumable/parallel
  capabilities.

Reference link:
https://fuweid.com/post/2025-containerd-220-rebase-snapshot/

- OCI community discussions continue around better handling of large objects in
  image/distribution specs.

Reference link:
https://github.com/opencontainers/image-spec/issues/1190

## A practical adoption roadmap

1. **Short-term (1-2 months)**: Move Helm charts to OCI registries (official
   workflow exists today).

Reference link:
https://helm.sh/docs/topics/registries/

2. **Mid-term (1-2 quarters)**: Adopt ORAS for non-image artifacts (SBOMs,
   policies, model attachments).

Reference link:
https://oras.land/

3. **Long-term**:

   - Evaluate Kubernetes ImageVolume (v1.35 default-enabled Beta) for
     models/config/plugins; upgrade runtimes accordingly (e.g., containerd
     v2.1+).

Reference link:
https://kubernetes.io/blog/2025/12/17/kubernetes-v1-35-release/

   - Push model packaging standardization (ModelPack) + registry-native support
     (Harbor) to complete the governance loop.

Reference link:
https://github.com/modelpack/model-spec

4. **Community direction**: **Today's model distribution remains fragmented,
   and OCI is the unifying bridge**. Consider developing tools like hg2oci to
   sync Hugging Face Hub models to OCI registries (e.g., GitHub Container
   Registry or Docker Hub) for offline deployment and enterprise intranet
   distribution.

Reference link:
https://www.docker.com/blog/oci-artifacts-for-ai-model-packaging/

## References

### KubeCon & CNCF

- KubeCon Atlanta Takeaways:
  https://metalbear.com/blog/kubecon-atlanta-takeaways/
- CNCF Blog - OCI Artifacts for AI:
  https://www.cncf.io/blog/2025/08/27/how-oci-artifacts-will-drive-future-ai-use-cases/

### Kubernetes

- Kubernetes v1.31 Image Volume Source:
  https://kubernetes.io/blog/2024/08/16/kubernetes-1-31-image-volume-source/
- Kubernetes v1.35 Release:
  https://kubernetes.io/blog/2025/12/17/kubernetes-v1-35-release/
- Image Volumes Documentation:
  https://kubernetes.io/docs/tasks/configure-pod-container/image-volumes/

### ModelPack & Harbor

- ModelPack model-spec:
  https://github.com/modelpack/model-spec
- Harbor v2.14.0 Release Notes:
  https://github.com/goharbor/harbor/releases/tag/v2.14.0
- Harbor Community Proposal:
  https://github.com/goharbor/community/blob/main/proposals/new/AI-model-processor.md
- Harbor AI Model Issue:
  https://github.com/goharbor/harbor/issues/21229

### Docker

- Why Docker Chose OCI Artifacts for AI Model Packaging:
  https://www.docker.com/blog/oci-artifacts-for-ai-model-packaging/
- Docker Model Runner + vLLM:
  https://www.docker.com/blog/docker-model-runner-integrates-vllm/
- Docker Model Runner on Hugging Face:
  https://www.docker.com/blog/docker-model-runner-on-hugging-face/
- Docker Hardened Images:
  https://docs.docker.com/dhi/
- Docker DHI Press Release:
  https://www.docker.com/press-release/docker-makes-hardened-images-free-open-and-transparent-for-everyone/
- Docker Hardened Images Blog:
  https://www.docker.com/blog/docker-hardened-images-for-every-developer/

### ORAS & Tools

- ORAS Official Site:
  https://oras.land/
- Helm OCI Registries:
  https://helm.sh/docs/topics/registries/

### WASM

- wasmCloud OCI Registries:
  https://wasmcloud.com/docs/deployment/netconf/registries/

### containerd

- containerd v2.2.0 Rebase Snapshot:
  https://fuweid.com/post/2025-containerd-220-rebase-snapshot/

### OCI Spec

- OCI Image Spec Issue #1190:
  https://github.com/opencontainers/image-spec/issues/1190

### Industry News

- Bitnami Charts Catalog Changes (Aug 28, 2025):
  https://github.com/bitnami/charts/issues/35164

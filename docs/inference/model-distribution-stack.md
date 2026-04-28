---
status: Active
maintainer: pacoxu
last_updated: 2026-04-28
tags: inference, model-distribution, registry, huggingface, oci
canonical_path: docs/inference/model-distribution-stack.md
---

# One Diagram for Model Distribution: Hugging Face, MatrixHub, Harbor, Dragonfly, ModelPack, and ModelExpress

This page puts several frequently mixed-up projects on a single diagram. The
goal is to separate the **model source**, **private registry**, **cluster
distribution**, and **runtime acceleration** layers.

## The Stack in One Diagram

```mermaid
flowchart TB
  classDef oci fill:#e8f3ff,stroke:#2b6cb0,color:#0f172a;
  classDef model fill:#fff1e6,stroke:#c2410c,color:#111827;
  classDef runtime fill:#ecfdf5,stroke:#047857,color:#111827;
  classDef neutral fill:#f8fafc,stroke:#64748b,color:#111827;

  subgraph S["1. Provider / Server View"]
    direction LR

    subgraph OCI_LANE["Docker image / OCI artifact lane"]
      direction TB
      DH["Docker Hub<br/>public image registry"]
      HB["Harbor<br/>local Docker Hub / distribution<br/>private OCI registry"]
      DH -->|"sync / replicate / private image management"| HB
    end

    subgraph MODEL_LANE["Model distribution lane"]
      direction TB
      HF["Hugging Face<br/>public model hub"]
      MS["ModelScope<br/>public model / dataset / API platform"]
      MX["MatrixHub<br/>private Hugging Face<br/>HF-compatible private hub"]
      MP["ModelPack<br/>package model as OCI artifact"]
      HF -->|"mirror / cache"| MX
      MS -. "one public upstream" .-> MX
      MP -->|"model enters OCI workflow"| HB
    end
  end

  subgraph C["2. Client / Download View"]
    direction LR
    PULL["HF-compatible SDK / CLI / API"]
    DF["Dragonfly<br/>node-level P2P<br/>image / artifact / model files"]
  end

  subgraph U["3. End User / Runtime View"]
    direction LR
    APP["End users / apps"]
    SVC["Inference service<br/>vLLM / SGLang / Dynamo"]
    ME["ModelExpress<br/>GPU worker weight P2P"]

    subgraph N1["Node 1"]
      direction TB
      F1["Local image / model file cache"]
      subgraph G1["GPU workers"]
        W11["GPU 0 worker"]
        W12["GPU 1 worker"]
      end
    end

    subgraph N2["Node 2"]
      direction TB
      F2["Local image / model file cache"]
      subgraph G2["GPU workers"]
        W21["GPU 0 worker"]
        W22["GPU 1 worker"]
      end
    end
  end

  MX -->|"HF-compatible endpoint"| PULL
  HF -->|"hf://"| DF
  MS -->|"modelscope://"| DF
  HB -->|"OCI pull"| DF

  PULL --> F1
  PULL --> F2
  DF --> F1
  DF --> F2
  F1 <-->|"Dragonfly: node-level P2P file chunks"| F2

  F1 --> W11
  F1 --> W12
  F2 --> W21
  F2 --> W22

  APP --> SVC
  SVC --> W11
  SVC --> W21

  ME -. "weight reuse / hot replica propagation" .-> W11
  ME -. "weight reuse / hot replica propagation" .-> W12
  ME -. "weight reuse / hot replica propagation" .-> W21
  ME -. "weight reuse / hot replica propagation" .-> W22

  W11 <-->|"same-node GPU / NVLink"| W12
  W12 <-->|"cross-node RDMA / UCX / NIXL"| W21
  W21 <-->|"same-node GPU / NVLink"| W22

  class DH,HB oci;
  class HF,MS,MX,MP,PULL model;
  class DF,F1,F2 neutral;
  class APP,SVC,ME,W11,W12,W21,W22 runtime;

  style OCI_LANE fill:#e8f3ff,stroke:#2b6cb0,stroke-width:2px
  style MODEL_LANE fill:#fff1e6,stroke:#c2410c,stroke-width:2px
  style N1 fill:#f0fdf4,stroke:#16a34a,stroke-width:1px
  style N2 fill:#f0fdf4,stroke:#16a34a,stroke-width:1px
  linkStyle 5,6,7,9,10 stroke:#c2410c,stroke-width:3px,color:#c2410c
  linkStyle 8 stroke:#2b6cb0,stroke-width:3px,color:#2b6cb0
```

## Read the Diagram by Role

- **Provider / server view**: The blue lane is the Docker image / OCI artifact
  path. Harbor is easiest to read here as a local Docker Hub / Distribution
  style private registry. The orange lane is the model distribution path, with
  Hugging Face, ModelScope, and MatrixHub on that side.
- **Download view**: MatrixHub exposes an HF-compatible pull path. Dragonfly
  handles node-level file distribution and can serve OCI pulls from Harbor as
  well as `hf://` and `modelscope://` downloads.
- **End user / runtime view**: Model files first land in node-local caches,
  then feed GPU workers. ModelExpress sits later in the path and accelerates
  weight reuse between workers, including cross-node GPU transfers over RDMA.

Line colors also carry meaning:

- **Orange links**: HF-compatible or public model hub download paths
- **Blue links**: OCI pull paths
- **Grey node-to-node links**: Dragonfly node-level file chunk propagation
- **Green GPU-to-GPU links**: runtime weight sharing paths relevant to ModelExpress

## Focused Reference Diagrams

### 1. Dragonfly path: Harbor plus public model hubs

```mermaid
flowchart LR
  classDef oci fill:#e8f3ff,stroke:#2b6cb0,color:#0f172a;
  classDef model fill:#fff1e6,stroke:#c2410c,color:#111827;
  classDef neutral fill:#f8fafc,stroke:#64748b,color:#111827;

  HF["Hugging Face / ModelScope<br/>public model hub"]
  HB["Harbor<br/>private OCI registry"]
  DF["Dragonfly<br/>seed peer + scheduler + peers"]

  subgraph CL["Cluster nodes"]
    direction LR
    N1["Node 1<br/>local file cache"]
    N2["Node 2<br/>local file cache"]
    N3["Node 3<br/>local file cache"]
  end

  HF -->|"hf:// / modelscope://"| DF
  HB -->|"OCI pull"| DF
  DF --> N1
  DF --> N2
  DF --> N3
  N1 <-->|"node-level P2P file chunks"| N2
  N2 <-->|"node-level P2P file chunks"| N3

  class HB oci;
  class HF model;
  class DF,N1,N2,N3 neutral;
  linkStyle 0 stroke:#c2410c,stroke-width:3px,color:#c2410c
  linkStyle 1 stroke:#2b6cb0,stroke-width:3px,color:#2b6cb0
```

### 2. MatrixHub path: private Hugging Face style access

```mermaid
flowchart LR
  classDef public fill:#fff1e6,stroke:#c2410c,color:#111827;
  classDef private fill:#ecfdf5,stroke:#047857,color:#111827;
  classDef client fill:#f8fafc,stroke:#64748b,color:#111827;

  DEV["Model provider / fine-tune team"]
  HF["Hugging Face / ModelScope<br/>public model hub"]
  MX["MatrixHub<br/>private Hugging Face<br/>HF-compatible endpoint"]
  CLI["HF-compatible clients<br/>transformers / vLLM / SDK / CLI"]
  N1["Training / eval / inference node A"]
  N2["Training / eval / inference node B"]

  DEV -->|"private upload"| MX
  HF -->|"mirror / cache"| MX
  CLI -->|"HF-compatible pull"| MX
  MX --> N1
  MX --> N2

  class HF public;
  class MX private;
  class DEV,CLI,N1,N2 client;
  linkStyle 1,2 stroke:#c2410c,stroke-width:3px,color:#c2410c
```

### 3. ModelExpress path: runtime weight sharing after initial pull

```mermaid
flowchart LR
  classDef public fill:#fff1e6,stroke:#c2410c,color:#111827;
  classDef runtime fill:#ecfdf5,stroke:#047857,color:#111827;
  classDef neutral fill:#f8fafc,stroke:#64748b,color:#111827;

  HF["Hugging Face<br/>public model hub"]
  ME["ModelExpress<br/>metadata + runtime weight P2P"]

  subgraph N1["Source node"]
    direction TB
    F1["local model cache"]
    W11["GPU 0 worker"]
    W12["GPU 1 worker"]
  end

  subgraph N2["Target node"]
    direction TB
    F2["local model cache / fallback"]
    W21["GPU 0 worker"]
    W22["GPU 1 worker"]
  end

  HF -->|"first pull / seed load"| F1
  F1 --> W11
  F1 --> W12
  F2 --> W21
  F2 --> W22

  ME -. "coordination" .-> W11
  ME -. "coordination" .-> W12
  ME -. "coordination" .-> W21
  ME -. "coordination" .-> W22

  W11 <-->|"same-node NVLink"| W12
  W12 <-->|"cross-node RDMA / UCX / NIXL"| W21
  W21 <-->|"same-node NVLink"| W22

  class HF public;
  class ME,W11,W12,W21,W22 runtime;
  class F1,F2 neutral;
```

## Read the Diagram from Left to Right

### 1. Hugging Face

Hugging Face is the public upstream model hub. It is the default source for
many training and inference workflows using `huggingface_hub`,
`transformers`, `vLLM`, and similar clients.

### 2. Private Hugging Face

Private Hugging Face is a **target state**, not a single product. It means:

- private model hosting
- access control and governance
- low-friction compatibility with existing HF-style workflows
- predictable distribution inside enterprise or air-gapped environments

### 3. MatrixHub

MatrixHub is the most direct path to that target state in this stack. It acts
as an **HF-compatible private hub**, so teams can keep the Hugging Face
interaction model while moving to a governed internal endpoint.

In practice, MatrixHub is the layer for:

- private model registry and lifecycle governance
- transparent HF proxy behavior
- on-demand caching from public Hugging Face
- multi-region or air-gapped distribution workflows

### 4. ModelPack + Harbor + Dragonfly

This path is different. It is **OCI-first**, not HF-first.

- `ModelPack` provides a packaging/spec path for OCI-based model artifacts.
- `Harbor` provides the private OCI registry, including enterprise governance
  features such as RBAC, signing, replication, and retention. A useful mental
  model is to treat it as an enterprise-local Docker Hub / Distribution style
  system with stronger management features.
- `Dragonfly` accelerates distribution from the registry to nodes using
  preheat and P2P transfer patterns.

This stack is a strong answer to **private model artifact management**, but it
does not by itself provide a native Hugging Face-compatible endpoint.

### 5. ModelExpress

ModelExpress sits later in the path. It is not the primary model hub. Its main
job is **runtime weight movement and cold-start reduction inside the cluster**.

That usually means:

- coordinating cache usage in the inference cluster
- reducing repeated model pulls and loads
- enabling worker-to-worker transfer
- accelerating the last mile from storage or cache toward serving workers

The official documentation focuses on **in-cluster multi-node coordination**
rather than a global multi-cluster control plane.

## The Most Common Architecture Patterns

### Pattern A: Public Hugging Face

Use this when convenience matters more than control.

`Clients -> Hugging Face`

Tradeoff:

- simplest workflow
- least governance
- repeated public downloads
- weak fit for air-gapped or regulated environments

### Pattern B: Private Hugging Face with MatrixHub

Use this when existing HF workflows should remain almost unchanged.

`Clients -> MatrixHub -> Hugging Face or private storage`

Tradeoff:

- lowest migration cost for HF-first teams
- strong fit for internal mirroring and governance
- less aligned with OCI-first platform standardization than Harbor

### Pattern C: Private Model Registry with Harbor + ModelPack + Dragonfly

Use this when the platform is already centered on OCI artifacts and Kubernetes.

`Build/package -> ModelPack -> Harbor -> Dragonfly -> cluster nodes`

Tradeoff:

- strong standardization and enterprise controls
- clean fit for OCI-native platform teams
- more workflow translation if users expect native HF semantics

### Pattern D: MatrixHub + ModelExpress

Use this when you need both **private Hugging Face-style access** and **faster
cluster runtime loading**.

`Clients -> MatrixHub -> cluster cache/source -> ModelExpress -> workers`

Division of responsibility:

- `MatrixHub` is the upstream system of record and governed distribution layer.
- `ModelExpress` is the in-cluster runtime acceleration layer.

This is especially natural in multi-cluster environments where each cluster
runs its own runtime acceleration path while a shared upstream model source
keeps versions and access policies consistent.

## Quick Positioning Table

| Component | Primary layer | Best for |
| --- | --- | --- |
| Hugging Face | Public upstream hub | Public model discovery and default client workflows |
| Private Hugging Face | Capability / target state | Internal HF-like experience |
| MatrixHub | Private model hub | HF-compatible internal distribution and governance |
| ModelPack | Packaging/spec | OCI-based model artifact definition |
| Harbor | Private registry | OCI artifact governance and replication |
| Dragonfly | Cluster distribution | Large-scale node-level pull acceleration |
| ModelExpress | Runtime acceleration | In-cluster cold-start and weight transfer optimization |

## Practical Rule of Thumb

- If the question is **"where should models live and be governed?"**, think
  `MatrixHub` or `Harbor`.
- If the question is **"do we want HF-compatible developer experience or
  OCI-first artifact workflows?"**, choose between `MatrixHub` and
  `Harbor + ModelPack`.
- If the question is **"how do we reduce cluster cold-start and repeated weight
  movement?"**, think `Dragonfly` and `ModelExpress`.
- If the question is **"how do we keep HF-like access while improving
  last-mile runtime loading?"**, combine `MatrixHub` with `ModelExpress`.

## References

- [MatrixHub](https://github.com/matrixhub-ai/matrixhub)
- [ModelExpress](https://github.com/ai-dynamo/modelexpress)
- [Harbor](https://goharbor.io/)
- [Dragonfly](https://d7y.io/)
- [ModelPack](https://modelpack.org/)
- [Hugging Face](https://huggingface.co/)

---
status: Active
maintainer: pacoxu
last_updated: 2025-10-29
tags: repository, structure, documentation, organization
---

# Repository Structure

This document describes the organization and structure of the AI-Infra repository
after the refactoring to follow content management best practices.

## Design Principles

The repository structure follows these principles:

1. **Single Source of Truth**: Each topic appears in only ONE canonical file
2. **Centralized Assets**: All images and diagrams stored in `diagrams/`
3. **Clear Hierarchy**: Content organized by domain (kubernetes, inference, training)
4. **Metadata**: Every markdown file includes status, maintainer, and tags
5. **Relative Links**: All internal references use relative paths

## Directory Structure

```text
AI-Infra/
├── README.md                          # Main entry point and learning path
├── LICENSE                            # Repository license
├── STRUCTURE.md                       # This file - repository organization guide
├── diagrams/                          # Centralized image storage
│   ├── ai-infra-landscape.png        # AI infrastructure landscape visualization
│   └── pod-lifecycle.png             # Kubernetes pod lifecycle diagram
├── docs/                              # All documentation content
│   ├── kubernetes/                   # Kubernetes and scheduling topics
│   │   ├── README.md                 # Overview and navigation for K8s topics
│   │   ├── learning-plan.md          # Structured 3-phase learning path
│   │   ├── pod-lifecycle.md          # Pod creation, scheduling, and termination
│   │   ├── pod-startup-speed.md      # Optimization strategies for pod startup
│   │   ├── scheduling-optimization.md # Large-scale scheduling patterns
│   │   ├── isolation.md              # Workload isolation techniques
│   │   ├── dra.md                    # Dynamic Resource Allocation reference
│   │   └── nri.md                    # Node Resource Interface reference
│   ├── inference/                    # LLM inference and serving topics
│   │   ├── README.md                 # Overview and comparison of inference engines
│   │   ├── aibrix.md                 # AIBrix platform and features
│   │   ├── pd-disaggregation.md      # Prefill-Decode disaggregation patterns
│   │   ├── caching.md                # KV cache and prefix caching strategies
│   │   ├── memory-context-db.md      # Memory management for AI agents
│   │   ├── large-scale-experts.md    # Mixture of Experts (MoE) architectures
│   │   ├── model-lifecycle.md        # Cold-start, sleep mode, offloading
│   │   └── ome.md                    # OME Kubernetes operator
│   └── training/                     # AI model training topics
│       ├── README.md                 # Overview of training on Kubernetes
│       ├── kubeflow.md               # Kubeflow training operators
│       └── argocd.md                 # GitOps workflows with ArgoCD
└── .github/
    └── copilot-instructions.md       # AI assistant guidelines

6 directories, 23 markdown files
```

## Content Organization

### Main Entry Point

- **README.md**: The main learning path that provides:
  - Overview of AI infrastructure landscape
  - Structured learning path across three tiers
  - Links to all detailed documentation
  - Coming soon topics and roadmap

### Domain Categories

#### 1. Kubernetes (`docs/kubernetes/`)

**Purpose**: Core Kubernetes concepts and AI workload optimization

**Canonical Files**:

- `README.md` - Navigation hub for Kubernetes topics
- `learning-plan.md` - 3-phase structured learning path
- `pod-lifecycle.md` - Detailed pod lifecycle and PLEG
- `pod-startup-speed.md` - Startup optimization strategies
- `scheduling-optimization.md` - Large-scale scheduling patterns
- `isolation.md` - Security and multi-tenancy isolation
- `dra.md` - Dynamic Resource Allocation API reference
- `nri.md` - Node Resource Interface reference

**Cross-references**: Links to `../inference/` and `../training/` for related topics

#### 2. Inference (`docs/inference/`)

**Purpose**: LLM inference engines, serving platforms, and optimization

**Canonical Files**:

- `README.md` - Comparison of inference platforms (AIBrix, llmaz, OME, Kthena)
- `aibrix.md` - AIBrix platform features and architecture
- `pd-disaggregation.md` - Prefill-Decode disaggregation implementations
- `caching.md` - KV cache and prefix caching techniques
- `memory-context-db.md` - Memory management for AI agents
- `large-scale-experts.md` - MoE architecture and deployment
- `model-lifecycle.md` - Model lifecycle management strategies
- `ome.md` - OME Kubernetes operator features

**Cross-references**: Links to `../kubernetes/` for infrastructure topics

#### 3. Training (`docs/training/`)

**Purpose**: Distributed training, fault tolerance, and ML pipelines

**Canonical Files**:

- `README.md` - Overview of training challenges and best practices
- `kubeflow.md` - Kubeflow training operators and Trainer V2
- `argocd.md` - GitOps workflows for training management

**Cross-references**: Links to `../kubernetes/` for scheduling and resources

### Assets (`diagrams/`)

All images referenced by documentation files are stored here:

- Visual diagrams (landscape, architecture)
- Flowcharts (pod lifecycle)
- Reference images

**Reference Pattern**: `../../diagrams/image-name.png` from doc files

## Metadata Format

Every markdown file includes a YAML front matter header:

```yaml
---
status: Active | Draft | Deprecated
maintainer: pacoxu
last_updated: YYYY-MM-DD
tags: comma, separated, tags
canonical_path: docs/category/filename.md
---
```

**Fields**:

- `status`: Current state of the document
- `maintainer`: Primary author/maintainer
- `last_updated`: Date of last significant update
- `tags`: Topics covered (for searchability)
- `canonical_path`: Full path (for stub references)

## Content Guidelines

### Single Source of Truth

Each major topic has ONE canonical location:

- **Pod Lifecycle** → `docs/kubernetes/pod-lifecycle.md` (canonical)
  - Other files reference this with relative links
  - No duplicate explanations elsewhere

- **Prefill-Decode** → `docs/inference/pd-disaggregation.md` (canonical)
  - Mentioned in other files with link to canonical version
  - Implementation details only in canonical file

### Creating Stub References

When a topic is mentioned but detailed elsewhere, use a stub pattern:

```markdown
## Topic Name

For comprehensive coverage of Topic Name, see [Topic Name](../category/topic.md).

Key points:
- Brief bullet point
- Brief bullet point
```

**Maximum 3-4 lines** plus link to canonical version.

### Adding New Content

1. **Determine category**: kubernetes, inference, or training
2. **Create file** in appropriate `docs/` subdirectory
3. **Add metadata header** with status, maintainer, date, tags
4. **Update parent README.md** to link to new content
5. **Update main README.md** if adding major new topic
6. **Use relative paths** for all internal links
7. **Place images** in `diagrams/` directory

### Link Patterns

**From main README to docs**:

```markdown
[Topic](./docs/category/topic.md)
```

**Between docs files (same directory)**:

```markdown
[Topic](./topic.md)
```

**Between docs files (different directory)**:

```markdown
[Topic](../other-category/topic.md)
```

**To images from docs**:

```markdown
![Description](../../diagrams/image.png)
```

## Maintenance

### Regular Tasks

1. **Update timestamps**: Change `last_updated` when making significant edits
2. **Validate links**: Run `markdown-link-check` periodically
3. **Check for duplicates**: Search for repeated content and consolidate
4. **Update tags**: Keep tags relevant and consistent
5. **Lint markdown**: Run `markdownlint` before committing

### Quality Standards

- **Technical accuracy**: Verify with official documentation
- **Link integrity**: All internal links must resolve correctly
- **Image references**: All images must exist in `diagrams/`
- **Metadata completeness**: Every file must have full metadata
- **Stub discipline**: Avoid duplicating content; link to canonical version

## Migration Notes

### What Changed in Refactoring

1. **Directory structure**:
   - Old: `kubernetes/`, `inference/`, `training/` at root
   - New: `docs/kubernetes/`, `docs/inference/`, `docs/training/`

2. **Images**:
   - Old: Scattered in category directories
   - New: Centralized in `diagrams/`

3. **File renames**:
   - `kubernetes/kubernetes.md` → `docs/kubernetes/learning-plan.md`

4. **All files gained**:
   - Metadata headers
   - Canonical path markers
   - Updated relative links

### Backward Compatibility

Old links are broken after refactoring. Update any external references:

- `./kubernetes/pod-lifecycle.md` → `./docs/kubernetes/pod-lifecycle.md`
- `./ai-infra-landscape.png` → `./diagrams/ai-infra-landscape.png`

## Future Enhancements

Planned improvements to repository structure:

1. **Stub pages**: Create redirects for frequently referenced topics
2. **Topic index**: Automated tag-based index of all content
3. **Change log**: Track document evolution over time
4. **Contribution guide**: Detailed guidelines for adding content
5. **Search integration**: Enable full-text search across docs

## Questions and Feedback

For questions about repository structure or suggestions for improvements:

- Open an issue in the repository
- Contact maintainer: pacoxu
- Refer to `.github/copilot-instructions.md` for detailed guidelines

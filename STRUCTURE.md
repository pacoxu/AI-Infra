---
status: Active
maintainer: pacoxu
last_updated: 2026-11-13
tags: repository, structure, documentation, organization
---

# Repository Structure

This document describes the organization and structure of the AI-Infra repository
after the refactoring to follow content management best practices.

## Design Principles

The repository structure follows these principles:

1. **Single Source of Truth**: Each topic appears in only ONE canonical file
2. **Centralized Assets**: All images and diagrams stored in `diagrams/`
3. **Clear Hierarchy**: Content organized by domain (kubernetes, inference,
   training) and dedicated `agent-infra/` track
4. **Metadata**: Every markdown file includes status, maintainer, and tags
5. **Relative Links**: All internal references use relative paths

## Directory Structure

```text
AI-Infra/
├── README.md                          # Main entry point and learning path (EN)
├── README.zh-CN.md                    # Main entry point and learning path (ZH)
├── RoadMap.md                         # Future topics and planning
├── BLOG.md                            # Public blog entry point (recent posts)
├── STRUCTURE.md                       # This file - repository organization guide
├── project_watchlist.json             # Upstream projects tracked by the repo
├── diagrams/                          # Centralized image storage + landscape data
├── docs/                              # All documentation content
│   ├── kubernetes/                    # Kubernetes, scheduling, DRA, release notes
│   │   └── sig-release/vX.Y/          # Per-release AI Infra articles
│   ├── inference/                     # LLM inference and serving topics
│   ├── training/                      # AI model training topics
│   ├── observability/                 # Observability content
│   ├── hardware/                      # SuperNode and other hardware topics
│   ├── planning/                      # Executable backlog (item-level planning)
│   ├── blog/                          # Active blog posts and full index
│   └── archive-blog/                  # Historical blog posts archive
├── agent-infra/                       # Agent Infra docs and benchmark assets
│   ├── README.md                      # Agent platforms, sandboxes, and ecosystem
│   ├── runtime-benchmark.md           # runc/gVisor/Kata/VM benchmark
│   └── scripts/
│       └── agent-sandbox-benchmark/   # Reproducible benchmark scripts
├── case-study/                        # Per-vendor open source portfolios
│   └── assets/                        # Images used only by case studies
├── archive/                           # Retired material (e.g. mcm-radar)
├── scripts/                           # Utility, generation, and PoC scripts
│   ├── generate-landscape-svg.js      # Renders diagrams/ai-infra-landscape.svg
│   ├── conformance/                   # Inference preflight gate
│   └── dra-kueue-kwok/                # DRA + Kueue KWOK-only PoC
└── .github/                           # Issue templates and Copilot instructions

Directory/file counts evolve frequently; avoid hard-coded totals.
```

## Content Organization

### Main Entry Point

- **README.md**: The main learning path that provides:
  - Overview of AI infrastructure landscape
  - Structured learning path across three tiers
  - Links to all detailed documentation
  - Coming soon topics and roadmap

### Domain Categories

Each category's `README.md` is the maintained index of its files. This page
only names the category, its purpose, and anchor documents; when you add a
file, update the category README (and the main README) instead of this list.

#### 1. Kubernetes (`docs/kubernetes/`)

**Purpose**: Core Kubernetes concepts and AI workload optimization

**Index**: `docs/kubernetes/README.md`. Anchor documents include
`learning-plan.md`, `pod-lifecycle.md`, `scheduling-optimization.md`,
`dra.md`, `isolation.md`, and the per-release articles under
`sig-release/vX.Y/release.md`.

**Cross-references**: Links to `../inference/` and `../training/` for related topics

#### 2. Inference (`docs/inference/`)

**Purpose**: LLM inference engines, serving platforms, and optimization

**Index**: `docs/inference/README.md` (platform landscape: AIBrix, OME,
Kthena, KServe, llm-d, Dynamo). Anchor documents include
`pd-disaggregation.md`, `caching.md`, `model-lifecycle.md`, and `dynamo.md`.

**Cross-references**: Links to `../kubernetes/` for infrastructure topics

#### 3. Training (`docs/training/`)

**Purpose**: Distributed training, fault tolerance, and ML pipelines

**Index**: `docs/training/README.md`. Anchor documents include
`kubeflow.md` (Kubeflow Trainer), `parallelism.md`, and `mlops.md`.

**Cross-references**: Links to `../kubernetes/` for scheduling and resources

#### 4. Agent Infra (`agent-infra/`)

**Purpose**: AI Agent platforms, frameworks, and infrastructure

**Canonical Files**:

- `README.md` - Overview of agent platforms, MCP protocol, Kubernetes-native
  solutions, and ecosystem snapshots
- `ai-agent-infra-9-layers-zh.md` - Production Agent Infra layered architecture
  view: 9 layers plus security, release, FinOps, and DevEx cross-cutting
  capabilities
- `runtime-benchmark.md` - Runtime benchmark and reproducibility guide

**Cross-references**: Links to `../docs/kubernetes/isolation.md` for
sandboxing, `../docs/inference/memory-context-db.md` for agent memory

#### 5. Observability (`docs/observability/`)

**Purpose**: Monitoring, telemetry, and diagnostics for AI workloads

**Canonical Files**:

- `README.md` - Overview of observability approaches and references

#### 6. Blog (`docs/blog/`, `docs/archive-blog/`)

**Purpose**: Time-ordered technical blogs and case-study posts

**Canonical Files**:

- `docs/blog/README.md` - Full blog index (active and archived posts)
- `BLOG.md` - Public entry point with recent posts
- `YYYY-MM-DD/YYYY-MM-DD-topic-name(_zh).md` - Blog posts, one folder per
  date; older posts move to `docs/archive-blog/` with the same layout

#### 7. Hardware (`docs/hardware/`)

**Purpose**: Rack-scale and accelerator hardware that shapes scheduling,
for example `supernode.md`

#### 8. Planning (`docs/planning/`)

**Purpose**: Item-level execution backlog; `RoadMap.md` keeps the strategic
direction

#### 9. Case Studies (`case-study/`)

**Purpose**: Per-vendor open source portfolios. `case-study/README.md` is the
index; vendor-specific images live in `case-study/assets/`

### Assets (`diagrams/`)

All images referenced by documentation files are stored here:

- Visual diagrams (landscape, architecture)
- Flowcharts (pod lifecycle)
- Reference images

**Reference Pattern**: `../../diagrams/image-name.svg` (or `.png`) from doc files

## Metadata Format

Every markdown file includes a YAML front matter header:

```yaml
---
status: Active | Draft | Deprecated
maintainer: pacoxu
last_updated: YYYY-MM-DD
tags: comma, separated, tags
canonical_path: path/from/repo/root.md
---
```

**Fields**:

- `status`: Current state of the document
- `maintainer`: Primary author/maintainer
- `last_updated`: Date of last significant update
- `tags`: Topics covered (for searchability)
- `canonical_path`: Full path (for stub references)

Blog posts also carry `date:` (publication date) and usually `source_urls:`;
archived posts may have `date:` without `last_updated`.

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

1. **Determine category**: kubernetes, inference, training, observability,
   blog, archive-blog, or agent-infra
2. **Create file** in appropriate `docs/` subdirectory or `agent-infra/`
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
- `./ai-infra-landscape.svg` → `./diagrams/ai-infra-landscape.svg`

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

# Diagrams Directory

This directory contains all diagrams and images used across the AI-Infra
documentation.

## Current Diagrams

- `ai-infra-landscape.png` - Main AI infrastructure landscape overview
- `dra-driver-architecture.png` - Dynamic Resource Allocation driver architecture
- `dra-user-flow.svg` - DRA user workflow diagram
- `dynamo-memory.png` - Dynamo memory architecture
- `nixl-design.png` - NIXL design diagram
- `parallelism.png` - Parallelism strategies visualization
- `pod-lifecycle.png` - Kubernetes Pod lifecycle diagram

## Pending Diagrams

### Multi-Cluster Use Cases (KubeCon NA 2025)

**Status**: Missing - needs manual download

**Required file**: `multicluster-use-cases.png`

**Source**: <https://github.com/user-attachments/assets/5f42f1bb-2d38-4f22-880a-a9512a502983>

**Used in**:

- `docs/blog/2025-12-05/ai-infrastructure-kubernetes-2025.md`
- `docs/blog/2025-12-05/ai-infrastructure-kubernetes-2025_zh.md`

**Translation Guide**: See `multicluster-use-cases-translation.md` for creating
a Chinese version of this diagram.

**Details**: This diagram from the KubeCon North America 2025 SIG Multi-Cluster
presentation shows common reasons why organizations run multi-cluster
deployments, including:

- Environment-based separation (Dev/Staging/Prod)
- Region-based deployment for performance
- Business unit isolation
- Security and management isolation
- Infrastructure provider flexibility

## Adding New Diagrams

1. Place image files in this directory
2. Use descriptive, lowercase, hyphenated filenames
3. Preferred formats: PNG for raster, SVG for vector graphics
4. Reference from markdown using relative paths:
   `../../../diagrams/your-diagram.png`
5. Include alt text for accessibility
6. For diagrams with text, consider creating localized versions
   (e.g., `diagram-name-zh.png` for Chinese)

## Image Guidelines

- **Resolution**: Minimum 1000px width for clarity
- **Format**: PNG for screenshots/photos, SVG for diagrams when possible
- **Size**: Optimize images to keep repository size manageable
- **Naming**: Use descriptive names, lowercase with hyphens
- **Attribution**: Document source for third-party diagrams

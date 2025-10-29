# AI-Infra Repository Copilot Instructions

**ALWAYS follow these instructions first and fallback to additional search and
context gathering only if the information here is incomplete or found to be in
error.**

## Repository Overview

AI-Infra is a documentation-focused repository providing curated landscape and
structured learning paths for engineers building and operating modern AI
infrastructure, especially in the Kubernetes and cloud-native ecosystem. This
is a pure documentation repository with no source code - only markdown files
organized into learning topics.

## Working Effectively

### Repository Bootstrap & Validation

- **Bootstrap dependencies:**

  ```bash
  npm install -g markdownlint-cli markdown-link-check
  ```

  - Takes 1-2 minutes. NEVER CANCEL. Set timeout to 5+ minutes.

- **Validate all markdown files:**

  ```bash
  markdownlint **/*.md
  ```

  - Takes 10-30 seconds. Identifies formatting issues, line length
    violations, and style problems.

- **Check all external links:**

  ```bash
  markdown-link-check README.md
  ```

  - Takes 30-60 seconds per file. Some external links may be temporarily
    unreachable (Status: 0 errors are common for conference websites).
  - Check key documentation files: `README.md`, `docs/inference/README.md`,
    `docs/kubernetes/learning-plan.md`

### Content Validation Requirements

- **ALWAYS run markdown linting before committing:**

  ```bash
  markdownlint **/*.md
  ```

  - Fix line length violations (80 character limit)
  - Fix trailing spaces and multiple blank lines
  - Address inline HTML warnings where appropriate

- **ALWAYS validate external links for new content:**

  ```bash
  find . -name "*.md" -exec markdown-link-check {} \;
  ```

  - NEVER CANCEL: Full link check takes 3-5 minutes across all files.
    Set timeout to 10+ minutes.
  - Ignore Status: 0 errors for conference websites and GitHub assets -
    these are often temporary

### Repository Structure

```text
/home/runner/work/AI-Infra/AI-Infra/
├── README.md                          # Main learning path and landscape overview
├── diagrams/                          # All images centralized
│   ├── ai-infra-landscape.png        # Visual landscape diagram
│   └── pod-lifecycle.png             # Pod lifecycle diagram
├── docs/
│   ├── kubernetes/
│   │   ├── README.md                 # Kubernetes overview (canonical)
│   │   ├── learning-plan.md          # Kubernetes learning plan (3-phase approach)
│   │   ├── pod-lifecycle.md          # Pod lifecycle documentation
│   │   ├── pod-startup-speed.md      # Pod startup optimization guide
│   │   ├── scheduling-optimization.md # Scheduling strategies and optimization
│   │   ├── isolation.md              # Workload isolation techniques
│   │   ├── dra.md                    # Dynamic Resource Allocation reference
│   │   └── nri.md                    # Node Resource Interface reference
│   ├── inference/
│   │   ├── README.md                 # LLM inference engine comparisons
│   │   ├── aibrix.md                 # AIBrix platform
│   │   ├── pd-disaggregation.md      # Prefill-Decode disaggregation
│   │   ├── caching.md                # Caching strategies
│   │   ├── memory-context-db.md      # Memory/Context DB
│   │   ├── large-scale-experts.md    # MoE models
│   │   ├── model-lifecycle.md        # Model lifecycle
│   │   └── ome.md                    # OME platform
│   └── training/
│       ├── README.md                 # Training on Kubernetes overview
│       ├── kubeflow.md               # Kubeflow training operators
│       └── argocd.md                 # GitOps with ArgoCD
└── .github/
    └── copilot-instructions.md
```

### Common Development Tasks

#### Adding New Learning Materials

1. **Create new markdown files in appropriate directories:**
   - Scheduling/Workloads content → `docs/kubernetes/`
   - Inference optimization content → `docs/inference/`
   - Training and ML pipelines → `docs/training/`

2. **Always include metadata headers and proper structure:**

   ```markdown
   ---
   status: Active
   maintainer: pacoxu
   last_updated: YYYY-MM-DD
   tags: tag1, tag2, tag3
   canonical_path: docs/category/filename.md
   ---
   
   # Title
   
   Brief introduction paragraph.
   
   ## Section Headers
   
   Content with proper formatting.
   ```

3. **Reference external projects consistently:**

   ```markdown
   - <a href="https://github.com/org/project">`ProjectName`</a>: Brief description.
     CNCF Status if applicable.
   ```

4. **Images should be placed in diagrams/ and referenced with relative paths:**

   ```markdown
   ![Image Description](../../diagrams/image-name.png)
   ```

5. **Add learning topics and roadmap sections for educational content:**

   ```markdown
   ## Learning Topics
   - Topic 1
   - Topic 2
   
   ## RoadMap (Ongoing Proposals)
   - Link to KEPs, issues, or proposals
   ```

#### Updating the Main README

- **Always update the main learning path when adding new topics**
- **Maintain the three-tier structure: Scheduling & Workloads, Inference &
  Runtime, AI Gateway & Agentic Workflow**
- **Include CNCF project status (Graduated, Incubating, Sandbox) where
  applicable**
- **Link to detailed documentation in subdirectories using relative paths:
  `./docs/inference/README.md`**

#### Content Quality Standards

- **Use imperative tone for instructions: "Run this command", "Do not do this"**
- **Include project status and organizational context (CNCF, Apache,
  Company-specific)**
- **Link to original sources, documentation, and GitHub repositories**
- **Add warning notes for content generated by AI: "Some were generated by
  ChatGPT. So please be careful before you use them."**

### Validation Scenarios

After making changes, ALWAYS complete these validation steps:

1. **Lint all markdown files:**

   ```bash
   markdownlint **/*.md
   ```

2. **Check links in modified files:**

   ```bash
   markdown-link-check path/to/modified/file.md
   ```

3. **Verify cross-references work:**
   - Check that internal links (`./inference/README.md`) resolve correctly
   - Ensure referenced images exist in the repository

4. **Manual content review:**
   - Verify technical accuracy of new content
   - Check that new projects are accurately categorized (CNCF status, maturity)
   - Ensure learning paths maintain logical progression

### Known Issues and Limitations

- **No CI/CD workflows:** The repository has no automated validation -
  manual validation is critical
- **External link reliability:** Conference websites and GitHub asset links
  frequently return Status: 0 errors - these can often be ignored
- **Image references:** The main landscape image uses GitHub user-attachments
  URLs which may be unstable
- **Content freshness:** Project statuses and links need regular manual
  verification as the AI infrastructure landscape evolves rapidly

### Time Expectations

- **Markdown linting:** 10-30 seconds for full repository
- **Link checking:** 30-60 seconds per file, 3-5 minutes for full repository
- **Tool installation:** 1-2 minutes for npm packages
- **Content validation:** Manual review should take 5-10 minutes per
  significant change

### Repository-Specific Knowledge

- **This is a personal learning repository by pacoxu:** Content includes
  personal notes and may contain AI-generated content that needs verification
- **Focus on cloud-native AI infrastructure:** Primarily Kubernetes-based
  solutions, CNCF projects, and enterprise-grade tools
- **Educational purpose:** Designed to help engineers navigate and master the
  rapidly evolving AI infrastructure stack
- **Community contributions welcome:** New projects, learning materials, and
  diagram updates are encouraged via PRs and issues

### Quick Reference Commands

```bash
# Complete validation workflow
npm install -g markdownlint-cli markdown-link-check
markdownlint **/*.md
find . -name "*.md" -exec markdown-link-check {} \;

# Common file operations
ls -la /home/runner/work/AI-Infra/AI-Infra/
find . -name "*.md" | head -10
grep -r "keyword" . --include="*.md"
```

**Remember: This repository contains learning materials that evolve rapidly with
the AI infrastructure landscape. Always verify the current status of projects
and technologies before making significant additions or changes.**

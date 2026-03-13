---
status: Active
maintainer: pacoxu
last_updated: 2025-12-22
tags: oci, kubernetes, ai-infrastructure, docker, modelpack, harbor
---

# OCI 正在悄悄"占领一切"：AI 时代的镜像、Chart、模型与 WASM 如何走向同一条分发路径

**注意：** 部分内容由 AI 辅助生成，使用前请仔细验证。

## 目录

- [引子：KubeCon Atlanta 的一句话，点破了趋势](#引子kubecon-atlanta-的一句话点破了趋势)
- [为什么 AI 时代更需要 OCI：从"镜像"到"制品分发底座"](#为什么-ai-时代更需要-oci从镜像到制品分发底座)
- [Kubernetes：OCI Image Volume 在 v1.35 默认启用（Beta）](#kubernetesoci-image-volume-在-v135-默认启用beta)
- [ModelPack：把"模型"变成 OCI 世界的一等公民](#modelpack把模型变成-oci-世界的一等公民)
- [Harbor：从"镜像/Chart 仓库"走向"模型制品仓库"](#harbor从镜像chart-仓库走向模型制品仓库)
- [Docker Model Runner：把本地推理与 OCI 分发直接焊死](#docker-model-runner把本地推理与-oci-分发直接焊死)
- [ORAS：OCI Artifacts 的"瑞士军刀"](#orasoci-artifacts-的瑞士军刀)
- [Ollama 与"类 Ollama spec"：先统一分发协议，再谈统一格式](#ollama-与类-ollama-spec先统一分发协议再谈统一格式)
- [WASM 制品库：OCI 的下一块"统一分发拼图"](#wasm-制品库oci-的下一块统一分发拼图)
- [相关新闻信号：Bitnami 变化与 Docker DHI](#相关新闻信号bitnami-变化与-docker-dhi)
- [性能与未来：大模型时代，OCI 还需要继续进化](#性能与未来大模型时代oci-还需要继续进化)
- [落地路线图建议](#落地路线图建议)
- [参考资料](#参考资料)

## 引子：KubeCon Atlanta 的一句话，点破了趋势

KubeCon North America（Atlanta）回顾里有一句非常"轻描淡写"，但信息量极大的
总结：**OCI 正在悄悄地占领一切**——它不再只是"容器镜像的打包方式"，而在成为
云原生世界的**默认分发协议与仓库形态**：Helm chart、WASM 模块，乃至 AI 模型，
都在往 OCI Registry 汇聚。

参考链接：
https://metalbear.com/blog/kubecon-atlanta-takeaways/

这背后并不是"概念升级"，而是工程现实在逼迫生态做出统一选择：

- 分发对象从"可执行软件"扩展到"不可执行但巨大且关键的资产"（模型权重、
  数据包、策略、SBOM/VEX、插件、WASM 组件）。
- 企业已经有成熟的 Registry、权限体系、镜像扫描与供应链治理；复用它，
  比重复造一个"模型仓库协议栈"更务实。

参考链接：
https://www.docker.com/blog/oci-artifacts-for-ai-model-packaging/

## 为什么 AI 时代更需要 OCI：从"镜像"到"制品分发底座"

AI 工作负载把"分发"的痛点放大了几个数量级：

- **体积**：模型与依赖镜像动辄数十 GiB；分发效率与断点续传变成刚需。

参考链接：
https://fuweid.com/post/2025-containerd-220-rebase-snapshot/

- **可追溯与合规**：需要 SBOM、签名、溯源、策略审计，且希望与现有容器供应链
  工具链打通。

参考链接：
https://www.docker.com/blog/docker-hardened-images-for-every-developer/

- **一体化治理**：同一个组织不想维护"镜像仓库 + Helm 仓库 + 模型仓库 +
  插件仓库 + WASM 仓库"五套系统。

因此，OCI 正在从"镜像格式"变成更抽象的：**用同一套 Registry 基础设施，
承载不同类型制品（Artifacts）**。Docker 在其模型打包决策里也明确强调了这一点：
把模型作为 OCI Artifacts，可以直接复用现有 registry 与工作流，并为未来与
containerd / Kubernetes 的深度集成铺路。

参考链接：
https://www.docker.com/blog/oci-artifacts-for-ai-model-packaging/

同时，CNCF 也发布了相关博客文章，讨论 OCI Artifacts 如何推动未来的 AI 应用场景：

参考链接：
https://www.cncf.io/blog/2025/08/27/how-oci-artifacts-will-drive-future-ai-use-cases/

## Kubernetes：OCI Image Volume 在 v1.35 默认启用（Beta）

Kubernetes 在"让 OCI 制品直接进入 Pod 文件系统"这件事上，路线非常清晰：

- v1.31：引入"基于 OCI Artifacts 的只读卷（Image Volume Source）"作为
  **Alpha**，用于把配置、二进制、模型等以声明式方式拉取并挂载到 Pod。

参考链接：
https://kubernetes.io/blog/2024/08/16/kubernetes-1-31-image-volume-source/

- v1.33：该能力进入 **Beta**（官方文档与后续版本说明中持续强调 Beta 状态）。

参考链接：
https://kubernetes.io/docs/tasks/configure-pod-container/image-volumes/

- v1.35：该 Beta 能力在默认配置下**直接启用**（enabled by default），并要求
  运行时满足条件（例如 containerd v2.1+）。

参考链接：
https://kubernetes.io/blog/2025/12/17/kubernetes-v1-35-release/

> **矫正点**：Kubernetes v1.35 的 ImageVolume/OCI Image Volume 仍是 Beta，
> 但在 1.35 起默认启用，并非 GA。

### 它解决的是什么问题？

过去 Pod 需要"模型/配置/二进制"常见做法是：

- 打进应用镜像（导致镜像极大、变更频繁）
- initContainer 启动时下载（导致启动慢、不稳定、不可审计）

ImageVolume 的价值在于：**把"运行镜像"与"运行所需制品（模型、配置、
WASM 等）"解耦**，并把分发路径统一到 OCI Registry。

参考链接：
https://kubernetes.io/blog/2024/08/16/kubernetes-1-31-image-volume-source/

Kubernetes 官方 blog 地址：

https://kubernetes.io/blog/2024/08/16/kubernetes-1-31-image-volume-source/
https://kubernetes.io/blog/2025/12/17/kubernetes-v1-35-release/

## ModelPack：把"模型"变成 OCI 世界的一等公民

ModelPack 的定位可以理解为：**给 AI 模型一个与 OCI 生态对齐的"格式与打包/
元数据约定"**。其 model-spec 明确提出"AI 模型中心化基础设施时代"的到来，
并强调与 OCI image spec / artifact guidelines 的兼容，且点名它可以作为
Kubernetes 的 OCI volume source 使用。

参考链接：
https://github.com/modelpack/model-spec

你可以用它在文章中强化一个主线观点：

> **Kubernetes 提供"挂载 OCI 制品"的入口；ModelPack 提供"模型如何被描述/
> 打包成 OCI 制品"的规范。**
> 两者拼起来，才是 AI 时代 OCI 真正"占领一切"的工程闭环。

参考链接：
https://github.com/modelpack/model-spec

ModelPack 的工作流程如下图所示：

![ModelPack Flow](https://github.com/user-attachments/assets/184db2f5-a6b5-4011-8167-be9310e7fffd)

（图示：ModelPack 打包 AI 模型 → OCI Artifact 提供跨 Registry 的分发标准 →
Image Volume 让终端用户直接从 Kubernetes API 消费）

## Harbor：从"镜像/Chart 仓库"走向"模型制品仓库"

Harbor 在 v2.14.0 release notes 中明确写到：**Enhanced CNAI Model
integration**，并且"支持 raw CNAI model format（参考 model spec）"。

参考链接：
https://github.com/goharbor/harbor/releases

这意味着 Harbor 正在把"模型"纳入其 artifact 体系，与扫描、复制、代理缓存等
企业能力一起管理，而不是单独做一个"模型孤岛"。

参考链接：
https://github.com/goharbor/harbor/releases

Harbor 社区提案详情：
https://github.com/goharbor/community/blob/main/proposals/new/AI-model-processor.md

相关 GitHub Issue：
https://github.com/goharbor/harbor/issues/21229

## Docker Model Runner：把本地推理与 OCI 分发直接焊死

Docker 在两条线上同时推进：

1. **模型以 OCI Artifacts 打包**：解释为什么选择 OCI artifacts 作为 AI 模型
   分发载体，并引入相应规范与工作流。

参考链接：
https://www.docker.com/blog/oci-artifacts-for-ai-model-packaging/

2. **推理引擎层统一入口**：Model Runner 同时覆盖 llama.cpp 与 vLLM，并且能
   "按模型格式智能路由"：

   - GGUF → llama.cpp
   - safetensors → vLLM

   并强调这两种格式都可以作为 OCI 镜像推送/拉取到任意 OCI registry。

参考链接：
https://www.docker.com/blog/docker-model-runner-integrates-vllm/

中文参考：
https://mp.weixin.qq.com/s/wGBiGjCuLnJHf3Z7hr25yQ

另外，Docker 还把 Model Runner 与 Hugging Face 的"本地运行入口"打通，让
"从模型发现到本地运行"像拉镜像一样自然。

参考链接：
https://www.docker.com/blog/docker-model-runner-on-hugging-face/

## ORAS：OCI Artifacts 的"瑞士军刀"

如果说 OCI registry 是"制品的高速公路"，ORAS 就是最常用的通用车辆：它被
定位为处理 OCI Artifacts 的事实标准工具，提供 CLI 与多语言库，强调"不要
假设所有东西都是容器镜像"。

参考链接：
https://oras.land/

这对"模型 / WASM / SBOM / 策略附件"等非镜像资产尤其关键，也是把生态从
"镜像中心"推向"制品中心"的关键一环。

参考链接：
https://oras.land/

## Ollama 与"类 Ollama spec"：先统一分发协议，再谈统一格式

Ollama 的成功证明了：

- 开发者需要一个"从获取模型到运行模型"的端到端体验
- 并且会自然产生自己的模型组织与元数据习惯

但从企业/云原生角度看，**更可落地的共识往往先从"分发协议与仓库兼容
（OCI Distribution/Registry）"开始**，再逐步收敛"模型格式与元数据规范"。
ModelPack 在其生态集成目标里也直接把 Ollama 列为潜在对接对象之一。

参考链接：
https://github.com/modelpack/model-spec

## WASM 制品库：OCI 的下一块"统一分发拼图"

WASM 模块/组件的分发，几乎复刻了模型分发的需求结构：体积更小但类型更多、
版本迭代快、强依赖签名与供应链治理。

因此行业普遍选择把 WASM 组件作为 OCI artifacts 存入 registry：

- CNCF TAG Runtime 的指南介绍了 WASM 到 OCI 的映射与分发方式。

参考链接：
https://github.com/modelpack

- Microsoft 也明确讨论了用 OCI registries 分发 WASM 组件的路径。

参考链接：
https://wasmcloud.com/docs/deployment/netconf/registries/

- wasmCloud 与 Fermyon Spin 都提供了基于 OCI registry 的分发/拉取工作流。

参考链接：
https://github.com/goharbor/harbor/issues/21229

## 相关新闻信号：Bitnami 变化与 Docker DHI

### Bitnami：免费镜像/Chart 分发策略调整（2025-08-28 起生效）

Bitnami/charts 的公告明确给出时间线与变更：

- 2025-08-28 起，公共目录发生变化；大量内容迁移到 legacy；社区免费层收缩为
  "开发用途、latest 为主"的一小部分；并给出 brownout 计划与迁移建议。

参考链接：
https://github.com/bitnami/charts/issues/35164

这类事件在文章里非常适合作为"为什么需要可控的分发底座"的现实案例：你的
生产系统不应把关键依赖完全押注在单一公共目录的长期稳定性上。

### Docker DHI：把"更安全的基础镜像/图表"推向默认选项

Docker 在 2025-12-17 的公告中强调：其 Docker Hardened Images（DHI）目录
（基于 Debian/Alpine）将以 Apache 2.0 方式开放，并把"可验证溯源、可复现
构建、证明材料（attestations）"作为默认安全基线的一部分。

参考链接：
https://docs.docker.com/dhi/
https://www.docker.com/press-release/docker-makes-hardened-images-free-open-and-transparent-for-everyone/

## 性能与未来：大模型时代，OCI 还需要继续进化

当模型与"超级大镜像"变成常态，生态开始在运行时与规范层补齐短板：

- containerd v2.2 引入的 Rebase Snapshot 被认为可以显著提升大镜像下载效率，
  并利用 OCI Distribution 的断点续传/分段并发能力改善体验。

参考链接：
https://fuweid.com/post/2025-containerd-220-rebase-snapshot/

- OCI 社区也在讨论更适合"超大分发对象"的规范演进，例如 image-spec 与
  distribution-spec 里围绕大对象处理方式的议题。

参考链接：
https://github.com/opencontainers/image-spec/issues/1190

## 落地路线图建议

1. **短期（1-2 个月）**：用 OCI registry 统一 Helm chart 分发（官方已提供
   oci:// 工作流）。

参考链接：
https://helm.sh/docs/topics/registries/

2. **中期（1-2 个季度）**：引入 ORAS 作为通用制品工具，把 SBOM / policy /
   模型附件等纳入 OCI。

参考链接：
https://oras.land/

3. **中长期**：

   - 在集群侧评估 ImageVolume（Kubernetes v1.35 默认启用 Beta）用于模型/
     配置/插件分发；同时升级运行时（如 containerd v2.1+）。

参考链接：
https://kubernetes.io/blog/2025/12/17/kubernetes-v1-35-release/

   - 推动 ModelPack/Model Spec 与 Harbor 等 registry 的模型原生支持，形成
     企业级治理闭环。

参考链接：
https://github.com/modelpack/model-spec

4. **社区方向**：**今天的模型分发仍较碎片化，而 OCI 正是统一桥梁**。可以
   考虑开发类似 hg2oci 的工具，用于把 Hugging Face Hub 的模型同步到 OCI
   Registry（如 GitHub Container Registry 或 Docker Hub），实现离线部署和
   企业内网分发。

参考链接：
https://www.docker.com/blog/oci-artifacts-for-ai-model-packaging/

## 参考资料

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

### 中文参考

- Docker Model Runner 携手 vLLM（微信公众号）:
  https://mp.weixin.qq.com/s/wGBiGjCuLnJHf3Z7hr25yQ
- OCI 制品如何推动未来的 AI 应用场景（微信公众号）:
  https://mp.weixin.qq.com/s/E-55ORZfoPWtIur7C9sIPg
- 相关技术文章:
  https://mp.weixin.qq.com/s/zMBkujlmQXL5yECbP7XSkg

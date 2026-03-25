---
status: Draft
maintainer: community
last_updated: 2025-12-03
tags: ai, open-source, contribution, policy
---

# 各大开源社区如何对待 AI 生成代码

AI 辅助开发正在加速贡献效率，但不同社区对 AI 生成代码的接受程度和流程要求并不相同。本文梳理 Kubernetes、Zulip、CPython、Apache DataFusion 等社区正在实施或讨论中的政策，帮助贡献者理解"可以用什么"、"需要怎么用"以及"仍待澄清的灰色地带"，也欢迎更多社区分享实践，共同完善。

## 目录

- [为什么要关注 AI 政策](#为什么要关注-ai-政策)
- [政策速览](#政策速览)
- [Kubernetes：将 AI 产物视为大型自动化改动](#kubernetes将-ai-产物视为大型自动化改动)
- [Zulip：强调披露、可验证性与人类审阅责任](#zulip强调披露可验证性与人类审阅责任)
- [CPython：把关版权、隐私与技术准确性](#cpython把关版权隐私与技术准确性)
- [Apache DataFusion：鼓励透明协作与测试证据](#apache-datafusion鼓励透明协作与测试证据)
- [正在收敛的共识](#正在收敛的共识)
- [给贡献者的操作建议](#给贡献者的操作建议)
- [开放讨论：我们缺的还是什么？](#开放讨论我们缺的还是什么)
- [参考资料](#参考资料)

## 为什么要关注 AI 政策

1. **审查资源有限**：维护者无法为低质量 AI 输出兜底，政策通常把责任推回到提交者身上。  
2. **许可与合规风险**：模型训练语料不透明，社区需要确保最终代码仍符合其开源许可（如 Apache-2.0、GPL）。  
3. **安全与隐私**：不少政策提醒不要把安全问题、凭证或尚未公开的设计上传到第三方模型。  
4. **协作文化**：AI 参与写作后，如何记录过程、如何 credit、如何评审，都是新的协作话题。

## 政策速览

| 社区 | 是否允许 AI 产出直接提交 | 是否需要披露 | 额外要求/关键词 |
|------|--------------------------|--------------|-----------------|
| Kubernetes | **允许**，但按"大型或自动化编辑"流程处理 | 建议在 PR 描述中说明生成方式 | 拆分改动、提供脚本/生成方法、接受额外レビュー |
| Zulip | **允许**，前提是提交者彻底理解代码 | 鼓励说明使用了哪些 AI 工具 | 必须自测、禁止机械粘贴、AI 不能代替 code review |
| CPython | **允许**，需满足 PSF 版权和隐私要求 | 无硬性要求，但推荐透明说明 | 不得泄露未公开信息、需提供可验证依据、防止幻觉内容 |
| Apache DataFusion | **允许**，需要人工验证和测试 | 要在 PR 描述中标注 AI 协助 | 需要附带重现步骤/测试结果、确保许可证兼容 |

> 表格着重总结官方最新文档的主线要求，细节仍以各仓库链接为准。

## Kubernetes：将 AI 产物视为大型自动化改动

- 在 [Kubernetes Contributor Guide - Large or automatic edits](https://www.kubernetes.dev/docs/guide/pull-requests/#large-or-automatic-edits) 中，社区明确提醒：任何脚本批量生成的改动（无论是代码生成器还是 AI）都要被视作"大型编辑"。  
- 核心做法包括：  
  - **拆分 PR**：避免一次性提交巨大 diff，降低 Review 负担。  
  - **附带脚本/指令**：让 Reviewer 能复现实验，确认不是"一次性手活"。  
  - **接受额外审核**：同样的改动可能需要更多 Approver、SIG 协调。  
- 虽然文档没逐字写"AI"，但 AI 生成代码本质上就是"自动化编辑"。遵循这一流程可以在 Kubernetes 生态中降低摩擦。

## Zulip：强调披露、可验证性与人类审阅责任

- [Zulip 的 AI Use Policy](https://github.com/zulip/zulip/blob/main/CONTRIBUTING.md#ai-use-policy-and-guidelines) 目前是最细致的范例之一。关键点：  
  1. **作者责任不可转移**：你必须完全理解 AI 生成的代码/文档，Reviewers 不会为"模型幻觉"兜底。  
  2. **可验证性优先**：提交前要运行测试、给出 reproduce 步骤，避免 Reviewer 花时间分辨真伪。  
  3. **披露使用场景**：建议在 PR 描述中说明用了哪些工具、输入了什么上下文，以便评估潜在的版权/隐私风险。  
  4. **AI 不是 Reviewer**：不能用 AI 生成的"review 意见"代替真实的人类审核流程。  
- Zulip 还特别提醒：公共模型的服务条款可能与 Zulip 的许可冲突，用前自己确认。

## CPython：把关版权、隐私与技术准确性

- 在 [Python Developer Guide - Generative AI](https://devguide.python.org/getting-started/generative-ai/) 中，核心态度是"欢迎，但要负责任"：  
  - **版权保证**：提交者需要确认 AI 输出不会引入闭源或不兼容许可的代码。  
  - **隐私管理**：不得把尚未公开的安全漏洞、凭证或私人邮件粘进 AI 提示。  
  - **技术事实核验**：生成的设计、 bug 分析、文档都要注明数据来源，并经过实际测试或链接到 issue 证据。  
  - **审查效率**：如果 AI 贡献较大，建议在 PR 描述中说明你的验证过程，减少 Reviewer 反复问询。  
- 由于 CPython 长期强调"小步提交、配套测试"，AI 用户也需要提供最小复现脚本，否则很难通过核心开发者的审核。

## Apache DataFusion：鼓励透明协作与测试证据

- [DataFusion Contributor Guide](https://datafusion.apache.org/contributor-guide/index.html#ai-assisted-contributions) 明确提到 AI：  
  1. **可以用 AI 生成初稿**，但最终版本必须经过作者理解、修改和测试。  
  2. **披露 AI 协助**：在 PR 描述中说明使用了 AI，以便 Reviewer 评估可能的风险。  
  3. **测试与 reproducibility**：需要附带单元测试、 benchmark 或命令行脚本证明结果可信。  
  4. **许可证兼容**：Apache 项目对版权极其敏感，禁止导入"来源不明"的片段。  
- 该指南还建议贡献者保留用于生成代码的提示词和脚本，必要时可与 Reviewer 私下分享以协助排查。

## 正在收敛的共识

- **AI 不是免责盾**：所有社区都强调"你写的代码你负责"，哪怕 99% 来自模型。  
- **透明度越高越好**：越来越多项目倡导在 PR 中描述 AI 的参与方式，既方便审查也能累积经验。  
- **自动化≠一次性提交**：大规模 AI 改动往往需要拆分、多轮 review，以及配套的脚本或实验记录。  
- **测试和上下文最打动 Reviewer**：相比"我让模型写的"，更有说服力的是"我运行了这些测试/对比了这些数据"。

## 给贡献者的操作建议

1. **提交前自测**：在本地跑 linters、单测，用事实证明 AI 输出正确。  
2. **写清生成流程**：在 PR 描述中标明提示词、使用的模型、后期人工修改要点。  
3. **保留脚本或 Notebook**：便于 Reviewer 重现，符合 Kubernetes 等社区的自动化改动要求。  
4. **关注许可证**：确认模型服务条款允许开源再分发，必要时选择开源模型或自建实例。  
5. **别让 AI 当 Reviewer**：最终代码 review 仍需人类完成，AI 建议可以附带，但不要"自审自过"。  
6. **主动与 Maintainer 沟通**：大型改动先在 issue / Slack / 邮件列表同步，避免因为流程不合规被拒。

## 开放讨论：我们缺的还是什么？

- 你的社区是否已经制定 AI 贡献政策？  
- 有无更好的工具来标注或追踪 PR 中的 AI 参与度？  
- 是否需要一个跨社区的最佳实践合集，帮助 Reviewer 快速识别风险？  

欢迎在 Issue、讨论区或 PR 中继续分享经验，帮助整个生态更平滑地拥抱 AI 生产力。

## 参考资料

1. [Kubernetes Contributor Guide: Large or automatic edits](https://www.kubernetes.dev/docs/guide/pull-requests/#large-or-automatic-edits)  
2. [Zulip Contributing Guide: AI use policy and guidelines](https://github.com/zulip/zulip/blob/main/CONTRIBUTING.md#ai-use-policy-and-guidelines)  
3. [Python Developer Guide: Generative AI](https://devguide.python.org/getting-started/generative-ai/)  
4. [Apache DataFusion Contributor Guide: AI-assisted contributions](https://datafusion.apache.org/contributor-guide/index.html#ai-assisted-contributions)

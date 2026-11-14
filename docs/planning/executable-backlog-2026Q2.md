---
status: Active
maintainer: pacoxu
last_updated: 2026-11-06
tags: roadmap, backlog, execution, issues, ai-native
canonical_path: docs/planning/executable-backlog-2026Q2.md
---

# AI-Infra 可执行 Backlog（脱敏版，2026 Q2）

## 1. 文档目的

把外部研究输入整理成可直接执行的仓库任务，优先形成：

- 可提交的文档增量（`docs/*`、`agent-infra/*`、`case-study/*`）
- 可复用配置/脚本骨架（`scripts/*`、`configs/*`）
- 可追踪的 issue 列表（按条目 ID 拆分）

## 2. 脱敏规则

本版已执行以下脱敏：

- 移除检索痕迹、引用占位符、对话系统标记。
- 移除与仓库落地无关的外部上下文描述，仅保留可执行任务。
- 将“建议路径”重映射为当前仓库结构，不强制新增 `talks/` 顶层。
- 对“状态可能变化”的事实加上快照日期，避免长期误用。

## 3. 执行优先级（主题级）

| ID | 主题 | 优先级 | 目标产物 | 建议落位 |
| --- | --- | --- | --- | --- |
| T01 | DRA GPU 身份治理 | High | 门禁说明 + RBAC/Webhook 样例 + 回收脚本 | `docs/kubernetes/` + `scripts/` |
| T02 | LLM/SLM 混合路由 | Medium | 路由策略文档 + 最小 router demo | `docs/inference/` + `scripts/` |
| T03 | Agent 可观测（OTel GenAI） | High | trace/metric 规范 + 回放脚本 | `docs/observability/` |
| T04 | Pre-generative Agent 设计 | Low | PRD 模板 + 设计评审清单 | `docs/` + `templates` 型文档 |
| T05 | Air-gapped LLM 平台 | Medium | 离线部署与同步流程 | `docs/kubernetes/` + `scripts/` |
| T06 | K8s 实验跟踪（MLflow） | Medium | 架构文档 + 最小部署样例 | `docs/training/` |
| T07 | AI right-sizing 闭环 | Medium | case study + baseline 策略 | `case-study/` + `docs/observability/` |
| T08 | SLM 训练推理一体 | High | QLoRA + serving + autoscaling 路径 | `docs/training/` + `docs/inference/` |
| T09 | Agent 驱动 Terraform→Crossplane 迁移 | Medium | 迁移 PRD 模板 + loop 流程 | `docs/kubernetes/` + `scripts/` |
| T10 | 平台内自治 Agent 治理 | High | 最小权限/隔离/审计基线 | `agent-infra/` + `docs/kubernetes/` |
| T11 | MCP 授权与 CIMD | Medium | 授权流程说明 + 示例配置 | `agent-infra/` |
| T12 | Envoy AI Gateway | High | token/cost-aware 网关样例 | `docs/inference/` |
| T13 | 推理 Conformance 门禁 | High | preflight checklist + probes/gate 模板 | `docs/inference/` + `scripts/` |

## 4. Top 12（建议先开 issue）

以下条目按“先可观测/安全/评测，再扩展调度与多集群”的原则排序。

### Wave 1（第 1-4 周）：可观测 + 安全 + 评测

1. `[O01]` OTel GenAI 语义规范落地（Status 快照见第 6 节）
2. `[O03]` vLLM 指标与仪表盘对齐
3. `[H03]` Agent 运行命名空间 PSS 基线
4. `[H04]` Seccomp `RuntimeDefault` 默认化
5. `[E06]` LLM 系统级 evals CI 门禁

### Wave 2（第 5-8 周）：调度 + 推理可靠性

1. `[C01]` Kueue GPU 队列与配额治理
2. `[C02]` DRA ResourceClaim 生命周期与权限边界
3. `[C07]` PD 拆分实验与 TTFT/ITL 对照
4. `[T13]` 推理 preflight + admission gate 最小集

### Wave 3（第 9-12 周）：跨集群 + 存储统一

1. `[N01]` 多集群虚拟节点池化（最小 PoC）
2. `[N04]` 跨集群统一排队策略
3. `[D01]` 模型权重统一存储与挂载基线

### 执行状态快照（2026-11-06）

Q2 窗口已过，未完成条目顺延到 2026 Q4。上游版本变化按领域在
[#413](https://github.com/pacoxu/AI-Infra/issues/413)（Kubernetes / 调度 / 设备）、
[#414](https://github.com/pacoxu/AI-Infra/issues/414)（推理）、
[#415](https://github.com/pacoxu/AI-Infra/issues/415)（Agent Infra）、
[#416](https://github.com/pacoxu/AI-Infra/issues/416)（训练 / 可观测）跟踪。

| ID | 状态 | 关联 issue / PR | 落地物 / 下一步 |
| --- | --- | --- | --- |
| O01 | done | [#404](https://github.com/pacoxu/AI-Infra/pull/404) | `docs/observability/agent-otel-genai.md` |
| O03 | in-progress | [#288](https://github.com/pacoxu/AI-Infra/issues/288) | 按 vLLM v0.32（MRV2 默认、Fast Start）重新对齐指标 |
| H03 | todo | [#256](https://github.com/pacoxu/AI-Infra/issues/256) | 与 Pod/VM 准入策略一起交付 PSS 基线 |
| H04 | todo | [#256](https://github.com/pacoxu/AI-Infra/issues/256) | 同上；对齐 AI Conformance KAR-0020（[#286](https://github.com/pacoxu/AI-Infra/issues/286)） |
| E06 | todo | - | 尚未开 issue |
| C01 | in-progress | [#285](https://github.com/pacoxu/AI-Infra/issues/285)（done）、[#376](https://github.com/pacoxu/AI-Infra/issues/376) | `scripts/dra-kueue-kwok/`；基线升级到 Kueue v0.20 |
| C02 | in-progress | [#388](https://github.com/pacoxu/AI-Infra/issues/388) | v1.37 DRA gate 快照已更新；v1.38 跟踪中 |
| C07 | todo | [#288](https://github.com/pacoxu/AI-Infra/issues/288) | `docs/inference/pd-disaggregation.md` 已有方案对比，缺实测 |
| T13 | done | [#403](https://github.com/pacoxu/AI-Infra/pull/403)、[#371](https://github.com/pacoxu/AI-Infra/issues/371) | `docs/inference/inference-conformance.md`、`scripts/conformance/preflight.sh` |
| N01 | todo | - | 尚未开 issue |
| N04 | todo（已解除阻塞） | [#363](https://github.com/pacoxu/AI-Infra/issues/363) | MultiKueue 验证可基于 KWOK 脚本开始 |
| D01 | in-progress | - | `docs/inference/model-distribution-stack.md` 已覆盖分发链路，缺挂载基线 |

## 5. Issue 切分格式（统一 DoD）

每个 issue 使用以下结构：

1. 背景与问题：当前失败模式、影响范围、为什么现在做。  
2. 目标与非目标：这次只交付什么，不交付什么。  
3. 交付物：文档/脚本/配置/示例输出路径。  
4. 验收标准：可执行命令 + 可观察结果 + 失败回滚路径。  
5. 风险与依赖：上游版本、CRD 稳定性、环境前置条件。  

Definition of Done（统一）：

- 至少 1 个主文档更新（含背景、方案、边界、风险）。
- 至少 1 个可运行入口（脚本或命令序列）。
- 至少 1 组验证步骤（成功与失败各 1 条）。
- 明确回滚/清理命令。

## 6. 事实状态快照（需要定期复核）

### 2026-11-06 复核

- DRA：核心能力自 v1.34 GA。v1.37 新增 GA：`DRADeviceTaints`、
  `DRADeviceTaintRules`、`DRAExtendedResource`、`DRAResourceClaimDeviceStatus`。
  Partitionable / Consumable Capacity 等仍为 Beta（见
  [#388](https://github.com/pacoxu/AI-Infra/issues/388)）。
- OTel GenAI Semantic Conventions：已拆分到独立仓库
  [open-telemetry/semantic-conventions-genai](https://github.com/open-telemetry/semantic-conventions-genai)，
  仍为 Development，尚无 release。
- MCP：最新规范版本 `2026-07-28` 将 Dynamic Client Registration 标为 deprecated，
  替代方案为 CIMD；最早在 2027-07-28 及之后发布的版本中移除。
- Keycloak：26.6.0 起提供实验性 CIMD（`--features=cimd`）；截至 26.8.2
  未见升级为正式支持，仍按风险前提处理。
- Envoy AI Gateway：v1.2.0 起更名为
  [Agent Router](https://github.com/theagentrouter/agent-router)。T12 的落地文件名需要相应调整（见
  [#370](https://github.com/pacoxu/AI-Infra/issues/370)）。

### 2026-04-03 初始快照

以下结论仅作为初次规划快照，日期：`2026-04-03`。

- DRA：按 Kubernetes 文档相关页面，设备分配能力处于稳定阶段。
- OTel GenAI Semantic Conventions：仍在 Development 阶段。
- MCP 授权中的 CIMD：规范鼓励 client/auth server 支持。
- Keycloak 在 MCP 场景下的 CIMD：以“计划支持”作为风险前提处理。

建议在每次季度规划时重审此节。

## 7. 仓库落地映射（首批文件建议）

为兼容当前仓库结构，首批优先新增/更新以下文件：

- [x] `docs/observability/agent-otel-genai.md`
- [ ] `docs/kubernetes/dra-identity-governance.md`
- [ ] `docs/kubernetes/agent-runtime-guardrails.md`
- [x] `docs/inference/inference-conformance.md`
- [ ] `docs/inference/envoy-ai-gateway.md`（项目已更名 Agent Router，见
  [#370](https://github.com/pacoxu/AI-Infra/issues/370)）
- [ ] `docs/training/slm-finetune-serving.md`
- [ ] `agent-infra/mcp-auth-cimd.md`
- [ ] `case-study/telco-rightsizing.md`
- [x] `scripts/conformance/preflight.sh`
- [ ] `scripts/airgapped/sync-models.sh`

状态复核于 2026-11-06。

## 8. 维护方式

- RoadMap 只保留方向与阶段目标，本文件维护执行条目与拆分粒度。
- 每个条目状态建议采用：`todo` / `in-progress` / `done` / `blocked`。
- 每月末更新一次本文件的 Top 12 排序与状态。

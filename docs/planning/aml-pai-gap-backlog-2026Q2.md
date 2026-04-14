---
status: Active
maintainer: pacoxu
last_updated: 2026-04-14
tags: roadmap, backlog, aml, pai, ai-platform-engineering
canonical_path: docs/planning/aml-pai-gap-backlog-2026Q2.md
---

# AML vs PAI 视角下的 AI-Infra 补齐 Backlog（2026 Q2）

## 1. 目标

基于 `AML vs PAI` 对照结果，补齐本仓库在“平台控制面闭环”上的短板，
形成可 issue 化、可验收、可复用的内容增量。

## 2. 优先级总览

| ID | Priority | 缺口主题 | 目标产物 | 建议落位 |
| --- | --- | --- | --- | --- |
| GAP-01 | P0 | AI 平台统一分层架构 | 主文档 + 总览图 | `docs/architecture/` |
| GAP-02 | P0 | 资源治理模型（组/队列/优先级） | 策略文档 + YAML 样例 | `docs/kubernetes/` + `scripts/` |
| GAP-03 | P0 | 数据-特征-模型闭环 | 参考架构 + 元数据字段模板 | `docs/training/` |
| GAP-04 | P0 | 实验追踪与模型注册 | MLflow on K8s 最小方案 | `docs/training/` |
| GAP-05 | P0 | 训练容错与恢复 | 容错模式文档 + 运行手册 | `docs/training/` |
| GAP-06 | P0 | 推理控制面治理 | 路由/灰度/扩缩容/SLO 基线 | `docs/inference/` |
| GAP-07 | P1 | AI 存储分层基线 | 存储选型对照 + 压测模板 | `docs/kubernetes/` |
| GAP-08 | P1 | 平台安全与多租户治理 | 权限/隔离/审计基线 | `docs/kubernetes/` + `agent-infra/` |
| GAP-09 | P1 | AI FinOps 成本归因 | 指标定义 + 仪表盘草图 | `docs/observability/` |
| GAP-10 | P1 | 字节 AML 案例深化 | 产品架构深拆文档 | `case-study/` |
| GAP-11 | P1 | 阿里 PAI 案例深化 | 产品架构深拆文档 | `case-study/` |
| GAP-12 | P2 | 能力成熟度雷达 | 雷达维度定义 + 数据模板 | `diagrams/` + `docs/planning/` |

## 3. P0 条目（本季度必须落地）

### GAP-01 AI 平台统一分层架构

- 交付物：
  - `docs/architecture/ai-platform-reference-architecture.md`
  - 1 张 Mermaid 总览图（控制面/数据面/治理面）
- 验收标准：
  - 清晰映射训练、推理、MLOps、资源治理四条主链路
  - 至少 3 个厂商案例映射（AML、PAI、1 个开源平台）

### GAP-02 资源治理模型（组/队列/优先级）

- 交付物：
  - `docs/kubernetes/ai-platform-resource-governance.md`
  - `scripts/governance/` 下最小策略样例（队列、优先级、配额）
- 验收标准：
  - 给出“资源组 -> 队列 -> 作业”的策略链
  - 覆盖抢占、闲时任务、配额超卖边界处理

### GAP-03 数据-特征-模型闭环

- 交付物：
  - `docs/training/data-feature-model-closed-loop.md`
  - 元数据模板（数据集版本、特征版本、模型版本、血缘 ID）
- 验收标准：
  - 能表达训练/推理一致性（training-serving consistency）
  - 给出至少 1 个推荐或风控场景示例

### GAP-04 实验追踪与模型注册

- 交付物：
  - `docs/training/mlflow-k8s-reference.md`
  - 最小部署与操作流程（实验记录 -> 模型注册 -> 发布）
- 验收标准：
  - 提供可复现步骤（命令或 YAML）
  - 明确“复现失败时”的诊断路径

### GAP-05 训练容错与恢复

- 交付物：
  - `docs/training/training-fault-tolerance-playbook.md`
  - 容错策略对照（进程故障、节点故障、网络抖动、GPU XID）
- 验收标准：
  - 给出 checkpoint 频率、恢复 RTO 目标建议
  - 区分“任务级容错”和“平台级容错”的责任边界

### GAP-06 推理控制面治理

- 交付物：
  - `docs/inference/inference-control-plane-governance.md`
  - 路由/灰度/扩缩容策略模板（策略示例即可）
- 验收标准：
  - 覆盖 TTFT/TPOT/SLA 三类核心目标
  - 给出“容量不足、抖动、回滚”处理闭环

## 4. 执行波次（12 周）

- Wave 1（第 1-4 周）：`GAP-01` `GAP-02` `GAP-04`
- Wave 2（第 5-8 周）：`GAP-03` `GAP-05` `GAP-06`
- Wave 3（第 9-12 周）：`GAP-07` `GAP-08` `GAP-09` + 案例深化与雷达

## 5. Issue 模板建议（每个条目统一）

1. 背景与问题（失败模式 + 影响范围）
2. 本次目标与非目标
3. 交付清单（文件路径级）
4. 验收步骤（成功与失败各至少 1 条）
5. 回滚与风险（版本、依赖、前置环境）

## 6. 与现有规划文档关系

- 本文是 `AML/PAI` 专题补齐清单
- 通用季度执行仍以：
  - `docs/planning/executable-backlog-2026Q2.md`
  - `RoadMap.md`
  为主


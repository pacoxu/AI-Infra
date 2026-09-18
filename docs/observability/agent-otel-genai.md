---
status: Draft
maintainer: pacoxu
last_updated: 2026-06-08
tags: observability, opentelemetry, genai, agents, sandbox
canonical_path: docs/observability/agent-otel-genai.md
---

# Agent Observability with OTel GenAI

Define a minimal but extensible observability model that correlates
`agent_step`, `tool_call`, MCP traffic, and sandbox execution in one query.

## Why This Doc Exists

The current direction already requires tracing `agent_step`, `tool_call`, and
`sandbox_id` together for debugging and cost attribution. What is still
missing is an explicit causal model that answers:

- Which `agent_step` decided to invoke a tool?
- Which `tool_call` triggered a sandbox operation?
- Which later step consumed or misinterpreted the result?

This document proposes a two-layer model:

1. Reuse OpenTelemetry traces and spans as the primary execution graph.
2. Add structured events and local attributes where OTel GenAI or MCP
   conventions do not yet cover the needed semantics.

## Goals

- Correlate agent, tool, MCP, and sandbox activity end to end.
- Preserve causal edges for synchronous and asynchronous flows.
- Support failure attribution in one query.
- Support cost attribution per conversation, step, tool call, and sandbox.
- Stay aligned with OpenTelemetry and MCP conventions where possible.

## Non-Goals

- Define every dashboard or alert in this first draft.
- Replace trace/span semantics with a custom event-only model.
- Standardize every vendor-specific metric name.
- Cover non-agent workload observability across the whole platform.

## Source of Truth Hierarchy

Use this precedence order when the same concept exists in multiple layers:

1. OpenTelemetry trace and span relationships
2. OTel semantic attributes
3. Structured event IDs and parent IDs
4. Log body details for human debugging

The intent is to avoid inventing a parallel tracing system unless the standard
model is insufficient.

## Proposed Span Topology

Use spans for the primary execution graph.

```text
conversation / request span
└── invoke_agent
    ├── agent_step (plan / reason / decide)
    │   └── execute_tool
    │       ├── mcp.client.call
    │       └── sandbox.execute
    │           ├── sandbox.process
    │           ├── sandbox.fs
    │           └── sandbox.network
    └── agent_step (consume result / finalize)
```

### Relationship Rules

- Use parent-child when execution is synchronous and directly nested.
- Use span links when one result fans out to multiple downstream consumers.
- Use span links when work resumes across async boundaries or retries.
- Keep one `trace_id` across the full agent request whenever possible.

## Structured Event Model

Structured events complement spans for logs, replay, and ad hoc analytics.

### Required Event Fields

| Field | Meaning | Notes |
| --- | --- | --- |
| `event_id` | Unique event identifier | Local event stream identity |
| `parent_event_id` | Immediate causal parent | Null for root events |
| `trace_id` | End-to-end trace correlation | Must match OTel trace |
| `span_id` | Producing span identity | Optional only when no span exists |
| `agent_session_id` | Agent conversation/session identity | Prefer OTel GenAI conversation mapping |
| `agent_step_id` | Agent decision-step identity | Local extension |
| `tool_call_id` | Tool invocation identity | Prefer OTel GenAI tool-call mapping |
| `sandbox_id` | Sandbox runtime identity | Local extension |
| `mutation_type` | Side-effect category | `read`, `write`, `network`, `process`, `none` |
| `outcome` | Success/failure/timeout/cancelled | Normalize for queries |
| `error_type` | Stable error taxonomy | Avoid free-form only |
| `timestamp` | Event time | RFC 3339 |

### Optional Event Fields

- `retry_attempt`
- `input_size_bytes`
- `output_size_bytes`
- `token_input`
- `token_output`
- `latency_ms`
- `resource_cpu_ms`
- `resource_memory_bytes`
- `network_peer`
- `file_path_hash`

## Attribute Mapping

Prefer standard attributes first, then add local extensions.

| Concept | Preferred Mapping | Fallback / Extension |
| --- | --- | --- |
| Conversation or session | `gen_ai.conversation.id` | `agent.session.id` |
| Tool call identity | `gen_ai.tool.call.id` | `agent.tool_call.id` |
| Agent step identity | None today | `agent.step.id` |
| Sandbox identity | None today | `sandbox.id` |
| Mutation type | None today | `sandbox.mutation.type` |
| Error category | OTel error fields | `error.type` + local taxonomy |

## Context Propagation

The propagation chain should remain explicit:

1. Agent runtime starts or joins a trace.
2. Agent runtime passes trace context into tool execution spans.
3. MCP client forwards `traceparent` and `tracestate`.
4. Sandbox controller or executor continues the trace in sandbox spans/events.
5. Agent result-consumption steps link back to the tool and sandbox work that
   produced the result.

### MCP Notes

- Prefer MCP metadata carriage for W3C trace context.
- Treat MCP request/response as first-class correlation boundaries.
- Record both client-side latency and downstream execution latency.

## Failure Attribution Rules

Queries should distinguish at least these cases:

1. Tool call succeeded but sandbox execution failed.
2. Sandbox execution succeeded but tool adapter misreported output.
3. Tool and sandbox both succeeded but a later `agent_step` consumed the
   result incorrectly.
4. Retry recovered the request but shifted cost to a different step or tool.

Minimum rule set:

- The failing span owns the primary error status.
- Upstream spans record propagated error summaries but not duplicate root cause.
- Structured events must preserve `parent_event_id` so replay can reconstruct
  the local causal chain even when traces are sampled.

## Cost Attribution Rules

At minimum, support rollups by:

- `agent_session_id`
- `agent_step_id`
- `tool_call_id`
- `sandbox_id`
- model name
- tool name

Suggested first metrics:

- input and output tokens
- tool latency
- sandbox lifecycle latency
- sandbox process count
- network egress bytes
- retry count

## Query Patterns to Support

### Failure Debugging

- Given a `trace_id`, show all `agent_step`, `tool_call`, and `sandbox_id`
  activity in order.
- Given a `tool_call_id`, find the exact sandbox operation and the consuming
  follow-up step.
- Given an `error_type`, rank top failing tools and top failing sandboxes.

### Cost Analysis

- Top cost contributors by tool call.
- Sessions with highest sandbox churn.
- Retries that increase token cost or sandbox time.

## Phased Implementation Plan

### Phase 1: Spec

- Define span topology and local field schema.
- Document attribute mappings and naming rules.
- Freeze a minimal error taxonomy.

### Phase 2: Propagation

- Propagate trace context from agent runtime to MCP calls.
- Propagate trace context from MCP/tool layer to sandbox execution.
- Verify trace continuity across success and failure paths.

### Phase 3: Instrumentation

- Emit `invoke_agent`, `agent_step`, `execute_tool`, and sandbox spans.
- Emit structured events with `event_id` and `parent_event_id`.
- Record `mutation_type` for filesystem, process, and network side effects.

### Phase 4: Validation

- Add example queries for failure and cost attribution.
- Sketch dashboards for SLO, cost, and top failure contributors.
- Test sampled-trace scenarios against structured-event replay.

## Open Questions

- Should `agent_step` be a dedicated span name, span attribute, or both?
- Do we need both `event_id` and `span_id` on every sandbox event, or only on
  sampled boundaries?
- How should batch tool execution or parallel tool calls map to
  `parent_event_id` and span links?
- Which sandbox mutations require redaction or hashing before export?

## Next Edits

- Add concrete span names and example JSON payloads.
- Add an error taxonomy table.
- Add example OTel Collector pipeline snippets.
- Add sample dashboard panels and alert conditions.

## References

- OpenTelemetry GenAI semantic conventions
- OpenTelemetry trace context and span links
- OpenTelemetry MCP semantic conventions

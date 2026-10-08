---
status: Active
maintainer: pacoxu
last_updated: 2026-10-08
tags: agent, observability, opentelemetry, genai, sandbox
canonical_path: docs/observability/agent-otel-genai.md
---

# Agent, Tool, and Sandbox Observability

This specification describes how to correlate an agent step, its tool calls,
and sandbox operations for end-to-end debugging and cost attribution. Use
OpenTelemetry (OTel) traces for execution topology and structured events for
causal records; neither model replaces the other.

## Trace topology and context propagation

Represent synchronous work with parent-child spans:

```text
invoke_agent
└── agent_step
    └── execute_tool
        └── mcp.request
            └── sandbox.operation
```

Use span links when work crosses an asynchronous boundary, is retried as a new
trace, or has multiple causal parents/consumers. Do not manufacture a
parent-child relationship for work that did not execute synchronously.

Propagate the active trace context from agent to tool, MCP server, and sandbox.
For MCP, forward W3C `traceparent` and `tracestate` in `params._meta` where
supported. Extract the context at each receiver before creating its span.
Preserve trace context across queues with message context and span links; start
a new trace only when required by a trust boundary or retention policy, and
link it to the originating span.

## Field and semantic conventions

Use standard OTel trace/span identifiers and GenAI semantic attributes where
available. Keep identifiers on spans and structured events so a trace backend
and an event store can be joined:

| Field | Meaning and guidance |
| --- | --- |
| `trace_id` | OTel trace identifier; use the trace backend's native field. |
| `agent_session_id` | Conversation/session identifier; map to `gen_ai.conversation.id`. |
| `agent_step_id` | Local identifier for one agent reasoning/action step. |
| `tool_call_id` | Tool invocation identifier; map to `gen_ai.tool.call.id`. |
| `sandbox_id` | Local identifier for the sandbox instance executing the operation. |
| `event_id` | Unique structured-event identifier. |
| `parent_event_id` | Causal parent event, when one exists; not a replacement for span parentage. |
| `is_root_cause` | Whether this event represents the original failure rather than a propagated error. |
| `mutation_type` | Sandbox action class, such as `read`, `write`, `exec`, or `network`. |

Also record `service.name`, `span_id`, `parent_span_id`, `event_name`,
`status`, `error.type`, and timestamps. On spans, prefer OTel's native trace
context and parent relationships over copying trace IDs into custom
attributes. Use `agent_step_id`, `sandbox_id`, and `mutation_type` as local
extension attributes. Record tool name, sandbox image/runtime, and outcome as
bounded attributes. Avoid putting prompts, tool arguments, secrets, or user
content in attributes or events.

Each structured event should include `event_id`, `event_name`, `event_time`,
`trace_id`, `span_id`, `parent_event_id` when known, and the applicable
`agent_session_id`, `agent_step_id`, `tool_call_id`, and `sandbox_id`.
Include `mutation_type` for sandbox mutations, plus `status` and normalized
`error.type` for failures. Set `is_root_cause` on the event that first
represents a failure; leave it false on propagated errors. Emit lifecycle
events such as sandbox `created`, `ready`, `operation_started`,
`operation_completed`, and `terminated`.

## Minimum instrumentation

Instrument `invoke_agent`, each `agent_step`, `execute_tool`, the MCP request,
and each sandbox operation as spans. At minimum, emit a correlated structured
event when a tool call starts and completes, and when a sandbox is created,
becomes ready, performs an operation, or terminates. Propagate the active
context and applicable correlation fields across every boundary. Record token
usage on the agent/model operation and sandbox lifecycle/operation outcomes on
their corresponding spans and events. This is the smallest useful closure;
framework-specific hooks can add detail without changing the field contract.

## Metrics, errors, and log policy

Record token usage as `gen_ai.client.token.usage` or the implementation's
equivalent, with `gen_ai.token.type` distinguishing input and output tokens.
Record tool duration as a histogram and sandbox lifecycle durations such as
creation-to-ready and operation duration as histograms. Count operations,
timeouts, and failures by bounded dimensions such as tool name, operation
class, runtime, and normalized error type. Keep session, trace, tool-call, and
sandbox IDs out of metric labels; use trace exemplars or the event store to
drill down.

Attribute an error to the span where it first occurs and mark dependent spans
with an appropriate outcome without counting the same root failure multiple
times. Use a stable `error.type` taxonomy:

- `agent`: planning, orchestration, or response handling failure
- `tool`: tool lookup, invocation, or tool-level failure
- `mcp`: protocol, transport, or server failure
- `sandbox.provision`: sandbox creation or readiness failure
- `sandbox.operation`: execution, policy, or resource-limit failure
- `timeout`, `cancelled`, and `unknown`: cross-cutting or unclassified outcomes

Keep the original failure message in access-controlled logs, not metric labels.
Emit structured lifecycle and error events for all failures. Sample successful
traces using a consistent trace-level policy, and retain all error traces plus
a representative baseline of successful traces. Use tail-based sampling when
available so sampling can consider final status and latency. Keep the sampling
decision consistent across services and retain event identifiers for sampled
traces.

## Verification queries

The following SQL uses illustrative `spans` and `agent_events` views; map their
columns to the trace backend or warehouse in use. Filter on the exact
`trace_id` to reconstruct a single execution:

```sql
SELECT
  s.trace_id,
  s.span_id,
  s.parent_span_id,
  s.name AS span_name,
  s.start_time,
  s.duration_ms,
  s.status,
  e.event_id,
  e.parent_event_id,
  e.event_name,
  e.agent_session_id,
  e.agent_step_id,
  e.tool_call_id,
  e.sandbox_id,
  e.mutation_type,
  e.error_type
FROM spans AS s
LEFT JOIN agent_events AS e
  ON e.trace_id = s.trace_id AND e.span_id = s.span_id
WHERE s.trace_id = :trace_id
ORDER BY s.start_time, e.event_time;
```

Find top failure contributors by grouping failed spans or root-cause events by
`error_type`, tool, and runtime over a fixed time window. Count root-cause
events (not every propagated failed span):

```sql
SELECT error_type, tool_name, runtime, COUNT(*) AS failures
FROM agent_events
WHERE status = 'error'
  AND is_root_cause = TRUE
  AND event_time >= :window_start
GROUP BY error_type, tool_name, runtime
ORDER BY failures DESC
LIMIT 10;
```

Find top cost contributors by grouping token usage and sandbox resource cost
using the session, tool-call, and sandbox identifiers:

```sql
SELECT
  agent_session_id,
  tool_name,
  sandbox_id,
  SUM(input_tokens) AS input_tokens,
  SUM(output_tokens) AS output_tokens,
  SUM(sandbox_cost) AS sandbox_cost
FROM agent_cost_events
WHERE event_time >= :window_start
GROUP BY agent_session_id, tool_name, sandbox_id
ORDER BY SUM(estimated_cost) DESC
LIMIT 10;
```

Cost events should carry the same trace/session/tool/sandbox correlation
fields as execution events. Document whether token and sandbox costs are
measured or estimated, and the pricing version used. The example
`agent_cost_events` view exposes input/output token counts, sandbox and
estimated costs, plus tool name and event time.

## Dashboard and alert recommendations

Build one dashboard with shared time range and filters for service, tool,
runtime, and error type. Link trace exemplars and event IDs from aggregate
panels to the detailed trace/event query.

| Dashboard area | SLO/SLA view |
| --- | --- |
| Agent request health | Successful completed requests and end-to-end latency percentiles against the service SLO. |
| Tool execution | Tool-call success rate, latency percentiles, timeout count, and slowest tools. |
| Sandbox lifecycle | Provision-to-ready and operation latency, capacity, lifecycle failures, and termination outcomes. |
| Failure attribution | Root-cause failures by taxonomy, tool, runtime, and sandbox image; link to representative traces. |
| Cost attribution | Input/output tokens and estimated/actual sandbox cost by model, tool, session, and tenant where authorized. |

Use the service's published SLO/SLA as the threshold source. Suggested initial
alerts, to be tuned against a baseline:

- Page when the agent or tool failure rate breaches its error-budget burn
  threshold over both a short and long window; group by root-cause taxonomy.
- Alert when tool or sandbox operation timeout rate exceeds its SLO, or
  sandbox readiness latency breaches its latency objective.
- Alert on a sustained increase in cost per successful request or token usage
  versus a rolling baseline; include top model/tool contributors.
- Alert on sandbox provisioning failures and abnormal lifecycle durations
  before they cause request-level SLO violations.

Every alert should include the affected service/tool/runtime, time window,
error type or cost driver, and a link to the dashboard and sampled trace
query. Avoid IDs as alert grouping labels.

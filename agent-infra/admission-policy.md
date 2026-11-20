---
status: Active
maintainer: pacoxu
last_updated: 2026-11-18
tags: agents, sandbox, admission, policy, kubernetes, isolation
canonical_path: agent-infra/admission-policy.md
---

# Agent Workload Sandbox Admission Policy

This design turns the Pod-versus-VM choice into a fail-closed admission
contract. It complements the [sandbox selection guide](../docs/kubernetes/isolation.md#layered-agent-sandbox-selection-2026-08-25):
the decision matrix is the policy, while admission both selects an execution
profile and rejects a workload if its effective runtime does not match.

## Trust and policy inputs

Do not treat labels supplied by an untrusted Pod creator as evidence of its
tenant or risk. The workload broker (or a trusted policy resolver) must derive
the inputs below from tenant identity, the tool registry, data catalog, GPU
request, and compliance system. It writes the resulting labels to the Pod and
the policy checks them before allowing it. Limit `create pods`, template
updates, and label mutation to that broker; tenant users should request a
workload through the broker, not directly create a lower-risk Pod.

| Input | Pod label | Allowed values / source |
| ----- | ---------- | ----------------------- |
| Tenant tier | `agent.example.com/tenant-tier` | `standard`, `regulated`; tenant registry |
| Data classification | `agent.example.com/data-classification` | `public`, `internal`, `confidential`, `restricted`; data catalog |
| Tool risk | `agent.example.com/tool-risk` | `low`, `medium`, `high`, `critical`; approved tool manifest |
| GPU requirement | `agent.example.com/gpu-required` | `true`, `false`; validated resource request |
| Compliance tag | `agent.example.com/compliance` | `none`, `regulated`; compliance system |
| Selected profile | `agent.example.com/placement` | `gvisor`, `kata`, `vm`; computed by the resolver |

Unknown or missing values are an admission error, not a reason to fall back to
a weaker runtime. `placement` is not an independent user choice: the resolver
computes it using the precedence in the matrix below.

## Decision matrix

Apply the first matching row. Higher rows override the lower-risk choice.
`vm` means a dedicated VM/microVM worker pool; its actual isolation mechanism
and node labels are cluster-specific.

| Agent scenario | Conditions | Runtime / placement output | Substrate sandbox class |
| --------------- | ---------- | -------------------------- | ----------------------- |
| Read-only retrieval or summarization | Standard tenant, public/internal data, low-risk tools, no GPU, no regulated tag | `runsc` / `gvisor-shared` | `gvisor` |
| Untrusted code or browser automation | Standard tenant, confidential data or medium-risk tools, no regulated tag | Kata / `kata-shared` | `kata` |
| High-risk tool execution | High/critical-risk tools, restricted data, regulated tenant, or regulated compliance tag | Kata on `vm-dedicated` pool; dedicated VM backend where required | `kata` or the platform's VM class |
| GPU code execution | GPU required and no condition in the higher-risk row | Kata on `kata-gpu` pool | `kata` |
| GPU plus restricted/regulated workload | GPU required and any higher-risk condition | Dedicated GPU VM pool; deny if unavailable | Platform-specific VM class |

`runc` is not an agent execution profile in this policy. gVisor is the
density-oriented profile, not a security boundary equivalent to a VM. Kata
provides a VM boundary when supported by the cluster. A `vm` placement still
requires a backend that actually provisions a dedicated VM; setting a node
label alone does not create one.

For Substrate, treat the class names above as policy-level intent and map them
to the sandbox classes supported by the installed Substrate release. Do not
assume the class name is a Kubernetes `RuntimeClass`. OpenShell's Kubernetes
supervisor can consume `runtimeClassName`; use the same policy output when
configuring its supervisor Pod. For
[agent-sandbox v1.0.x](https://github.com/kubernetes-sigs/agent-sandbox/tree/v1.0.11),
the API example below uses `agents.x-k8s.io/v1beta1` and places runtime and
scheduling requirements in `SandboxTemplate.spec.podTemplate.spec`.

The policy output can also be retained as evidence for
[KAR-0020 `workload_sandboxing`](https://github.com/cncf/k8s-ai-conformance/blob/main/docs/AIConformance-1.37.yaml).
Record the policy version, resolved inputs, selected profile, effective
`runtimeClassName`, and node pool with the workload's audit record. Treat
conformance status as version-specific; the v1.38 MUST requirement mentioned
in the issue discussion was a draft, not a substitute for checking the
published conformance version.

## Admission policy example

This Kyverno `ClusterPolicy` is the enforcement half of the design. It routes
the broker-computed profile to a runtime and node pool, and rejects requests
whose risk inputs require a stronger profile. Install Kyverno and the
`gvisor`, `kata` RuntimeClasses and pool labels first. Adapt the namespace
selector and pool values to the cluster. Do not grant tenants permission to
set the trusted labels or create `PolicyException` resources.

```yaml
apiVersion: kyverno.io/v1
kind: ClusterPolicy
metadata:
  name: agent-sandbox-placement
spec:
  background: false
  rules:
    - name: require-trusted-placement-inputs
      match:
        any:
          - resources:
              kinds:
                - Pod
              namespaces:
                - agent-*
      validate:
        failureAction: Enforce
        message: "Agent Pods require broker-resolved placement inputs."
        pattern:
          metadata:
            labels:
              agent.example.com/tenant-tier: "?*"
              agent.example.com/data-classification: "?*"
              agent.example.com/tool-risk: "?*"
              agent.example.com/gpu-required: "?*"
              agent.example.com/compliance: "?*"
              agent.example.com/placement: "gvisor | kata | vm"
    - name: deny-unknown-policy-inputs
      match:
        any:
          - resources:
              kinds:
                - Pod
              namespaces:
                - agent-*
      validate:
        failureAction: Enforce
        message: "Agent sandbox policy inputs must use an allowed value."
        deny:
          conditions:
            any:
              - key: "{{ request.object.metadata.labels.\"agent.example.com/tenant-tier\" }}"
                operator: NotIn
                value:
                  - standard
                  - regulated
              - key: "{{ request.object.metadata.labels.\"agent.example.com/data-classification\" }}"
                operator: NotIn
                value:
                  - public
                  - internal
                  - confidential
                  - restricted
              - key: "{{ request.object.metadata.labels.\"agent.example.com/tool-risk\" }}"
                operator: NotIn
                value:
                  - low
                  - medium
                  - high
                  - critical
              - key: "{{ request.object.metadata.labels.\"agent.example.com/gpu-required\" }}"
                operator: NotIn
                value:
                  - "true"
                  - "false"
              - key: "{{ request.object.metadata.labels.\"agent.example.com/compliance\" }}"
                operator: NotIn
                value:
                  - none
                  - regulated
    - name: route-gvisor
      match:
        any:
          - resources:
              kinds:
                - Pod
              namespaces:
                - agent-*
              selector:
                matchLabels:
                  agent.example.com/placement: gvisor
      mutate:
        patchStrategicMerge:
          spec:
            runtimeClassName: gvisor
            nodeSelector:
              sandbox.example.com/pool: gvisor-shared
    - name: route-kata-shared
      match:
        any:
          - resources:
              kinds:
                - Pod
              namespaces:
                - agent-*
              selector:
                matchLabels:
                  agent.example.com/placement: kata
                matchExpressions:
                  - key: agent.example.com/gpu-required
                    operator: In
                    values:
                      - "false"
      mutate:
        patchStrategicMerge:
          spec:
            runtimeClassName: kata
            nodeSelector:
              sandbox.example.com/pool: kata-shared
    - name: route-kata-gpu
      match:
        any:
          - resources:
              kinds:
                - Pod
              namespaces:
                - agent-*
              selector:
                matchLabels:
                  agent.example.com/placement: kata
                  agent.example.com/gpu-required: "true"
      mutate:
        patchStrategicMerge:
          spec:
            runtimeClassName: kata
            nodeSelector:
              sandbox.example.com/pool: kata-gpu
    - name: route-vm-gpu
      match:
        any:
          - resources:
              kinds:
                - Pod
              namespaces:
                - agent-*
              selector:
                matchLabels:
                  agent.example.com/placement: vm
                  agent.example.com/gpu-required: "true"
      mutate:
        patchStrategicMerge:
          spec:
            runtimeClassName: kata
            nodeSelector:
              sandbox.example.com/pool: vm-dedicated-gpu
    - name: route-vm
      match:
        any:
          - resources:
              kinds:
                - Pod
              namespaces:
                - agent-*
              selector:
                matchLabels:
                  agent.example.com/placement: vm
                matchExpressions:
                  - key: agent.example.com/gpu-required
                    operator: In
                    values:
                      - "false"
      mutate:
        patchStrategicMerge:
          spec:
            runtimeClassName: kata
            nodeSelector:
              sandbox.example.com/pool: vm-dedicated
    - name: deny-under-isolated-sensitive-workloads
      match:
        any:
          - resources:
              kinds:
                - Pod
              namespaces:
                - agent-*
      preconditions:
        any:
          - key: "{{ request.object.metadata.labels.\"agent.example.com/tenant-tier\" || '' }}"
            operator: Equals
            value: regulated
          - key: "{{ request.object.metadata.labels.\"agent.example.com/data-classification\" || '' }}"
            operator: Equals
            value: restricted
          - key: "{{ request.object.metadata.labels.\"agent.example.com/tool-risk\" || '' }}"
            operator: Equals
            value: critical
          - key: "{{ request.object.metadata.labels.\"agent.example.com/compliance\" || '' }}"
            operator: Equals
            value: regulated
      validate:
        failureAction: Enforce
        message: "Sensitive or regulated agent workloads must use the dedicated VM profile."
        deny:
          conditions:
            all:
              - key: "{{ request.object.metadata.labels.\"agent.example.com/placement\" || '' }}"
                operator: NotEquals
                value: vm
    - name: deny-high-risk-without-vm
      match:
        any:
          - resources:
              kinds:
                - Pod
              namespaces:
                - agent-*
      preconditions:
        any:
          - key: "{{ request.object.metadata.labels.\"agent.example.com/tool-risk\" || '' }}"
            operator: Equals
            value: high
      validate:
        failureAction: Enforce
        message: "High-risk tools must use the dedicated VM profile."
        deny:
          conditions:
            all:
              - key: "{{ request.object.metadata.labels.\"agent.example.com/placement\" || '' }}"
                operator: NotEquals
                value: vm
    - name: deny-gpu-without-kata-or-vm
      match:
        any:
          - resources:
              kinds:
                - Pod
              namespaces:
                - agent-*
      preconditions:
        all:
          - key: "{{ request.object.metadata.labels.\"agent.example.com/gpu-required\" || '' }}"
            operator: Equals
            value: "true"
          - key: "{{ request.object.metadata.labels.\"agent.example.com/tenant-tier\" || '' }}"
            operator: NotEquals
            value: regulated
          - key: "{{ request.object.metadata.labels.\"agent.example.com/data-classification\" || '' }}"
            operator: NotEquals
            value: restricted
          - key: "{{ request.object.metadata.labels.\"agent.example.com/tool-risk\" || '' }}"
            operator: NotEquals
            value: critical
          - key: "{{ request.object.metadata.labels.\"agent.example.com/compliance\" || '' }}"
            operator: NotEquals
            value: regulated
      validate:
        failureAction: Enforce
        message: "GPU agent workloads require Kata or the dedicated VM profile."
        deny:
          conditions:
            all:
              - key: "{{ request.object.metadata.labels.\"agent.example.com/placement\" || '' }}"
                operator: Equals
                value: gvisor
    - name: deny-medium-risk-on-gvisor
      match:
        any:
          - resources:
              kinds:
                - Pod
              namespaces:
                - agent-*
      preconditions:
        any:
          - key: "{{ request.object.metadata.labels.\"agent.example.com/tool-risk\" || '' }}"
            operator: Equals
            value: medium
          - key: "{{ request.object.metadata.labels.\"agent.example.com/data-classification\" || '' }}"
            operator: Equals
            value: confidential
      validate:
        failureAction: Enforce
        message: "Medium-risk or confidential agent workloads require Kata or the dedicated VM profile."
        deny:
          conditions:
            all:
              - key: "{{ request.object.metadata.labels.\"agent.example.com/placement\" || '' }}"
                operator: Equals
                value: gvisor
```

The sample deliberately keeps the decision resolver and admission enforcement
as separate responsibilities: the resolver computes `placement` from the full
matrix using trusted records; Kyverno applies the output and rejects the most
important under-classifications. Production policies must add rules for every
matrix row, validate each input against its allowed values, ensure the GPU
resource request agrees with `gpu-required`, and reject conflicting
`runtimeClassName`/`nodeSelector` values. Test the installed Kyverno version's
mutation and validation behavior before enabling `Enforce`. A missing RuntimeClass,
unavailable pool, resolver timeout, or policy error must fail closed rather
than silently downgrade.

### Agent Sandbox template

Use one immutable template per placement profile; do not let an untrusted
claim choose a weaker template. The template is a runtime/scheduling target,
not the source of tenant or risk classification. The example uses the
v1beta1 API and represents the shared Kata profile:

```yaml
apiVersion: agents.x-k8s.io/v1beta1
kind: SandboxTemplate
metadata:
  name: agent-kata
  namespace: agent-workloads
spec:
  podTemplate:
    spec:
      runtimeClassName: kata
      nodeSelector:
        sandbox.example.com/pool: kata-shared
      automountServiceAccountToken: false
      containers:
        - name: agent
          image: registry.example.com/agent-runtime:stable
          securityContext:
            allowPrivilegeEscalation: false
            capabilities:
              drop:
                - ALL
```

Pin and review the sandbox image, and apply Pod Security and network policies
independently. For GPU and dedicated-VM profiles, publish separate templates
with matching resource requests, pool selectors, and runtime; restrict
`SandboxClaim` creation so a requester cannot bypass admission by choosing a
different template.

## Default deny, exceptions, and audit

1. **Default deny:** only broker-owned agent namespaces are in scope. Reject
   missing/unknown inputs, unrecognized placement, unsupported GPU/runtime
   combinations, and any request that cannot be scheduled into its required
   pool. Never silently retry a denied VM placement as gVisor.
2. **Exception request:** the tenant owner submits a ticket with workload
   identity, requested deviation, reason, data/tool scope, compensating
   controls, and an expiry. Security and the workload owner approve it;
   compliance approves regulated-data deviations. Deny exceptions that remove
   the required isolation boundary for restricted data.
3. **Narrow exception:** an administrator creates a Kyverno
   `PolicyException` for the exact policy rule and workload identity, with
   ticket and expiry annotations. Use the `PolicyException` API supported by
   the installed Kyverno policy type/version. RBAC permits only the approval
   automation to create it. A controller removes expired exceptions; monitor
   exceptions and alert before expiry. Do not use a namespace-wide or wildcard
   exception.
4. **Audit:** enable Kubernetes API audit logging for Pod, SandboxTemplate,
   SandboxClaim, policy, and exception changes. Retain the admission decision,
   denied request, old/new placement, policy version, authenticated principal,
   ticket, and controller decision in the security audit system. Kyverno
   policy reports/logs are supplemental evidence, not a replacement for API
   audit logs.
5. **Misclassification and recovery:** on a false-low classification or
   runtime mismatch, stop/revoke the workload session, preserve audit evidence,
   correct the trusted registry entry, and recreate into the newly resolved
   stronger profile. Never move a live process into a weaker boundary. A
   false-high classification is reviewed by the tenant owner and security;
   rerun admission after the trusted source is corrected. Record reason,
   approver, old/new profile, and time for both cases.
6. **Rollout:** run policies in audit mode against representative Pods, compare
   predicted profile with actual runtime/pool, then enable enforcement. Keep a
   tested emergency rollback that disables only the new policy after security
   approval; retain existing Pod Security and network controls throughout.

Useful implementation references:

- [Kyverno policy exceptions](https://kyverno.io/docs/guides/exceptions/)
- [OpenShell RuntimeClass support](https://github.com/NVIDIA/OpenShell/pull/5349)
- [Agent Sandbox Kata and gVisor router support](https://github.com/kubernetes-sigs/agent-sandbox/pull/2003)
- [Agent Sandbox Nitro example](https://github.com/kubernetes-sigs/agent-sandbox/pull/2239)
- [Agent Sandbox Hyperlight example](https://github.com/kubernetes-sigs/agent-sandbox/pull/2119)
- [Agent Substrate v1.0.0](https://github.com/agent-substrate/substrate/releases/tag/v1.0.0)

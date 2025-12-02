---
status: Active
maintainer: pacoxu
date: 2025-12-01
tags: kubernetes, upgrade, rollback, emulation-version, compatibility
canonical_path: docs/blog/2025-12-01/safe-upgrade-rollback.md
---

# Kubernetes Safe Upgrade and Rollback: Emulation Version and Compatibility

## Introduction

Kubernetes upgrade has always been a one-way operation. Once you upgrade your
control plane to a new version, rolling back was not officially supported.
This has been a significant pain point for organizations running large-scale
clusters where upgrade failures can have severe consequences.

With the introduction of **Emulation Version** and **Minimum Compatibility
Version**, Kubernetes now provides a safer upgrade path with robust rollback
capabilities. This is a game-changer for cluster operators and platform
engineers.

## GKE Reliability at Scale

Google Kubernetes Engine (GKE) has achieved remarkable reliability:

<img width="600" alt="GKE Reliability"
  src="https://github.com/user-attachments/assets/f129580f-0c8d-4cc4-8562-59bc819543a0" />

- **99.98% Upgrade Success** across all GKE minor and patch upgrades
- **97% of GKE fleet** running on the 3 most recent Kubernetes versions

These numbers demonstrate the stability and maturity of the upgrade process,
but even with such high success rates, the remaining 0.02% of failures can be
critical for large organizations. That's why rollback capability is essential.

## The Future: Skip-Version Upgrades and Graceful Degradation

<img width="600" alt="Path Ahead"
  src="https://github.com/user-attachments/assets/143ca7eb-1083-461a-bb79-babf700b2950" />

The path ahead for Kubernetes upgrades includes:

- **Skip-version Upgrades**: Imagine... one upgrade, once a year
- **Graceful Degradation**: The ability to roll back without data loss

*Note: This is not an excuse to stop upgrading now!* Regular upgrades remain
important for security patches and feature improvements.

## Kubernetes Rollback is (finally) Here

<img width="800" alt="Kubernetes Rollback"
  src="https://github.com/user-attachments/assets/1243b8ac-bb61-4a01-b083-45256bcfb6d4" />

The key innovation is the separation of **Binary Version** and **Emulation
Version**:

### Binary Version Upgrade / Downgrade

- Binary: 1.32 → Binary: **1.33**
- Emulation: 1.32 → Emulation: 1.32

With this approach:

- Kubernetes API stays exactly the same
- All features stay exactly the same (none are removed or added, regardless
  of deprecations)
- **Fundamentally safe to roll back**

### Emulated Version Upgrade

- Binary: 1.33 → Binary: 1.33
- Emulation: 1.32 → Emulation: **1.33**

With this approach:

- New APIs and features become available
- Deprecations go into effect

## How It Works: Emulation Version and Compatibility Version

### `--emulation-version` (Kubernetes 1.31+)

The `--emulation-version` flag allows the API server to emulate the behavior
of a previous Kubernetes version, even when running a newer binary.

```bash
# Run 1.33 binary but behave like 1.32
kube-apiserver --emulation-version=1.32
```

Key benefits:

- **Granular upgrade steps**: Upgrade binary first, then enable new features
- **Robust rollback capability**: Can downgrade binary without data
  incompatibility

### `--min-compatibility-version` (Kubernetes 1.35+)

The `--min-compatibility-version` flag enables faster feature development and
adoption while maintaining backward compatibility.

```bash
# Ensure compatibility with 1.34 clients
kube-apiserver --min-compatibility-version=1.34
```

Key benefits:

- **Faster feature development**: New features can be developed without
  worrying about breaking older clients
- **Faster feature adoption**: Users can adopt new features more quickly

## Safer Upgrade, Safer Kubernetes

<img width="600" alt="Safer Upgrade"
  src="https://github.com/user-attachments/assets/02530976-ead6-4cc4-8144-6501a485200b" />

### Emulated Version

- Granular upgrade steps
- Robust rollback capability

### Min Compatibility Version

- Faster feature development
- Faster feature adoption

## Different Stages of Readiness During Upgrade

<img width="600" alt="Stages of Readiness"
  src="https://github.com/user-attachments/assets/6744abd9-336e-45cf-a051-1d346eeba6a9" />

The upgrade process can be broken down into three stages:

### Stage 1: Not Too Late to Regret

- Binary: N
- Emulated: N-1
- MinCompat: N-1

At this stage, you've upgraded the binary but are still emulating the previous
version. You can safely roll back to the previous binary version.

### Stage 2: New Chapter

- Binary: N
- Emulated: N
- MinCompat: N-1

At this stage, you've started using new features from version N. Rolling back
is still possible but may require some manual intervention for workloads
using new features.

### Stage 3: No Looking Back

- Binary: N
- Emulated: N
- MinCompat: N

At this stage, you're fully committed to version N. All clients and workloads
should be compatible with version N.

## Best Practices for Safe Upgrades

### 1. Staged Rollout

```bash
# Step 1: Upgrade binary, keep emulation version
kube-apiserver --emulation-version=1.32

# Step 2: Validate cluster health and workloads

# Step 3: Upgrade emulation version
kube-apiserver --emulation-version=1.33

# Step 4: Validate new features and deprecations
```

### 2. Pre-Upgrade Checklist

- Review deprecated APIs and feature gates
- Test workloads against the new version in a staging environment
- Ensure all operators and controllers are compatible
- Document rollback procedures

### 3. Rollback Procedure

```bash
# If issues arise after emulation version upgrade:
# Roll back emulation version first
kube-apiserver --emulation-version=1.32

# If issues persist after binary upgrade:
# Roll back to previous binary
# (Only safe if emulation version matches)
```

## KEP-4330: Compatibility Versions

For detailed technical information, see the Kubernetes Enhancement Proposal:

- [KEP-4330: Compatibility
  Versions](https://github.com/kubernetes/enhancements/tree/master/keps/sig-architecture/4330-compatibility-versions)

### Timeline

| Version | Feature |
| --- | --- |
| 1.31 | `--emulation-version` introduced (Alpha) |
| 1.34 | `--emulation-version` promoted (Beta) |
| 1.35 | `--min-compatibility-version` introduced |

## Use Cases

### Large Enterprise Clusters

For organizations running hundreds or thousands of clusters, the ability to
roll back provides a safety net during upgrade cycles. This is especially
important for:

- Financial services with strict SLAs
- Healthcare systems requiring high availability
- E-commerce platforms during peak traffic periods

### AI/ML Workloads

AI training jobs often run for days or weeks. The ability to roll back an
upgrade without disrupting long-running workloads is invaluable.

### Multi-Tenant Platforms

Platform providers can upgrade their control plane while giving tenants time
to migrate their workloads to use new APIs.

## Conclusion

The introduction of emulation version and compatibility version represents a
significant step forward for Kubernetes cluster management. By separating
binary upgrades from feature activation, operators now have:

1. **Safer upgrades**: Test new binaries without enabling new features
2. **Robust rollback**: Return to previous behavior without data loss
3. **Gradual adoption**: Enable new features at your own pace
4. **Better planning**: Clear stages for upgrade readiness

This is particularly important for AI infrastructure, where stability and
predictability are essential for running expensive GPU workloads.

---

## References

### KEPs and Documentation

- [KEP-4330: Compatibility
  Versions](https://github.com/kubernetes/enhancements/tree/master/keps/sig-architecture/4330-compatibility-versions)
- [Google Cloud Blog: Kubernetes gets minor version
  rollback](https://cloud.google.com/blog/products/containers-kubernetes/kubernetes-gets-minor-version-rollback)

### Conference Talks

- [KubeCon NA 2025 Keynote: GKE Reliability at
  Scale](https://www.youtube.com/watch?v=kPUdlmov5TM&list=PLj6h78yzYM2OPbGEIqJk2AT25wGu9mY8V&index=5&t=495s)
  (Navigating the Multi-Version Kubernetes Universe: How Emulation Version
  Shapes Your... - Siyuan Zhang)

### Related Topics

- [Kubernetes Learning Plan](../../kubernetes/learning-plan.md)
- [Scheduling Optimization](../../kubernetes/scheduling-optimization.md)

---

**Author**: AI Infrastructure Learning Path  
**Date**: December 1, 2025  
**Tags**: #kubernetes #upgrade #rollback #emulation-version #compatibility

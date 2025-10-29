---
status: Active
maintainer: pacoxu
last_updated: 2025-10-29
tags: kubernetes, learning-path, docker, cloud-native
canonical_path: docs/kubernetes/learning-plan.md
---

# 📘 Kubernetes Learning Plan

This document provides a structured learning path for Kubernetes. For specific
AI Infra-related topics, see:

- [Pod Startup Speed Optimization](./pod-startup-speed.md)
- [Workload Isolation](./isolation.md)
- [Pod Lifecycle](./pod-lifecycle.md)
- [Scheduling Optimization](./scheduling-optimization.md)
- [Dynamic Resource Allocation (DRA)](./dra.md)

## 🔰 Phase 0 – Foundations: Docker & Container Basics

Before diving into Kubernetes, it’s essential to understand how containers work.

### ✅ Key Topics

- **Docker Basics**
  - Images, Containers, Volumes
- **Docker Networking**
  - Bridge, Host, Overlay
- **Container Registry**
  - DockerHub, Harbor
- **Container Orchestration (Docker Native)**
  - `docker-compose`
  - Swarm & SwarmKit: cluster management, Raft-based leader election

---

## ⚙️ Phase 1 – Kubernetes 0.1 Era: First Steps into K8s

Understand the early architecture and ecosystem of Kubernetes.

### ✅ Key Topics

- **Basic Networking**
  - CNI Plugins: Calico, Flannel, Macvlan
  - Ingress, NodePort, External Load Balancer (e.g., F5)
- **Storage**
  - Drivers: ScaleIO, Portworx
- **RBAC & Resource Management**
  - Role-Based Access Control (RBAC)
  - ResourceQuota & LimitRange
  - Horizontal Pod Autoscaler (HPA)
- **Observability**
  - Prometheus (monitoring)
  - EFK Stack (Elasticsearch + Fluentd + Kibana)
- **Runtime**
  - Containerd

---

## 🚀 Phase 2 – Kubernetes 0.2 Era: Tools & Ecosystem Expansion

Dive into tools and components that enhance Kubernetes usability and operational capabilities.

### ✅ Key Topics

- **CoreDNS** – DNS for service discovery
- **Knative** – Serverless workloads on Kubernetes
- **Bootstrap Tools**
  - `kubeadm`, `kind`
- **Advanced Networking**
  - VLAN integrations
  - Istio service mesh
  - Keepalived (Virtual IP for HA)
- **Cluster Tools**
  - Velero (Backup/Restore)
  - KubeFed v2 (Federation)
  - VPA (Vertical Pod Autoscaler)
  - Thanos (Prometheus long-term storage)

---

## 🌐 Phase 3 – Kubernetes 0.3 Era: Cloud-Native Ecosystem

Learn how to manage production-grade, scalable, multi-cluster Kubernetes environments.
And as this include more ecosystem projects, some may be at sandbox level.

### ✅ Key Topics

- **Cluster Deployment**
  - Kubespray, Kops
- **Next-Gen Networking**
  - Cilium (eBPF)
  - Submariner (cross-cluster)
  - Whereabouts (IPAM)
  - MetalLB (bare-metal load balancing)
- **Modern Storage**
  - HwameiStor, local persistent volumes
- **Image Management & Federation**
  - Harbor (container registry)
  - Karmada (multi-cluster orchestration)
- **Authentication & Authorization**
  - Dex, Pinniped (identity and access management)
- **Observability & Service Mesh Enhancements**
  - Clusterpedia (cluster state query)
  - Merbridge (eBPF-based Istio acceleration)
  - OpenTelemetry (tracing, metrics, logging)

---

## 🛠 Suggested Resources

- [Kubernetes Official Docs](https://kubernetes.io/)
- [Awesome Kubernetes GitHub List](https://github.com/ramitsurana/awesome-kubernetes)
- Hands-on Tools:
  - [Play with Kubernetes](https://labs.play-with-k8s.com/)
  - `kind`, `minikube`, `k3s`

---

Happy learning! 🚀

Refer to https://kubernetes.io/ if you want to learn more about Kubernetes. Here is my personal learning notes.

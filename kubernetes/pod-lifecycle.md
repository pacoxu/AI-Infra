# Pod Lifecycle in Kubernetes

![pod-lifecycle](pod-lifecycle.png)


In Kubernetes, a Pod goes through several standard lifecycle **phases**. These phases describe the high-level status of the Pod, not the state of individual containers.

## Pod Phases

- **Pending**  
- **Running**  
- **Succeeded**  
- **Failed**  
- **Unknown**  

## Related Concepts (not expanded here)

- Container states  
- Init containers
- Sidecar containers
- Liveness probes  
- Readiness probes  
- Startup probes
- Restart policy
- Hooks: `preStop`, `postStart`
- SchedulingGates

More refer to [Issue #1](https://github.com/pacoxu/AI-Infra/issues/1) or [official docs](https://kubernetes.io/docs/concepts/workloads/pods/pod-lifecycle/).

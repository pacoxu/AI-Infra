# Pod Lifecycle in Kubernetes

![pod-lifecycle](pod-lifecycle.png)


In Kubernetes, a Pod goes through several standard lifecycle **phases**. These phases describe the high-level status of the Pod, not the state of individual containers.

## Pod Phases

- **Pending**  
  The Pod has been accepted by the Kubernetes system, but one or more of the containers are not yet created. This typically means scheduling is in progress or images are being pulled.

- **Running**  
  The Pod has been scheduled to a node. All containers have been created, and at least one is running or is in the process of starting or restarting.

- **Succeeded**  
  All containers in the Pod have terminated successfully and will not be restarted.

- **Failed**  
  All containers have terminated, and at least one container terminated with an error (non-zero exit status or was terminated by the system).

- **Unknown**  
  The state of the Pod cannot be determined, usually due to a communication error with the node hosting the Pod.

## Related Concepts (not expanded here)

- Container states  
- Init containers  
- Liveness probes  
- Readiness probes  
- Restart policy

More refer to [Issue #1](https://github.com/pacoxu/AI-Infra/issues/1) or [official docs](https://kubernetes.io/docs/concepts/workloads/pods/pod-lifecycle/).

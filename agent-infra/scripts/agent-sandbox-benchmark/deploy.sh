#!/usr/bin/env bash
# deploy.sh — Deploy agent-sandbox with the specified RuntimeClasses.
#
# Usage:
#   ./deploy.sh --runtimes runc,gvisor,kata,vm [--namespace benchmark]

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
NAMESPACE="benchmark"
RUNTIMES="runc,gvisor,kata,vm"

while [[ $# -gt 0 ]]; do
  case $1 in
    --runtimes) RUNTIMES="$2"; shift 2 ;;
    --namespace) NAMESPACE="$2"; shift 2 ;;
    *) echo "Unknown argument: $1" >&2; exit 1 ;;
  esac
done

echo "==> Creating namespace '${NAMESPACE}'..."
kubectl create namespace "${NAMESPACE}" --dry-run=client -o yaml | kubectl apply -f -

echo "==> Deploying SandboxWarmPools for runtimes: ${RUNTIMES}..."
IFS=',' read -ra RUNTIME_LIST <<< "${RUNTIMES}"
for runtime in "${RUNTIME_LIST[@]}"; do
  case "${runtime}" in
    runc)
      RUNTIME_CLASS_NAME=""
      ;;
    gvisor)
      RUNTIME_CLASS_NAME="gvisor"
      ;;
    kata)
      RUNTIME_CLASS_NAME="kata-qemu"
      ;;
    vm)
      echo "  Skipping WarmPool for 'vm' (not supported)."
      continue
      ;;
    *)
      echo "WARN: Unknown runtime '${runtime}', skipping." >&2
      continue
      ;;
  esac

  MANIFEST_FILE="${SCRIPT_DIR}/k8s/warmpool-${runtime}.yaml"
  if [[ ! -f "${MANIFEST_FILE}" ]]; then
    echo "WARN: ${MANIFEST_FILE} not found, skipping warm pool for '${runtime}'." >&2
    continue
  fi

  echo "  Deploying WarmPool for runtime '${runtime}'..."
  kubectl apply -n "${NAMESPACE}" -f "${MANIFEST_FILE}"
done

echo "==> Waiting for WarmPool pods to become Ready (timeout: 120s)..."
kubectl wait pod \
  -n "${NAMESPACE}" \
  --for=condition=Ready \
  --selector="agent-sandbox.kubernetes.io/warm-pool=true" \
  --timeout=120s 2>/dev/null || \
  echo "WARN: Some warm pool pods may not be ready yet. Check 'kubectl get pods -n ${NAMESPACE}'."

echo "==> Deployment complete."
echo "    Next: ./run-benchmark.sh --task-suite cpu --rounds 3 --output ./results"

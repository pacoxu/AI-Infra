#!/usr/bin/env bash
# setup.sh — Install dependencies for the agent-sandbox runtime benchmark.
#
# Requirements:
#   - kubectl configured against a running Kubernetes cluster
#   - helm v3.x
#   - go 1.21+ (for the oha / hey load generator)
#   - gVisor and Kata node pools already provisioned (see deploy.sh)
#
# Usage:
#   ./setup.sh

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

echo "==> Checking prerequisites..."
for cmd in kubectl helm go; do
  if ! command -v "$cmd" &>/dev/null; then
    echo "ERROR: '$cmd' not found. Please install it and re-run." >&2
    exit 1
  fi
done
echo "    kubectl: $(kubectl version --client -o json | python3 -c 'import sys,json; print(json.load(sys.stdin)["clientVersion"]["gitVersion"])')"
echo "    helm:    $(helm version --short)"
echo "    go:      $(go version)"

echo "==> Installing oha (HTTP load generator)..."
if ! command -v oha &>/dev/null; then
  go install github.com/hatoo/oha@latest
  echo "    oha installed at $(which oha)"
else
  echo "    oha already installed: $(oha --version 2>/dev/null || true)"
fi

echo "==> Installing agent-sandbox CRDs..."
export VERSION="${AGENT_SANDBOX_VERSION:-v0.1.0}"
kubectl apply -f "https://github.com/kubernetes-sigs/agent-sandbox/releases/download/${VERSION}/manifest.yaml" || \
  echo "WARN: Could not apply manifest (offline or version mismatch). Install manually."

echo "==> Installing RuntimeClasses..."
kubectl apply -f "${SCRIPT_DIR}/k8s/runtimeclasses.yaml"

echo "==> Setup complete."
echo "    Next: ./deploy.sh --runtimes runc,gvisor,kata,vm"

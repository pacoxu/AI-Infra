#!/usr/bin/env bash

set -euo pipefail

# Constants are consumed by poc.sh after this file is sourced.
# shellcheck disable=SC2034  # shellcheck cannot see consumers across source boundaries.

readonly POC_KUBERNETES_VERSION="v1.36.3"
# shellcheck disable=SC2034
readonly POC_KWOK_VERSION="v0.8.0"
# shellcheck disable=SC2034
readonly POC_KUEUE_VERSION="v0.19.0"
readonly POC_CLUSTER_NAME="${POC_CLUSTER_NAME:-dra-kueue-285}"
# shellcheck disable=SC2034
readonly POC_NAMESPACES=(dra-kueue-direct dra-kueue-tenant-a dra-kueue-tenant-b dra-kueue-failures)

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/../.." && pwd)"

log() {
  printf '[dra-kueue-kwok] %s\n' "$*"
}

fail() {
  printf '[dra-kueue-kwok] ERROR: %s\n' "$*" >&2
  exit 1
}

need_command() {
  command -v "$1" >/dev/null 2>&1 || fail "required command not found: $1"
}

version_word() {
  "$1" --version 2>&1 | awk '{for (i=1; i<=NF; i++) if ($i ~ /^v[0-9]+\./) {print $i; exit}}'
}

kwok_cluster_exists() {
  "${KWOKCTL_BIN}" get clusters -o name 2>/dev/null | awk '{print $1}' | grep -Fxq "${POC_CLUSTER_NAME}"
}

use_poc_kubeconfig() {
  export KUBECONFIG="${POC_KUBECONFIG}"
  [[ -s "${KUBECONFIG}" ]] || fail "kubeconfig not found: ${KUBECONFIG}; run setup first"
}

profile_nodes() {
  case "$1" in
    functional) printf '10\n' ;;
    scale) printf '100\n' ;;
    *) fail "profile must be functional or scale, got: $1" ;;
  esac
}

profile_workloads() {
  case "$1" in
    functional) printf '100\n' ;;
    scale) printf '1000\n' ;;
    *) fail "profile must be functional or scale, got: $1" ;;
  esac
}

wait_for_count() {
  local description="$1"
  local expected="$2"
  local command="$3"
  local timeout_seconds="${4:-180}"
  local start current
  start="$(date +%s)"
  while true; do
    current="$(eval "${command}" 2>/dev/null || printf '0')"
    [[ "${current}" == "${expected}" ]] && return 0
    if (( $(date +%s) - start >= timeout_seconds )); then
      fail "timed out waiting for ${description}: expected ${expected}, observed ${current}"
    fi
    sleep 2
  done
}

ensure_output_layout() {
  mkdir -p "${POC_OUTPUT}" "${POC_OUTPUT}/runs" "${POC_STATE}/bin" "${POC_STATE}/cache" "${POC_STATE}/generated"
}

set_runtime_paths() {
  POC_OUTPUT="${POC_OUTPUT:-${REPO_ROOT}/docs/kubernetes/dra-kueue-kwok-results-data}"
  POC_STATE="${POC_STATE:-${REPO_ROOT}/.artifacts/dra-kueue-kwok}"
  POC_KUBECONFIG="${POC_KUBECONFIG:-${POC_STATE}/kubeconfig}"
  KWOKCTL_BIN="${KWOKCTL_BIN:-kwokctl}"
  KUBECTL_BIN="${KUBECTL_BIN:-kubectl}"
  export POC_OUTPUT POC_STATE POC_KUBECONFIG KWOKCTL_BIN KUBECTL_BIN
}

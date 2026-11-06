#!/usr/bin/env bash

set -Eeuo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck disable=SC1091
source "${SCRIPT_DIR}/lib.sh"

PROFILE="functional"
ROUNDS=3
ACTION=""
POC_OUTPUT=""

usage() {
  cat <<'EOF'
Usage: poc.sh setup|run|collect|verify|cleanup [options]

Options:
  --profile functional|scale  Profile to setup or run (default: functional)
  --rounds N                  Number of rounds (default: 3)
  --output DIR                Versioned raw-result directory
  -h, --help                  Show this help

The fixed baseline is Kubernetes v1.36.3, KWOK v0.8.0 and Kueue v0.19.0.
EOF
}

parse_args() {
  [[ $# -gt 0 ]] || { usage >&2; exit 2; }
  ACTION="$1"
  shift
  case "${ACTION}" in
    setup|run|collect|verify|cleanup) ;;
    -h|--help) usage; exit 0 ;;
    *) usage >&2; fail "unknown action: ${ACTION}" ;;
  esac
  while [[ $# -gt 0 ]]; do
    case "$1" in
      --profile)
        [[ $# -ge 2 ]] || fail "--profile requires a value"
        PROFILE="$2"
        shift 2
        ;;
      --rounds)
        [[ $# -ge 2 ]] || fail "--rounds requires a value"
        ROUNDS="$2"
        shift 2
        ;;
      --output)
        [[ $# -ge 2 ]] || fail "--output requires a value"
        POC_OUTPUT="$2"
        shift 2
        ;;
      -h|--help)
        usage
        exit 0
        ;;
      *) usage >&2; fail "unknown option: $1" ;;
    esac
  done
  profile_nodes "${PROFILE}" >/dev/null
  [[ "${ROUNDS}" =~ ^[1-9][0-9]*$ ]] || fail "--rounds must be a positive integer"
}

download() {
  local url="$1"
  local destination="$2"
  if [[ -s "${destination}" ]]; then
    return 0
  fi
  log "downloading ${url}"
  curl --fail --location --retry 4 --retry-delay 2 --output "${destination}.tmp" "${url}"
  mv "${destination}.tmp" "${destination}"
}

bootstrap_kwokctl() {
  local os arch url downloaded system_version
  os="$(uname -s | tr '[:upper:]' '[:lower:]')"
  case "$(uname -m)" in
    arm64|aarch64) arch="arm64" ;;
    x86_64|amd64) arch="amd64" ;;
    *) fail "unsupported architecture for kwokctl: $(uname -m)" ;;
  esac
  downloaded="${POC_STATE}/bin/kwokctl-${POC_KWOK_VERSION}"
  if [[ ! -x "${downloaded}" ]] || [[ "$(version_word "${downloaded}")" != "${POC_KWOK_VERSION}" ]]; then
    system_version=""
    if command -v kwokctl >/dev/null 2>&1; then
      system_version="$(version_word kwokctl)"
    fi
    if [[ "${system_version}" == "${POC_KWOK_VERSION}" ]]; then
      KWOKCTL_BIN="$(command -v kwokctl)"
      export KWOKCTL_BIN
      return 0
    fi
    if command -v go >/dev/null 2>&1; then
      log "building exact kwokctl ${POC_KWOK_VERSION} from its tagged Go module"
      GOBIN="${POC_STATE}/bin" go install "sigs.k8s.io/kwok/cmd/kwokctl@${POC_KWOK_VERSION}"
      mv "${POC_STATE}/bin/kwokctl" "${downloaded}"
    else
      url="https://github.com/kubernetes-sigs/kwok/releases/download/${POC_KWOK_VERSION}/kwokctl-${os}-${arch}"
      download "${url}" "${downloaded}"
      chmod +x "${downloaded}"
    fi
  fi
  KWOKCTL_BIN="${downloaded}"
  export KWOKCTL_BIN
  [[ "$(version_word "${KWOKCTL_BIN}")" == "${POC_KWOK_VERSION}" ]] || \
    fail "kwokctl must be exactly ${POC_KWOK_VERSION}"
}

prepare_kueue_manifest() {
  local upstream manifest_dir patched config
  upstream="${POC_STATE}/cache/kueue-${POC_KUEUE_VERSION}-manifests.yaml"
  manifest_dir="${POC_STATE}/generated/kueue-${POC_KUEUE_VERSION}-kwok"
  patched="${manifest_dir}/manifests.yaml"
  config="${POC_STATE}/generated/kwokctl.yaml"
  download "https://github.com/kubernetes-sigs/kueue/releases/download/${POC_KUEUE_VERSION}/manifests.yaml" "${upstream}"
  python3 "${SCRIPT_DIR}/generate.py" patch-kueue-manifest \
    --source "${upstream}" \
    --config "${SCRIPT_DIR}/config/kueue-manager-config.yaml" \
    --output "${patched}"
  python3 "${SCRIPT_DIR}/generate.py" kwok-config \
    --template "${SCRIPT_DIR}/config/kwokctl.yaml" \
    --manifest "${manifest_dir}" \
    --output "${config}"
  POC_KWOK_CONFIG="${config}"
  POC_KWOK_CONFIG_ARGS=(--config "${POC_KWOK_CONFIG}" --config "${SCRIPT_DIR}/config/stages.yaml")
  export POC_KWOK_CONFIG
}

assert_server_version() {
  local observed
  observed="$(${KUBECTL_BIN} version -o json | jq -r '.serverVersion.gitVersion')"
  [[ "${observed}" == "${POC_KUBERNETES_VERSION}" ]] || \
    fail "server version must be exactly ${POC_KUBERNETES_VERSION}; observed ${observed}; refusing to downgrade"
}

preflight_apis() {
  local resource group
  local -a resources
  ${KUBECTL_BIN} api-versions | grep -Fxq 'resource.k8s.io/v1' || \
    fail 'required API version not discoverable: resource.k8s.io/v1'
  ${KUBECTL_BIN} api-versions | grep -Fxq 'kueue.x-k8s.io/v1beta2' || \
    fail 'required API version not discoverable: kueue.x-k8s.io/v1beta2'
  for group in resource.k8s.io kueue.x-k8s.io; do
    case "${group}" in
      resource.k8s.io) resources=(resourceslices resourceclaimtemplates deviceclasses) ;;
      kueue.x-k8s.io) resources=(clusterqueues localqueues workloads) ;;
    esac
    for resource in "${resources[@]}"; do
      ${KUBECTL_BIN} api-resources --api-group="${group}" -o name | \
        sed 's/\..*$//' | grep -Fxq "${resource}" || \
        fail "required API not discoverable: ${resource}.${group}"
    done
  done
  local image
  image="$(docker ps --format '{{.Image}} {{.Names}}' | awk -v cluster="${POC_CLUSTER_NAME}" '$2 ~ cluster && $1 ~ /kueue/ {print $1; exit}')"
  [[ "${image}" == "registry.k8s.io/kueue/kueue:${POC_KUEUE_VERSION}" ]] || \
    fail "Kueue component image must be ${POC_KUEUE_VERSION}; observed ${image:-missing}"
}

dry_run_manifests() {
  local generated="$1"
  local file start
  for file in \
    "${SCRIPT_DIR}/manifests/base.yaml" \
    "${SCRIPT_DIR}/manifests/claim-templates.yaml" \
    "${generated}/namespaces.yaml" \
    "${generated}/queues.yaml" \
    "${generated}/resource-slices.yaml"; do
    start="$(date +%s)"
    while ! ${KUBECTL_BIN} apply --server-side --dry-run=server -f "${file}" >/dev/null 2>&1; do
      if (( $(date +%s) - start >= 120 )); then
        ${KUBECTL_BIN} apply --server-side --dry-run=server -f "${file}" >/dev/null
        fail "server-side dry-run did not become ready for ${file}"
      fi
      sleep 2
    done
  done
  if rg -n 'resource\.k8s\.io/v1beta|kueue\.x-k8s\.io/v1beta1' \
    "${SCRIPT_DIR}/manifests" "${SCRIPT_DIR}/config" "${generated}" \
    -g '*.yaml' -g '*.yml' >/dev/null; then
    fail "deprecated DRA or Kueue API found in PoC manifests"
  fi
}

reset_poc_objects() {
  ${KUBECTL_BIN} delete namespace "${POC_NAMESPACES[@]}" --ignore-not-found --wait=true >/dev/null
  ${KUBECTL_BIN} delete resourceslices.resource.k8s.io -l benchmark.aiinfra.dev/suite=dra-kueue-kwok \
    --ignore-not-found >/dev/null 2>&1 || true
  ${KUBECTL_BIN} delete clusterqueue dra-kueue-tenant-a dra-kueue-tenant-b --ignore-not-found >/dev/null
  ${KUBECTL_BIN} delete cohort dra-kueue-kwok --ignore-not-found >/dev/null
  ${KUBECTL_BIN} delete resourceflavor kwok-gpu --ignore-not-found >/dev/null
  ${KUBECTL_BIN} delete deviceclass gpu.kwok.aiinfra.dev empty-gpu.kwok.aiinfra.dev extended-gpu.kwok.aiinfra.dev \
    --ignore-not-found >/dev/null
  ${KUBECTL_BIN} delete priorityclass dra-kueue-low dra-kueue-high --ignore-not-found >/dev/null
}

apply_poc_model() {
  local nodes="$1"
  local generated="${POC_STATE}/generated/${PROFILE}"
  mkdir -p "${generated}"
  reset_poc_objects
  ${KUBECTL_BIN} get nodes -o json >"${generated}/nodes.json"
  python3 "${SCRIPT_DIR}/generate.py" setup \
    --nodes "${nodes}" \
    --nodes-json "${generated}/nodes.json" \
    --output "${generated}"
  ${KUBECTL_BIN} apply --server-side -f "${generated}/namespaces.yaml" >/dev/null
  dry_run_manifests "${generated}"
  ${KUBECTL_BIN} apply --server-side -f "${SCRIPT_DIR}/manifests/base.yaml" >/dev/null
  ${KUBECTL_BIN} apply --server-side -f "${generated}/queues.yaml" >/dev/null
  ${KUBECTL_BIN} apply --server-side -f "${generated}/resource-slices.yaml" >/dev/null
  for namespace in "${POC_NAMESPACES[@]}"; do
    ${KUBECTL_BIN} apply --server-side -n "${namespace}" -f "${SCRIPT_DIR}/manifests/claim-templates.yaml" >/dev/null
  done
}

do_setup() {
  need_command curl
  need_command docker
  need_command jq
  need_command python3
  need_command rg
  need_command "${KUBECTL_BIN}"
  docker version >/dev/null
  ensure_output_layout
  bootstrap_kwokctl
  prepare_kueue_manifest
  local nodes
  nodes="$(profile_nodes "${PROFILE}")"
  if kwok_cluster_exists; then
    "${KWOKCTL_BIN}" delete cluster --name "${POC_CLUSTER_NAME}" --kubeconfig "${POC_KUBECONFIG}" >/dev/null
  fi
  log "creating KWOK ${POC_KWOK_VERSION} cluster with Kubernetes ${POC_KUBERNETES_VERSION} and Kueue ${POC_KUEUE_VERSION}"
  "${KWOKCTL_BIN}" create cluster \
    --name "${POC_CLUSTER_NAME}" \
    "${POC_KWOK_CONFIG_ARGS[@]}" \
    --kubeconfig "${POC_KUBECONFIG}" \
    --timeout 15m \
    --wait 5m
  "${KWOKCTL_BIN}" get kubeconfig --name "${POC_CLUSTER_NAME}" "${POC_KWOK_CONFIG_ARGS[@]}" >"${POC_KUBECONFIG}"
  use_poc_kubeconfig
  assert_server_version
  preflight_apis
  "${KWOKCTL_BIN}" scale node --name "${POC_CLUSTER_NAME}" "${POC_KWOK_CONFIG_ARGS[@]}" \
    --replicas "${nodes}" \
    --param '.metadata.labels.type="kwok"' \
    --param '.status.allocatable.cpu="32"' \
    --param '.status.allocatable.memory="256Gi"' \
    --param '.status.allocatable.pods="4096"'
  wait_for_count "KWOK nodes" "${nodes}" "${KUBECTL_BIN} get nodes -o json | jq '.items | length'" 300
  apply_poc_model "${nodes}"
  log "setup complete: ${nodes} nodes and $((nodes * 8)) simulated, non-shareable DRA devices"
}

wait_for_logical_ready() {
  local run="$1"
  local expected="$2"
  local expected_pods="$3"
  local timeout_seconds="$4"
  local path="$5"
  local selector="benchmark.aiinfra.dev/run=${run},benchmark.aiinfra.dev/path=${path}"
  local start total ready total_pods ready_pods
  start="$(date +%s)"
  while true; do
    total="$(${KUBECTL_BIN} get pod -A -l "${selector}" -o json | jq '[.items[].metadata.labels["benchmark.aiinfra.dev/workload"]] | unique | length')"
    ready="$(${KUBECTL_BIN} get pod -A -l "${selector}" -o json | jq '[.items[] | select(any(.status.conditions[]?; .type == "Ready" and .status == "True")) | .metadata.labels["benchmark.aiinfra.dev/workload"]] | unique | length')"
    total_pods="$(${KUBECTL_BIN} get pod -A -l "${selector}" -o json | jq '.items | length')"
    ready_pods="$(${KUBECTL_BIN} get pod -A -l "${selector}" -o json | jq '[.items[] | select(any(.status.conditions[]?; .type == "Ready" and .status == "True"))] | length')"
    if [[ "${total}" == "${expected}" && "${ready}" == "${expected}" && \
          "${total_pods}" == "${expected_pods}" && "${ready_pods}" == "${expected_pods}" ]]; then
      return 0
    fi
    if (( $(date +%s) - start >= timeout_seconds )); then
      fail "timed out waiting for ${expected} logical/${expected_pods} Pod workloads: observed logical=${total}, ready-logical=${ready}, Pods=${total_pods}, ready-Pods=${ready_pods}"
    fi
    sleep 2
  done
}

wait_for_preemption() {
  local run="$1"
  local timeout_seconds="$2"
  local start observed
  start="$(date +%s)"
  while true; do
    observed="$(${KUBECTL_BIN} get workloads -A \
      -l "benchmark.aiinfra.dev/run=${run},benchmark.aiinfra.dev/scenario=mixed" -o json | \
      jq '[.items[].status.conditions[]? | select(.type == "Evicted" and .status == "True" and .reason == "Preempted")] | length')"
    if (( observed > 0 )); then
      return 0
    fi
    if (( $(date +%s) - start >= timeout_seconds )); then
      fail "timed out waiting for low-priority borrower preemption"
    fi
    sleep 2
  done
}

apply_phase() {
  local run="$1"
  local round_number="$2"
  local total="$3"
  local phase="$4"
  local output="$5"
  python3 "${SCRIPT_DIR}/generate.py" workloads \
    --run "${run}" --profile "${PROFILE}" --round "${round_number}" --total "${total}" \
    --phase "${phase}" --output "${output}/${phase}.yaml"
  ${KUBECTL_BIN} apply --server-side --dry-run=server -f "${output}/${phase}.yaml" >/dev/null
  ${KUBECTL_BIN} apply --server-side -f "${output}/${phase}.yaml" >/dev/null
}

run_short_churn() {
  local run="$1"
  local round_number="$2"
  local total="$3"
  local path="$4"
  local output="$5"
  local short_count="$((total * 60 / 100))"
  local wave_size=20
  local start count ready_expected
  for ((start = 0; start < short_count; start += wave_size)); do
    count="${wave_size}"
    if (( start + count > short_count )); then
      count="$((short_count - start))"
    fi
    python3 "${SCRIPT_DIR}/generate.py" workloads \
      --run "${run}" --profile "${PROFILE}" --round "${round_number}" --total "${total}" \
      --phase "$([[ "${path}" == "direct" ]] && printf 'direct' || printf 'short')" \
      --start "${start}" --count "${count}" --output "${output}/${path}-short-wave-${start}.yaml"
    ${KUBECTL_BIN} apply --server-side --dry-run=server -f "${output}/${path}-short-wave-${start}.yaml" >/dev/null
    ${KUBECTL_BIN} apply --server-side -f "${output}/${path}-short-wave-${start}.yaml" >/dev/null
    ready_expected="$((start + count))"
    wait_for_logical_ready "${run}" "${ready_expected}" "${ready_expected}" 180 "${path}"
  done
}

delete_phase() {
  local run="$1"
  local phase="$2"
  local selector="benchmark.aiinfra.dev/run=${run}"
  case "${phase}" in
    direct)
      ${KUBECTL_BIN} delete jobs -A -l "${selector},benchmark.aiinfra.dev/path=direct" \
        --ignore-not-found --wait=true >/dev/null
      ;;
    short)
      ${KUBECTL_BIN} delete jobs -A -l "${selector},benchmark.aiinfra.dev/scenario=short,benchmark.aiinfra.dev/path=kueue" \
        --ignore-not-found --wait=true >/dev/null
      ;;
    mixed-low)
      ${KUBECTL_BIN} delete deployments -n dra-kueue-tenant-a -l "${selector},benchmark.aiinfra.dev/scenario=mixed" \
        --ignore-not-found --wait=true >/dev/null
      ;;
    mixed-high)
      ${KUBECTL_BIN} delete deployments -n dra-kueue-tenant-b -l "${selector},benchmark.aiinfra.dev/scenario=mixed" \
        --ignore-not-found --wait=true >/dev/null
      ;;
    extended-smoke)
      ${KUBECTL_BIN} delete jobs -A -l "${selector},benchmark.aiinfra.dev/scenario=extended-smoke" \
        --ignore-not-found --wait=true >/dev/null
      ;;
    steady)
      ${KUBECTL_BIN} delete jobs,deployments -A -l "${selector},benchmark.aiinfra.dev/scenario in (long,inference)" \
        --ignore-not-found --wait=true >/dev/null
      ;;
  esac
}

capture_diagnostics() {
  local round_dir="$1"
  ${KUBECTL_BIN} get clusterqueues,cohorts -o json >"${round_dir}/queues.json"
  ${KUBECTL_BIN} get events -A -o json >"${round_dir}/kubernetes-events.json"
  ${KUBECTL_BIN} get --raw '/apis/visibility.kueue.x-k8s.io/v1beta1/clusterqueues/dra-kueue-tenant-a/pendingworkloads' \
    >"${round_dir}/pending-tenant-a.json" 2>"${round_dir}/pending-tenant-a.error" || true
  local output
  output="${round_dir}/kueue-metrics.prom"
  # kwokctl v0.8.0 turns Kueue Services into port-less ExternalNames and does
  # not expose the controller's metrics port. The Kueue log is still collected,
  # while object samples below retain queue wait and weighted-share evidence.
  : >"${output}"
  output="${round_dir}/kube-scheduler-metrics.prom"
  curl --fail --insecure --silent --show-error 'https://127.0.0.1:10259/metrics' >"${output}"
  [[ -s "${output}" ]] || fail "failed to collect kube-scheduler metrics"
  "${KWOKCTL_BIN}" logs kube-scheduler --name "${POC_CLUSTER_NAME}" "${POC_KWOK_CONFIG_ARGS[@]}" \
    >"${round_dir}/kube-scheduler.log" 2>&1 || true
  "${KWOKCTL_BIN}" logs kueue --name "${POC_CLUSTER_NAME}" "${POC_KWOK_CONFIG_ARGS[@]}" \
    >"${round_dir}/kueue.log" 2>&1 || true
}

run_failure_case() {
  local run="$1"
  local round_number="$2"
  local total_gpu="$3"
  local case="$4"
  local round_dir="$5"
  python3 "${SCRIPT_DIR}/generate.py" failure \
    --run "${run}" --profile "${PROFILE}" --round "${round_number}" --total-gpu "${total_gpu}" \
    --case "${case}" --output "${round_dir}/failure-${case}.yaml"
  ${KUBECTL_BIN} apply --server-side --dry-run=server -f "${round_dir}/failure-${case}.yaml" >/dev/null
  ${KUBECTL_BIN} apply --server-side -f "${round_dir}/failure-${case}.yaml" >/dev/null
  case "${case}" in
    quota-insufficient)
      sleep 15
      ;;
    no-matching-slice|admitted-unschedulable)
      sleep 75
      ;;
    wait-for-pods-ready)
      # 60s timeout + 5s and 10s backoffs; allow time to observe two requeues.
      sleep 155
      ;;
  esac
  ${KUBECTL_BIN} delete job -n dra-kueue-failures "failure-${case}" --ignore-not-found --wait=true >/dev/null
  if [[ "${case}" == "quota-insufficient" ]]; then
    ${KUBECTL_BIN} delete resourceclaimtemplate -n dra-kueue-failures too-many-gpus --ignore-not-found >/dev/null
  fi
  sleep 3
}

run_round() {
  local round_number="$1"
  local total="$2"
  local nodes="$3"
  local run
  run="${PROFILE}-r${round_number}-$(date -u +%Y%m%dT%H%M%SZ)"
  local round_dir="${POC_OUTPUT}/runs/${PROFILE}/round-${round_number}"
  local stop_file="${round_dir}/collector.stop"
  local collector_pid
  mkdir -p "${round_dir}"
  [[ ! -e "${round_dir}/run.json" && ! -e "${round_dir}/workloads.jsonl" && ! -e "${round_dir}/events.jsonl" ]] || \
    fail "round output already exists: ${round_dir}; choose a new --output directory or remove it explicitly"
  rm -f "${stop_file}"
  local namespace
  for namespace in "${POC_NAMESPACES[@]}"; do
    ${KUBECTL_BIN} delete jobs,deployments -n "${namespace}" -l 'benchmark.aiinfra.dev/run' \
      --ignore-not-found --wait=true >/dev/null 2>&1 || true
  done
  python3 "${SCRIPT_DIR}/collect.py" \
    --run "${run}" --profile "${PROFILE}" --round "${round_number}" --devices "$((nodes * 8))" \
    --output "${round_dir}" --stop-file "${stop_file}" --kubectl "${KUBECTL_BIN}" &
  collector_pid=$!
  POC_ROUND_STOP_FILE="${stop_file}"
  POC_COLLECTOR_PID="${collector_pid}"
  trap 'touch "${POC_ROUND_STOP_FILE}"; wait "${POC_COLLECTOR_PID}" || true' EXIT INT TERM

  local short_count="$((total * 60 / 100))"
  local steady_count="$((total * 20 / 100))"
  local mixed_half="$((total * 10 / 100))"

  log "${PROFILE} round ${round_number}: direct no-Kueue baseline"
  run_short_churn "${run}" "${round_number}" "${total}" direct "${round_dir}"
  sleep 2
  delete_phase "${run}" direct
  sleep 4

  log "${PROFILE} round ${round_number}: Kueue short-job churn"
  run_short_churn "${run}" "${round_number}" "${total}" kueue "${round_dir}"
  sleep 2
  delete_phase "${run}" short
  sleep 4

  log "${PROFILE} round ${round_number}: long training and quasi-online inference"
  apply_phase "${run}" "${round_number}" "${total}" steady "${round_dir}"
  wait_for_logical_ready "${run}" "${steady_count}" "$((total * 60 / 100))" 900 kueue
  sleep 15

  log "${PROFILE} round ${round_number}: low-priority borrower, then high-priority owner reclaim"
  apply_phase "${run}" "${round_number}" "${total}" mixed-low "${round_dir}"
  wait_for_logical_ready "${run}" "$((steady_count + mixed_half))" "$((total * 80 / 100))" 900 kueue
  apply_phase "${run}" "${round_number}" "${total}" mixed-high "${round_dir}"
  wait_for_preemption "${run}" 300
  # Preserve the transient Evicted=True condition for at least four collector
  # polls before deleting the borrower.
  sleep 2
  delete_phase "${run}" mixed-low
  wait_for_logical_ready "${run}" "$((steady_count + mixed_half))" "$((total * 80 / 100))" 900 kueue
  sleep 10
  delete_phase "${run}" steady
  delete_phase "${run}" mixed-high
  sleep 5

  log "${PROFILE} round ${round_number}: extended-resource compatibility smoke"
  apply_phase "${run}" "${round_number}" "${total}" extended-smoke "${round_dir}"
  wait_for_logical_ready "${run}" 1 1 180 kueue
  sleep 2
  delete_phase "${run}" extended-smoke
  sleep 4

  log "${PROFILE} round ${round_number}: fixed failure suite"
  local failure
  for failure in quota-insufficient no-matching-slice admitted-unschedulable wait-for-pods-ready; do
    run_failure_case "${run}" "${round_number}" "$((nodes * 8))" "${failure}" "${round_dir}"
  done
  capture_diagnostics "${round_dir}"
  touch "${stop_file}"
  wait "${collector_pid}"
  trap - EXIT INT TERM
  jq -n \
    --arg run "${run}" --arg profile "${PROFILE}" --argjson round "${round_number}" \
    --argjson nodes "${nodes}" --argjson workloads "${total}" \
    --arg kubernetes "${POC_KUBERNETES_VERSION}" --arg kwok "${POC_KWOK_VERSION}" --arg kueue "${POC_KUEUE_VERSION}" \
    '{run:$run,profile:$profile,round:$round,nodes:$nodes,logicalWorkloads:$workloads,versions:{kubernetes:$kubernetes,kwok:$kwok,kueue:$kueue}}' \
    >"${round_dir}/run.json"
}

do_run() {
  ensure_output_layout
  bootstrap_kwokctl
  prepare_kueue_manifest
  use_poc_kubeconfig
  assert_server_version
  preflight_apis
  local nodes total observed_nodes
  nodes="$(profile_nodes "${PROFILE}")"
  total="$(profile_workloads "${PROFILE}")"
  observed_nodes="$(${KUBECTL_BIN} get nodes -o json | jq '.items | length')"
  [[ "${observed_nodes}" == "${nodes}" ]] || \
    fail "profile ${PROFILE} needs ${nodes} nodes, observed ${observed_nodes}; run setup --profile ${PROFILE}"
  local round_number
  for ((round_number = 1; round_number <= ROUNDS; round_number++)); do
    run_round "${round_number}" "${total}" "${nodes}"
  done
  log "run complete; execute poc.sh collect --profile ${PROFILE} --rounds ${ROUNDS}"
}

do_collect() {
  ensure_output_layout
  python3 "${SCRIPT_DIR}/analyze.py" \
    --input "${POC_OUTPUT}" \
    --profiles "${PROFILE}" \
    --rounds "${ROUNDS}" \
    --summary "${POC_OUTPUT}/summary-${PROFILE}.json" \
    --report "${POC_OUTPUT}/report-${PROFILE}.md"
  log "summary written to ${POC_OUTPUT}/summary-${PROFILE}.json"
}

do_verify() {
  ensure_output_layout
  python3 "${SCRIPT_DIR}/analyze.py" \
    --input "${POC_OUTPUT}" \
    --profiles "${PROFILE}" \
    --rounds "${ROUNDS}" \
    --summary "${POC_OUTPUT}/summary-${PROFILE}.json" \
    --report "${POC_OUTPUT}/report-${PROFILE}.md" \
    --verify
}

do_cleanup() {
  ensure_output_layout
  bootstrap_kwokctl
  prepare_kueue_manifest
  if kwok_cluster_exists; then
    if [[ -s "${POC_KUBECONFIG}" ]]; then
      use_poc_kubeconfig
      reset_poc_objects
      local residual=0 namespace
      for namespace in "${POC_NAMESPACES[@]}"; do
        if ${KUBECTL_BIN} get namespace "${namespace}" >/dev/null 2>&1; then
          residual=$((residual + 1))
        fi
      done
      residual=$((residual + $(${KUBECTL_BIN} get resourceslices -l benchmark.aiinfra.dev/suite=dra-kueue-kwok -o json | jq '.items | length')))
      residual=$((residual + $(${KUBECTL_BIN} get clusterqueues -l 'benchmark.aiinfra.dev/suite=dra-kueue-kwok' -o json 2>/dev/null | jq '.items | length' || printf '0')))
      (( residual == 0 )) || fail "cleanup left ${residual} PoC objects before cluster deletion"
    fi
    "${KWOKCTL_BIN}" delete cluster --name "${POC_CLUSTER_NAME}" "${POC_KWOK_CONFIG_ARGS[@]}" \
      --kubeconfig "${POC_KUBECONFIG}"
  fi
  rm -f "${POC_KUBECONFIG}"
  if [[ -s "${POC_KUBECONFIG}" ]]; then
    fail "cleanup left kubeconfig behind: ${POC_KUBECONFIG}"
  fi
  if kwok_cluster_exists; then
    fail "cleanup left KWOK cluster behind: ${POC_CLUSTER_NAME}"
  fi
  log "cleanup complete; raw results under ${POC_OUTPUT} were preserved"
}

parse_args "$@"
set_runtime_paths
case "${ACTION}" in
  setup) do_setup ;;
  run) do_run ;;
  collect) do_collect ;;
  verify) do_verify ;;
  cleanup) do_cleanup ;;
esac

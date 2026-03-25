#!/usr/bin/env bash
# run-benchmark.sh — Execute the agent-sandbox runtime benchmark.
#
# Usage:
#   ./run-benchmark.sh \
#     --task-suite cpu|gpu|browser|all \
#     --rounds 3 \
#     --output ./results \
#     [--namespace benchmark] \
#     [--runtimes runc,gvisor,kata,vm] \
#     [--concurrency 10] \
#     [--requests 500]
#
# Output layout:
#   ./results/
#     round-1/
#       runc/      cold-start.jsonl  tasks.jsonl
#       gvisor/    cold-start.jsonl  tasks.jsonl
#       kata/      cold-start.jsonl  tasks.jsonl
#       vm/        cold-start.jsonl  tasks.jsonl
#     round-2/  ...
#     round-3/  ...

set -euo pipefail

NAMESPACE="benchmark"
RUNTIMES="runc,gvisor,kata,vm"
TASK_SUITE="cpu"
ROUNDS=3
OUTPUT_DIR="./results"
CONCURRENCY=10
REQUESTS=500

while [[ $# -gt 0 ]]; do
  case $1 in
    --task-suite)  TASK_SUITE="$2";  shift 2 ;;
    --rounds)      ROUNDS="$2";       shift 2 ;;
    --output)      OUTPUT_DIR="$2";   shift 2 ;;
    --namespace)   NAMESPACE="$2";    shift 2 ;;
    --runtimes)    RUNTIMES="$2";     shift 2 ;;
    --concurrency) CONCURRENCY="$2";  shift 2 ;;
    --requests)    REQUESTS="$2";     shift 2 ;;
    *) echo "Unknown argument: $1" >&2; exit 1 ;;
  esac
done

# ---------------------------------------------------------------------------
# Task definitions
# ---------------------------------------------------------------------------
declare -A TASK_COMMANDS
TASK_COMMANDS["shell-basic"]='echo hello && ls /etc/os-release && cat /etc/hostname'
TASK_COMMANDS["shell-compute"]='python3 -c "n=100000;s=[True]*(n+1);s[0]=s[1]=False;[s.__setitem__(j,False) for i in range(2,int(n**.5)+1) if s[i] for j in range(i*i,n+1,i)];print(sum(s))"'
TASK_COMMANDS["code-python"]='python3 /bench/cpu_task.py'
TASK_COMMANDS["code-node"]='node /bench/cpu_task.js'
TASK_COMMANDS["browser-fetch"]='chromium-browser --headless --disable-gpu --dump-dom https://example.com 2>/dev/null | wc -c'
TASK_COMMANDS["tool-call-chain"]='/bench/tool_chain.sh'
TASK_COMMANDS["gpu-torch-smoke"]='python3 -c "import torch; print(torch.cuda.is_available())"'
TASK_COMMANDS["gpu-matmul"]='python3 /bench/gpu_matmul.py'

cpu_tasks="shell-basic shell-compute code-python code-node"
gpu_tasks="gpu-torch-smoke gpu-matmul"
browser_tasks="browser-fetch tool-call-chain"
all_tasks="${cpu_tasks} ${gpu_tasks} ${browser_tasks}"

case "${TASK_SUITE}" in
  cpu)     TASKS="${cpu_tasks}" ;;
  gpu)     TASKS="${gpu_tasks}" ;;
  browser) TASKS="${browser_tasks}" ;;
  all)     TASKS="${all_tasks}" ;;
  *)       echo "Unknown task suite: ${TASK_SUITE}" >&2; exit 1 ;;
esac

IFS=',' read -ra RUNTIME_LIST <<< "${RUNTIMES}"

mkdir -p "${OUTPUT_DIR}"

# ---------------------------------------------------------------------------
# Helper: convert runtime name to RuntimeClass name (empty = runc default)
# ---------------------------------------------------------------------------
runtime_to_class() {
  local rt="$1"
  case "${rt}" in
    runc)   echo "" ;;
    gvisor) echo "gvisor" ;;
    kata)   echo "kata-qemu" ;;
    vm)     echo "vm-isolated" ;;
    *)      echo "" ;;
  esac
}

# ---------------------------------------------------------------------------
# Helper: generate Sandbox manifest YAML
# ---------------------------------------------------------------------------
sandbox_manifest() {
  local name="$1"
  local runtime_class="$2"
  local sleep_secs="${3:-60}"

  if [[ -n "${runtime_class}" ]]; then
    cat <<YAML
apiVersion: agents.x-k8s.io/v1alpha1
kind: Sandbox
metadata:
  name: ${name}
spec:
  podTemplate:
    spec:
      runtimeClassName: ${runtime_class}
      containers:
      - name: agent
        image: ghcr.io/kubernetes-sigs/agent-sandbox/agent-runtime:v0.1.0
        command: ["sleep", "${sleep_secs}"]
YAML
  else
    cat <<YAML
apiVersion: agents.x-k8s.io/v1alpha1
kind: Sandbox
metadata:
  name: ${name}
spec:
  podTemplate:
    spec:
      containers:
      - name: agent
        image: ghcr.io/kubernetes-sigs/agent-sandbox/agent-runtime:v0.1.0
        command: ["sleep", "${sleep_secs}"]
YAML
  fi
}

# ---------------------------------------------------------------------------
# Helper: measure cold start
# ---------------------------------------------------------------------------
measure_cold_start() {
  local runtime="$1"
  local outfile="$2"
  local n_samples=50
  local runtime_class
  runtime_class=$(runtime_to_class "${runtime}")

  echo "  Measuring cold-start latency for runtime '${runtime}' (${n_samples} samples)..."
  for i in $(seq 1 "${n_samples}"); do
    local sandbox_name="bench-cs-${runtime}-${i}"
    local start_ts end_ts elapsed_ms

    start_ts=$(date +%s%N)

    # Create sandbox
    sandbox_manifest "${sandbox_name}" "${runtime_class}" 30 \
      | kubectl apply -n "${NAMESPACE}" -f - >/dev/null 2>&1

    # Wait for sandbox to be Ready
    kubectl wait sandbox "${sandbox_name}" \
      -n "${NAMESPACE}" \
      --for=condition=Ready \
      --timeout=60s >/dev/null 2>&1

    end_ts=$(date +%s%N)
    elapsed_ms=$(( (end_ts - start_ts) / 1000000 ))
    echo "{\"runtime\":\"${runtime}\",\"sample\":${i},\"cold_start_ms\":${elapsed_ms}}" >> "${outfile}"

    # Cleanup
    kubectl delete sandbox "${sandbox_name}" -n "${NAMESPACE}" >/dev/null 2>&1 || true

    # Brief cooldown between samples
    sleep 2
  done
}

# ---------------------------------------------------------------------------
# Helper: measure task latency
# ---------------------------------------------------------------------------
measure_task_latency() {
  local runtime="$1"
  local task="$2"
  local outfile="$3"
  local cmd="${TASK_COMMANDS[${task}]}"
  local runtime_class
  runtime_class=$(runtime_to_class "${runtime}")

  echo "    Task: ${task} (runtime=${runtime}, N=${REQUESTS})..."

  for i in $(seq 1 "${REQUESTS}"); do
    local sandbox_name="bench-task-${runtime}-${i}"
    local start_ts end_ts elapsed_ms exit_code

    start_ts=$(date +%s%N)

    # Create sandbox
    sandbox_manifest "${sandbox_name}" "${runtime_class}" 120 \
      | kubectl apply -n "${NAMESPACE}" -f - >/dev/null 2>&1

    # Wait for sandbox to be Ready before executing the task
    kubectl wait sandbox "${sandbox_name}" \
      -n "${NAMESPACE}" \
      --for=condition=Ready \
      --timeout=60s >/dev/null 2>&1

    # Execute task and capture exit code
    kubectl exec -n "${NAMESPACE}" "${sandbox_name}" -- bash -c "${cmd}" \
      >/dev/null 2>&1
    exit_code=$?

    end_ts=$(date +%s%N)
    elapsed_ms=$(( (end_ts - start_ts) / 1000000 ))

    echo "{\"runtime\":\"${runtime}\",\"task\":\"${task}\",\"sample\":${i},\"latency_ms\":${elapsed_ms},\"exit_code\":${exit_code}}" \
      >> "${outfile}"

    # Cleanup
    kubectl delete sandbox "${sandbox_name}" -n "${NAMESPACE}" >/dev/null 2>&1 || true
  done
}

# ---------------------------------------------------------------------------
# Main benchmark loop
# ---------------------------------------------------------------------------
for round in $(seq 1 "${ROUNDS}"); do
  echo "==> Round ${round}/${ROUNDS}..."

  for runtime in "${RUNTIME_LIST[@]}"; do
    round_dir="${OUTPUT_DIR}/round-${round}/${runtime}"
    mkdir -p "${round_dir}"

    echo "  Runtime: ${runtime}"

    # Cold-start measurement
    measure_cold_start "${runtime}" "${round_dir}/cold-start.jsonl"

    # Task latency measurement
    for task in ${TASKS}; do
      measure_task_latency "${runtime}" "${task}" "${round_dir}/tasks.jsonl"
    done
  done

  if [[ "${round}" -lt "${ROUNDS}" ]]; then
    echo "  Cooldown 5 minutes before next round..."
    sleep 300
  fi
done

echo ""
echo "==> Benchmark complete. Results written to: ${OUTPUT_DIR}"
echo "    Next: ./report.sh --input ${OUTPUT_DIR} --output benchmark-report.md"

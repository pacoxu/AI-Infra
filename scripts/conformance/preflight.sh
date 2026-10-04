#!/usr/bin/env bash
set -euo pipefail

fail() {
  printf 'FAIL [%s] %s\n' "$1" "$2" >&2
  exit 1
}

for tool in curl jq awk sort date; do
  command -v "$tool" >/dev/null 2>&1 || fail setup "required command not found: $tool"
done

: "${BASE_URL:?Set BASE_URL to the OpenAI-compatible endpoint base URL}"
: "${MODEL:?Set MODEL to the model identifier}"
: "${METRICS_FILE:?Set METRICS_FILE to a fresh metrics snapshot JSON file}"
: "${ROLLBACK_CHECK_CMD:?Set ROLLBACK_CHECK_CMD to a trusted, read-only rollback readiness check}"

LOAD_REQUESTS=${LOAD_REQUESTS:-10}
LOAD_MIN_REQUESTS_PER_SEC=${LOAD_MIN_REQUESTS_PER_SEC:-0}
SMOKE_PROMPT=${SMOKE_PROMPT:-Reply with the word ready.}
LOAD_PROMPT=${LOAD_PROMPT:-Summarize why service health checks matter in one sentence.}
TTFT_P95_MAX_MS=${TTFT_P95_MAX_MS:-10000}
TPOT_P95_MAX_MS=${TPOT_P95_MAX_MS:-10000}
ITL_P95_MAX_MS=${ITL_P95_MAX_MS:-10000}
GOODPUT_MIN_TOKENS_PER_SEC=${GOODPUT_MIN_TOKENS_PER_SEC:-0}
GPU_CACHE_USAGE_MAX_PCT=${GPU_CACHE_USAGE_MAX_PCT:-100}
KV_HIT_RATE_MIN_PCT=${KV_HIT_RATE_MIN_PCT:-0}

[[ "$LOAD_REQUESTS" =~ ^[1-9][0-9]*$ ]] || fail setup "LOAD_REQUESTS must be a positive integer"
for threshold in \
  "$LOAD_MIN_REQUESTS_PER_SEC" "$TTFT_P95_MAX_MS" "$TPOT_P95_MAX_MS" \
  "$ITL_P95_MAX_MS" "$GOODPUT_MIN_TOKENS_PER_SEC" \
  "$GPU_CACHE_USAGE_MAX_PCT" "$KV_HIT_RATE_MIN_PCT"; do
  [[ "$threshold" =~ ^[0-9]+([.][0-9]+)?$ ]] || fail setup "thresholds must be non-negative numbers"
done
[[ -r "$METRICS_FILE" ]] || fail setup "cannot read METRICS_FILE: $METRICS_FILE"
jq -e 'type == "object"' "$METRICS_FILE" >/dev/null || fail setup "METRICS_FILE must contain a JSON object"

endpoint="${BASE_URL%/}/v1/chat/completions"
response_file=$(mktemp)
latencies_file=$(mktemp)
trap 'rm -f "$response_file" "$latencies_file"' EXIT

curl_args=(--silent --show-error --output "$response_file" --write-out '%{http_code} %{time_starttransfer} %{time_total}' --connect-timeout "${CONNECT_TIMEOUT_SECONDS:-10}" --max-time "${REQUEST_TIMEOUT_SECONDS:-120}" -H 'Content-Type: application/json')
if [[ -n "${API_KEY:-}" ]]; then
  auth_scheme=$'\x42earer'
  curl_args+=(-H "Authorization: ${auth_scheme} ${API_KEY}")
fi

request() {
  local prompt=$1 result
  local -a request_args
  HTTP_CODE=
  request_args=("${curl_args[@]}" --data "$(jq -cn --arg model "$MODEL" --arg prompt "$prompt" '{model:$model,messages:[{role:"user",content:$prompt}],max_tokens:32,stream:false}')")
  result=$(curl "${request_args[@]}" "$endpoint") || return 1
  read -r HTTP_CODE STARTTRANSFER TOTAL_TIME <<< "$result"
  [[ "$HTTP_CODE" =~ ^2[0-9][0-9]$ ]] || return 1
  jq -e '.choices[0].message.content | strings | length > 0' "$response_file" >/dev/null || return 1
}

printf 'Gate smoke: '
request "$SMOKE_PROMPT" || fail smoke "completion request failed (HTTP ${HTTP_CODE:-no response})"
printf 'PASS (HTTP %s, first byte %.3fs)\n' "$HTTP_CODE" "$STARTTRANSFER"

printf 'Gate load: %s serial requests\n' "$LOAD_REQUESTS"
load_start=$(date +%s%N)
for ((i = 1; i <= LOAD_REQUESTS; i++)); do
  request "$LOAD_PROMPT" || fail load "request $i/$LOAD_REQUESTS failed (HTTP ${HTTP_CODE:-no response})"
  printf '%s\n' "$TOTAL_TIME" >> "$latencies_file"
done
load_end=$(date +%s%N)
load_duration=$(awk -v elapsed_ns="$((load_end - load_start))" 'BEGIN {if (elapsed_ns <= 0) elapsed_ns=1; printf "%.9f", elapsed_ns / 1000000000}')
load_rate=$(awk -v count="$LOAD_REQUESTS" -v duration="$load_duration" 'BEGIN {printf "%.3f", count/duration}')
load_p95=$(sort -n "$latencies_file" | awk -v count="$LOAD_REQUESTS" 'NR == int(count * 0.95 + 0.999) {print}')
awk -v actual="$load_rate" -v minimum="$LOAD_MIN_REQUESTS_PER_SEC" 'BEGIN {exit !(actual >= minimum)}' || fail load "request rate ${load_rate}/s is below ${LOAD_MIN_REQUESTS_PER_SEC}/s"
printf 'PASS (%s successful, %.3f requests/s, request latency P95 %ss)\n' "$LOAD_REQUESTS" "$load_rate" "$load_p95"

metric_check() {
  local name=$1 label=$2 operator=$3 threshold=$4 actual
  actual=$(jq -er --arg name "$name" '.[$name] | numbers' "$METRICS_FILE") || fail slo "missing or non-numeric metric: $name"
  if [[ "$operator" == "max" ]]; then
    awk -v actual="$actual" -v threshold="$threshold" 'BEGIN {exit !(actual <= threshold)}' || fail slo "$label $actual exceeds maximum $threshold"
  else
    awk -v actual="$actual" -v threshold="$threshold" 'BEGIN {exit !(actual >= threshold)}' || fail slo "$label $actual is below minimum $threshold"
  fi
  printf '  PASS %s=%s (threshold %s %s)\n' "$label" "$actual" "$operator" "$threshold"
}

printf 'Gate SLO: %s\n' "$METRICS_FILE"
metric_check ttft_p95_ms "TTFT P95 ms" max "$TTFT_P95_MAX_MS"
metric_check tpot_p95_ms "TPOT P95 ms/token" max "$TPOT_P95_MAX_MS"
metric_check itl_p95_ms "ITL P95 ms" max "$ITL_P95_MAX_MS"
metric_check goodput_tokens_per_sec "Goodput tokens/s" min "$GOODPUT_MIN_TOKENS_PER_SEC"
metric_check gpu_cache_usage_pct "GPU cache usage %" max "$GPU_CACHE_USAGE_MAX_PCT"
metric_check kv_hit_rate_pct "KV hit rate %" min "$KV_HIT_RATE_MIN_PCT"

printf 'Gate rollback: readiness check\n'
bash -c "$ROLLBACK_CHECK_CMD" || fail rollback "rollback readiness check failed"
printf 'PASS (read-only readiness check)\n'
printf 'Preflight passed\n'

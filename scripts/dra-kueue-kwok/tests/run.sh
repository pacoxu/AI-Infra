#!/usr/bin/env bash

set -euo pipefail

TEST_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
POC_DIR="$(cd "${TEST_DIR}/.." && pwd)"
PYTHONPYCACHEPREFIX="${TMPDIR:-/tmp}/dra-kueue-kwok-pycache"
export PYTHONPYCACHEPREFIX

python3 -m unittest discover -s "${TEST_DIR}" -p 'test_*.py' -v
python3 -m py_compile "${POC_DIR}/generate.py" "${POC_DIR}/collect.py" "${POC_DIR}/analyze.py"
bash -n "${POC_DIR}/poc.sh" "${POC_DIR}/lib.sh"
if command -v shellcheck >/dev/null 2>&1; then
  shellcheck -x "${POC_DIR}/poc.sh" "${POC_DIR}/lib.sh" "${TEST_DIR}/run.sh"
fi

if rg -n 'resource\.k8s\.io/v1beta|kueue\.x-k8s\.io/v1beta1' "${POC_DIR}" \
  -g '*.yaml' -g '*.yml'; then
  printf 'deprecated DRA or Kueue API found\n' >&2
  exit 1
fi

#!/usr/bin/env bash
set -euo pipefail

PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
INBOX_DIR="${1:-${PROJECT_DIR}/data/raw/inbox}"
RUN_ID="$(date +%Y%m%d_%H%M%S)"
OUTPUT_DIR="${PROJECT_DIR}/data/processed/${RUN_ID}"
LOG_DIR="${PROJECT_DIR}/logs/${RUN_ID}"

if [[ ! -d "${INBOX_DIR}" ]]; then
  echo "Input directory not found: ${INBOX_DIR}" >&2
  exit 1
fi

echo "Input: ${INBOX_DIR}"
echo "Output: ${OUTPUT_DIR}"
echo "Logs: ${LOG_DIR}"

python3 -m mail_processor \
  --input "${INBOX_DIR}" \
  --output "${OUTPUT_DIR}" \
  --log-dir "${LOG_DIR}" \
  --mode copy

if [[ ! -f "${LOG_DIR}/processing_log.csv" ]]; then
  echo "processing_log.csv was not created" >&2
  exit 1
fi

if [[ ! -f "${LOG_DIR}/stats.json" ]]; then
  echo "stats.json was not created" >&2
  exit 1
fi

echo "Basic checks passed"
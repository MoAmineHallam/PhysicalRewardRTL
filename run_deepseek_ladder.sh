#!/usr/bin/env bash
set -euo pipefail

cd /zeng_gk/Amine/mas/fpga
mkdir -p logs
: "${FRONTIER_API_KEY:?FRONTIER_API_KEY must be set}"
: "${FRONTIER_BASE_URL:=https://api.deepseek.com}"

run_mode() {
  local label="$1" model="$2" thinking="$3" effort="$4" max_tokens="$5" out_dir="$6"
  local log="logs/frontier_${label}.log"
  echo "[$(date -Is)] START ${label}: model=${model} thinking=${thinking} effort=${effort}"
  FRONTIER_MODEL="$model" \
  FRONTIER_RUN_LABEL="$label" \
  FRONTIER_THINKING="$thinking" \
  FRONTIER_REASONING_EFFORT="$effort" \
  FRONTIER_OUT_DIR="$out_dir" \
    /opt/conda/envs/mas/bin/python3.10 -u gen_frontier_baseline.py --n 8 --temp 1.0 --max-tokens "$max_tokens" \
      >"$log" 2>&1
  echo "[$(date -Is)] DONE ${label}"
}

# Flash non-thinking is already complete in rtl/frontier_eval.
run_mode flash_think deepseek-v4-flash enabled max 16384 rtl/frontier_eval_flash_think
run_mode pro_nt deepseek-v4-pro disabled high 4096 rtl/frontier_eval_pro_nt
run_mode pro_think deepseek-v4-pro enabled max 16384 rtl/frontier_eval_pro_think

echo "[$(date -Is)] DeepSeek ladder complete"

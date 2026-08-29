#!/usr/bin/env bash
# Prepared launcher only. This file does nothing unless the user invokes it.
set -euo pipefail

HERE=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)
PYTHON_BIN=
FROZEN=
OUT_ROOT=
SFT_GPU=5
RF_S1_GPU=6
RF_S2_GPU=7
NOTIFY_SCRIPT=

usage() {
  echo "usage: $0 --python PATH --frozen PATH --out-root PATH [--sft-gpu N --rf-s1-gpu N --rf-s2-gpu N] [--notify-script PATH]" >&2
  exit 2
}

while [[ $# -gt 0 ]]; do
  case "$1" in
    --python) PYTHON_BIN=$2; shift 2 ;;
    --frozen) FROZEN=$2; shift 2 ;;
    --out-root) OUT_ROOT=$2; shift 2 ;;
    --sft-gpu) SFT_GPU=$2; shift 2 ;;
    --rf-s1-gpu) RF_S1_GPU=$2; shift 2 ;;
    --rf-s2-gpu) RF_S2_GPU=$2; shift 2 ;;
    --notify-script) NOTIFY_SCRIPT=$2; shift 2 ;;
    *) usage ;;
  esac
done
[[ -n "$PYTHON_BIN" && -x "$PYTHON_BIN" ]] || usage
[[ -n "$FROZEN" && -f "$FROZEN" ]] || usage
[[ -n "$OUT_ROOT" ]] || usage
[[ ! -e "$OUT_ROOT" ]] || { echo "refusing existing out-root: $OUT_ROOT" >&2; exit 2; }
[[ "$SFT_GPU" != "$RF_S1_GPU" && "$SFT_GPU" != "$RF_S2_GPU" && "$RF_S1_GPU" != "$RF_S2_GPU" ]] || {
  echo "each policy requires a distinct physical GPU" >&2; exit 2;
}

export PYTHONNOUSERSITE=1
export HF_HUB_OFFLINE=1
export TRANSFORMERS_OFFLINE=1
export TOKENIZERS_PARALLELISM=false
export CUBLAS_WORKSPACE_CONFIG=:4096:8

for gpu in "$SFT_GPU" "$RF_S1_GPU" "$RF_S2_GPU"; do
  name=$(nvidia-smi -i "$gpu" --query-gpu=name --format=csv,noheader | tr -d '\r')
  [[ "$name" == "NVIDIA L40S" ]] || {
    echo "GPU $gpu is $name, not the frozen NVIDIA L40S" >&2; exit 2;
  }
  active=$(nvidia-smi -i "$gpu" --query-compute-apps=pid --format=csv,noheader,nounits | tr -d '[:space:]')
  [[ -z "$active" ]] || { echo "GPU $gpu has active compute PID(s): $active" >&2; exit 2; }
done

FROZEN_SHA=$(
  "$PYTHON_BIN" -c 'import hashlib,sys; print(hashlib.sha256(open(sys.argv[1],"rb").read()).hexdigest())' "$FROZEN"
)
mkdir -p -- "$OUT_ROOT"

"$PYTHON_BIN" "$HERE/run_policy.py" --policy sft --frozen "$FROZEN" \
  --frozen-raw-sha256 "$FROZEN_SHA" --out-dir "$OUT_ROOT/sft" --gpu-index "$SFT_GPU" \
  >"$OUT_ROOT/sft.log" 2>&1 &
pid_sft=$!
"$PYTHON_BIN" "$HERE/run_policy.py" --policy rf_s1 --frozen "$FROZEN" \
  --frozen-raw-sha256 "$FROZEN_SHA" --out-dir "$OUT_ROOT/rf_s1" --gpu-index "$RF_S1_GPU" \
  >"$OUT_ROOT/rf_s1.log" 2>&1 &
pid_rf_s1=$!
"$PYTHON_BIN" "$HERE/run_policy.py" --policy rf_s2 --frozen "$FROZEN" \
  --frozen-raw-sha256 "$FROZEN_SHA" --out-dir "$OUT_ROOT/rf_s2" --gpu-index "$RF_S2_GPU" \
  >"$OUT_ROOT/rf_s2.log" 2>&1 &
pid_rf_s2=$!

set +e
wait "$pid_sft"; status_sft=$?
wait "$pid_rf_s1"; status_rf_s1=$?
wait "$pid_rf_s2"; status_rf_s2=$?
set -e
if [[ $status_sft -ne 0 || $status_rf_s1 -ne 0 || $status_rf_s2 -ne 0 ]]; then
  echo "policy failure: sft=$status_sft rf_s1=$status_rf_s1 rf_s2=$status_rf_s2" >&2
  [[ -z "$NOTIFY_SCRIPT" ]] || bash "$NOTIFY_SCRIPT" "VerilogEval failed: sft=$status_sft rf_s1=$status_rf_s1 rf_s2=$status_rf_s2" || true
  exit 1
fi

"$PYTHON_BIN" "$HERE/validate.py" --frozen "$FROZEN" --frozen-raw-sha256 "$FROZEN_SHA" \
  --policy-dir "$OUT_ROOT/sft" --policy-dir "$OUT_ROOT/rf_s1" \
  --policy-dir "$OUT_ROOT/rf_s2" --rehash-inputs >"$OUT_ROOT/validation.log" 2>&1
"$PYTHON_BIN" "$HERE/aggregate.py" --sft-dir "$OUT_ROOT/sft" \
  --rf-s1-dir "$OUT_ROOT/rf_s1" --rf-s2-dir "$OUT_ROOT/rf_s2" \
  --out-dir "$OUT_ROOT/comparison" >"$OUT_ROOT/aggregate.log" 2>&1
[[ -z "$NOTIFY_SCRIPT" ]] || bash "$NOTIFY_SCRIPT" "VerilogEval SFT/RF1/RF2 complete and validated" || true
echo "all policy runs validated; comparison is in $OUT_ROOT/comparison"

#!/usr/bin/env bash
# Run the V3 SFT policy on a healthy nonzero L40S after an existing job releases it,
# then validate and aggregate it with the two already-running RF policies.
set -euo pipefail

PYTHON_BIN=
PACKAGE_DIR=
FROZEN=
RF_ROOT=
OUT_DIR=
COMPARISON_DIR=
GPU_INDEX=
RELEASE_PID=
RF1_PID=
RF2_PID=
NOTIFY_SCRIPT=

usage() {
  echo "usage: $0 --python PATH --package-dir DIR --frozen FILE --rf-root DIR --out-dir DIR --comparison-dir DIR --gpu-index N --release-pid PID --rf1-pid PID --rf2-pid PID [--notify-script PATH]" >&2
  exit 2
}

while [[ $# -gt 0 ]]; do
  case "$1" in
    --python) PYTHON_BIN=$2; shift 2 ;;
    --package-dir) PACKAGE_DIR=$2; shift 2 ;;
    --frozen) FROZEN=$2; shift 2 ;;
    --rf-root) RF_ROOT=$2; shift 2 ;;
    --out-dir) OUT_DIR=$2; shift 2 ;;
    --comparison-dir) COMPARISON_DIR=$2; shift 2 ;;
    --gpu-index) GPU_INDEX=$2; shift 2 ;;
    --release-pid) RELEASE_PID=$2; shift 2 ;;
    --rf1-pid) RF1_PID=$2; shift 2 ;;
    --rf2-pid) RF2_PID=$2; shift 2 ;;
    --notify-script) NOTIFY_SCRIPT=$2; shift 2 ;;
    *) usage ;;
  esac
done

[[ -x "$PYTHON_BIN" && -d "$PACKAGE_DIR" && -f "$FROZEN" ]] || usage
[[ -d "$RF_ROOT/rf_s1" && -d "$RF_ROOT/rf_s2" ]] || usage
[[ -n "$OUT_DIR" && -n "$COMPARISON_DIR" && -n "$GPU_INDEX" ]] || usage
[[ "$GPU_INDEX" =~ ^[0-9]+$ && "$GPU_INDEX" -ne 0 ]] || {
  echo "GPU 0 is permanently excluded; supply a healthy nonzero GPU" >&2
  exit 2
}
for pid in "$RELEASE_PID" "$RF1_PID" "$RF2_PID"; do
  [[ "$pid" =~ ^[1-9][0-9]*$ ]] || usage
done
[[ ! -e "$OUT_DIR" ]] || { echo "refusing existing SFT output: $OUT_DIR" >&2; exit 2; }
[[ ! -e "$COMPARISON_DIR" ]] || { echo "refusing existing comparison output: $COMPARISON_DIR" >&2; exit 2; }

notify() {
  [[ -z "$NOTIFY_SCRIPT" ]] || bash "$NOTIFY_SCRIPT" "$1" || true
}

export PYTHONNOUSERSITE=1
export HF_HUB_OFFLINE=1
export TRANSFORMERS_OFFLINE=1
export TOKENIZERS_PARALLELISM=false
export CUBLAS_WORKSPACE_CONFIG=:4096:8

gpu_name=$(nvidia-smi -i "$GPU_INDEX" --query-gpu=name --format=csv,noheader | tr -d '\r')
[[ "$gpu_name" == "NVIDIA L40S" ]] || {
  echo "GPU $GPU_INDEX is $gpu_name, not the frozen NVIDIA L40S" >&2
  exit 2
}

echo "waiting for PID $RELEASE_PID to release GPU $GPU_INDEX"
while kill -0 "$RELEASE_PID" 2>/dev/null; do sleep 30; done
while :; do
  active=$(nvidia-smi -i "$GPU_INDEX" --query-compute-apps=pid --format=csv,noheader,nounits | tr -d '[:space:]')
  [[ -z "$active" ]] && break
  echo "GPU $GPU_INDEX is still occupied by PID(s) $active; waiting"
  sleep 30
done

frozen_sha=$("$PYTHON_BIN" -c 'import hashlib,sys; print(hashlib.sha256(open(sys.argv[1],"rb").read()).hexdigest())' "$FROZEN")
echo "launching fresh SFT on healthy GPU $GPU_INDEX"
set +e
"$PYTHON_BIN" "$PACKAGE_DIR/run_policy.py" --policy sft --frozen "$FROZEN" \
  --frozen-raw-sha256 "$frozen_sha" --out-dir "$OUT_DIR" \
  --gpu-index "$GPU_INDEX" >"${OUT_DIR}.log" 2>&1
sft_status=$?
set -e
if [[ $sft_status -ne 0 ]]; then
  notify "VerilogEval V3 SFT recovery failed on GPU $GPU_INDEX (GPU 0 remained excluded)"
  exit "$sft_status"
fi

echo "SFT complete; waiting for both RF jobs"
for pid in "$RF1_PID" "$RF2_PID"; do
  while kill -0 "$pid" 2>/dev/null; do sleep 30; done
done

validation_log="${COMPARISON_DIR}.validation.log"
aggregate_log="${COMPARISON_DIR}.aggregate.log"
set +e
"$PYTHON_BIN" "$PACKAGE_DIR/validate.py" --frozen "$FROZEN" \
  --frozen-raw-sha256 "$frozen_sha" --policy-dir "$OUT_DIR" \
  --policy-dir "$RF_ROOT/rf_s1" --policy-dir "$RF_ROOT/rf_s2" \
  --rehash-inputs >"$validation_log" 2>&1
validation_status=$?
set -e
if [[ $validation_status -ne 0 ]]; then
  notify "VerilogEval V3 recovery finished but validation failed; results were not aggregated"
  exit "$validation_status"
fi

"$PYTHON_BIN" "$PACKAGE_DIR/aggregate.py" --sft-dir "$OUT_DIR" \
  --rf-s1-dir "$RF_ROOT/rf_s1" --rf-s2-dir "$RF_ROOT/rf_s2" \
  --out-dir "$COMPARISON_DIR" >"$aggregate_log" 2>&1
notify "VerilogEval V3 SFT/RF1/RF2 complete, validated, and aggregated; GPU 0 was not used for recovery"
echo "PASS comparison=$COMPARISON_DIR"

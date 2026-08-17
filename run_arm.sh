#!/usr/bin/env bash
# run_arm.sh  -  launch ONE preregistered GRPO arm.
#
#   ./run_arm.sh rf_struct 1 [gpu]
#   ./run_arm.sh correctness 2
#   ./run_arm.sh mlp 1
#
# Every hyperparameter below is fixed by preregistration.json (training_protocol)
# and is IDENTICAL across arms. The only things that vary are the reward and the
# seed -- which is what makes the arms a controlled comparison rather than three
# separate experiments. Do not edit values here to "try something"; that is what
# the stop rules forbid.
#
# Arms are matched on NON-FLAT OPTIMIZER UPDATES (276), not attempted groups: a
# group whose rewards are all equal produces no gradient, and the correctness-only
# arm goes flat far more often, so step-matching would give it less learning.
# --max-groups 2000 is the ceiling; a run that hits it ends there and says so in
# run_summary.json rather than being quietly extended.
set -euo pipefail

REWARD="${1:?usage: run_arm.sh <rf_struct|mlp|correctness> <seed> [gpu]}"
SEED="${2:?usage: run_arm.sh <rf_struct|mlp|correctness> <seed> [gpu]}"
GPU="${3:-0}"

cd "$(dirname "$0")"
export PATH=/zeng_gk/Amine/mas/env_mas/bin:$PATH
export CUDA_VISIBLE_DEVICES="$GPU"
export TOKENIZERS_PARALLELISM=false

BASE="${RTLCODER_PATH:-/zeng_gk/Amine/mas/rtlcoder}"
SFT=sft_v6c_out

case "$REWARD" in
  rf_struct)   TAG=rf   ; EXTRA="--reward rf_struct --rf rf_struct.joblib" ;;
  mlp)         TAG=mlp  ; EXTRA="--reward mlp --surrogate surrogate_v3.pt" ;;
  correctness) TAG=corr ; EXTRA="--reward correctness" ;;
  *) echo "unknown reward '$REWARD'"; exit 2 ;;
esac
OUT="grpo_${TAG}_s${SEED}"

# The preregistration requires this to pass at the START of every arm. If an
# artifact drifted, the arm would not be the experiment that was registered.
echo "== verifying pinned artifacts =="
python freeze_hashes.py --verify hashes.json

# Crash policy: a dead run is DISCARDED and restarted from step 0 with the same
# seed; partial runs are never resumed or merged. grpo_oracle.py refuses to start
# if a group log already exists, so a stale directory must be moved aside
# deliberately -- never silently reused.
if [ -e "$OUT/group_log.jsonl" ]; then
  echo "REFUSING: $OUT/group_log.jsonl exists."
  echo "A crashed run is discarded, not resumed. Move it aside on purpose:"
  echo "    mv $OUT ${OUT}.abandoned.\$(date +%s)"
  exit 3
fi

echo "== arm=$REWARD seed=$SEED gpu=$GPU out=$OUT =="
python -u grpo_oracle.py \
  --base "$BASE" --sft "$SFT" $EXTRA \
  --seed "$SEED" \
  --steps 2000 --max-updates 276 --max-groups 2000 \
  --save-at-updates 138,276 \
  --group 8 --gen-batch 4 --temp 1.0 --max-tokens 1536 \
  --lr 1e-5 --kl_coef 0.1 \
  --out "$OUT" --log "${OUT}_log.jsonl" 2>&1 | tee "${OUT}_stdout.log"

echo
echo "== $OUT finished =="
cat "$OUT/run_summary.json"
echo
echo "Check 'ended': 'target updates reached (276)' is the intended stop."
echo "'attempt ceiling reached' means the reward went flat too often to reach"
echo "276 updates in 2000 groups -- report it, do not raise the ceiling."

#!/usr/bin/env bash
# run_arm.sh  -  launch ONE preregistered GRPO arm.
#
#   ./run_arm.sh rf_struct 1 [gpu]
#   ./run_arm.sh correctness 1
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
# The attempt ceiling is 2000 for the physical-reward arms and 4500 for the
# correctness-only arm; a run that hits it reports that stop in run_summary.json
# rather than being quietly extended.
set -euo pipefail

REWARD="${1:?usage: run_arm.sh <rf_struct|mlp|correctness> <seed> [gpu]}"
SEED="${2:?usage: run_arm.sh <rf_struct|mlp|correctness> <seed> [gpu]}"
GPU="${3:-0}"
case "$GPU" in
  0|1) ;;
  *) echo "REFUSING: gpu must be 0 or 1 on the pinned two-V100 server."; exit 2 ;;
esac

cd "$(dirname "$0")"
export PATH=/zeng_gk/Amine/mas/env_mas/bin:$PATH
export CUDA_VISIBLE_DEVICES="$GPU"
export TOKENIZERS_PARALLELISM=false
export HF_HUB_OFFLINE=1

BASE="${RTLCODER_PATH:-/zeng_gk/Amine/mas/rtlcoder}"
SFT=sft_v6c_out

# PER-ARM attempt ceiling (preregistration revision 2, amendment 1). A SHARED
# ceiling silently reintroduces step-matching, which the protocol explicitly
# rejects: a flat group yields no gradient, and the flat RATE differs by arm by
# construction. Measured on an existing log, grpo_ablate_const_matched_log.jsonl,
# the binary-correctness reward went non-flat on only 159 of 1997 groups (0.080),
# because a group is flat when all 8 candidates are correct OR all 8 are wrong and
# sft_v6c is ~95% correct on train designs (0.95^8 = 0.66 all-correct). Reaching
# 276 updates therefore needs ~3450 groups, so its ceiling is 4500. The MATCHED
# QUANTITY -- 276 non-flat updates -- is identical across arms; only the number of
# attempts differs, which is exactly what matching on updates means.
case "$REWARD" in
  rf_struct)   TAG=rf   ; MAXG=2000 ; EXTRA="--reward rf_struct --rf rf_struct.joblib" ;;
  mlp)         TAG=mlp  ; MAXG=2000 ; EXTRA="--reward mlp --surrogate surrogate_v3.pt" ;;
  correctness) TAG=corr ; MAXG=4500 ; EXTRA="--reward correctness" ;;
  *) echo "unknown reward '$REWARD'"; exit 2 ;;
esac
case "$REWARD:$SEED" in
  rf_struct:1|rf_struct:2|mlp:1|mlp:2|correctness:1) ;;
  *)
    echo "REFUSING: '$REWARD' seed '$SEED' is not a preregistered arm."
    echo "Allowed: rf_struct {1,2}; mlp {1,2}; correctness {1}."
    exit 2
    ;;
esac
OUT="grpo_${TAG}_s${SEED}"

# The preregistration requires this to pass at the START of every arm. If an
# artifact drifted, the arm would not be the experiment that was registered.
echo "== verifying pinned artifacts =="
python freeze_hashes.py --verify hashes.json

echo "== verifying GPU and functional oracle =="
command -v iverilog >/dev/null
command -v vvp >/dev/null
python -c 'import torch; assert torch.cuda.is_available(); print(torch.cuda.get_device_name(0))'
python -c 'import oracle, gen_accelerator_catalog as G; r=oracle.score(G.fir_ref("fir8_8b", G.fir_coeffs(8)), "fir8_8b", n=64); assert r["correct"], r; print("oracle canary PASS")'

# Crash policy: a dead run is DISCARDED and restarted from step 0 with the same
# seed; partial runs are never resumed or merged. grpo_oracle.py refuses to start
# if a group log already exists, so a stale directory must be moved aside
# deliberately -- never silently reused.
if [ -e "$OUT" ] || [ -e "${OUT}_log.jsonl" ] || [ -e "${OUT}_stdout.log" ]; then
  echo "REFUSING: output from $OUT already exists."
  echo "A crashed run is discarded, not resumed. Move it aside on purpose:"
  echo "    mv $OUT ${OUT}.abandoned.TIMESTAMP"
  echo "and move ${OUT}_log.jsonl / ${OUT}_stdout.log if either exists."
  exit 3
fi

echo "== arm=$REWARD seed=$SEED gpu=$GPU out=$OUT =="
python -u grpo_oracle.py \
  --base "$BASE" --sft "$SFT" $EXTRA \
  --seed "$SEED" \
  --steps "$MAXG" --max-updates 276 --max-groups "$MAXG" \
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
echo "276 updates within its frozen ceiling -- report it, do not raise the ceiling."

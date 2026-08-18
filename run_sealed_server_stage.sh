#!/usr/bin/env bash
# Generate every frozen sealed-study evaluation replicate on the GPU server.
#
# Run this only after all five run_arm.sh jobs finish.  The script verifies the
# pinned artifacts and all training runs, audits every distinct RF training
# candidate, and only then opens the sealed evaluation.  Any pre-existing output
# makes the relevant evaluator fail rather than merging partial replicates.
set -euo pipefail

cd "$(dirname "$0")"
export PATH=/zeng_gk/Amine/mas/env_mas/bin:$PATH
export HF_HUB_OFFLINE=1
export TOKENIZERS_PARALLELISM=false
export CUDA_VISIBLE_DEVICES="${1:-0}"

BASE="${RTLCODER_PATH:-/zeng_gk/Amine/mas/rtlcoder}"

echo "== verify pinned pre-outcome artifacts =="
python freeze_hashes.py --verify hashes.json

echo "== verify all five training runs =="
python verify_sealed_training.py --out sealed_training_audit.json

echo "== materialize actual RF-arm training candidates =="
python materialize_rf_candidates.py \
  --group-log grpo_rf_s1/group_log.jsonl \
  --group-log grpo_rf_s2/group_log.jsonl \
  --out-dir rtl/sealed_rf_training_candidates \
  --manifest rf_training_candidates.json

echo "== pre-open canonicalisation, compilation, and trace contract =="
python canonicalize.py --backend lexical --check-traces \
  --dirs rtl/sealed_rf_training_candidates \
  --out rf_training_contract.json
python -c 'import json,sys; x=json.load(open("rf_training_contract.json")); bad=(x.get("n",0)<=0 or x.get("passed")!=x.get("n") or x.get("rejected")!=0 or x.get("collisions")!=0 or any(x.get("failures",{}).values())); print("RF training contract:", "FAIL" if bad else "PASS", x.get("passed"), "/", x.get("n")); sys.exit(1 if bad else 0)'

echo "== open sealed split exactly once: SFT =="
python eval_sealed.py --base "$BASE" --adapter sft_v6c_out \
  --policy sft --training-seed 0 --generation-seed 100 --n 48 \
  --score-rf --out-dir rtl/sealed_sft

echo "== RF structural reward: endpoints =="
python eval_sealed.py --base "$BASE" --adapter grpo_rf_s1/upd_276 \
  --policy rf_s1 --training-seed 1 --generation-seed 101 --n 24 \
  --score-rf --out-dir rtl/sealed_rf_s1
python eval_sealed.py --base "$BASE" --adapter grpo_rf_s2/upd_276 \
  --policy rf_s2 --training-seed 2 --generation-seed 102 --n 24 \
  --score-rf --out-dir rtl/sealed_rf_s2

echo "== RF structural reward: update-138 midpoint =="
python eval_sealed.py --base "$BASE" --adapter grpo_rf_s1/upd_138 \
  --policy rf_mid_s1 --training-seed 1 --generation-seed 101 --n 8 \
  --score-rf --out-dir rtl/sealed_rf_mid_s1
python eval_sealed.py --base "$BASE" --adapter grpo_rf_s2/upd_138 \
  --policy rf_mid_s2 --training-seed 2 --generation-seed 102 --n 8 \
  --score-rf --out-dir rtl/sealed_rf_mid_s2

echo "== original MLP reward control =="
python eval_sealed.py --base "$BASE" --adapter grpo_mlp_s1/upd_276 \
  --policy mlp_s1 --training-seed 1 --generation-seed 101 --n 24 \
  --out-dir rtl/sealed_mlp_s1
python eval_sealed.py --base "$BASE" --adapter grpo_mlp_s2/upd_276 \
  --policy mlp_s2 --training-seed 2 --generation-seed 102 --n 24 \
  --out-dir rtl/sealed_mlp_s2

echo "== correctness-only control =="
python eval_sealed.py --base "$BASE" --adapter grpo_corr_s1/upd_276 \
  --policy correctness_s1 --training-seed 1 --generation-seed 101 --n 48 \
  --out-dir rtl/sealed_corr_s1

echo
echo "SERVER STAGE COMPLETE. Do not inspect or select candidates."
echo "Commit every rtl/sealed_* evaluation directory plus the audit manifests,"
echo "then run the one identical Vivado flow over each directory on the laptop."

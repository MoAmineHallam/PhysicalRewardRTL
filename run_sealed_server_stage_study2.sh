#!/usr/bin/env bash
# Study 2 server stage: validate reward-eligible RF implementations, then and
# only then generate the unchanged sealed evaluation arms.
set -euo pipefail

cd "$(dirname "$0")"
ENV_BIN="${FPGA_ENV_BIN:-/home/adam/mas/mas/env_fpga/bin}"
export PATH="$ENV_BIN:$PATH"
export PYTHONNOUSERSITE=1
export HF_HUB_OFFLINE=1
export TOKENIZERS_PARALLELISM=false
export CUDA_VISIBLE_DEVICES="${1:-7}"
export RTLCODER_PATH="${RTLCODER_PATH:-/home/adam/mas/mas/rtlcoder}"

BASE="$RTLCODER_PATH"

study2_artifacts=(
  sealed_training_audit_study2.json
  rf_reward_eligible_manifest_study2.json
  rf_reward_eligible_contract_study2.json
  rtl/sealed_rf_reward_eligible_study2
  rtl/sealed_sft
  rtl/sealed_rf_s1
  rtl/sealed_rf_s2
  rtl/sealed_rf_mid_s1
  rtl/sealed_rf_mid_s2
  rtl/sealed_mlp_s1
  rtl/sealed_mlp_s2
  rtl/sealed_corr_s1
)
for artifact in "${study2_artifacts[@]}"; do
  if [[ -e "$artifact" ]]; then
    echo "Refusing pre-existing Study 2 artifact: $artifact" >&2
    exit 1
  fi
done

echo "== verify frozen Study 2 identity =="
python freeze_hashes.py --verify hashes_study2.json

echo "== verify all five completed training runs =="
python verify_sealed_training.py --out sealed_training_audit_study2.json

echo "== audit exactly the candidates that reached the RF reward =="
python audit_rf_reward_eligible.py \
  --prereg preregistration_study2.json \
  --output-dir rtl/sealed_rf_reward_eligible_study2 \
  --manifest rf_reward_eligible_manifest_study2.json \
  --contract rf_reward_eligible_contract_study2.json \
  grpo_rf_s1/group_log.jsonl grpo_rf_s2/group_log.jsonl
python -c 'import json,sys; x=json.load(open("rf_reward_eligible_contract_study2.json")); bad=(x.get("study_id")!="rf_reward_eligible_study2" or x.get("n")!=801 or x.get("passed")!=801 or x.get("rejected")!=0 or bool(x.get("failures")) or bool(x.get("collisions")) or bool(x.get("pre_contract_errors"))); print("Study 2 RF reward-eligible contract:", "FAIL" if bad else "PASS", x.get("passed"), "/", x.get("n")); sys.exit(1 if bad else 0)'

echo "== gate passed; open sealed split exactly once: SFT =="
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
echo "SERVER STAGE STUDY2 COMPLETE. Do not inspect or select candidates."
echo "Transfer every evaluation directory and the Study 2 audit artifacts to the laptop."

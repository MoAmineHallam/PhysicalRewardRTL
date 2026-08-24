#!/usr/bin/env bash
# Final artifact-derived Study 2 analysis after laptop Vivado results return.
set -euo pipefail

cd "$(dirname "$0")"
ENV_BIN="${FPGA_ENV_BIN:-/home/adam/mas/mas/env_fpga/bin}"
export PATH="$ENV_BIN:$PATH"
export PYTHONNOUSERSITE=1
export RTLCODER_PATH="${RTLCODER_PATH:-/home/adam/mas/mas/rtlcoder}"

python freeze_hashes.py --verify hashes_study2.json
python verify_sealed_training.py --out sealed_training_audit_study2.json
python verify_sealed_ppa.py --out sealed_ppa_audit_study2.json

python analyze_sealed_v3.py \
  --sft rtl/sealed_sft \
  --arm rf=rtl/sealed_rf_s1,rtl/sealed_rf_s2 \
  --arm mlp=rtl/sealed_mlp_s1,rtl/sealed_mlp_s2 \
  --arm correctness=rtl/sealed_corr_s1 \
  --primary rf \
  --mid rf=rtl/sealed_rf_mid_s1,rtl/sealed_rf_mid_s2 \
  --rf-group-log grpo_rf_s1/group_log.jsonl \
  --rf-group-log grpo_rf_s2/group_log.jsonl \
  --mutation-contract rf_reward_eligible_contract_study2.json \
  --mutation-scope reward_eligible \
  --out sealed_results_study2.json

echo "Study 2 analysis complete. Report the frozen outcome exactly."

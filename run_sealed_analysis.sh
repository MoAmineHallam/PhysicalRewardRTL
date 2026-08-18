#!/usr/bin/env bash
# Final artifact-derived analysis after laptop Vivado results return to server.
set -euo pipefail

cd "$(dirname "$0")"
export PATH=/zeng_gk/Amine/mas/env_mas/bin:$PATH

python freeze_hashes.py --verify hashes.json
python verify_sealed_training.py --out sealed_training_audit.json
python verify_sealed_ppa.py --out sealed_ppa_audit.json

python analyze_sealed_v3.py \
  --sft rtl/sealed_sft \
  --arm rf=rtl/sealed_rf_s1,rtl/sealed_rf_s2 \
  --arm mlp=rtl/sealed_mlp_s1,rtl/sealed_mlp_s2 \
  --arm correctness=rtl/sealed_corr_s1 \
  --primary rf \
  --mid rf=rtl/sealed_rf_mid_s1,rtl/sealed_rf_mid_s2 \
  --rf-group-log grpo_rf_s1/group_log.jsonl \
  --rf-group-log grpo_rf_s2/group_log.jsonl \
  --mutation-contract rf_training_contract.json \
  --out sealed_results_v3.json

echo "Analysis complete. Report the assigned outcome exactly; do not add seeds or"
echo "change endpoints after seeing sealed_results_v3.json."

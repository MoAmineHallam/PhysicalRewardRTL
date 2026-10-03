# Physical-quality scaling tools

Implements the [physical-quality scaling plan](../research/fpga2/PHYSICAL_SCALING_PLAN_20261003.md).
Like `student/`, everything wraps the previous project's frozen code instead of
copying it.

| File | Purpose |
|---|---|
| `eda_vivado.py` | `run`: parallel Vivado implementation with the frozen primary flow (`run_ppa.run_one` + `ppa_synth.tcl`), resumable, with per-job wall time; `calibrate`: re-implement 20 Gate 0 circuits and compare with the laptop's records under the Phase 0 rule |
| `test_eda_vivado.py` | CPU checks with a fake Vivado |

```bash
python -m unittest scaling.test_eda_vivado -v
```

## K1 kill test ([protocol](../research/fpga2/K1_PROTOCOL_20261003.md))

| File | Purpose |
|---|---|
| `make_confirmation_split.py` | Draw the confirmation split once (seed 20261003, dev split excluded) |
| `sft.py` | `train`: frozen `sft_train_v2.py` plus a seed and a training record; `val-loss`: held-out completion NLL |
| `k1.py` | `prepare`, `work --worker v100a-0`, `status`, `collect`, `analyze` |
| `test_k1.py` | CPU checks of the validation split, leak check, queue, learning-rate choice and decision rule |

```bash
cd /zeng_gk/Amine/mas/fpga2-student-20261001
PY=/zeng_gk/Amine/mas/env_mas/bin/python
$PY scaling/make_confirmation_split.py \
    --tokenizer /zeng_gk/Amine/mas/models/Qwen/Qwen2___5-Coder-1___5B \
    --out scaling_splits/confirmation_split.json --exclude-split gate0/dev_split.json \
    --also-exclude-from /zeng_gk/Amine/mas/fpga-v100-v2 /zeng_gk/Amine/mas/fpga-comparison-v3-20260915 \
    /zeng_gk/Amine/mas/fpga2-student-20261001
$PY scaling/k1.py prepare
nohup $PY scaling/k1.py work --worker v100a-0 > k1_v100a-0.out 2>&1 &   # one per GPU
$PY scaling/k1.py status
```

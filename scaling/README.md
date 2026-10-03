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

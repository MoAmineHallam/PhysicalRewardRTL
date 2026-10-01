# Student Gate 0 tools

Implements Gate 0 of the [RTL-student plan](../research/fpga2/RTL_STUDENT_PLAN_20261001.md).
Everything here wraps the previous project's frozen code (`moaminehallam/fpga`,
branch `claude/amazing-hopper-ytsbvr`) rather than copying it.

| File | Purpose |
|---|---|
| `compress.py` | RTN and GPTQ group-wise weight fake-quantization; SFT-format calibration; output-vocabulary mask equal to a trimmed head |
| `make_dev_split.py` | Fresh development split with the frozen split generator (sealed split excluded) |
| `make_keep_vocab.py` | Kept-token set from training completions only |
| `eval_compressed.py` | One compressed policy × one seed on a split; same outputs as `eval_sealed.py` |
| `footprint.py` | Analytical bytes per decoded token from a `config.json` |
| `gate0.py` | Gate 0 launcher: `prepare` once, `work --worker v100a-0` per GPU, `status` |
| `gate0_physical.py` | `collect` distinct correct circuits for Vivado; `analyze` with the frozen rule |
| `test_student.py` | CPU checks |

## Server workflow

Gate 0 follows [GATE0_PROTOCOL_20261001.md](../research/fpga2/GATE0_PROTOCOL_20261001.md).
`gate0.py prepare` (once, on V100a) picks the checkout matching the frozen
evaluator, runs the oracle self-check, draws `gate0/dev_split.json`, freezes
`gate0/keep_vocab_qwen.json` and writes `gate0/plan.json`.  Then start one
worker per GPU on its own box:

```bash
cd /zeng_gk/Amine/mas/fpga2-student-20261001
PY=/zeng_gk/Amine/mas/env_mas/bin/python
$PY student/gate0.py prepare                                   # V100a, once
nohup $PY student/gate0.py work --worker v100a-0 > gate0/logs/v100a-0.out 2>&1 &
nohup $PY student/gate0.py work --worker v100a-1 > gate0/logs/v100a-1.out 2>&1 &
# on V100b:
nohup $PY student/gate0.py work --worker v100b-0 > gate0/logs/v100b-0.out 2>&1 &
nohup $PY student/gate0.py work --worker v100b-1 > gate0/logs/v100b-1.out 2>&1 &
$PY student/gate0.py status
```

Completed runs are skipped on restart; an incomplete run directory is moved
aside and the run starts again from scratch.

## Checks

```bash
python -m unittest student.test_student student.test_gate0 -v
```

Twenty-one tests pass on CPU (`test_student`, `test_gate0`).  The end-to-end evaluator test runs only when
`FPGA_ROOT` points at the old checkout.

# Student Gate 0 tools

Implements Gate 0 of the [RTL-student plan](../research/fpga2/RTL_STUDENT_PLAN_20261001.md).
Everything here wraps the previous project's frozen code (`moaminehallam/fpga`,
branch `claude/amazing-hopper-ytsbvr`) rather than copying it.

| File | Purpose |
|---|---|
| `compress.py` | RTN group-wise weight fake-quantization; output-vocabulary mask equal to a trimmed head |
| `make_dev_split.py` | Fresh development split with the frozen split generator (sealed split excluded) |
| `make_keep_vocab.py` | Kept-token set from training completions only |
| `eval_compressed.py` | One compressed policy × one seed on a split; same outputs as `eval_sealed.py` |
| `footprint.py` | Analytical bytes per decoded token from a `config.json` |
| `test_student.py` | CPU checks |

## Server workflow

Paths below are examples; confirm them first.  `FPGA` is the old checkout.

```bash
FPGA=/zeng_gk/Amine/mas/fpga
PY=/zeng_gk/Amine/mas/env_mas/bin/python
QWEN15=/path/to/qwen2.5-coder-1.5b

# 1. Draw the development split once (needs iverilog for the oracle check).
$PY student/make_dev_split.py --fpga-root $FPGA --tokenizer $QWEN15 \
    --out gate0/dev_split.json

# 2. Freeze the kept vocabulary from training completions only.
$PY student/make_keep_vocab.py --tokenizer $QWEN15 \
    --corpus $FPGA/sft_corpus.jsonl $FPGA/sft_corpus_v5.jsonl $FPGA/distill_corpus.jsonl \
    --exclude-split gate0/dev_split.json --out gate0/keep_vocab.json

# 3. One arm = one invocation into a fresh directory.
$PY student/eval_compressed.py --fpga-root $FPGA --base $QWEN15 \
    --adapter $FPGA/../student_v1_out --split gate0/dev_split.json \
    --policy student_w4 --generation-seed 1001 --n 24 --bits 4 \
    --out-dir gate0/student_w4
```

Then run the existing `run_ppa.py` flow on each output directory.  Commit the
split, kept-vocabulary file and a frozen protocol before the first draw.

## Checks

```bash
python -m unittest student.test_student -v
```

Eleven tests pass on CPU.  The end-to-end evaluator test runs only when
`FPGA_ROOT` points at the old checkout.

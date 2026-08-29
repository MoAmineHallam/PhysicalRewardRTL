# Repaired-RF VerilogEval extension (protocol V2)

This directory is a new, outcome-independent evaluation package for the Study 2
SFT adapter and the two repaired-RF endpoint adapters. It does not read, append,
rewrite, or summarize the historical `passk_*.jsonl` files. The primary endpoint
is VerilogEvalV2 pass@1 over all 156 `spec-to-RTL` problems, with 20 samples per
problem under one decoding and oracle configuration shared by all three policies.

V1 stopped before creating a frozen-input manifest or generating any completion:
it incorrectly assumed that the clean pinned dataset directory contains only the
156 problem triplets. The official commit also tracks exactly
`Prob062_bugs_mux2.sv`, `problems-temp.txt`, and `problems.txt`. V2 permits and
raw-hashes only those three auxiliaries. They never enter model context; policies
still receive only the 156 prompt files. No result informed this repair.

## What is frozen now

`protocol.json` fixes the official benchmark repository and commit, the four
legacy Study 2 model/adapter directory identities, the software and
hardware stack, the prompt, decoding parameters, RNG derivation, judge, output
state machine, and reporting rule. In particular, RF seed 1 and seed 2 remain
separate experimental replicates; their 40 samples are never pooled as if they
came from one trained policy.

The benchmark corpus is not committed in this repository, so its content digest
cannot honestly be filled in here. Before the first GPU job, `freeze_inputs.py`
requires a clean checkout at the pinned commit, verifies all 156 complete file
triplets and the three explicitly pinned tracked auxiliaries, hashes all 471
files, and emits one immutable `frozen_inputs.json`. Every
policy process rehashes those same inputs before model loading. Generation is
therefore blocked until a real dataset digest exists; no placeholder digest is
accepted.

The old Study 2 directory identity normalized CRLF to LF for text-like files.
That algorithm is retained under the explicit name
`legacy_study2_dir_sha256` only to prove that these are the four already
recorded checkpoints. During freezing, the same streaming pass also creates a
raw-byte directory manifest for every model/adapter. The benchmark, package,
`frozen_inputs.json`, shards, JSONL, summaries, and all other new evidence use
raw-byte SHA-256 only; line endings are evidence and are never normalized.

## One-time preparation on the authorized L40S host

All paths are parameters. The example keeps every artifact below the user's
authorized `/home/adam/mas/mas` tree.

```bash
export PYTHONNOUSERSITE=1
export HF_HUB_OFFLINE=1
export TRANSFORMERS_OFFLINE=1
export TOKENIZERS_PARALLELISM=false
export CUBLAS_WORKSPACE_CONFIG=:4096:8

/home/adam/mas/mas/env_fpga/bin/python \
  verilogeval_rf_extension_v2/freeze_inputs.py \
  --base /home/adam/mas/mas/rtlcoder \
  --sft-adapter /home/adam/mas/mas/fpga/sft_v6c_out \
  --rf-s1-adapter /home/adam/mas/mas/fpga/grpo_rf_s1/upd_276 \
  --rf-s2-adapter /home/adam/mas/mas/fpga/grpo_rf_s2/upd_276 \
  --benchmark-repo /home/adam/mas/mas/verilog-eval-v2 \
  --out /home/adam/mas/mas/verilogeval_rf_frozen_inputs.json
```

The benchmark checkout must be exactly commit
`c498220d0a52248f8e3fdffe279075215bde2da6`, with no staged, modified, or
untracked file under `dataset_spec-to-rtl`. Preparation prints the raw-byte SHA-256 of
the resulting frozen manifest. Keep that digest with the run record.

## Matched three-policy execution

`launch_three.sh` is a convenience wrapper; it is provided but is not executed
by this package preparation. It first proves the requested physical GPUs are
idle, then launches SFT, RF seed 1, and RF seed 2 concurrently. Logs live beside,
not inside, the policy result directories so that the result validator has a
closed file allowlist.

```bash
bash verilogeval_rf_extension_v2/launch_three.sh \
  --python /home/adam/mas/mas/env_fpga/bin/python \
  --frozen /home/adam/mas/mas/verilogeval_rf_frozen_inputs.json \
  --out-root /home/adam/mas/mas/verilogeval_rf_20260827 \
  --sft-gpu 5 --rf-s1-gpu 6 --rf-s2-gpu 7
```

If a process is interrupted, never invoke it normally against the old result
directory. Invoke the same policy command with `--resume`. Resume revalidates
the frozen manifest, run configuration, and every complete 20-sample shard.
It skips only valid complete shards and regenerates no accepted sample. A
truncated/unknown file or altered shard stops the run; archive that directory
and start a fresh one rather than repairing it in place.

For example, to resume only RF seed 1 on physical GPU 7:

```bash
FROZEN_SHA=$(/home/adam/mas/mas/env_fpga/bin/python -c \
  'import hashlib,sys; print(hashlib.sha256(open(sys.argv[1],"rb").read()).hexdigest())' \
  /home/adam/mas/mas/verilogeval_rf_frozen_inputs.json)
/home/adam/mas/mas/env_fpga/bin/python \
  verilogeval_rf_extension_v2/run_policy.py \
  --policy rf_s1 \
  --frozen /home/adam/mas/mas/verilogeval_rf_frozen_inputs.json \
  --frozen-raw-sha256 "$FROZEN_SHA" \
  --out-dir /home/adam/mas/mas/verilogeval_rf_20260827/rf_s1 \
  --gpu-index 7 --resume
```

Finalization builds `final/samples.jsonl`, `final/summary.json`, and
`final/COMPLETE.json` in a staging directory beside the run and publishes the
whole directory with one atomic rename. There is consequently no state in which
a summary can be mistaken for belonging to a partially written JSONL file.
Problem shards are likewise staged beside the policy directory and moved into
`problems/` atomically, so a process kill cannot leave a partial shard inside
the resumable result set.

## Validation and aggregation

After all three policy jobs complete:

```bash
FROZEN_SHA=$(/home/adam/mas/mas/env_fpga/bin/python -c \
  'import hashlib,sys; print(hashlib.sha256(open(sys.argv[1],"rb").read()).hexdigest())' \
  /home/adam/mas/mas/verilogeval_rf_frozen_inputs.json)
/home/adam/mas/mas/env_fpga/bin/python \
  verilogeval_rf_extension_v2/validate.py \
  --frozen /home/adam/mas/mas/verilogeval_rf_frozen_inputs.json \
  --frozen-raw-sha256 "$FROZEN_SHA" \
  --policy-dir /home/adam/mas/mas/verilogeval_rf_20260827/sft \
  --policy-dir /home/adam/mas/mas/verilogeval_rf_20260827/rf_s1 \
  --policy-dir /home/adam/mas/mas/verilogeval_rf_20260827/rf_s2 \
  --rehash-inputs

/home/adam/mas/mas/env_fpga/bin/python \
  verilogeval_rf_extension_v2/aggregate.py \
  --sft-dir /home/adam/mas/mas/verilogeval_rf_20260827/sft \
  --rf-s1-dir /home/adam/mas/mas/verilogeval_rf_20260827/rf_s1 \
  --rf-s2-dir /home/adam/mas/mas/verilogeval_rf_20260827/rf_s2 \
  --out-dir /home/adam/mas/mas/verilogeval_rf_20260827/comparison
```

The aggregate reports each training seed separately, paired RF-minus-SFT
differences, and the predeclared two-seed RF average with a paired problem-level
bootstrap interval. It does not merge raw draws across RF seeds.
That interval resamples benchmark problems and is explicitly conditional on the
three realized checkpoints; two RF checkpoints do not support a credible
training-seed-variance interval.

## Tests

The unit suite uses synthetic temporary corpora and no model, GPU, or journal
result. It checks raw/legacy hash separation, corpus completeness, seed stability,
pass@k, shard integrity, and fail-closed resume behavior.

```bash
python -m unittest discover -s verilogeval_rf_extension_v2/tests -v
```

This package deliberately makes no claim about the repaired-RF VerilogEval
result until all three independently validated runs exist.

## Planning cost

The frozen experiment generates exactly 9,360 completions: 156 problems x 20
draws x three policies. With the policies running concurrently on three L40S
GPUs, a prudent first allocation is 3--6 hours of wall time (roughly 9--18 GPU
hours), with an 8-hour operational window for long prompts, initial model/hash
I/O, and Icarus simulation. This is a planning range, not a promised runtime;
the elapsed times printed for the first ten completed problems provide the
correct host-specific extrapolation. The package invokes neither Vivado nor the
PYNQ-Z2 board.

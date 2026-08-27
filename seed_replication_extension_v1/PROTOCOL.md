# Prospective seed-replication extension v1

## Scientific status

This is a **prospective, post-primary extension**. It estimates training-seed
variability for the repaired random-forest (RF) reward and the
correctness-only control. It does not reopen Study 2, replace its primary
endpoint, or authorize pooling these runs into the preregistered Study-2
confidence interval.

The extension was frozen before any of its four jobs was launched. The training
launcher cannot generate endpoint samples. Endpoint generation and Vivado
evaluation require a later, separately reviewed command that obeys the frozen
contract in `config.json`.

## Frozen jobs

| Run ID | Condition | Training seed | Physical L40S GPU | Update target | Attempt ceiling |
|---|---|---:|---:|---:|---:|
| `rf_s3` | repaired RF | 3 | 7 | 276 non-flat updates | 2,000 groups |
| `rf_s4` | repaired RF | 4 | 6 | 276 non-flat updates | 2,000 groups |
| `correctness_s2` | correctness-only | 2 | 5 | 276 non-flat updates | 15,000 groups |
| `correctness_s3` | correctness-only | 3 | 4 | 276 non-flat updates | 15,000 groups |

Seeds and GPU assignments are identities, not a scheduling pool. An occupied
GPU makes only its assigned run ineligible to launch; it does not authorize
moving that seed to another GPU. This permits a free assigned run to start while
other assigned GPUs remain occupied.

The RF total after this extension will be four training seeds (the original
seeds 1/2 plus extension seeds 3/4). The correctness-only total will be three
training seeds (original seed 1 plus extension seeds 2/3).

## Mandatory go/no-go gate

No extension job may start unless all ten candidates in the separately frozen
`timing_closure_gate_v1` pilot complete and its machine-readable result is a
PASS. The extension validator independently requires:

- the result identifies schema 1, study `timing_closure_gate_v1`, scope
  `pilot_10`, and the exact frozen manifest digest;
- `completed_candidates == expected_candidates == 10`;
- the verdict is `PASS`, all four registered criteria are true, failures are
  empty, metrics are non-null, and every `generated_from` hash verifies; and
- the content of `manifest.json` matches `manifest.sha256` and the digest pinned
  in this extension's `config.json`.

Missing, incomplete, stale, malformed, or failed timing evidence is a hard
NO-GO. A failed pilot is scientific evidence to revise the endpoint, not a
condition the seed launcher may bypass.

## Training controls

All jobs use the same byte-identical `sft_v6c_out` initialization as the frozen
study, the same frozen SFT adapter as the KL reference, FP16, group size 8,
generation batch 4, temperature 1.0, 1,536 generated tokens, learning rate
`1e-5`, KL coefficient 0.1, incorrect reward 0, and checkpoints at non-flat
updates 138 and 276. The RF runs use the pinned `rf_struct.joblib`.

Every dependency in `config.json` is hashed. Text hashes use LF-normalized
bytes; binaries use raw bytes; model/adapter directories use a sorted manifest
digest. Server preflight recomputes the base-model and adapter directory hashes,
checks the isolated environment, runs a CUDA/oracle canary, and requires at
least 25 GiB free on the repository filesystem.

The exact isolated stack is Python 3.10.20, torch 2.4.1+cu121, Transformers
4.46.3, PEFT 0.13.2, Accelerate 1.0.1, NumPy 2.2.6, SciPy 1.15.3,
scikit-learn 1.7.2, joblib 1.5.3, and Icarus Verilog 12.0. Preflight requires
`PYTHONNOUSERSITE=1` before importing anything. This is load-bearing: a
read-only audit found that Adam's user site otherwise shadows the isolated
environment with newer torch/Transformers packages. With user-site imports
disabled, the stack exactly matches the original L40 Study-2 run.

The RF joblib's authoritative raw binary SHA-256 is `e17f1e20...dfc1a0` as
fully recorded in `config.json`. The original run configuration reports
`7fb56b44...bb0b` because the legacy `_sha` helper in `grpo_oracle.py`
LF-normalizes every file, including binary joblib data. Applying that same
legacy transformation to the pinned joblib reproduces `7fb56b44...bb0b`
exactly. The validator checks both identities; this is not artifact drift.

`run_arm.sh` remains unchanged because it is the frozen launcher for the
original Study-2 arms and correctly rejects these new seeds. Its pinned
LF-normalized SHA-256 remains
`32986c616cf92b9d01ddb5e8b671d1fcd3939eeb5a02b0228e78c3d72e022eca`.
The extension launcher invokes `grpo_oracle.py` directly with the same fixed
arguments and records the exact argument vector in each status artifact.

## Safe server commands (prepared, not executed)

First push/pull the frozen files to `/home/adam/mas/mas/fpga`. These commands are
documentation only; do not run a launch command until the timing pilot has a
complete PASS.

Configuration-only validation (does not query GPUs or launch anything):

```bash
cd /home/adam/mas/mas/fpga
PYTHONNOUSERSITE=1 /home/adam/mas/mas/env_fpga/bin/python \
  seed_replication_extension_v1/validate.py --mode config
```

Preflight a particular assigned run:

```bash
cd /home/adam/mas/mas/fpga
bash seed_replication_extension_v1/launch.sh preflight correctness_s3
```

Launch only that run after its preflight passes:

```bash
cd /home/adam/mas/mas/fpga
bash seed_replication_extension_v1/launch.sh launch-one correctness_s3
```

Launch any subset whose assigned GPUs are idle:

```bash
cd /home/adam/mas/mas/fpga
bash seed_replication_extension_v1/launch.sh launch-selected rf_s3 rf_s4
```

`launch-all` exists but intentionally fails if any of GPUs 7, 6, 5, and 4 is
not idle. At preparation time, the read-only resource audit found GPU 4 free and
GPUs 5/6/7 occupied by another user's active jobs. Therefore
`correctness_s3` is the only currently schedulable assignment, and even it must
wait for timing-gate PASS. No process was killed, moved, or launched.

Immediately before each launch, the validator performs one GPU check and the
launcher performs two more checks two seconds apart. Each requires no compute
PID, at most 128 MiB used, and at most 1% utilization. Output, optimizer log,
stdout log, and status paths must all be absent. A repository-level `flock` and
an atomic `RESERVED` status close duplicate-launch races.

Inspect status without launching:

```bash
cd /home/adam/mas/mas/fpga
bash seed_replication_extension_v1/launch.sh status
tail -f seed_replication_extension_v1/logs/correctness_s3.stdout.log
```

After all four jobs finish, create the machine-readable completion audit:

```bash
cd /home/adam/mas/mas/fpga
PYTHONNOUSERSITE=1 /home/adam/mas/mas/env_fpga/bin/python \
  seed_replication_extension_v1/validate.py --mode completed \
  --out seed_replication_extension_v1/completion_audit.json
```

For an already completed subset, repeat `--run-id`, for example
`--run-id correctness_s3`. A completion PASS requires exactly 276 sequential
updates, complete update-138/update-276 checkpoints, a consistent eight-row
group log, matching optimizer/group/summary counts, exit code zero, exact code
hashes, and the frozen command line.

## Failure and restart policy

A crashed or ceiling-limited job is not resumed, merged, extended, reseeded, or
silently substituted. Preserve its complete run directory, optimizer log,
stdout log, and status as an explicitly labelled abandoned attempt. A restart,
if scientifically authorized, begins from update zero with the same declared
seed only after the abandoned artifacts are deliberately archived out of all
four active paths. The launcher never deletes or overwrites them.

Hitting the attempt ceiling before update 276 is a reported outcome. It is not
permission to raise the ceiling.

## Frozen implementation identities

The final implementation digests are recorded here after the timing manifest is
frozen and are also pinned inside `launch.sh` where applicable:

- timing manifest: `2e0674f96c57be3864a6fab7683b0edc76f732762f78547d5e6a3e8efc17e194`
- `config.json` (LF-normalized): `3ae8f352b0cbaf92dbcacd0f15e2791c8c72ee588d51628e51554275985c80ff`
- `validate.py` (LF-normalized): `394700a3b278eeff07ceca025655a00806357e0bea39b406b21becd18e7885b4`
- `launch.sh` (LF-normalized): `796a2c1bd861c32fa8106513df7a791adfcde34d67174e5ada77bea8de24113f`

Any mismatch is a NO-GO until the prospective protocol is explicitly revised,
reviewed, and re-frozen before launch.

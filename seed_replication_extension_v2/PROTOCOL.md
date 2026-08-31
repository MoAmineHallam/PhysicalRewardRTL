# Prospective seed-replication extension V2 — V100 execution amendment

Status: **prepared, not launched**. This version supersedes the unlaunched V1
package for the same four seeds. V1 remains immutable evidence and none of its
output paths may be used or combined with V2.

Execution uses the clean shared worktree
`/zeng_gk/Amine/mas/fpga-v100-v2`; the historical checkout remains untouched
because it contains untracked retained study artifacts.

## What changed

The user prospectively selected the two guaranteed-available, two-GPU V100
boxes. At preparation time five of ten V7 timing candidates were complete, the
sixth was running, and no seed-extension training or evaluation existed. The
hardware decision did not use a downstream training or endpoint outcome.

V2 changes only execution placement, absolute server paths, and the identity of
the applicable timing gate. All training and endpoint quantities are inherited
byte-for-byte from the raw-hash-pinned V1 config: seeds, FP16, model and adapter,
rewards, 276 non-flat updates, attempt ceilings, checkpoints, generation
settings, evaluation multiplicity, failure scoring, and analysis rules.

The old V1 gate can never pass because it is immutable failed evidence. V2
therefore requires a complete PASS from the already-frozen
`timing_closure_candidate_v7` package. Its candidate package digest, original
V1 candidate manifest digest, Vivado version, ten-candidate count, criteria,
and generated-from hashes are all checked before launch.

## Fixed balanced allocation

| Run | Condition | Seed | Host | GPU | Model |
|---|---|---:|---|---:|---|
| `rf_s3` | repaired RF | 3 | `v100a` | 0 | V100-SXM2 32 GB |
| `rf_s4` | repaired RF | 4 | `v100b` | 0 | V100S-PCIe 32 GB |
| `correctness_s2` | correctness-only | 2 | `v100a` | 1 | V100-SXM2 32 GB |
| `correctness_s3` | correctness-only | 3 | `v100b` | 1 | V100S-PCIe 32 GB |

Each hardware type therefore receives one RF run and one correctness run.
Assignments are identities, not a scheduling pool. A run is never migrated,
resumed on another GPU, or substituted after launch. Hardware remains explicit
in every status and analysis record; V100 and L40S are not described as
identical numerical execution substrates.

## Readiness and launch boundary

`host-ready` is the only mode authorized before the V7 gate completes. It
checks parent hashes, every frozen artifact, exact isolated packages, disk,
Icarus 12.0, assigned GPU identity/idleness, and a bounded CUDA plus functional
oracle canary independently on each selected GPU. It launches no study process.

After and only after an exact V7 PASS, the two local launch commands are:

```bash
# on v100a
bash seed_replication_extension_v2/launch.sh launch-local

# on v100b
bash seed_replication_extension_v2/launch.sh launch-local
```

The launcher fails closed on a missing/incomplete/failed gate, hash drift,
wrong host/GPU model, active GPU, existing output, or environment mismatch.
Runs start from update zero in independent detached workers. The V1 crash and
completion policies remain unchanged.

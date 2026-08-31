# PPA-RTL DPO independent adaptation V2 — V100 execution amendment

Status: **prepared, not launched**. This package supersedes the unlaunched V1
execution plan while retaining V1 as immutable evidence.

Model phases use the clean shared worktree
`/zeng_gk/Amine/mas/fpga-v100-v2`, preserving the historical checkout and its
untracked retained artifacts.

Every scientific choice in V1 remains unchanged except the prospectively
disclosed Vivado infrastructure amendment: the 229-slot construction,
oracle gate, exact physical-label budget, best-versus-worst rule, two DPO seeds,
276 updates, FP16, 20 held-out designs, 24 draws/design/seed, failure-zero rule,
and routed true-closure endpoint remain fixed. Physical labels and endpoint
closure now use the validated Vivado 2026.1 V7 runtime because the retained
2023.1 runtime is unusable on this host. V2 otherwise changes only the
applicable timing gate, execution hardware, and absolute server paths. The RF
policy's historical surrogate was learned from 2023.1 labels; both compared
policies nevertheless receive the same new 2026.1 true-closure evaluation.
This training-label-version asymmetry is retained and reported as a limitation.

The model workload is balanced across the guaranteed-free V100 boxes:

- generated label slots alternate by frozen generated-slot order between
  `v100a:0` and `v100b:0`;
- DPO/evaluation seed 1 uses `v100a:0`;
- DPO/evaluation seed 2 uses `v100b:0`.

The seed-replication RF jobs have scheduling precedence on those GPU-0 lanes.
PPA-RTL begins there after each RF run completes, while the much longer
correctness jobs continue independently on GPU 1. No run is migrated after
launch and hardware identity is retained in every artifact.

No scientific phase is executable from this package yet. Consistent with V1,
phase-specific launchers must be implemented, tested, hashed, and reviewed
after the complete V7 PASS and before the first generated candidate. This file
does not authorize candidate generation or EDA by itself.

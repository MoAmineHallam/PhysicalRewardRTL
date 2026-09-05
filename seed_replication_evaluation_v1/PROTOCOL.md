# Additional-seed endpoint evaluation V1

Prepared 2026-09-05 before the first additional-seed endpoint generation. This
implements the evaluation contract already frozen in seed extension V1 and
inherited by V2; it does not amend training or the original Study-2 result.

Each run must independently pass V2's completed-training audit. Use its final
update-276 adapter, its assigned V100 host/GPU, the unchanged `eval_sealed.py`,
and all 20 frozen prompts with their individual token budgets. RF seeds 3/4 get
24 draws/design; correctness seeds 2/3 get 48. Generation seed is 100 plus the
training seed; temperature 1, batch 4, inherited top-p 1, FP16. The original
sampler's remaining generation settings are unchanged. The frozen oracle uses
seeds 1 and 2, 1024 vectors each. RF scoring is recorded for RF runs only, as in
the original evaluation; it never selects samples.

Freeze LF-normalized code/dependency hashes before generation. Store a selected
run's completion audit before loading its adapter. Require an idle assigned GPU
twice, check host identity, refuse all existing state/output paths, retain
stdout and failure status, and never resume or merge a failed generation run.
A failed run requires a separately documented recovery decision. No worker
waits for or modifies another training run. In particular, starting the three
completed runs does not authorize use of correctness_s3's busy GPU.

Generation outputs live under this package only. Validate all 20 design
denominators, correct multiplicities, emitted hashes, oracle parameters, adapter
identity, policy/seed identity and dependency hashes before marking COMPLETE.
Incorrect/extraction/implementation failures retain zero-frequency outcomes.
Physical evaluation must retain every emitted candidate and its multiplicity,
use the previously validated Vivado-2026.1 infrastructure, and preserve all
constraint/path diagnostics. This launcher does not itself claim physical
evaluation has completed or silently substitute a new timing estimator.

Report individual seeds and seed dispersion, followed by explicitly post-primary
paired design contrasts. Do not pool new seeds into or rewrite the original
primary confidence interval. Shared SFT initialization and reward-data limitations
remain even with additional policy-training seeds.

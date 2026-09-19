# Automated post-primary method comparison — V3

Prepared September 15, 2026, following the user's request to prepare the method
comparisons and automatically hand off each completed stage. V1 and V2 remain
unchanged. This amendment supplies executable workers and orchestration.

The external-method arm is an **independent adaptation of PPA-RTL's
performance-only best-versus-worst DPO strategy**, not the authors' implementation.
Primary source: https://ece.k-state.edu/research/hardware-security/papers/DAC2025_RLPFA_Processing.pdf

## Fixed scientific contract

- Retain V1's frozen 46 training prompts and 229 label slots (46 references,
  183 generated slots), family quotas, best/worst rule and 16-attempt generation
  cap. No prompt replacement, label replacement or budget increase. Require at
  least four non-tied prompt pairs or stop as infeasible under this budget.
- Two DPO training seeds, same frozen SFT adapter and base model as RF. Standard
  reference-anchored DPO with beta 0.1, summed completion log probabilities,
  completion EOS included, dropout disabled, AdamW at 1e-5, four pairs/update,
  276 **executed** optimizer steps. Process one pair at a time and accumulate
  its loss/4 to fit the V100. Reference log probabilities are computed once from
  the frozen SFT adapter. Log AMP skipped steps separately; stop above 552
  attempted updates. FP16 base, FP32 trainable adapter parameters. Save updates
  138 and 276. The preflight found V1's reference `med9` requires 3,112 completion
  tokens; its old 1,536-completion/2,048-sequence limits made the frozen plan
  impossible. Before any study candidates, amend training limits to
  512/3,584/4,096 prompt/completion/sequence tokens. Generation remains capped
  at the original 1,536 new tokens for training slots. Retain the complete
  reference without truncation or prompt substitution. The disposable GPU
  pilot uses the longest training reference to test memory at this longer length.
- The common functional check uses both fixed 1024-vector streams, clock-edge
  race-free stimulation, two episodes separated by reset, zero reset output,
  and a common latency in 0..40 cycles across streams/episodes. Compare all
  reference samples after the declared eight-sample warmup, including the tail
  using 40 flush cycles. This remains simulation coverage, not a formal proof.
  Apply it uniformly to training candidates and **all three evaluation arms**.
- Labels: one 5 ns constrained-before-synthesis Vivado 2026.1 implementation per
  slot. Invalid measurements receive zero and still consume one of 229 attempts.
  No training-label retries. Higher WNS-derived frequency is preferred.
- Endpoint: the existing bounded routed **setup-period** search on
  xc7z020clg400-1, with its 1..200 ns bounds and confirmations. This is not full
  hold/pulse-width timing signoff. Allow one retry of an invalid endpoint trial;
  every attempted trial is logged. A 900-second timeout per trial is an explicit
  new operational bound applied equally to all arms. Infrastructure/hash faults
  stop the queue instead of producing spurious all-zero comparisons.
- Fresh evaluation: all 20 existing test designs, same prompts/token budgets,
  SFT, RF checkpoints from training seeds 3/4, and DPO seeds 1/2. Two 24-draw
  replicates per design per arm: 960 draws/arm, 2880 total. SFT's two replicates
  are sampling replication of one checkpoint, not two training seeds. RF/DPO
  replicas correspond to two independently trained policy adapters sharing SFT.
  No new RF training is included. Preserve every incorrect or extraction-failed
  draw at zero; do not substitute the best seed or mix old primary measurements.
- Decoding: temperature 1, top-p 1, explicitly top-k 50, one draw per generation
  call, original per-design maximum tokens, endmodule stopping. Each draw and
  each label attempt has a deterministic seed; retain raw text and token IDs.
  This changes batching/seeding relative to historical evaluation for every arm.
- Best-of-N: N=1,4,8,24, contiguous nonoverlapping blocks within each 24-draw
  replicate. Implement selection using the newly measured physical scores.
  Apply the same N and failure rule to SFT, RF and DPO. An all-failed block is
  zero. This is an executed finite-sample selection comparison, not a claim
  about an unseen perfect selector. Exact byte-identical designs may share a
  measurement; retain all draw multiplicities. Report actual GPU/simulation/
  EDA work and cache assumptions; these totals are not end-to-end deployment
  latency or an amortized training-cost break-even calculation.
- Equal-design averages, both seeds separately, and paired RF–DPO/DPO–SFT/RF–SFT
  differences. Use the fixed family-by-regime design bootstrap (100,000 draws,
  seed 20260915). Intervals condition on these checkpoints and samples; they do
  not include SFT training variance. Secondary selection analyses are descriptive.

## Limits on interpretation

This is a post-primary comparison: existing test results have already been seen.
Freeze this package before new scientific candidates. No test-result-driven
tuning is included. Two-step software pilots use a training reference and an
artificial comment difference; their adapters never enter evaluation or DPO
training. They test implementation and memory feasibility, not efficacy.

The historical RF labels came from Vivado 2023.1 and a different row population;
new DPO labels use 2026.1. Matching the 229-label count and starting model does
not isolate only the optimizer or establish equal total training compute.
Historical RF's update counter is not retrospectively certified by DPO's new
actual-step counter. Describe an adapted method-package comparison and report
these asymmetries. This new comparison does not resolve the previous audit or
authorize changes to the original manuscript results.

## Automatic execution and recovery

Two isolated GPU workers use GPU 0 on their existing V100 hosts. Local Windows
coordinates one Vivado lane. No notifications to other people, paper edits,
submission, or publication are performed automatically.

1. Verify package/model hashes, hardware, simulator and timing pilot.
2. Run disposable two-update DPO software pilots on both servers.
3. Generate the two frozen training-candidate shards and verify all slots.
4. Transfer candidates, execute 229 physical-label attempts, construct preferences.
5. Transfer preferences and train two seeds. Each host immediately proceeds to
   DPO, SFT and RF evaluation when its training completes.
6. Transfer and validate all 2880 draws; measure each distinct valid circuit.
7. Calculate paired results and measured best-of-N summaries; write REPORT.md.

Completion status is written atomically; failed workers stop dependent stages.
Coordinator and host locks prevent duplicate launches. Completed stages, draws,
slots and recorded physical trials can be reused on restart with matching hashes.
Interrupted training or an unrecorded in-flight physical trial stops for review:
it is never invisibly retried or combined with a previous failed training run.
The coordinator survives closing this conversation. It prevents automatic idle
sleep while running, but power loss, Windows restart or manual sleep interrupt it.
After an interruption, rerunning the queue revalidates saved work. It never
silently removes a failure record. An SSH outage stops coordination; a detached
remote worker can continue and be reattached when the queue is restarted.

## Commands

Preparation: `python comparison_pipeline_v3/prepare.py configure`, then tests,
`python comparison_pipeline_v3/prepare.py freeze`, and `.../prepare.py deploy`.

Preflight only: `powershell -File comparison_pipeline_v3/start.ps1 -PreflightOnly`.

Entire automatic queue: `powershell -File comparison_pipeline_v3/start.ps1`.

Status: `python comparison_pipeline_v3/coordinator.py status`.
Detailed local logs and state: `comparison_pipeline_v3/artifacts/`.
Remote logs: the isolated deployment's `comparison_pipeline_v3/artifacts/logs/`.

# September 26 controlled screening protocol

Frozen before launching this campaign. This is an exploratory, four-times-longer
development screen, not a quality-preservation or novelty demonstration.

- Use the unchanged September 23 token arrays, tokenizer, audited split, and
  65,536-token development evaluation. Their upstream provenance and earlier
  validation reuse remain limitations. No new independent test set is implied.
- Width 384, six layers/heads, context 256, batch 8, accumulation 4. Run 1,024
  updates, or 8,388,608 sampled tokens per run, with replacement from the 8M-token
  stream. This is exposure count, not unique data. Position table remains 4096;
  longer-context quality is not evaluated.
- Keep the original optimizer/numerics, with the cosine schedule stretched to
  1,024 steps. The first 256 steps therefore do not reproduce the older run's
  learning-rate schedule. Dense attention remains ordinary SDPA during training.
- Primary comparison: seven arms, seeds 42/43/44, `fan_matched` initialization.
  Common non-FFN tensors are exactly paired by name and seed. The data-window
  order must match across arms for each seed.
- Arms: dense (hidden 1024), narrow dense (256), four-group, four-group plus
  shuffle, rectangular Monarch with four blocks, Monarch-budget dense (320),
  and rank-64 projections. Monarch and its dense control have exactly equal FFN
  parameter counts; grouped/shuffle match narrow. Low-rank has no exact matched
  dense arm in this screen; do not claim a same-budget low-rank advantage.
- Additional initialization diagnostic: narrow/grouped/shuffle, seed 42 only,
  legacy initialization, at the same 1,024 steps. Dense initialization is
  unchanged by `fan_matched`, so its primary run is also the legacy reference.
  This single-seed sensitivity check is not a confidence interval.
- Pair all seven arms within the same GPU for a seed: seed 42 on V100a GPU 0,
  seed 43 on V100a GPU 1, seed 44 on V100b GPU 0. Legacy diagnostic on V100b
  GPU 1. Use fixed, differing arm orders, recorded in `stage1/campaign.py`.
  GPU type is confounded with seed; report paired quality differences rather
  than treating cross-device times as architecture-only effects.
- Preflight: CPU algebra/gradient/cache tests, a direct comparison with pinned
  author Monarch reference code, and GPU FP16/FP32 first-FFN comparisons with
  finite gradients. Legacy and corrected initial activation RMS are recorded
  for all seven arms and three seeds. Expected-variance matching does not match
  full distributions, gradients, or optimization conditioning.
- Estimated training-only budget from earlier measured runs: approximately
  127–147 seconds per 1,024-step standard-arm run, about 0.85–0.98 GPU-hours
  for 24 runs before structured-kernel differences and startup/evaluation/I/O.
  Measure actual process wall time. Each worker stops on failure, skipped update,
  sample-order mismatch, or a 20-minute per-run timeout. No silent retries,
  optimizer resume, hyperparameter search, or replacement of failed results.
- Report all arms and seeds, initial/final NLL, perplexity, paired differences,
  sample standard deviation, update counts, parameters, and measured runtimes.
  A screening heuristic is mean excess NLL <= 0.10 nats/token versus full dense;
  also compare with the relevant equal-parameter dense control. This heuristic
  only prioritizes follow-up; it is not a statistical non-inferiority margin.
  No confidence or generalization claim follows from three development seeds.

Do not select a proposed new block from this screen alone. Next decisions require
a complete equation/schedule prior-work comparison, a larger pinned corpus and
independent quality suite, and matched quantized FPGA schedules. Any improved
initialization or training recipe must be disclosed separately from architecture.
Distillation and physical-reward optimization remain Stage 2.

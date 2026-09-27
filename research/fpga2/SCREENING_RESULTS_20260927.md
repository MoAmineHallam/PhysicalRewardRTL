# Three-seed screening: complete

Checked September 27. All 24 trials completed successfully on September 26,
13:36:09 UTC (21:36 Shanghai). The campaign ran for 17.82 minutes, with about
1.00 summed process-hours across four GPU workers, including process startup,
evaluation and checkpoint writing. This is not measured energy or a model-serving
speed comparison. Both servers had no GPU compute processes at the latest check.

## Audit

The [frozen protocol](SCREENING_PROTOCOL_20260926.md) specified 21 primary trials
(seven arms, seeds 42/43/44) and three legacy-initialization checks at seed 42.
Every run completed 1,024 optimizer updates and 8,388,608 sampled tokens, with
zero skipped updates. All 24,576 step records were checked for complete sequential
numbering and skipped updates. All runs use identical data manifests; sampled
window hashes match across arms within each seed. Recorded source hashes match
the preserved remote source snapshot. No failed trial was replaced.

Total exposure was 201,326,592 sampled tokens across trials, not unique corpus
size. Training remains from scratch at context 256 using an approximately
8M-token development stream. Evaluation uses the same reused 65,536 development
tokens. These models remain undertrained; no independent quality confirmation,
long-context evaluation, distillation, FPGA implementation or energy measurement
was performed in this campaign.

## Primary results

Means over three seeds; SD is sample standard deviation across seeds, not a
confidence interval. Lower NLL/perplexity is better. Mean perplexity is the
arithmetic mean of seed perplexities. All primary runs use `fan_matched`.

| FFN arm | Total parameters | Mean NLL ± SD | Mean perplexity | Paired excess NLL vs dense ± SD |
|---|---:|---:|---:|---:|
| Full dense, hidden 1024 | 31,498,368 | 6.10890 ± 0.00651 | 449.85 | 0 |
| Narrow dense, hidden 256 | 26,189,952 | 6.18740 ± 0.00468 | 486.58 | +0.07850 ± 0.00493 |
| Four-group | 26,189,952 | 6.25982 ± 0.00426 | 523.13 | +0.15092 ± 0.00310 |
| Four-group plus shuffle | 26,189,952 | 6.23907 ± 0.00550 | 512.39 | +0.13017 ± 0.01197 |
| Monarch | 26,632,320 | 6.26362 ± 0.00971 | 525.13 | +0.15472 ± 0.00450 |
| Monarch-budget dense, hidden 320 | 26,632,320 | 6.16360 ± 0.00711 | 475.14 | +0.05470 ± 0.00468 |
| Low-rank, rank 64 | 25,895,040 | 6.30499 ± 0.01235 | 547.32 | +0.19609 ± 0.01232 |

Ordinary dense width reduction outperforms the structured operators at exactly
matched FFN and total parameter counts in every tested seed: grouped versus
narrow loses 0.07242 mean NLL, shuffle versus narrow loses 0.05168, and Monarch
versus its dense match loses 0.10002. There is no exact parameter-matched dense
low-rank arm, so no same-budget low-rank conclusion is asserted.

Only the two reduced-width dense controls meet the protocol's exploratory
mean-excess-NLL <= 0.10 heuristic. This is a prioritization rule, not evidence
of statistical non-inferiority or preserved model quality. Dense remains best
in quality at its larger budget. Different architectures may need different
optimization recipes; this is a fixed-recipe screen, not their best attainable
performance or a reproduction of the Monarch paper's recipe.

## Initialization sensitivity

Seed 42 only, with identical sampled windows and training length:

| Arm | Legacy NLL | Variance-matched NLL | Matched minus legacy |
|---|---:|---:|---:|
| Narrow dense | 6.18851 | 6.18897 | +0.00045 |
| Four-group | 6.35198 | 6.25907 | -0.09291 |
| Four-group plus shuffle | 6.34175 | 6.24145 | -0.10030 |

Correcting initial activation scale helps grouping substantially in this check,
but the grouped variants still lose to the equal-parameter dense baseline.
Initialization therefore matters, and does not explain away the whole observed
gap. The legacy check runs on a different GPU type than the paired seed-42
primary runs; small differences, especially the narrow result, should not be
interpreted as a causal initialization effect. No multi-seed initialization
effect was established.

## Decision and next work

Do not promote these grouped/Monarch/low-rank configurations directly to the
main FPGA implementation or claim that a useful new block has been found. Keep
the reduced-width dense controls as essential references. The result motivates
revisiting the communication restriction and its quality cost before expensive
hardware work; it does not disprove structured architectures in general.

The next research step is to finish the closest-work equation/schedule audit and
define any revised restriction with a concrete bank/buffer/traffic schedule.
Larger training then needs a pinned corpus and independent quality suite, fair
optimization budgets, and numerical contracts for matched hardware comparisons.
No further training or board job was launched during this progress check.

Full [summary](evidence/screening-20260926/complete/summary.json), per-seed
results, manifests, 24 training logs and worker timings are archived under
[complete evidence](evidence/screening-20260926/complete/). Checkpoints remain
on the shared server filesystem; they and the source data are not committed.

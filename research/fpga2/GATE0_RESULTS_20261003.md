# Gate 0 results — 2026-10-03

Protocol: [GATE0_PROTOCOL_20261001.md](GATE0_PROTOCOL_20261001.md) (with
amendments 1–2).  All 18 runs completed; 382 distinct correct circuits were
implemented once each with the primary flow (Vivado 2023.1, `xc7z020clg400-1`,
5.0 ns).  Table from `gate0_physical.py analyze` on the server
(`gate0/vivado/gate0_analysis.json`); contrasts are arm minus FP16 of the same
policy, with stratified paired design-bootstrap 95% intervals.

## Pre-registered decision: **B**

No GPTQ arm lowered the frequency of correct circuits (`μ`) by the required
≥10% with an interval below zero, and every GPTQ point loss in `μ` is below 5%.
Rule C (student GPTQ-4 correctness below half of FP16) did not fire.  Under the
frozen rule, compression costs correctness only; **the hidden-physical-cost
paper (RQ1) is not supported**.

## Results

| Run | Designs | Δq (pp) | Δμ (MHz) | ΔF (MHz) |
|---|---:|---|---|---|
| stu_rtn8 | 18 | +0.00 [−4.40, +4.17] | +1.63 [−0.69, +5.67] | −0.02 [−8.51, +7.96] |
| stu_rtn4 / rtn3 / gptq3 | 18 | −43.52 [−50.93, −35.88] | n/a (no correct draws) | −80.15 [−94.05, −65.98] |
| stu_gptq4 | 18 | −8.80 [−18.75, +1.39] | +2.17 [−0.71, +6.91] | −15.03 [−33.45, +4.00] |
| stu_fp16t | 18 | +2.78 [−1.39, +6.94] | +2.07 [−0.00, +6.19] | +5.24 [−2.76, +13.37] |
| stu_gptq4t | 18 | −9.03 [−16.44, −1.62] | −10.22 [−24.29, +3.86] | −16.30 [−30.35, −2.35] |
| qsft_rtn4 | 14 | −24.11 [−29.76, −18.15] | +56.55 [+45.34, +68.07] | +0.21 [−7.92, +8.28] |
| qsft_rtn3 | 14 | −50.60 [−54.76, −46.43] | n/a | −32.42 [−36.79, −28.45] |
| qsft_gptq4 | 14 | +2.38 [−1.19, +6.85] | +13.68 [+5.87, +21.42] | +7.07 [−1.18, +17.03] |
| qsft_gptq3 | 14 | −27.68 [−30.95, −24.40] | +39.39 [+33.70, +46.76] | −8.15 [−12.44, −4.22] |
| qgrpo_rtn4 | 14 | −31.55 [−37.20, −26.49] | −3.52 [−3.65, −3.39] | −63.68 [−79.84, −50.22] |
| qgrpo_rtn3 | 14 | −53.87 [−61.31, −49.40] | n/a | −106.36 [−130.39, −92.98] |
| qgrpo_gptq4 | 14 | +4.17 [+0.89, +8.04] | −1.55 [−2.46, +0.00] | +8.98 [+0.87, +19.47] |
| qgrpo_gptq3 | 14 | −41.67 [−52.38, −31.25] | −1.18 [−2.69, +0.34] | −83.44 [−108.44, −59.94] |

## Reading (pre-registered findings first)

1. **4-bit GPTQ preserves generated-circuit quality.**  For both 7B policies,
   GPTQ-4 changes neither correctness nor failure-penalized frequency
   materially; the RL-trained policy keeps its physical gain (`μ` −1.55 MHz).
   For the 1.5B student, GPTQ-4 costs about 9 points of correctness (interval
   includes zero) and nothing in `μ`.
2. **Output-head trimming is free** at FP16 (`stu_fp16t`).  Combined with GPTQ-4
   (`stu_gptq4t`) it lowers correctness by 9 points; its `μ` interval includes
   zero.  Trimmed arms do not enter the decision rule.
3. **3-bit and RTN-4 break the small student** (no correct circuit) and cost
   the 7B models 24–54 correctness points.

## Exploratory observation (post hoc, not a confirmed result)

For the SFT 7B policy, compression *raised* the frequency of surviving correct
circuits (`μ` +14 MHz at GPTQ-4, +39 at GPTQ-3, +57 at RTN-4) while lowering
correctness, so failure-penalized `F` did not improve.  A plausible explanation
is selective survival: compression breaks some implementation styles more
often than others, and the surviving correct circuits were faster.  This was
not a pre-registered hypothesis, `μ` is computed only on designs where both
arms pass, and the strata are small; it would need its own protocol and a fresh
split before any claim.  The RL policy, already concentrated on fast forms,
shows no such shift.

## Mechanism statistics (descriptive)

`support` is the mean over designs of the inverse-Simpson number of distinct
correct circuits (0 for a design with no correct draw), so it also falls
mechanically when correctness falls.  `off-majority` is the share of an arm's
correct draws that differ from the FP16 policy's most frequent correct circuit,
on designs where both arms pass.

| Run | support FP16 → arm | off-majority |
|---|---|---:|
| stu_rtn8 | 2.92 → 2.52 | 0.64 |
| stu_gptq4 | 2.92 → 1.99 | 0.66 |
| stu_fp16t | 2.92 → 2.54 | 0.65 |
| stu_gptq4t | 2.92 → 2.19 | 0.66 |
| stu_rtn4 / rtn3 / gptq3 | 2.92 → 0.00 | — |
| qsft_rtn4 | 2.04 → 2.98 | 0.66 |
| qsft_gptq4 | 2.04 → 2.75 | 0.65 |
| qsft_gptq3 | 2.04 → 3.46 | 0.83 |
| qsft_rtn3 | 2.04 → 0.00 | — |
| qgrpo_rtn4 | 0.71 → 1.24 | 0.89 |
| qgrpo_gptq4 | 0.71 → 0.86 | 0.17 |
| qgrpo_gptq3 | 0.71 → 0.61 | 0.42 |
| qgrpo_rtn3 | 0.71 → 0.00 | — |

Reading, with one limitation: no FP16-versus-FP16 resampling baseline was run,
so off-majority shares have no null reference.  The near-lossless student arms
(`stu_rtn8`, `stu_fp16t`, about 0.65) suggest that about two thirds of a diverse
student's correct draws leave its FP16 majority form by sampling alone; the
student's GPTQ-4 value (0.66) is at that level.

- **RL policy:** under GPTQ-4 it stays on its FP16 majority circuit for 83% of
  correct draws (off-majority 0.17), which accounts for its unchanged `μ`.
  Harsher compression moves it off that circuit (0.42, 0.89), yet `μ` changes by
  at most 3.5 MHz, so its alternative correct circuits are about as fast.
- **SFT policy:** compression spreads probability over more correct circuits
  (support 2.04 → 2.75 at GPTQ-4, 3.46 at GPTQ-3; off-majority 0.83 at GPTQ-3),
  consistent with the exploratory observation that surviving circuits were
  faster.  This remains post hoc.

## Consequence

Per the protocol, RQ1 stops here.  The finding that GPTQ-4 and head trimming
preserve the physical quality of a physically trained RTL model is the
enabling result for the alternative in the plan (RQ3: a measured edge
deployment on PYNQ-ZU), which needs a decision with the supervisor.

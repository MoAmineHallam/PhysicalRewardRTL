# Repaired-RF VerilogEvalV2 comparison

Primary endpoint: pass@1 from 20 samples on every one of the 156 official spec-to-RTL problems. Each training seed remains separate.

| Policy | Training seed | pass@1 | pass@5 | pass@10 | pass@20 | Compile+verdict |
|---|---:|---:|---:|---:|---:|---:|
| sft | 0 | 22.34% | 38.28% | 42.84% | 46.79% | 65.16% |
| rf_s1 | 1 | 21.12% | 36.42% | 40.97% | 44.87% | 68.65% |
| rf_s2 | 2 | 20.77% | 35.06% | 38.90% | 42.31% | 66.19% |

| Paired contrast | Difference (percentage points) | 95% CI |
|---|---:|---:|
| RF seed 1 - SFT | -1.22 | [-2.82, 0.38] |
| RF seed 2 - SFT | -1.57 | [-3.08, -0.10] |
| Mean of two RF seed estimates - SFT | -1.39 | [-2.69, -0.10] |

The RF-seed mean is formed after estimating each policy separately. The 20 draws from RF seed 1 and 20 draws from RF seed 2 are not pooled into an artificial 40-draw policy.

This matched V2 experiment must not be pooled with legacy n=10, temperature=0.8 VerilogEval files.

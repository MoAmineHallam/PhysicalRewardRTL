# External RTLLM v2.0-era slice v1

This package freezes an outcome-independent, balanced external slice for a later generalization study. It contains protocol code, audits, eight prompts, and their official simulation oracles. It contains **no generated candidate, model output, Vivado report, or experimental result**.

## Frozen identity

- Official upstream: `https://github.com/hkust-zhiyao/RTLLM.git`
- Benchmark snapshot: RTLLM v2.0-era 50-task corpus
- Commit: `e67f150603f52d6abf208ed0e97bd77a95b1ee34`
- Git tree: `a05b45fb1372c3525b6efd1452dfc914e1535a05`
- Commit date: 2024-10-12 05:38:45 UTC
- Upstream archive SHA-256: `da28c4be8e04e65d133572aea9668f7ac71ee040bf1acc2c1897ff54c3f2a9cf`
- Selection-manifest SHA-256: `0b827ccbe2e6092a253227594434ff09ee298008afe221cf867f055cc14a776f`

The pin is an immutable 50-task snapshot from the upstream v2.0-era history. The repository has no tag or release object establishing this commit as an official release boundary, so this package does not call it one. Later upstream revisions must not be silently mixed with this frozen snapshot.

## Frozen eight tasks

| Category | Task | Expected module |
|---|---|---|
| Arithmetic | `Arithmetic/Multiplier/multi_pipe_8bit` | `multi_pipe_8bit` |
| Arithmetic | `Arithmetic/Adder/adder_pipe_64bit` | `adder_pipe_64bit` |
| Control | `Control/Counter/up_down_counter` | `up_down_counter` |
| Control | `Control/Finite State Machine/sequence_detector` | `sequence_detector` |
| Memory | `Memory/LIFO/LIFObuffer` | `LIFObuffer` |
| Memory | `Memory/Shifter/LFSR` | `LFSR` |
| Miscellaneous | `Miscellaneous/Others/traffic_light` | `traffic_light` |
| Miscellaneous | `Miscellaneous/Others/edge_detect` | `edge_detect` |

Selection was not manual. For every eligible task, the code computes

```text
sha256(selection_salt + "|" + category + "|" + task_id)
```

and retains the two lexicographically smallest hashes per official category. The salt and exact ranking rule are in `selection_policy.json`.

## What was audited

1. `audit_manifest.json` accounts for all 50 upstream tasks. A task must have a named DUT, one official reference, an edge-triggered single-clock implementation, a terminating self-checking oracle, no external oracle file, and no obvious non-synthesizable or Xilinx-specific construct. Official random stimulus is allowed only when two fresh simulator processes have byte-identical transcripts.
2. `reference_preflight.json` compiles and runs only each statically eligible official reference against its official testbench with Icarus Verilog. It does not run generated RTL. Twenty-three tasks pass. `radix2_div` is excluded because its official reference reports three failures; `ring_counter` is excluded because its official oracle cannot elaborate under the frozen simulator.
3. `contamination_report.json` hashes 2,123 declared local fine-tuning/source files. It checks exact task names, exact and whitespace-normalized prompts, and comment/whitespace/top-module-normalized reference RTL. The only local name collision is `ring_counter`, already ineligible. Public pretraining exposure cannot be measured and remains an explicit limitation.
4. `selection_manifest.json` joins those three audits and applies the deterministic two-per-category ranking.

“xc7z020 compatible” here is a pre-run structural screen, not a claimed implementation result. No Vivado run was performed. A later experiment must retain every selected task even if generation, simulation, synthesis, placement, or routing fails; it may not substitute an easier task after outcomes are visible.

## Oracle isolation

Only `tasks/**/prompt.txt` may be given to a model. `tasks/**/oracle/testbench.v`, `task.json`, the audit files, and upstream references must not enter the generation context. Upstream reference RTL is deliberately not copied into this package. Candidate RTL and all experimental results must be written outside this frozen directory.

Before any model launch, a separate preregistration must freeze policy checkpoints, decoding, sample multiplicity, correctness command, Vivado version/device/constraints, timing endpoint, resource/power endpoints, and failure scoring. This package alone does not authorize or define that experiment.

## Reproduce the freeze

Starting from the pinned upstream checkout or GitHub archive directory:

```powershell
python external_rtllm_slice_v1/scripts/audit_upstream.py --upstream <RTLLM_ROOT>
python external_rtllm_slice_v1/scripts/reference_preflight.py --upstream <RTLLM_ROOT>
python external_rtllm_slice_v1/scripts/check_contamination.py --upstream <RTLLM_ROOT> --repo-root .
python external_rtllm_slice_v1/scripts/freeze_slice.py --upstream <RTLLM_ROOT>
python -m unittest discover -s external_rtllm_slice_v1/tests -p "test_*.py" -v
python external_rtllm_slice_v1/scripts/validate_slice.py --repo-root . --skip-package-lock
python external_rtllm_slice_v1/scripts/freeze_package.py
python external_rtllm_slice_v1/scripts/validate_slice.py --repo-root .
```

`UPSTREAM_LICENSE.txt` preserves the upstream MIT license.

# Candidate paper plan — RTL action interface and FPGA co-design

## Working thesis

**Can a student trained to emit typed RTL actions, rather than BPE Verilog
tokens, retain RTL-generation quality while giving an FPGA a smaller, regular
and formally constrained decode interface?**

The intended system has three parts:

1. An encoder--decoder student that reads a natural-language RTL specification.
2. A typed action decoder that selects only actions legal in its current RTL
   grammar and symbol-table state.
3. A hardware-resident grammar/symbol engine that renders the actions into
   Verilog and supplies the small state-specific action head.

This is a domain-specific student for RTL generation.  It is not presented as a
better general-purpose LLM.

## Contribution boundary

The paper must **not** claim that it invented grammar-constrained decoding, AST
action generation, knowledge distillation, output-head reduction, or
hardware-aware NAS.  These have direct precedents.

The claim under test is narrower:

> A typed, state-indexed RTL output interface can be trained and mapped as an
> integrated model--FPGA system, avoiding a full BPE-vocabulary projection at
> decode time and improving the measured RTL-quality--hardware frontier.

The contribution is credible only if the mechanism, trained model, renderer,
and post-route evidence are all necessary.  A grammar mask applied after a
normal BPE head is not sufficient, because it still reads the full head.

## Required baselines

All methods use the same data split, specification prompts, teacher, candidate
budget, numeric precision, compilation/simulation oracle and PPA workload.

| ID | Student output interface | Purpose |
| --- | --- | --- |
| BPE-dense | Ordinary BPE Verilog with its normal vocabulary head | Primary quality and complete-system baseline. |
| BPE-mask | Same BPE student with grammar masking after full logits | Separates validity from saved head traffic. |
| BPE-reduced | A strong published-style vocabulary/output-head reduction selected after code review | Tests whether a generic small head, rather than typed actions, explains any result. |
| Action-no-copy | Typed productions and fixed terminals only | Measures the value and limitation of formal actions. |
| Action-copy | Productions, bounded typed symbol selection, literals and controlled copy | Proposed full design. |

Report both equal-training-compute and equal-deployment-storage comparisons.
Do not call unequal parameter counts fair without reporting the complete Pareto
frontier.

## Execution gates

### Gate A — representation feasibility

Define a canonical synthesizable Verilog subset and reversible action
serialization.  Parse every corpus example into actions and render it back.
Publish coverage, round-trip failure rate, unsupported constructs, action-length
distribution and symbol/copy statistics.

**Stop:** if useful held-out RTL cannot be represented without ad hoc exceptions,
or action sequences are so much longer that they erase the head-traffic saving.

### Gate B — model quality

Train small BPE and action students with matched source data.  Distil from the
same teacher only after the direct-supervision baseline works.  Evaluate on an
untouched held-out set: parse, compile, simulation/functional pass, and
generated-circuit PPA only for passing designs.

**Stop:** if the action interface loses material functional quality to BPE at a
comparable deployment budget.  Valid syntax alone does not count as success.

### Gate C — physical mechanism

Implement the output interface, grammar state and renderer first.  Use the
PYNQ-ZU as the primary target and a reduced configuration on PYNQ-Z2 as a
portability result.  Under identical clock/precision/memory-interface rules,
measure post-route resources, achieved clock, cycles per decoded action,
off-chip bytes and complete prompt-plus-generation latency.

**Stop:** if head savings disappear once action length, state handling, copy and
CPU--FPGA transfers are included.  FLOPs, standalone head timing, or frequency
alone are insufficient.

### Gate D — end-to-end system

Keep the selected model on the FPGA across generation as far as the board
permits.  Compare complete decode requests, not only an isolated matrix.
Publish all resource limits, bit widths, memory residency, generated sequences,
failures and confidence intervals.

**Advance:** only with a repeatable full-system physical advantage at comparable
functional RTL quality, explained by measured reduced vocabulary-head traffic.

### Gate E — use the submitted method

After Gates A--D, apply the submitted paper's sequence: teacher distillation,
oracle-verified RTL SFT, then correctness-gated physical-reward policy training.
Treat an SFT checkpoint as the reference and use matched correctness-only and
physical-reward controls for both BPE and action students.

This stage tests whether the hardware-efficient student still learns to produce
physically useful circuits.  Its reward evaluates the **generated circuits**;
student execution PPA is separately measured and is not inserted as a constant
reward for a fixed architecture.

## Evidence needed for a publishable result

1. A formal, reproducible RTL action language and hardware interface.
2. A causal quality result: typed action training versus BPE, BPE masking and a
   strong generic reduced-head baseline.
3. Post-route PYNQ-ZU evidence for the whole decoder path, with a useful
   latency, traffic, energy, resource, or feasible-model-size improvement.
4. Functional RTL evidence and independent PPA evaluation that retains failed
   samples in the denominator.
5. A clear ablation showing that the benefit is not merely grammar masking,
   vocabulary pruning, distillation, or best-of-N selection.

The precise improvement margins should be preregistered after Gate C measures
the realistic baseline.  Promising publication-level evidence would be a
material complete-request physical gain together with no meaningful decline in
held-out functional pass rate; a smaller head with an equal or worse end-to-end
system is a negative result, not a paper claim.

## Paper outline

1. **Problem:** BPE-token RTL students impose a large, unconstrained output
   interface on a resource-limited accelerator.
2. **Method:** action language, typed state, controlled copy, grammar renderer
   and regular FPGA decode dataflow.
3. **Training:** canonicalization, direct action supervision, matched teacher
   distillation and, only after model selection, correctness-gated physical
   reward adaptation.
4. **Implementation:** memory map, state/action tables, arithmetic, bit widths,
   on-chip/off-chip residency and PYNQ targets.
5. **Evaluation:** representation coverage, quality controls, post-route
   end-to-end PPA, generated RTL functional/PPA results, ablations and failure
   accounting.
6. **Limitations:** specialized to a defined RTL subset; does not prove a
   general-purpose LLM or ASIC result.

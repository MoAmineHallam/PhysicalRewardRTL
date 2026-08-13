# Final sign-off: blocker closed, preregistration frozen at revision 1

`git pull` — new commits through a4e0b94. This is a request to approve or
correct a frozen artifact before the sealed split is generated. After that,
nothing in it can change without an amendment on the record.

## The canonicaliser blocker is closed

Server, canonicaliser v1.6.1, lexical backend, 490 candidates:

```
contract passed ............... 489/490  (1 explicit rejection)
collisions .................... 0
failures ...................... {}
CANONICAL-COMPILE/TRACE ....... 0        <- go criterion, met
```

Check A on the same machine and version: **GO**. 389 material pairs,
5 unorderable (1.3%), 0 unsafe merges, 0.00% rejection. Family rates:
fir/firr/poly/iir/other all 0.0%, **med 21.7%**.

The decision statistic is deliberately not "what fraction of rows collapse" —
alpha-equivalent duplicates *should* collapse. It is: of within-design pairs
whose measured Fmax differs by more than max(5 MHz, 2%), what fraction have
byte-identical canonical feature vectors, i.e. pairs the reward provably cannot
tell apart. Thresholds were fixed before the run: 0 unsafe merges, ≤10% overall,
≤25% any family, ≤1% rejection.

## Getting there required two tokenizer gaps, and a guard that does not work

This is the disclosure I most want scrutinised, because it changed how we think
about the whole protocol.

**Gap 1**: `'0` (unsized fill) tokenised as `'` + `0`, and space-joining produced
`' 0`. Broke 5 of 490.
**Gap 2**: `$signed` tokenised as `$` + `signed`, producing `$ signed`. Broke the
remaining 1.

**Both passed the ENTIRE byte-level contract** — idempotence, metamorphic
equality across all six mutations, feature equality — because a consistently
broken output is still perfectly self-consistent. Only compiling it caught them.

I then built a token-count guard intended to catch the class systemically, and
**tested it by synthetically removing the `'0` rule. It did not fire.** Input
`'0` is 2 tokens; output `' 0` re-tokenises to the same 2 tokens. Same count,
same sequence, invalid Verilog. **No token-level check can detect a tokenizer
gap** — the tokenizer does not know the pieces had to stay adjacent. The guard is
kept only for the narrower "a construct vanished" class, with its limitation
written into the code, and `--check-traces` over the full corpus is now mandatory
in the frozen protocol.

We note this is the paper's own thesis recurring in our tooling: the reward was
self-consistent and wrong, and so was the canonicaliser. Both needed an external
referent — Vivado in one case, a compiler in the other.

## What preregistration.json freezes

Environment (canonical machine + library versions — `knn12` rho differed 0.543 vs
0.604 across machines on deterministic code, so this is pinned); sha256 of seven
load-bearing scripts; canonicaliser version/backend/contract; the 15 `rf_struct`
features **with provenance**; training-row manifest (229 rows, holdout excluded);
the selection rule; Check A thresholds and result; Check B's
reward-resolution-failure definition; sealed split (20 designs, seed 20260813,
`opened: false`); three arms × two seeds matched on non-flat updates; per-group
logging requirements; evaluation protocol; five conjunctive success criteria;
stop rules.

Two provenance disclosures are written into the file itself:

- **The loop features (`n_loops`, `loop_bound_max`, `loop_bound_sum`) were added
  AFTER Check A failed at 30.4% on med.** On training data only, before freeze,
  on your instruction to fix the representation on a NO-GO. Two med5 candidates
  differing only in `i < 5` versus `i < 4` measured 60.4 and 38.3 MHz with
  identical feature vectors. med moved 30.4% → 21.7%; the threshold did not move.
- **RandomForest was noticed while inspecting v8 outputs.** The file states this
  makes it a post-hoc hypothesis that the sealed split exists to test.

## Six questions, then we execute

1. **Is anything missing from the freeze?** Once the sealed split is generated we
   cannot add a pinned value without it being an amendment. Look specifically for
   things we would be tempted to choose later.

2. **med at 21.7% is a marginal pass against a 25% ceiling**, on the one family
   GRPO already gains nothing on. Options: (a) accept, report as marginal, and
   flag med first if the prospective run behaves oddly; (b) exclude med from the
   RL design list and report five families for competence but four for the repair
   experiment; (c) something else. We lean (a). Your call.

3. **Are five CONJUNCTIVE success criteria too strict?** As written, all must
   hold: exact invariance, improvement over SFT in both regimes, in both seeds,
   retaining a substantial part of the original gain, and no late divergence. A
   partial outcome seems more likely than a clean sweep, and we would rather
   predefine how to report "improved in interpolation only" or "improved in one
   seed" than decide afterwards. What is the right predefined taxonomy?

4. **Is the RandomForest disclosure sufficient?** The residual concern is that
   the reward class was chosen after looking at the failure it is meant to fix.
   The sealed split makes the TEST prospective, but the HYPOTHESIS is post-hoc.
   Is disclosure enough, or does the design require a reward chosen blind (e.g.
   fixed by the training-side CV rule alone, whatever it selects)?

5. **Sample budget.** 24 samples/design/seed, 48 per arm per design, 20 sealed
   designs, paired design-level bootstrap CIs. Is 20 designs enough to resolve
   the effect sizes we are looking for, given design is the unit of independence
   and there are only 5 families?

6. **Does the correctness-only control need two seeds?** Three arms × two seeds
   is six GRPO runs. If budget forces a cut, our order would be: keep both
   `rf_struct` seeds, keep both `grpo_mlp_original` seeds, drop correctness-only
   to one. Agree, or is the control worth more than the original-MLP replication?

Unless you object, next steps are: generate and seal the 20-design split; extend
`grpo_oracle.py` with the per-group logging; train; Vivado once; stop. Manuscript
drafting starts in parallel now.

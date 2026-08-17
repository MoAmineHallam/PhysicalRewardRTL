# Is this the strongest story this evidence supports?

**Pull first.** `git pull` — the branch is at `133a941`. Read, in this order:
`preregistration.json` (revision 2, frozen), the last two sections of
`MASTER_REFERENCE.md`, `canonicalize.py`, `analyze_sealed.py`, and
`sealed_split.json`. The sealed split is generated and committed; its results
have not been looked at and no arm has trained yet.

This is not a request for more experiments. The methodology is frozen with stop
rules and the sealed split is sealed. This is a request to pressure-test the
NARRATIVE before ~75% of a manuscript gets written around it, and specifically
to tell us whether we are framing the strongest claim our evidence supports or a
weaker one.

---

## 1. Where the project started, and why that is no longer the paper

RTLCoder-6.7B, fine-tuned to generate FPGA DSP-accelerator RTL (FIR, FIR-ramp,
polynomial/Horner, IIR, median) that is functionally correct and fast.
Correctness comes from a per-design I/O-equivalence oracle; speed from
correctness-gated GRPO where `reward = clamp(surrogate_Fmax, 5, 500)` if
oracle-correct, else 0.

It worked, on real EDA and real silicon:

- SFT correctness 3.5% → 84.7%; the 5-family model reaches 94.8% on train-split
  competence.
- Held-out interpolation **+252%** real-Vivado Fmax with correctness rising
  91.1% → 94.6%; extrapolation **+265%**.
- **Silicon: 2.3–3.4× measured** on PYNQ-Z2, canary-attributed, run-to-run
  spread 0.0.
- One GRPO sample ≈ a perfect-selector best-of-48 SFT samples, so the gain is a
  policy shift, not better sampling.
- VerilogEval control: GRPO adds zero regression beyond SFT.
- HLS baseline: our NL-spec GRPO reaches 0.96× expert-HLS throughput (geomean),
  20–150× naive HLS.
- cordic remains a replicated negative result: 0% at 7B. We report it.

Three independent harsh reviews converged that this, as the headline, is
incremental against the VeriReason / ChipSeek-R1 class of 2025 work. We accept
that. It is now the setup, not the contribution.

## 2. What we actually found — the two-phase result

Reconstructing the v8 training trajectory against real Vivado at each
checkpoint, the run splits cleanly in two.

**Phase 1, to roughly step 100 (77 optimizer updates): the reward taught real
hardware.** Real post-implementation Fmax rose 81 → 240 MHz. Not a proxy
number — Vivado.

**Phase 2, updates 205 → 276 (checkpoints s300 → s400): the reward and reality
came apart.** Predicted reward rose **+281 MHz** while real Fmax moved
**−1 MHz**. Over the same interval the generated RTL gained ~20 lines and ~20
line-initial nonblocking assignments *while its token count fell*. The code got
smaller and more spread out.

**The mechanism is four lines of regex.** The deployed surrogate read `n_lines`,
and `nb_assign` was `^\s*\w+(\[..\])?\s*<=` with MULTILINE — it counted
assignments that BEGIN A LINE. Written packed as `a0 <= 0; a1 <= 0; a2 <= 0;`
that scores 1. Split one per line it scores 3. **Identical hardware.** The
policy found the newline.

**Attribution: 101.2% of the phase-2 reward jump disappears when every candidate
is re-scored on a layout-canonical form.** And without any modelling at all,
there are candidate pairs from different checkpoints with **byte-identical token
streams and materially different rewards** — same tokens, same hardware,
different score. That is the whole claim with no statistics in it.

We also have a second, cruder exploit already documented: the surrogate was
driven to predict **∞** for poly4 (exp overflow) and 441–566 "MHz" for firr8,
above any physically achievable value on this device. Fixed by clamping in log
space.

## 3. Why we think this is worth a paper, and the argument we want tested

**The reward hacking literature cannot measure the true objective. We can.**

In RLHF, reward overoptimization (Gao, Schulman, Hilton, arXiv:2210.10760) is
studied against a *gold reward model* — another proxy. Nobody can measure a
human's true utility. Our objective is **maximum clock frequency**, which is
physically measurable: place-and-route it, or run it on the board and sweep the
clock until it fails.

So this is a setting where reward overoptimization can be **quantified against
ground truth rather than inferred**. We can say "the reward gained 281 MHz and
the hardware gained −1 MHz" as a measurement, not an interpretation. We believe
that is the paper, and that the RTL-generation setting is incidental to *why it
matters* while being essential to *why it is possible*.

**The spine we want to build the paper on: self-consistency is not validity.**
We have four independent instances, and this is the part we think is unusually
clean:

1. **The reward** passed every offline metric we had — leave-one-design-out
   Spearman 0.959, top-1 correct on 15 of 17 designs — while being exploited.
   Detecting it required Vivado.
2. **The canonicaliser built to fix it** passed idempotence, metamorphic
   equality across all six mutations, and feature equality — while emitting
   **invalid Verilog**, twice (`'0` → `' 0`; `$signed` → `$ signed`). A
   consistently broken output is perfectly self-consistent. Detecting it
   required a compiler.
3. **The guard built to catch that class provably does not fire.** We
   implemented a token-count check and tested it by synthetically removing the
   `'0` rule. It did not trigger: `'0` is two tokens, `' 0` re-tokenises to the
   same two. No token-level check can detect a tokenizer gap, because the
   tokenizer does not know the pieces had to stay adjacent.
4. **And once more while building the sealed split, this week.** Eligibility
   asked "does this design's reference implementation fit the generation
   budget?" using one arbitrary reference style, and rejected the *entire*
   median extrapolation pool. `med_comb`, a fully unrolled comparator network,
   needs 6,670 tokens at W=13. `med_sort` expresses the same filter in ~680 and
   is the style that made the family learnable at all. The designs were always
   answerable; the witness was wrong. The rule now asks whether *any* correct
   style fits.

Each time, an internally coherent check certified something false, and only an
external referent — Vivado, a compiler, a second implementation — caught it. We
think that is a stronger and more transferable claim than any Fmax number in
section 1.

## 4. The prospective repair, already frozen

Reward v2: canonicalise (layout-blind), 15 structural features, RandomForest on
log-Fmax, clamped. `n_lines` deleted outright — it is the exploited channel and
has no hardware meaning.

Validated before use: 489/490 candidates canonicalise, compile, and produce
identical sampled traces (256 vectors, seeds 1 and 2); 0 collisions; 1 explicit
rejection. Check A — can the canonical form still ORDER candidates? — 389
materially-different within-design pairs, 5 unorderable (1.3%), 0 unsafe
semantic merges. **GO.**

Then a preregistered prospective test: 20 sealed designs (10 interpolation, 10
extrapolation, all five families, seed 20260813, zero rejections), three arms ×
two seeds matched on non-flat optimizer updates, one Vivado pass, an eight-label
outcome taxonomy fixed in advance, and stop rules. Full SHA-256 on the model,
adapter, reward artifact and labelled rows.

**We have already recorded two predictions before any arm trains**, so they
cannot be offered later as explanation:

- The loop features added to repair the median family carry **almost zero
  importance** in the fitted model (`n_loops` 0.0001). They made candidates
  *distinguishable* — which is what Check A measures, and med moved 30.4% →
  21.7% — but distinguishable is not correctly *ordered*.
- Within-design Spearman is **mean 0.555, median 0.816**, with `med3` at
  **−1.00** and `fir32` at −0.87. Only the ORDER inside a sampled group drives
  the GRPO gradient, so 0.555 is the number that matters, not the pooled 0.885.
  A null is a live outcome and the taxonomy already names it.

## 5. Everything we know is weak, stated plainly

- **The prospective result is unknown.** See question 1 below; it is the one
  that matters most.
- 20 designs = **10 independent units per regime**. Paired design SD ≈ 66 MHz
  (interp) / 59 MHz (extrap); 80%-power detectable effect ≈ 60–65 MHz.
  Underpowered below ~40 MHz. Two designs per family × regime means family
  results are **descriptive only**.
- Fmax is **WNS-derived from a single implementation run**, not timing closure.
- Invariance is **LEXICAL**, not canonical hardware structure. The yosys/RTLIL
  backend reached only 33/60 on the byte contract and is future work.
- The sealed designs are unseen **parameterisations of the same generator
  families** — not cross-template generalisation. Specs are template-generated
  natural language.
- **RandomForest is a post-hoc hypothesis**, noticed while inspecting v8. The
  sealed split makes the test prospective; it does not make the hypothesis
  blind, and we say so.
- The median family is a predeclared **high-risk stratum** and it drew W=19 and
  W=21 against a trained range of {3,5,9} — a very aggressive extrapolation.
- Trace equality is **sampled**, not formal equivalence. Compilation catches
  syntax only; a rename that merged two signals would compile cleanly.

## 6. The questions

1. **Does the paper survive a null?** If the prospective arms return
   `stable_null` or `reward_resolution_failure`, our intended reading is that it
   gets *stronger* in one specific way: "removing the exploited channel does not
   restore a usable reward, because the deeper failure is that layout-blind
   structural proxies cannot order candidates *within* a design" — with
   within-design rho 0.555 as the mechanism and Check A's med 21.7% as
   corroboration. Is that honest, or is it a rationalisation we have prepared in
   advance so that no outcome can disappoint us? We would rather hear the second
   answer now than believe the first one for three months.

2. **Which framing is strongest?**
   (a) A reward-validity / measured-Goodhart paper, with RTL as the setting that
   makes ground truth available — our current preference.
   (b) An evaluation-methodology paper: a gold standard for evaluating
   LLM-generated hardware, where the narrow domain is what makes per-design
   oracle + silicon rigor possible, and the hacking case study is the flagship
   demonstration.
   (c) The original capability paper with hacking as a section. We think (c) is
   dead. Is (a) actually stronger than (b), or are we over-weighting the finding
   because we found it?

3. **Is "we can measure the true objective, RLHF cannot" as strong as we think?**
   It is our central novelty claim. What is the best counterargument — that
   Fmax-vs-proxy is a much easier problem than human-preference-vs-proxy and
   therefore says less about the hard case? That single-run WNS is not really
   ground truth? Something we have not thought of?

4. **Is the four-instance self-consistency spine compelling or does it read as
   an engineering diary?** Instances 2, 3 and 4 are failures in OUR OWN TOOLING,
   not in the model. We think that is what makes them credible — nobody
   fabricates their own tool being wrong twice — but it could equally read as
   "these authors kept making mistakes." How would you write it so it lands as
   methodology rather than confession?

5. **Venue, given the reframing.** Earlier guidance was FPGA / FCCM / MLCAD for
   the silicon-validated capability paper, with ICCAD as the CCF-A shot. If the
   centre is now reward validity with silicon-grade ground truth, does that
   change the target? Is there an ML-side venue where the measured-Goodhart
   result is the contribution and the hardware is the apparatus?

6. **What is missing that we would regret?** One thing only, and it must be
   cheap: no new corpora, boards, EDA tools, reward architectures or mutation
   families before submission — the stop rules forbid them and we will not break
   them. Analysis of artifacts we already have is in scope.

Six arms are about to start training. Answers to 1 and 2 change what gets
written this week; the rest change how it is written.

# PROJECT MASTER REFERENCE — Hardware-Grounded RL for RTL Generation + Verilog MAS

> Single source of truth for the whole project. Two tracks live in the same
> server folder `/zeng_gk/Amine/mas/`:
> 1. **MAS** — a multi-agent autonomous Verilog→FPGA system (supervisor's original vision).
> 2. **Hardware-grounded RL** — fine-tuning an RTL LLM with rewards from a real
>    PYNQ-Z2, plus the simulation-vs-silicon "reward gap" study (the novel core).
>
> The RL track lives in the `fpga/` subfolder (git repo); the MAS lives in the
> parent. They are currently SEPARATE (the MAS uses base RTLCoder, not the
> fine-tuned model). Last updated: 2026-06-14.

---

## 0. TL;DR — what exists and what it's worth (honest provenance)

| Thing | State | Measurement basis | Headline result |
|---|---|---|---|
| MAS (design+verification agents) | works (server) | server run | self-correcting RTL gen + sim verify |
| MAS (synthesis→deploy loop) | **coded, never run end-to-end** | — | no MAS bitstream ever produced |
| Hardware golden capture (966 designs) | done | **silicon-measured** | 966 designs bit-exact vs board, 0 mismatch |
| RL dataset | done | **silicon-grounded** (silicon goldens, sim scoring) | 9,660 candidates, mean reward 0.858 |
| GRPO fine-tune (grpo_v3) | done | simulation (VerilogEval) | pass@1 **+2.2pp**, compile +1.4pp vs base |
| Sim/silicon gap — tier 1 | done | **silicon-measured** | 3 synth + multiple impl failures confirmed |
| Sim/silicon gap — tier 2 | done (1 batch) | **silicon-measured** | ≈1.6% gap; simulation is faithful for this catalog |
| PPA spread characterisation | done | **Vivado estimate (CAD)** | headroom concentrated; mean spread small on trivial catalog |
| PPA offline RL (grpo_v4) | done — **FAILED** | Vivado estimate (CAD) | KL explosion, correctness degraded |
| Best-of-N PPA reranking | done | **Vivado estimate (CAD)** | +3.6% avg LUT, −48% on satadd12b |
| Silicon Fmax measurement | **VALIDATED + catalog characterised (Phase 0–2)** | **silicon-measured** | 5 designs 45–125 MHz, ±0 repeatable; Vivado proxy ρ≈0.9, ratio 1.5–2.2× |
| Accelerator-block catalog | **BUILT + broadened (Phase 1)** | Vivado + iverilog + silicon | 13 designs / 3 families (FIR×5, poly×5, CORDIC×3); correctness-verified |

**Root problem with all PPA numbers:** the 966-design catalog consists of trivial primitives (counters, adders, comparators). These have no real architectural degrees of freedom, and their Fmax is ~400 MHz — above the Z2's programmable clock ceiling (~250 MHz). The PPA numbers above are Vivado CAD estimates on a catalog where silicon Fmax is unmeasurable. That is why the gains are modest. **This must be fixed before any more RL or PPA experiments.**

**Baseline to beat:** RTLCoder on VerilogEval-156 = **37.2% functional / 68.6% compile** (greedy).

---

## 1. INFRASTRUCTURE & ACCESS

### Machines
- **GPU server** — all training, dataset building, catalog generation.
  - SSH: `ssh root@10.251.171.18 -p 30324`
  - conda env: `mas`
  - 2× Tesla V100S-PCIE-32GB (NO bf16 hardware → use fp16)
  - Project root: `/zeng_gk/Amine/mas/`
  - NO Vivado, NO board access.
- **Laptop** — `C:\Users\Amine\mas\fpga-repo` (the git checkout; NOTE: the repo is
  in `fpga-repo`, NOT `C:\Users\Amine\mas\fpga`).
  - Has **Vivado 2023.1** at `C:\Xilinx\Vivado\2023.1\bin\vivado.bat`
    (add to PATH: `$env:PATH += ";C:\Xilinx\Vivado\2023.1\bin"`)
  - Has the **PYNQ-Z2 board** (board connects to laptop only).
  - PowerShell loop syntax: `for ($k=0; $k -le 7; $k++) { ... }` (NOT cmd `for /L`).
- **PYNQ-Z2 board** — Zynq-7020, `xc7z020clg400-1`.
  - SSH: `ssh xilinx@192.168.2.99` (password `xilinx`)
  - PYNQ lives in a venv: `/usr/local/share/pynq-venv/bin/python3`
    (run hardware scripts as `sudo /usr/local/share/pynq-venv/bin/python3 ...`)
  - Notebook dir: `/home/xilinx/jupyter_notebooks`
  - Runtime clock control works: `from pynq import Clocks; Clocks.fclk0_mhz = 100`
    (snaps to nearest achievable PLL freq, e.g. 150→142.857).
  - Power telemetry: IRPS5401 PMBus; **VCCINT current pinned at 0.5 A (too coarse
    for cell-level power)** → measured-power reward NOT viable on this board.
- **PYNQ-ZU board** (TUL, Zynq UltraScale+ `xczu5eg-sfvc784`) — available but NOT used.
  - Has PMBus power rails (`get_rails()` works) but VCCINT telemetry also too coarse.
  - Only worth using later for cross-part **Fmax** experiments, not the gap study.

### Bridge
- Server ↔ laptop: **git** (repo `moaminehallam/fpga`, branch
  `claude/amazing-hopper-ytsbvr`).
- Laptop ↔ board: **scp** / SSH (`xilinx@192.168.2.99`).

### Models available on server (`/zeng_gk/Amine/mas/`)
- `rtlcoder/` — the base RTL LLM (7B), the one being fine-tuned.
- `qwen2.5-coder-7b-instruct/`, `qwen3-coder-30b/`, `qwen3.6-35b/` — other LLMs
  (qwen3.6:35b is the MAS reasoning model, served via Ollama).
- HuggingFace offline: `export HF_HUB_OFFLINE=1`; mirror if needed:
  `os.environ["HF_ENDPOINT"]="https://hf-mirror.com"`.

---

## 2. TRACK A — THE MAS (Multi-Agent System)

Location: `/zeng_gk/Amine/mas/` (parent folder, outside the git repo).
Architecture: Redis pub/sub message bus; agents run as threads in `main.py`.

### Files
- `main.py` — launches the 4 agents as threads, submits a task via Orchestrator.
- `orchestrator.py` — parses request (part/clock), publishes to `verilog_design`.
- `message_bus.py` — thin Redis pub/sub wrapper (`send`/`subscribe`/`listen`).
- `llm.py` — LLM interface:
  - `coder_call()` → **base RTLCoder** (local, `RTLCODER_PATH="rtlcoder"`), code gen.
  - `reasoning_call()` → qwen3.6:35b via Ollama (`http://localhost:11434`), reasoning/fixes.
- `agents/verilog_design_agent.py` — RTLCoder generates RTL, `fix_rtl()` regex
  cleanups, iverilog pre-check, → verification.
- `agents/verification_agent.py` — LLM testbench gen, iverilog/vvp sim, checks
  `SIMULATION_PASS`; on fail loops back to design with error log (≤3 retries).
- `agents/synthesis_agent.py` — generates Vivado Tcl (IP package → PS7 + AXI-DMA
  block design → synth → impl → bitstream), warning-fix via reasoning LLM.
- `agents/deployment_agent.py` — paramiko SSH to board, upload `.bit`/`.hwh`,
  load overlay, check `VALIDATION_PASS`.

### Workflow
`Orchestrator → DesignAgent → VerificationAgent (retry loop) → SynthesisAgent → DeploymentAgent`
Channels: `verilog_design`, `verification`, `fpga_synthesis`, `deployment`, `done`.

### Outputs
- `generated/<task_id8>.v` + `_tb.v` — RTL + testbenches the MAS produced (exist).
- `mas_projects/<uuid>/synth.tcl` — synthesis scripts (10 runs; **only synth.tcl,
  no built projects, NO bitstreams**).

### CURRENT STATE (honest)
- ✅ Design + Verification loop runs (RTL + testbenches generated on server).
- ❌ Synthesis→impl→deploy NEVER ran end-to-end: `SynthesisAgent` skips when
  `shutil.which("vivado")` is None, and the server has no Vivado.
- ❌ No MAS bitstream ever produced; board deployment never executed via MAS.
- ❌ No RL-PPA agent (proposal's 6th agent); synthesis uses LLM warning-fixing, not RL.
- ⚠️ MAS uses **base RTLCoder**, NOT the fine-tuned model — the two tracks are unlinked.
- Cheap integration win (not yet done): point `llm.py` `coder_call` at base +
  `grpo_v3` adapter so the Design Agent uses the fine-tuned model.

### Run the MAS
```bash
cd /zeng_gk/Amine/mas
python main.py "Design a 4-bit synchronous up-counter ... 100 MHz."
```
(Needs Redis running. Synthesis/deploy only work where Vivado + board exist.)

---

## 3. TRACK B — HARDWARE-GROUNDED RL (the novel core)

Location: `/zeng_gk/Amine/mas/fpga/` = git repo `moaminehallam/fpga`,
branch `claude/amazing-hopper-ytsbvr`. Also on laptop at
`C:\Users\Amine\mas\fpga-repo`.

### The core idea
Prior RL-for-RTL rewards candidates in a **simulator**. We reward against **real
silicon**: capture each design's golden waveform once on the PYNQ-Z2, then score
LLM candidates against that silicon-certified golden.

### Pipeline stages (see `fpga/PIPELINE.md`)
1. **Catalog** — `gen_designs.py` → `rtl_library/<name>/{design.v,golden.py,spec.txt}`
   + `rtl_library/manifest.json` (1004 designs, 42 families). **single source of truth.**
2. **Verify** — `verify_manifest.py --jobs 8` → iverilog checks design.v == golden_body.
   **1004/1004 PASS.**
3. **Batched bitstreams** — `gen_bitstream.py --batch 64` → 16 batches of 64 DUTs,
   `rtl/batches/{dut_top_bK.v, build_bK.tcl, batch_manifest.json}`. Uses
   `rtl/la_axi_wide.v` (6-bit sel LA).
4. **Build** (laptop Vivado) — `for k in 0..15: vivado -mode batch -source build_bK.tcl`
   → `rtl/batches/out_bK/system_bK.{bit,hwh}`.
5. **Capture** (board) — `capture_waveforms.py` → `rtl_library/<name>/waveform.npy`.
   **1004/1004 captured.**
6. **Validate** — `validate_hw.py --report hw_bad.json`. The stimulus counter
   free-runs (not reset on arm), so each capture is a window of the golden at
   unknown phase; validation does a phase search. **966 exact match, 0 mismatch,
   38 long-period** (true period 4M–4G, unverifiable in a 32k window — excluded,
   not failures). Training pool = `hw_bad.json["good"]` (966).
7. **RL dataset** — `build_dataset.py` → `fpga/dataset.jsonl`.
8. **GRPO + eval** — `grpo_train_v3.py` → `run_verilogeval_*.py`.

### KEY FILES (in `fpga/`)
| File | Purpose |
|---|---|
| `gen_designs.py` | generate the 1004-design catalog (NOTE: manifest `period` is WRONG for acc/mac — input period, not state period; never trust it for alignment) |
| `verify_manifest.py` | iverilog-verify every design.v == golden |
| `gen_bitstream.py` | pack 64 reference DUTs/bitstream + build Tcl |
| `rtl/la_axi_wide.v` | logic analyzer, 6-bit sel, AXI-Lite, 32768 samples |
| `capture_waveforms.py` | board-side golden capture → waveform.npy |
| `validate_hw.py` | phase-search validation of capture vs golden → hw_bad.json |
| `hw_bad.json` | `{good:[966], bad:[], long_period:[38]}` |
| `score_candidate.py` | score one candidate (iverilog sim vs golden, masked Hamming, best of shifts 0/1/2); `load_manifest`, `load_good_names`, `golden_from_body`, `make_tb`, `score_rtl`, `score_file` |
| `build_dataset.py` | generate N candidates/design with RTLCoder, score each → dataset.jsonl. fp16 single-GPU batched backend (`--backend local`, default) |
| `analyze_dataset.py` | per-design/family reward stats → `design_weights.json` (sampling weight ∝ reward std) |
| `grpo_train_v3.py` | GRPO on the 966-design pool, variance-weighted sampling, batched gen, in-process scoring, fp16(V100)/bf16(Ampere) auto, KL-to-base via adapter-disable. Run from `/zeng_gk/Amine/mas`: `python fpga/grpo_train_v3.py --steps 600 --group_size 8` |
| `run_verilogeval_ft.py` | VerilogEval with the fine-tuned model (greedy) |
| `run_verilogeval_passk.py` | VerilogEval pass@k (n samples, temp 0.8, chunked gen `--gen-batch 5` to avoid OOM) |
| `compare_passk.py` | paired per-problem comparison of two pass@k runs |

### Legacy / earlier versions (kept, superseded)
- `grpo_train.py` (v1, 7 hardcoded designs, SFT-warmstart), `grpo_train_v2.py`
  (v2, fresh LoRA, 7 designs), `sft_train.py` (SFT, abandoned — caused forgetting).

### DATASET ATTRIBUTES (`fpga/dataset.jsonl`)
9,660 records, one JSON/line:
`{"design": str, "family": str, "reward": float 0–1, "compile_ok": bool, "rtl": str}`
- reward = masked Hamming similarity vs silicon golden (0 if compile/sim fail).
- 966 designs × 10 candidates. Stats: mean reward 0.858, compile 0.960, perfect 0.704,
  314 saturated, 2 dead, 634 live.
- Hard families (low reward, where RL signal lives): shift/rotate, prienc, demux,
  lfsr, gray. Saturated: cmp, min/max, alu, counters.

### TRAINED MODELS (LoRA adapters, on server, OUTSIDE the repo — too big to push)
- `grpo_v3/` — final adapter (step 600). **This is the model to use/eval.**
  - checkpoints: `grpo_v3/step_{50,100,150,200,400}/`
  - NOTE: a bug dropped some checkpoints on flat-skip steps (fixed in current
    `grpo_train_v3.py`); step_300 was never saved.
- `grpo_v2/`, `grpo_out/` (v1), `sft_out/` — earlier, superseded.
- Logs: `grpo_v3_log.jsonl` (server), copied to `fpga/`.

### RESULTS SO FAR
**Training (in-loop):** rolling mean reward 0.80 → 0.94 over 600 steps; previously-
failing families (e.g. 16-bit rotates) learned. KL stayed tiny.

**VerilogEval-156, greedy (run-A-identical):** base 58/156 (37.2%) → grpo_v3 58/156
(37.2%). Same headline BUT 8 problems fixed / 8 broken; fixes cluster in trained
families (popcount, rotate, reversal, dff, counter). Distribution moved, argmax tied.
(diff saved as `fpga/greedy_flips.txt`.)

**VerilogEval-156, pass@k temp 0.8 (n=20, the real comparison):**
| metric | base | grpo_v3 | Δ |
|---|---|---|---|
| pass@1 | 32.3% | 34.5% | **+2.2** |
| compile | 65.6% | 67.0% | +1.4 |
| pass@10 | 49.6% | 50.3% | +0.7 |
- 5 problems base never solved that grpo_v3 does; 5 the reverse. Biggest gains:
  vectorr 2→17, count1k 5→17, popcount3 7→18, rotate100 5→13, wire_decl 13→20.
- **Interpretation:** RL **sharpened** (reliability up on near-misses) but didn't
  **expand** (pass@10 ≈ flat) — RL concentrates latent skills, doesn't add knowledge.
- Checkpoint test: step_200 WORSE than step_600 (pass@1 +0.7 vs +2.2) → training
  longer helped, late overfitting ruled out. **Keep step_600.**
- Files: `fpga/passk_base.jsonl`, `fpga/passk_grpo_v3.jsonl`,
  `fpga/passk_grpo_v3_s200.jsonl`.

**Honest framing:** modest but real and attributable. The functional reward, though
silicon-validated, is sim-equivalent (golden ≡ silicon for correct designs), so a
reviewer asks "why hardware?" → motivates the gap study below.

---

## 4. THE SIM/SILICON GAP STUDY (the "jackpot" experiment, IN PROGRESS)

**Claim:** all prior RL-for-RTL uses simulation rewards; we test whether simulation
agrees with silicon on real LLM candidates. Disagreements = something only hardware
reveals. Two tiers.

### Tier 1 — sim-valid candidates that can't exist on hardware (no board needed)
- **Synth failures (3/462):** compile in iverilog but fail Vivado synth even under
  SystemVerilog (`synth_check.tcl`): `c2_rotl12_3`, `c3_logical_rsh8`, `c4_logical_rsh5`.
- **Implementation failures (multiple-driver DRC):** synthesize but fail impl
  (register driven from two places — physically impossible). Found in batches 2/3/4.
  Harvested by `extract_build_fails.py`.
- These are gap cases: simulation rewarded RTL that hardware fundamentally rejects.

### Tier 2 — behavioral sim-vs-silicon on candidates that DO run (the real number)
- Pack candidates onto the fabric, capture, score vs golden on silicon, compare to
  the sim reward already in dataset.jsonl. Predicted big source: reset/init (sim
  shows X for reset-less regs; Xilinx GSR zeroes them → works on silicon).

### GAP-STUDY FILES (in `fpga/`)
| File | Purpose | Runs on |
|---|---|---|
| `gen_candidate_bitstream.py` | select candidates (stratified by reward), rename each module unique (`c<idx>_<design>`), write as `.sv`, pack 64/bitstream. `--exclude <fails>`, `--n`, `--seed` | laptop (Python) |
| `synth_check.tcl` | fast 1-session OOC synth screen → `synth.fails` + `.detail` | laptop (Vivado) |
| `run_ppa.py` | per-candidate full impl via `ppa_synth.tcl` → PPA + synth/impl fails (Lever 3 data) | laptop (Vivado) |
| `ppa_synth.tcl` | OOC synth+impl of one module → timing/area/power JSON | laptop (Vivado) |
| `extract_build_fails.py` | harvest impl-failure culprits from build logs → enlarge exclude list | laptop |
| `score_hw_candidates.py` | board capture + score each candidate vs golden → `cand_gap.jsonl` (pure pynq+numpy, no iverilog) | board |
| `analyze_gap.py` | disagreement rate, under/over-reward split, per-family, biggest divergences | anywhere |

### GAP-STUDY ARTIFACTS
- Generated: `rtl/cand_batches/` → `cand/<module>.sv` (candidate RTL, renamed to
  SystemVerilog), `dut_top_cbK.v`, `build_cbK.tcl`, `cand_manifest.json`
  (maps batch+local_sel → module, design, sim_reward, probe_mask).
- Built bitstreams: `rtl/cand_batches/out_cbK/system_cbK.{bit,hwh}`.
- `synth.fails` — exclude list (synth + impl failures).
- `cand_gap.jsonl` — `{module, design, family, sim_reward, hw_reward, gap}` per candidate.

### CURRENT STATE / RESULT (2026-06-15) — tier-2 is essentially NULL

**Two confounds were found and fixed; after fixing them the behavioral gap
vanishes.** History (do not quote the intermediate numbers — they were artifacts):
- First free-running capture (267 cand): looked like 14.2% gap. CONFOUND 1: the
  sim reward (3 registration shifts) and silicon reward (4096-offset phase search)
  used different scorers.
- `verify_gap.py` control (re-sim, identical scorer): 13/38 "survived", looked like
  4.9% sim-over-rewards in ALU/gray. CONFOUND 2: `hw_reward` phase search
  (max_phase=4096) is far too small for large-period designs (ALU is aperiodic);
  a perfectly-correct ALU window scores 0.57–0.78 under that scorer (proven by a
  golden-vs-golden test). The "defects" were alignment failures.
- **FIX: reset-on-arm capture** (LA `capturing` output → `dut_top` holds the
  stimulus counter AND DUTs in reset until capture; every capture starts at phase 0
  = `golden[0:N]`; scorer = small registration-shift search, no phase search).
- **Reset-on-arm cb0 (64 candidates), verify_gap clean result: 1/8 survive.**
  Sanity gate PASSED — correct candidates (sim=1.0) score hw=1.0; ALU now 1.0.
  The lone survivor `c1_cmp2b` (sim 0.92 vs silicon 0.79, ~0.13) is small and
  possibly residual. **Tier-2 behavioral gap ≈ 1.6%, tiny — simulation is a
  faithful behavioral proxy for this synthesizable synchronous-logic catalog.**

**Honest conclusion:** the "silicon catches hidden behavioral defects" jackpot is
NOT real for this design class. LLM RTL broken enough to behave differently is
caught earlier in TIER 1 (won't synthesize/implement); what survives to run is
clean, and sim predicts it faithfully. Hardware-necessity therefore lives in:
(1) tier-1 (sim-valid but unsynthesizable/unimplementable — real, alignment-free),
(2) physical PPA / silicon-Fmax (sim-impossible). NOT behavioral re-checking.
This negative tier-2 result is itself publishable (it scopes when sim suffices).

TODO to finalize: build cb1–7 and re-capture (reset-on-arm) for the full ~460-
candidate confirmation; inspect `caps/c1_cmp2b.npy` to classify the one survivor.

### RL-PPA RESULTS (2026-06-16) — physical-quality direction, fully measured
Pipeline: `gen_ppa_set.py` (correct candidates from dataset.jsonl, by family) ->
`run_ppa.py`/`ppa_synth.tcl` (Vivado OOC synth+impl -> Fmax/LUT) -> `analyze_ppa.py`
(spread), `grpo_train_v4.py` (offline PPA GRPO), `eval_ppa_gen.py` (generate+score),
`bestofn_ppa.py` (reranking gain). All PPA metrics are Vivado estimates (CAD), not
silicon — clock-sweep Fmax not usable here (designs ~400 MHz, above the Z2 ceiling).

1. **Headroom exists but is CONCENTRATED.** Functionally-correct candidates of the
   same design vary physically only where coding style matters: satadd12b 13–38 LUT
   (236–410 MHz), free-running counters 2–20+ LUT. Multipliers: ZERO spread (`*` maps
   identically). Simple/idiomatic designs: zero spread. Mean LUT spread ~1.3 (diluted).
2. **Naive offline RL toward PPA FAILS (negative result).** `grpo_train_v4` (reward =
   timing_w·Fmax − area_w·LUT, group-relative, KL to base) over-optimised: KL ran to
   ~7 by step 400, and even step_100 DEGRADED functional correctness (mod108_counter
   0/8, mod152 1/8 vs base 8/8, 6/8). Cause: reward had no correctness term, so the
   model memorised lean candidates' tokens and lost correctness generalisation.
3. **Best-of-N reranking captures it safely.** Keep only correct generations, pick the
   leanest: **+3.6% area / +1.2% Fmax averaged over 80 designs**, but **−48% LUT on
   satadd12b (25→13), −82% on counter15b (11→2)** on the headroom subset. Never hurts
   correctness (selects among correct outputs only). This is the robust deliverable.

Honest verdict: as a standalone PPA contribution this is MODEST (concentrated headroom,
mostly idiomatic-vs-clumsy coding; avg gain small). The project's strength is the
silicon-grounded CHARACTERISATION (methodology + tier-1/tier-2 gap findings + this PPA
characterisation incl. the RL negative result), not a flashy optimisation number.

### EXACT COMMANDS (gap study, reset-on-arm)
```powershell
# laptop, in C:\Users\Amine\mas\fpga-repo
git pull
python gen_candidate_bitstream.py --dataset dataset.jsonl --n 512 --exclude rtl\cand_batches\synth.fails
$env:PATH += ";C:\Xilinx\Vivado\2023.1\bin"
for ($k=0; $k -le 7; $k++) { vivado -mode batch -source rtl\cand_batches\build_cb$k.tcl }
# stage bitstreams + scripts + rtl_library/manifest.json, scp to board ~/gap_study
# board: cd ~/gap_study; sudo /usr/local/share/pynq-venv/bin/python3 \
#   score_hw_candidates.py --bit-dir rtl/cand_batches \
#   --manifest rtl/cand_batches/cand_manifest.json --out cand_gap.jsonl --save-dir caps
# server (iverilog): python verify_gap.py --gap cand_gap.jsonl --dataset dataset.jsonl
```

---

## 5. THE THREE RL OBJECTIVES (don't conflate them)

| # | Objective | Question | Hardware signal | What it improves |
|---|---|---|---|---|
| 1 | Functional correctness (current GRPO) | does the RTL behave right? | waveform match | the code generator |
| 2 | Sim/silicon gap (the study) | does simulation judge correctly? | sim vs silicon disagreement | a finding about reward validity |
| 3 | PPA (supervisor's RL-PPA agent; "Lever 3") | is it fast/small/low-power? | measured Fmax/area/power | optimization OR generation |

- Supervisor's RL-PPA = #3 (learns optimization *strategies* on correct RTL).
- My current work = #1 + #2 (orthogonal to PPA — a design can be correct-but-slow).
- They are NOT interchangeable. Overlap is only on #3, where "learned generation
  (mine) vs learned optimization (his)" could be compared head-to-head.

---

## 6. PAPER STRATEGY & DECISIONS

- **Don't chase absolute VerilogEval SOTA** (50–70% = 13B–70B models + huge SFT;
  unreachable on 7B/V100). Compete on a NEW signal, not the leaderboard.
- **Core novelty:** first RL reward grounded in real silicon + the sim/silicon gap.
- **Strengtheners (in value order):** (1) the gap-study number; (2) a 2nd base model
  (DeepSeek-Coder-6.7B / CodeLlama-7B) for generality; (3) catalog expansion to the
  families both models fail (FSMs, combinational always/case, truth tables — the
  VerilogEval 0/20 cluster: lemmings, gshare, fsm_ps2data); (4) silicon-Fmax/PPA reward.
- **Generality argument:** mechanistic + multi-TOOL (iverilog vs Vivado vs Yosys),
  NOT multi-board. Gap mechanisms (multiple-driver, SV-vs-Verilog, GSR reset) are
  tool/fabric-general, not board quirks.
- **Reconcile with supervisor:** present the silicon-grounded RL as the rigorous core
  of his MAS's Design + Verification (+ future PPA) agents — "paper 1 = the science,
  MAS = the system it feeds." Name the divergences honestly (no RL-PPA agent yet,
  general designs not Transformers, MAS hardware loop unrun).
- **Abandoned:** measured-power reward (PMBus telemetry too coarse on both boards);
  SFT warm-start (caused forgetting).

### Citations: verify before use
ChipMATE and VFlow remain UNVERIFIED -- no public record found; do not cite.

CORRECTED 2026-08-11: **ChipSeek-R1 is REAL** and this list was wrong about it.
arXiv:2507.04736, Chen, Chang, Li, He, Chen, Li, Wang, Xu, Han, Wang. Note the
paper was retitled in a later version to "ChipSeek: Optimizing Verilog
Generation via EDA-Integrated Reinforcement Learning" -- check which title the
version we cite carries before camera-ready. It is cited in the preprint and is
one of the two works that preempted the original "correctness-gated GRPO makes
fast RTL" framing (the other being PPA-RTL, DOI 10.1109/DAC63849.2025.11132897).
Verify every SOTA number against the original paper before quoting.

---

## 7. HARD-WON LESSONS / GOTCHAS

- **V100 has no bf16 hardware** → use fp16 (bf16 is emulated, ~10–20× slower).
- **Don't shard the 7B across both GPUs** (`device_map="auto"`) for gen — ping-pong
  waits; use single GPU `{"":0}` + batched `num_return_sequences`.
- **Manifest `period` is WRONG for acc/mac** (input period, not state period) — never
  trust it for alignment/trimming.
- **Free-running counter** in dut_top is NOT reset on LA arm → captures are golden
  windows at unknown phase → must phase-search.
- **Candidate `.sv` extension** is required so Vivado reads them as SystemVerilog
  (Verilog-2001 mode rejects `int`, inline loop vars, logic-driven-by-assign — all
  valid SV the candidates use). `set_property file_type` via filter was unreliable.
- **Batch build dies if ANY candidate fails synth/impl** → pre-screen + `--exclude`,
  or skip the failed batch (capture is robust to missing bitstreams).
- **PYNQ is in `pynq-venv`**, not system python → `sudo /usr/local/share/pynq-venv/bin/python3`.
- **pass@k OOM** on long-prompt FSM problems at n=20 wide → `--gen-batch 5` chunks gen.
- **Laptop repo is `fpga-repo`**, not `fpga`. **Vivado not on PATH** by default.
- **Never use heredocs/echo for Verilog or long base64 on the server** (terminal
  line-length splits them). Verify ASCII-clean before base64.
- **git push rejected** (someone/webhook advanced remote) → `git pull --rebase` then push.

---

## 8. HONEST PROVENANCE OF ALL RESULTS TO DATE

The table below labels every number in this project by its actual measurement basis.
**Do not cite any of these numbers as "silicon-measured" unless the row says so.**

| Result | Value | Measurement basis | Status |
|---|---|---|---|
| 966 designs captured, 0 mismatch | 966/966 bit-exact | **SILICON** (PYNQ-Z2 board) | ✅ Real, validated |
| Tier-1 gap: 3 synth failures | 3 of 462 candidates | **SILICON** (Vivado synth/impl on laptop) | ✅ Real |
| Tier-1 gap: multiple-driver impl failures | several candidates | **SILICON** (Vivado impl DRC) | ✅ Real |
| Tier-2 gap after confound fixes | ~1.6% (1/64 candidates) | **SILICON** (board capture, reset-on-arm) | ✅ Real; negative result |
| GRPO v3 pass@1 +2.2pp | 32.3% → 34.5% | **simulation** (VerilogEval iverilog) | ✅ Real, not silicon |
| GRPO v3 compile +1.4pp | 65.6% → 67.0% | **simulation** | ✅ Real, not silicon |
| PPA spread on 300-candidate pool | mean LUT spread ~1.3 | **Vivado estimate (CAD)** | ✅ Measured; but catalog too trivial for silicon Fmax |
| grpo_v4 KL explosion / correctness degradation | KL→7, mod108 0/8 | **simulation** | ✅ Confirmed failure (documented negative result) |
| Best-of-N: +3.6% avg LUT reduction | 3.6% avg, −48% satadd12b | **Vivado estimate (CAD)** | ✅ Measured; catalog-limited |
| Silicon Fmax on current catalog | **NOT MEASURED** | — | ❌ Not possible: designs ~400 MHz > Z2 ceiling (~250 MHz) |
| Silicon Fmax on accelerator-class designs | **NOT MEASURED** | — | ❌ Not yet done; this is the gap to fill |
| GRPO with correctness-gated PPA/Fmax reward | **NOT TRAINED** | — | ❌ Never attempted |

**What is actually silicon-grounded right now:**
- The golden waveforms (scoring oracle) are real silicon captures.
- The functional reward training signal is silicon-grounded in the sense that correctness is
  defined by silicon-validated goldens — but the scoring itself is iverilog simulation against
  those goldens, which is equivalent for correct designs.
- Tier-1 and tier-2 gap measurements are real silicon measurements.
- Everything PPA-related is Vivado CAD estimates, **not hardware**.

**What is NOT real yet:**
- Silicon Fmax (no clock-sweep, no board measurement of timing).
- Any RL experiment that genuinely optimizes for a hardware-measured physical property.
- MAS end-to-end (synthesis→deploy never ran).

---

## 9. PHASED EXECUTION PLAN — THE REAL WORK

**Principle:** no phase produces numbers until its validation gate passes. If a gate fails,
stop, diagnose, fix the catalog/harness, and repeat before proceeding. Numbers from a failed
gate are worthless and must be discarded.

**Why this order (changed 2026-06-17):** the original draft built the whole accelerator
catalog FIRST and only then checked whether silicon Fmax is even measurable. That repeats the
old mistake — investing days of catalog work before knowing the measurement is real. The
silicon-Fmax harness is the single load-bearing, unproven assumption of this entire plan, so
**Phase 0 now proves the measurement on ONE hand-written design before anything else is
built.** If that fails, we learn it in half a day and pivot, instead of after a 3-day catalog.

**Two risks this plan explicitly guards against:**
1. **The harness measuring itself, not the DUT.** When `fclk0` is swept, the capture counter,
   the AXI interface, and the logic analyzer are all clocked by the same fabric clock. If the
   harness's timing fails before the DUT's, the "silicon Fmax" is the harness's, not the
   design's — a silent way to generate confident wrong numbers. Phase 0 must prove the DUT
   fails first.
2. **The framing risk.** Vivado static timing (STA) is signoff — the trusted number the field
   ships on. A reviewer will ask "why measure silicon Fmax when STA already exists?" Silicon
   typically runs 1.1–1.5× faster than signoff (room temp, -1 part), but nobody ships above
   signoff, so "sim can't produce it" is NOT a sufficient justification (it's not sim, it's
   STA). Treat the **Vivado-estimated, correctness-gated PPA result (Phase 3a) as the primary
   defensible contribution**; silicon Fmax (3b) is the novel bonus, not the foundation. If
   Phase 0 shows silicon Fmax is noisy/unviable, the paper still stands on 3a + the silicon
   characterisation (goldens, tier-1, tier-2) already in hand.

---

### Phase 0 — Silicon-Fmax Feasibility Spike (DO THIS FIRST, ~½–1 day)

**Goal:** before building any catalog, prove on ONE hand-written accelerator that silicon Fmax
is measurable, crisp, and attributable to the DUT. This is a go/no-go gate for the whole
silicon-Fmax direction.

**Steps:**
1. Hand-write ONE design with real timing depth and an expected Fmax well inside the Z2 range —
   a 16-tap direct-form FIR (8-bit data, 8-bit coeffs) is ideal: long MAC carry chain, ~120–180
   MHz, plenty of timing margin to fail before the harness does.
2. **Instrument the harness to prove it is NOT the bottleneck:** include a trivial "canary" DUT
   (e.g. a shift-register echo) in the same bitstream on the same clock. As you raise the clock,
   the FIR must diverge from its golden BEFORE the canary does. If the canary fails first (or
   with the FIR), you are measuring harness/capture timing, not the design — STOP and fix the
   harness (cross the DUT clock vs the capture/AXI clock, or pipeline the capture path).
3. Build bitstream (one FIR + one canary), sweep `Clocks.fclk0_mhz` 50 MHz up, reset-on-arm
   capture + score at each step (reuse `score_hw_candidates.py` scorer).
4. Record: FIR silicon Fmax, canary silicon Fmax, Vivado STA Fmax for the FIR.

**Validation gate (ALL must pass to proceed to Phase 1):**
- Canary Fmax > FIR Fmax by a clear margin (≥ 20 MHz) → the measured number is the DUT's, not
  the harness's.
- FIR silicon Fmax repeatable within ±5 MHz across 3 runs (re-arm; ideally a board power-cycle).
- FIR silicon Fmax / Vivado STA Fmax is in a plausible range (≈ 1.0–1.6×).
- **If the divergence point is noisy (jumps > ±10 MHz), or the canary fails first, or the ratio
  is implausible → silicon Fmax is NOT viable on this board. Do NOT build the accelerator
  catalog for silicon-Fmax. Pivot: the PPA story becomes Vivado-estimated only (Phase 3a), and
  the catalog is still built (Phase 1) but justified by Vivado-measured headroom, not silicon.**

**STATUS (2026-06-18): Phase-0 PASSED — silicon-Fmax measurement validated (GO).**
First real silicon Fmax number in the project, on the PYNQ-Z2:
- `fir16_8b` silicon Fmax = **90.9 MHz** (highest passing; first fail 100 MHz),
  **perfectly repeatable: 0 MHz spread across 3 runs.** SILICON-MEASURED.
- canary `echo8b` ran to **>200 MHz** (top of sweep, never failed) after the
  `la_axi_fast` (DEPTH=2048) fix → capture-harness ceiling > 200 MHz.
- canary margin = 109 MHz (≫ 20 MHz gate) → the 90.9 MHz is the DUT's own
  timing, NOT the harness. Vivado STA ≈ 46 MHz → silicon/STA ≈ 1.98× (high end
  of plausible room-temp-vs-worst-case-signoff; the canary rules out artifact).
- Harness lesson: la_axi_wide's 32768-deep distributed-RAM readback capped the
  harness at 111 MHz; the slim `la_axi_fast` (2048) lifted it past 200 MHz. Use
  `la_axi_fast` for all Fmax-sweep bitstreams.

Artifacts (all committed): `rtl_library/fir16_8b/`, `rtl_library/echo8b/`,
`rtl/la_axi_fast.v`, `gen_spike_bitstream.py`, `clock_sweep_fmax.py`,
board sweep log `rtl/spike/sweep_result.json`.
**Phase-1 (accelerator catalog) is now justified — proceed.**

---

### Phase 1 — Accelerator-Block Catalog (only after Phase 0 go/no-go)

**Goal:** replace the trivial-primitive catalog with designs that have real architectural
degrees of freedom AND run at Fmax in the 80–250 MHz range (within Z2's clock-sweep window).

**Why this is the fix:** a mod-counter or 2-bit AND has exactly one correct implementation
style — there is nothing to optimise, no architectural headroom, and no measurable silicon
Fmax. Accelerator blocks (FIR, CORDIC, systolic matmul, sorting net) have multiple
equivalent-but-physically-different implementations and run at 100–200 MHz on a 7-series part.

**Target designs (5–8 families, 3–5 parameterised variants each):**

| Family | Variants | Expected Fmax | Why this family |
|---|---|---|---|
| FIR filter (direct-form) | 8-tap, 16-tap, 32-tap; 8-bit, 12-bit coeff | 120–200 MHz | multiply-accumulate chain, pipelining has huge impact |
| CORDIC (iterative) | 8-stage, 16-stage rotation; sin/cos/atan | 100–180 MHz | shift-add chain, stage ordering matters |
| Systolic MAC array | 2×2, 4×4; int8, int16 | 80–160 MHz | local accumulator vs systolic vs tree — large area/Fmax spread |
| Bitonic sorting network | N=8, N=16 comparators; 8-bit keys | 150–250 MHz | comparator tree depth directly limits Fmax |
| Barrel shifter / priority encoder | 8/16/32-bit | 200–250 MHz | optional: gives continuity with current catalog |

(The Phase-0 FIR is the first catalog entry — it is reused, not thrown away.)

**Deliverable per design:**
1. `rtl_library/<name>/design.v` — parameterised RTL (at least one straightforward impl)
2. `rtl_library/<name>/golden.py` — Python reference model producing expected outputs
3. `rtl_library/<name>/spec.txt` — natural-language prompt spec for the LLM
4. `rtl_library/<name>/waveform.npy` — silicon-captured golden

**Validation gate (must pass before Phase 2):**
- `verify_manifest.py` on all new designs: 100% PASS (iverilog sim vs golden_body)
- `run_ppa.py` on at least 3 hand-written stylistic variants per design: Vivado reports
  Fmax in range [80, 250] MHz for at least 3 designs.
  If Fmax > 250 MHz for ALL variants → design is still too fast → replace it.

**Estimated effort:** 2–3 days (writing RTL + goldens; running Vivado to check Fmax range).

**STATUS (2026-06-18): Phase-1 catalog BUILT, gate PASSED.**
`gen_accelerator_catalog.py` → 5 designs in `rtl_library/` + 10 stylistic
variants in `rtl/accel_variants/` (+ `accel_manifest.json`).
- Correctness gate: all 5 designs + both variants each match their golden at
  100% under a two-sided shift (iverilog -g2012). fir16_8b regenerated with the
  silicon-validated coefficients/behaviour.
- Fmax-spread gate (Vivado OOC, `run_ppa.py --period 5.0`, laptop):

  | design | v0 (unpipelined) Fmax | v1 (pipelined) Fmax | note |
  |---|---|---|---|
  | poly4_8b | 61 MHz (2 DSP) | **191 MHz** (3 DSP) | clean 3.1× from pipelining |
  | poly6_8b | 39 MHz | **191 MHz** | clean 4.9× |
  | fir8_8b  | 82 MHz (LUT tree) | 80 MHz (8-DSP cascade) | ~flat |
  | fir16_8b | 48 MHz (LUT tree) | 38 MHz (16-DSP cascade) | v1 SLOWER |
  | fir32_8b | 25 MHz | 19 MHz (32-DSP cascade) | v1 SLOWER |

- **Silicon/Vivado ≈ 1.9× (validated on fir16: 48 Vivado → 91 silicon).** So the
  measurable-silicon window is Vivado ∈ ~[42,130]. In silicon terms the catalog
  spans ~48–360 MHz: slow ends measurable (fir16 91, fir8 156, poly4 116,
  poly6 74), headroom above (poly v1 ~360, above the 250 ceiling but a fine
  Vivado anchor).
- **Finding (kept, not hidden):** naive "register each product" pipelining of the
  FIRs forces all multiplies into a *linear DSP cascade* that is SLOWER than the
  balanced LUT adder tree (fir16 v1 38 < v0 48). Pipelining is NOT automatically
  beneficial — which is exactly why a search/RL over implementations is needed,
  not a fixed "add pipeline registers" rule. The scalar Horner chain (poly)
  pipelines cleanly (3–5×); the FIR MAC does not, naively.
- Verdict: in-window specs with large, real, pipelining-driven Fmax headroom
  exist and are demonstrated. **Phase-1 gate passed; proceed to Phase 2.**
- Files: `gen_accelerator_catalog.py`, `rtl_library/{fir8,fir16,fir32}_8b/`,
  `rtl_library/poly{4,6}_8b/`, `rtl/accel_variants/` (+ `ppa.jsonl`, laptop).

**BROADENED (2026-06-18, "more families before RL"):** catalog expanded to **13
designs / 3 families** for RL diversity — FIR ×5 (8/12/16/24/32-tap), poly ×5
(deg 3/4/5/6/8), **CORDIC ×3** (8/12/16 iterations; rotation-mode integer
shift-add, a genuinely different archetype — iterative, not MAC). All single-
input (x=cnt[7:0]) so they reuse the validated capture/sweep harness unchanged.
CORDIC uses pure integer signed arithmetic (Verilog `>>>` ≡ Python `>>`), so the
golden is exact. **Correctness re-verified: all 13 designs + both variants each
match their golden at 100% (iverilog, two-sided shift).**

**Vivado Fmax of the broadened set (run_ppa, 26 variants, laptop):** all 13
unpipelined refs land in the measurable silicon band (est. ×1.9 ≈ 48–160 MHz);
nothing dropped. Key per-family headroom (v0 unpipelined → v1 pipelined, Vivado):
- **CORDIC pipelines superbly** (pure-LUT shift-add, no DSP, retimes cleanly):
  cordic8 66→276 (4.2×), cordic12 43→284 (6.6×), cordic16 32→**275 (8.6×)**.
- **poly clean** across degrees: v0 28–84 → v1 191–200 (2.4–7×).
- **FIR pipelining still backfires** (DSP-cascade, every v1<v0) — the "hard"
  family where naive register-adding fails and a smart restructuring is needed.
So poly + CORDIC give clean large headroom; FIR gives hard headroom. Good RL mix.

**SILICON (broadened catalog, 14-DUT bitstream, 3 runs):** all 13 designs gate-OK,
repeatable (only poly5 ±9 MHz one-run jitter). silicon Fmax | Vivado-OOC v0 | ratio:
poly3 167|83.5|2.00 · fir8 125|81.5|1.53 · poly4 125|60.6|2.06 · cordic8 111|66.1|1.68 ·
fir12 91|61.7|1.47 · poly5 91|47.6|1.91 · poly6 77|38.7|1.99 · cordic12 71|43.2|1.65 ·
fir16 67|47.6|1.40 · poly8 59|28.5|2.07 · fir24 56|33.9|1.64 · cordic16 56|31.5|1.76 ·
fir32 45|25.4|1.79 (canary 200, never failed). Catalog spans 45–167 MHz.
- **Finding A — Vivado OOC is a faithful WITHIN-family proxy, poor CROSS-family.**
  Within FIR / poly / CORDIC, silicon and Vivado rankings agree perfectly
  (monotonic). But the ratio is family-specific (poly ≈2.0, CORDIC ≈1.7, FIR
  ≈1.4–1.5), so cross-family ranking scrambles. → **Good for the RL**: per-spec
  group-normalised Vivado reward operates within-family, where Vivado is faithful;
  headline numbers still need silicon.
- **Finding B — silicon Fmax is strongly build-context-dependent.** fir16:
  91 MHz standalone (Phase 0) → 77 (5-DUT) → 67 (14-DUT), ~27% compression with
  congestion. → RL candidates must be silicon-compared in a FIXED harness context.
- Board data: `rtl/catalog/catalog_fmax.json`.
**Broadening + silicon characterisation COMPLETE. Catalog ready for Phase 3.**
Pending optional: multi-input harness for matmul / sorting families.

### Phase 2 — Silicon Fmax Harness at Scale (only if Phase 0 said GO)

**Goal:** extend the Phase-0 harness to the full catalog and produce silicon Fmax for every
design (skip this phase entirely if Phase 0 was no-go; PPA stays Vivado-estimated).

**Method:**
1. Build bitstreams with the catalog designs (+ canary) via the existing `gen_bitstream.py`
   infrastructure.
2. Run `clock_sweep_fmax.py` per design; the canary must still fail last in every bitstream.
3. Silicon Fmax = highest frequency at which hw_reward ≥ 0.99 (reset-on-arm, small shift).
4. Tabulate silicon Fmax vs Vivado STA Fmax across the catalog.

**Validation gate (must pass before Phase 3b):**
- Canary fails last in every bitstream (re-confirm the Phase-0 guarantee at scale).
- Each design's silicon Fmax repeatable within ±5 MHz across 3 runs.
- Silicon/STA ratio consistent (within ±15%) across designs. If wildly inconsistent → harness
  bug or board PLL noise; debug before any RL.

**Estimated effort:** 1–2 days (board time + validation runs).

**STATUS (2026-06-18): Phase-2 DONE — whole catalog silicon-characterised.**
`gen_catalog_bitstream.py` (5 DUTs + echo canary, la_axi_fast, 200 MHz build) +
`sweep_catalog.py`. One board session, `--lo 30 --hi 200 --step 5 --runs 3`:

| design | silicon Fmax | Vivado v0 | ratio | gate |
|---|---|---|---|---|
| fir8_8b  | 125.0 MHz | 81.5 | 1.53 | OK |
| poly4_8b | 111.1 MHz | 60.6 | 1.83 | OK |
| poly6_8b | 83.3 MHz  | 38.7 | 2.15 | OK |
| fir16_8b | 76.9 MHz  | 47.6 | 1.62 | OK |
| fir32_8b | 45.5 MHz  | 25.4 | 1.79 | OK |
| echo8b   | 200 MHz (canary, never failed) | — | harness ref |

- **All SILICON-measured, 0 MHz spread across 3 runs, every gate OK** (each below
  the 200 MHz canary → the number is the DUT's, not the harness). Catalog spans
  45–125 MHz: good diversity, all measurable.
- **Finding 1 — Vivado is a good DIRECTIONAL but not faithful proxy.** Silicon/
  Vivado ratio is NOT constant (1.53–2.15×; poly6 +21% off the ~1.78 mean, so the
  ±15% sub-gate is marginally EXCEEDED, reported honestly). Deepest-logic designs
  (poly6, fir32) show the largest Vivado pessimism. Vivado mis-ranks one near-tie:
  silicon poly6(83.3)>fir16(76.9) but Vivado fir16(47.6)>poly6(38.7). Rank
  correlation ρ≈0.9 (4/5 pairs correct, one adjacent swap).
- **Finding 2 — silicon Fmax is build-context-dependent.** fir16 = 76.9 MHz here
  vs 90.9 MHz standalone in Phase 0 (~15% lower when packed with 4 other DUTs;
  placement/congestion). → compare RL candidates within ONE consistent harness.
- **Implication for Phase 3:** use Vivado Fmax as the RL TRAINING signal (cheap,
  directionally right, ρ≈0.9), but board-measure the headline numbers and final
  winner selection (Phase 3b), in a consistent harness. This empirically IS the
  project's thesis — CAD ≠ silicon — now quantified.
- Files: `gen_catalog_bitstream.py`, `sweep_catalog.py`, `rtl/catalog/` (bitstream
  + `catalog_sels.json` + board `catalog_fmax.json`).
**Phase-2 objective achieved; proceed to Phase 3 (correctness-gated Fmax RL).**

### Phase 3 — Correctness-Gated PPA / Silicon-Fmax RL

**STATUS (2026-06-18): Phase-3 entered via a DE-RISKING PROBE first (decided by
the user: "tell me the best next step").** Before building the full RL, confirm
the base model actually *generates* Fmax-diverse correct implementations — else
RL-for-Fmax has no signal (the Phase-0 lesson: prove the signal before the
machinery). Scripts written + locally validated:
- `score_accel.py` — correctness scorer vs `golden.py` (iverilog, two-sided
  shift). Verified: correct/pipelined-correct → 1.0, wrong logic/misnamed → ~0.
- `gen_accel_candidates.py` (server) — sample base RTLCoder N×/spec, keep correct
  (≥0.999), rename each `<design>__g<k>`, write to `rtl/accel_probe/`. Same
  outputs become the RL dataset.
- `analyze_accel_spread.py` — per-design Fmax spread among correct gens; verdict
  GO (median Vivado spread ≥15 MHz) vs WEAK (→ best-of-N instead of RL).
Decision rule: GO → expand specs + train correctness-gated grpo_v5 on Vivado
Fmax (faithful within-spec proxy, Finding A); board-validate winners in a fixed
harness (Finding B). WEAK → pivot to best-of-N reranking. Multi-input families
(matmul/sorting) deferred. Run: server `gen_accel_candidates.py --n 24` →
laptop `run_ppa --dir fpga/rtl/accel_probe` → `analyze_accel_spread.py`.

**RESULT (2026-06-19) — MODEL-GENERATION PROBE: NEGATIVE, cross-model.** The
probe answered a more fundamental question than Fmax-diversity: can the base
models generate CORRECT accelerators at all? They cannot, densely:

| model | scale / type | correct generations |
|---|---|---|
| RTLCoder | 7B, RTL-specialized | ~2% (best) |
| qwen2.5-coder-instruct | 7B, modern general code | ~2% |
| VeriGen (matthewdelorenzo r16) | 16B, RTL-specialized, CodeGen base | ~0% (mostly prose/garbage) |
| qwen3-coder-30B | 30B MoE | not loadable (needs transformers ≥4.51; env has 4.45) |

- On the original table-coefficient FIR/poly/CORDIC: RTLCoder 14/312, qwen ~0,
  CORDIC 0 for both (can't reproduce the arctan table).
- After removing the constant table (**ramp FIRs `firr*`, coeff=k+1**): qwen 3/120,
  RTLCoder 2/120 — still ~2%. Diagnosed failure modes (debug_gen): SystemVerilog
  `'{...}` that iverilog rejects (qwen), the **non-blocking-accumulation bug**
  (`sum <= sum + ...` in a loop — only the last term survives), coefficient-table
  mangling, and (VeriGen) rambling/incoherent output from a weak old base.
- **Conclusion:** silicon-Fmax RL/selection is NOT achievable with the available
  models — not a measurement failure (the harness is validated) but a model-
  competence wall: 7B–16B RTL/code models generate correct streaming accelerators
  at ~0–2%, too sparse for an RL foothold, Fmax diversity, or best-of-N. This is
  a rigorous, well-controlled NEGATIVE result (varied scale, specialization, base
  modernity) and it SCOPES when silicon-grounded RL is feasible (it worked on the
  primitive catalog where the model had competence: grpo_v3 +2.2pp).
- Files: `score_accel.py`, `gen_accel_candidates.py`, `debug_gen.py`,
  `rtl/accel_probe*/`, `rtl_library/firr{8,12,16,24,32}/`.

**DECISION: CONSOLIDATE.** The real, defensible contributions are (1) the
validated silicon-Fmax methodology, (2) the catalog silicon-characterisation +
CAD-vs-silicon findings, (3) this cross-model negative result on RL feasibility,
(4) the grpo_v3 functional gain on primitives. The "RL optimises silicon Fmax"
headline is not reachable with these models; do not force it.

**Goal (original Phase-3 plan, NOT pursued — model wall):** train GRPO where PPA
reward is ONLY given to functionally-correct candidates.
This is the correct formulation that grpo_v4 skipped.

**Two sub-options — 3a is the PRIMARY deliverable, 3b is the bonus (see framing risk above):**

#### 3a — Vivado-estimated Fmax (PRIMARY; offline, fast to iterate)
- Generate N candidates per accelerator design → score correctness with iverilog
- For correct candidates only: run `ppa_synth.tcl` → get Vivado Fmax + LUT
- Reward: `correctness × (timing_w × vivado_fmax − area_w × lut)` (zero reward if incorrect)
- This is online-ish: correctness gate is fast (iverilog); Vivado is slow (run offline, cache)
- This is the defensible result even if silicon-Fmax (Phase 0) turned out non-viable.

#### 3b — Silicon Fmax (BONUS; only if Phase 0/2 passed; slower, hardware-measured)
- Same as 3a but replace Vivado Fmax with measured silicon Fmax (Phase 2 harness)
- Only feasible for a subset of designs at a time (board throughput)
- The genuinely novel number — but it rides on 3a, it does not replace it

**Training recipe (fixing grpo_v4's failure):**
- Reward = `correctness_gate(c) × ppa_quality(c)` where `correctness_gate` = 0/1 from iverilog
- Group advantage normalised over correct candidates only; incorrect = zero advantage, not negative
  (negative advantage on wrong RTL teaches the model TO write wrong RTL to avoid the penalty)
- KL coef ≥ 0.1 (grpo_v4 used 0.05; insufficient)
- Log correctness rate alongside loss; stop immediately if correctness < base at any checkpoint

**New file to write:** `grpo_train_v5.py` — correctness-gated PPA GRPO using accelerator catalog.

**Validation gate (must pass before writing up Phase 3 results):**
- Correctness of grpo_v5 ≥ base model at every saved checkpoint (no regression).
- On accelerator designs: at least 3 designs show measurable Fmax/area improvement
  (grpo_v5 best-of-8 correct gens vs base best-of-8 correct gens). For 3a this is Vivado-
  measured; for 3b it is board-measured.
- Numbers must come from the same scoring harness for both base and grpo_v5 — no different
  evaluation pipelines.
- If correctness degrades → do NOT keep training; investigate the reward formula and fix it.

**Estimated effort:** 3–5 days (training + board eval).

---

### Phase 4 — MAS Completion (System Integration)

**Goal:** make the MAS end-to-end path actually run at least once, and wire the fine-tuned
model (grpo_v3 or grpo_v5) into the Design Agent.

**Steps:**
1. Point `llm.py` `coder_call()` at `base + grpo_v3 adapter` (one-line change).
2. Run `main.py` on a simple accelerator design with Vivado reachable (laptop).
   The synthesis agent needs `shutil.which("vivado")` to find Vivado on the laptop.
3. If synthesis produces a bitstream: upload to board via deployment agent (paramiko);
   capture waveform; confirm `VALIDATION_PASS`.

**Validation gate:**
- At least one MAS-generated design, synthesised end-to-end, deployed to board, passes
  `validate_hw.py` (hw_reward ≥ 0.99 on board). Document the full run.
- Record whether grpo_v3 Design Agent produces better first-attempt RTL than base
  (fewer verification retries or fewer synth warnings).

**Estimated effort:** 1–2 days (mostly debugging the synthesis→deploy path).

---

### Phase 5 — Second Model for Generality (Optional, Strengthens Paper)

**Goal:** show that the silicon-grounded reward framework is not specific to RTLCoder-7B.

**Steps:**
1. Run `build_dataset.py` with DeepSeek-Coder-6.7B (available on server) on the 966-design
   pool → `dataset_dsc.jsonl`.
2. Run `grpo_train_v3.py` (same recipe) → `grpo_dsc/`.
3. Eval: `run_verilogeval_passk.py` base vs grpo_dsc, same 156 problems.
4. Run tier-1 gap study (synth screen) on DeepSeek-Coder candidates — no board needed.

**Validation gate:**
- Eval run with identical script and seed for both base and grpo_dsc.
- Tier-1 gap measurement uses the same `synth_check.tcl` pipeline.
- Report the generality claim ONLY if BOTH models show positive direction (even if small).

**Estimated effort:** 1–2 days (dataset gen + training; eval is a known script).

---

### Summary: what produces real numbers and in what order

```
Phase 0: silicon-Fmax feasibility spike on ONE hand-written FIR + canary DUT
    ↓ GO/NO-GO gate: DUT fails before canary, Fmax repeatable ±5 MHz, ratio 1.0-1.6x
    │   NO-GO -> silicon Fmax dropped; PPA stays Vivado-estimated (skip Phases 2 & 3b)
Phase 1: accelerator catalog built, Vivado Fmax in [80,250] MHz confirmed
    ↓ gate: iverilog 100% pass + Vivado Fmax range check
Phase 2: silicon Fmax at scale (only if Phase 0 = GO)
    ↓ gate: canary fails last everywhere, repeatable ±5 MHz, ratio consistent
Phase 3a: correctness-gated PPA GRPO, Vivado estimates (PRIMARY publishable RL result)
    ↓ gate: zero correctness regression + >=3 designs with measurable Vivado Fmax/area gain
Phase 3b: same but silicon Fmax (BONUS number, genuinely hardware-measured)
    ↓ gate: same + board-measured Fmax improvement
Phase 4: MAS end-to-end with fine-tuned model (system paper contribution)
    ↓ gate: at least one bitstream deployed and board-validated
Phase 5: second model generality (optional but important for reviewers)
    ↓ gate: identical eval pipeline, both models positive
```

**Stop and reassess if:**
- Phase 0 canary fails first / Fmax noisy / ratio implausible → silicon Fmax not viable on this
  board → pivot to Vivado-estimated PPA (the plan still works, just without 3b)
- Phase 1 Vivado Fmax check shows ALL accelerator designs > 250 MHz → need different designs
- Phase 2 silicon/STA ratio unstable at scale → harness bug or Z2 PLL noise
- Phase 3 correctness drops at any checkpoint → reward formula wrong, stop immediately

**Do NOT start Phase 1's catalog build until Phase 0's go/no-go is answered**, and **do NOT
start Phase 3b until Phase 2's gate passes.** The point of the silicon-Fmax track is a real
hardware signal; if the harness is broken or noisy, any training result built on it is
meaningless — and we'd rather find that out in half a day (Phase 0) than after a 3-day catalog.

---

### Files to write (not yet existing)

| File | Phase | Purpose |
|---|---|---|
| `clock_sweep_fmax.py` | 0 | **(WRITTEN)** board-side: sweep fclk0, capture, score DUT + canary → silicon Fmax + GO/NO-GO gate |
| `gen_spike_bitstream.py` | 0 | **(WRITTEN)** pack FIR + canary into one reset-on-arm dut_top + build TCL |
| `gen_accelerator_catalog.py` | 1 | generate RTL + golden.py + spec.txt for accelerator families |
| `grpo_train_v5.py` | 3 | correctness-gated PPA/Fmax GRPO on accelerator catalog |
| `eval_silicon_fmax.py` | 3b | board eval: compare base vs grpo_v5 silicon Fmax, best-of-N |

`clock_sweep_fmax.py` (board, pseudo-code — the canary check is the load-bearing part):
```python
from pynq import Clocks
import time

def measure_fmax(overlay, dut_idx, golden, lo=50, hi=250, step=5):
    last_ok = lo
    for f in range(lo, hi + step, step):
        Clocks.fclk0_mhz = f
        time.sleep(0.01)                       # PLL settle
        cap = capture(overlay, dut_idx)        # reset-on-arm
        if score(cap, golden) >= 0.99:
            last_ok = f
        else:
            break
    return last_ok

# GATE: measure_fmax(canary) MUST exceed measure_fmax(FIR) by >= 20 MHz,
# else you are timing the harness, not the design -- fix before trusting any number.
```

The existing `run_ppa.py`, `ppa_synth.tcl`, `gen_candidate_bitstream.py`,
`score_hw_candidates.py`, `bestofn_ppa.py` all re-use without modification.

---

## 10. THE PROPER METHOD (V2) — board-grounded, coverage-driven, SFT-then-RL

**Decided 2026-06-19 after auditing the reward code.** The whole V1 effort rests
on a reward that is *not what we claimed*, and that is the root cause of the
modest/negative results. This section is the corrected foundation; everything
below supersedes the V1 reward/training design.

### The foundational flaws (proven in the code, not guessed)
1. **Silicon is NOT in the reward loop.** `grpo_train_v3 → score_candidate.score_rtl
   → simulate()` runs the candidate in **iverilog** and compares to
   `golden_from_body()` — a **Python reference model**. The PYNQ-Z2 capture
   (`waveform.npy`) is used only by `capture_waveforms`/`validate_hw`/
   `clock_sweep_fmax` — i.e., ONCE, offline, to certify the Python golden ==
   silicon. `score_candidate.py` never imports the capture. ⇒ Training reward is
   a **pure simulation reward**; "silicon-grounded" describes the reference's
   provenance, not a measurement in the loop. This is why tier-2 gap ≈ null and
   why the functional track collapses to a sim reward. **No board feedback ever
   reaches the model.**
2. **Stimulus = free-running counter** (`cnt<=cnt+1`, inputs are slices like
   `cnt[1:0]`). Deterministic, counter-correlated; coverage = "whatever the
   counter hits." No random/directed vectors, no corner cases ⇒ weak correctness
   oracle (314 designs "saturated", 2 "dead").
3. **Reward = masked Hamming similarity to ONE exact trajectory** (best of 3
   shifts). (a) Bit-match-one-design ⇒ a COPY task, not write-correct-for-spec
   (why pipelined variants don't count and accelerators became "reproduce these
   constants"); (b) graded Hamming gives partial credit to wrong designs ⇒ not a
   clean correct/incorrect signal.
4. **No SFT warm-start.** Base models sit at ~2% on the target designs ⇒ RL has
   no foothold (RL refines competence, can't create it). The supervisor's own
   MBRL roadmap lists SFT as step 1; we skipped it.

### The corrected architecture (ignore the 2×V100 limit; this is the right way)
**Stage 0 — Fix the oracle (THE fix; build first).**
- Functional reward = **I/O-equivalence to a reference model under broad
  randomized + directed stimulus** (cover input space, reset, corners),
  accepting ANY implementation (pipelined/retimed included) up to latency. Clean
  correct/incorrect, not saturating Hamming. Restores implementation diversity
  (revives the Fmax-headroom the PPA-RL needs).
- Physical reward = **real board Fmax (clock_sweep_fmax harness) + real impl
  area/power**. The genuinely-silicon signal.
- Composite = correctness_gate × (Fmax/area among correct).
**Stage 1 — SFT warm-start (missing prerequisite).** Curate a corpus of correct,
DIVERSE RTL (templated + augmented + reference designs incl. pipelined+unpipelined),
SFT base→competence, mixing general code to avoid forgetting (the earlier SFT
failure was fixable, not a reason to skip the stage). Only then does RL have signal.
**Stage 2 — Board-in-the-loop reward server.** candidate → fast iverilog functional
gate → passing ones → real synth/impl + board Fmax sweep + area/power. Slow ⇒ Stage 3.
**Stage 3 — MBRL surrogate (supervisor Architecture 1), anchored.** surrogate
(token/AST → predicted compile/correctness/Fmax/area); bulk GRPO rollouts
"imagined", a fixed fraction validated on real board/EDA, surrogate retrained on
fresh real data (Dyna). GRPO uses RELATIVE advantage ⇒ surrogate only needs
ranking consistency. This is the right answer to the EDA/board throughput
bottleneck — but only pays off AFTER Stages 0–1 (else it accelerates a bad signal).
**Stage 4 — GRPO** with composite correctness-gated reward, KL to the SFT model.
**Stage 5 — Held-out BOARD validation:** on unseen specs, fine-tuned model writes
more-correct and/or faster RTL than the SFT baseline, measured on the board. This
headline is genuinely silicon-grounded (reward AND eval are board-measured).

### Key ordering insight
Fix the oracle (board + coverage + I/O-equivalence) → SFT to competence →
surrogate-accelerated GRPO on the real signal. The supervisor's MBRL idea is
correct but is **Stage 3**, not the starting point.

### Build order (what we are doing now)
1. **`oracle.py`** — Stage-0 functional oracle (rich stimulus + reference-model
   I/O-equivalence + latency alignment), simulation-backed now, **board-replayable
   by construction** (deterministic seeded stimulus). FIRST. ✅ DONE
2. Board "vector player" harness — stream the SAME stimulus vectors to the DUT on
   the PYNQ-Z2 and capture outputs (replaces the free-running counter in dut_top),
   so the functional reward becomes board-measured. (board work)
3. SFT corpus + warm-start. ✅ DONE (see results below)
4. Surrogate + surrogate-accelerated GRPO with the composite reward.
5. Held-out board validation.

### Stage 1 RESULTS — SFT warm-start (oracle-verified corpus) ✅
**The V2 thesis is validated.** SFT on an oracle-verified, style- and
coefficient-diverse corpus lifts RTLCoder-7B from "no RL foothold" to a reliable
generator on three accelerator families. Measured by `probe_competence.py`
(oracle verdict, corpus-format prompts, base-vs-SFT toggled on the SAME model via
PeftModel.disable_adapter — so weights are the only variable).

Corpus (`gen_sft_corpus.py` → `sft_corpus.jsonl`): **350 oracle-verified
(spec→RTL) pairs, 0 rejected.** fir 87, firr 87, poly 162, cordic 14. Styles:
fir/firr {array+loop ref, pipelined, unrolled named-reg}; poly {Horner-chain,
pipelined, inline-nested} × 6 coefficient variants/degree; cordic {unrolled, pipe}.

Trainer (`sft_train_v2.py`): LoRA r=16 on q/k/v/o, loss MASKED to completion,
4 epochs, single V100 (CUDA_VISIBLE_DEVICES=0 to avoid DataParallel OOM),
gradient checkpointing, batch1/grad-accum16, max_length 2048. ~98 min. Adapter
`sft_v3_out`. Train loss 0.52→0.007.

Competence (n=16/design, oracle correct-rate), base (adapter off) → SFT (on):

| family | base | SFT | note |
|---|---|---|---|
| fir    | 9.4% | **100%**  | |
| firr   | 6.2% | **100%**  | |
| poly   | 0%   | **90.6%** | incl. UNSEEN coeff variants poly4_v2 (16/16), poly8_v3 (11/16) → genuine generalisation of the Horner `*x` recurrence, not memorisation |
| cordic | 0%   | 0%        | documented 7B capability ceiling (see below) |
| **overall** | **3.5%** | **84.7%** | **+81.2 pp** |

**poly rescue:** first SFT (215-pair corpus, 9 near-identical poly designs) left
poly at ~3% — diagnosis (`diagnose_competence.py`) showed a structural Horner bug
(`*8'd1` instead of `*x`), the memorise-don't-generalise signature of too-few/too-
similar data — the SAME failure firr had pre-fix. Fix: coefficient-randomized
variants `polyD_vV_8b` (deterministic; oracle rebuilds coeffs from the name),
poly 9→54 designs (27→162 pairs). Retrain → poly 90.6%. Confirms: SFT works where
the family is learnable AND the corpus is diverse; the lever is **data diversity**.

**cordic negative result (honest, citable):** from 14 examples of the hardest
family the 7B produces nonsense (2-bit counters that can't reach iteration N,
wrong tables) — compiles ~2/16, correct 0. A genuine model-capability ceiling for
iterative shift-add CORDIC at this scale, not a data-quantity gap. Left out of the
first GRPO scope; reportable as a limitation.

**Implication:** GRPO now has an overwhelming foothold on fir/firr/poly (≈90–100%
correct). Next gate (Stage 4 prep): confirm the SFT policy emits Fmax-DIVERSE
correct implementations (the RL headroom) and collect the first (RTL→Fmax) data
for the Stage-3 surrogate — generate oracle-verified correct candidates with
`sft_v3_out`, dedup, synth (Vivado) for the Fmax spread per design.

### Fmax-headroom gate RESULTS — GO ✅
Generated oracle-verified distinct-correct candidates with the SFT policy
(`gen_fmax_candidates.py`), synthesised on Vivado (`run_ppa.py`), analysed spread
(`analyze_accel_spread.py`). Two rounds:

- **v3 (sft_v3_out):** poly had huge headroom (61→191 MHz, ~3×) but fir/firr were
  flat (~7–10 MHz). Diagnosis: every trained FIR style (ref/pipe/unrolled) reduces
  taps through ONE big combinational adder, so even "pipe" doesn't break the
  critical path (fir32 pinned at 25 MHz). The "pipe" style even synthesised SLOWER
  than direct (38 vs 48 MHz) — registering products doesn't help when the adder is
  the bottleneck.
- **Fix:** added **transposed-form FIR** (one mult+add per stage, critical path
  independent of tap count), oracle-verified equivalent. Deterministic Vivado check
  confirmed fir16 48→**183 MHz**. Retrained (sft_v4_out, corpus 408 pairs).
- **v4 (sft_v4_out):** ALL families now expose large headroom:

| design | slowest | fastest | Vivado spread |
|---|---|---|---|
| fir8   | 80  | **302** | 222 MHz |
| fir16  | 38  | **196** | 158 |
| firr8  | 78  | **338** | 260 |
| firr16 | 38  | **214** | 176 |
| poly4  | 61  | **191** | 130 |
| poly6  | 39  | **191** | 152 |
| poly8_v3 | 27 | **133** | 106 |
| fir32  | 25  | 25 | 0 (model didn't sample a transposed form in 40 draws) |

**Median within-design Vivado Fmax spread 155 MHz (~295 MHz silicon-equiv at the
~1.9× CAD→silicon ratio), 185% of mean. VERDICT: GO for RL.** All three pre-RL
gates cleared: correctness, implementation diversity, Fmax headroom.

### Surrogate viability (Stage 3 de-risk) ✅ promising
The crux for affordable GRPO: predict Fmax from RTL TEXT alone (no Vivado per
sample). Quick probe on the 45 v4 (RTL→Fmax) pairs, TEXT-ONLY features (longest
multiply-chain per statement, accumulator-chain signature, posedge/nonblocking
counts, registered-vs-combinational output), leave-one-design-out:
- pooled Spearman(pred, actual) = **0.64** (trivial 7-feature linear model);
- per-design **top-1 = 5/7** (picks the true fastest correct implementation).

**Scaled dataset (Stage 3 confirmed):** broadened to 151 (RTL→Fmax) pairs over 19
designs (`rtl/fmax_data` 106 across fir/firr 4–32 + poly 3–10, plus `fmax_probe_v4`
45), all Vivado-synthesised. Same text-only features, leave-one-design-out:
- pooled Spearman = **0.90**, per-design **top-1 = 16/17**, mean within-design
  Spearman = **0.73**.
The surrogate reliably ranks Fmax and almost always identifies the fastest
implementation → GRPO has a solid Vivado-free reward. Dominant signal: long
combinational multiply chains → slow; staged/transposed accumulator chains → fast.
Note fir32/firr32 stay flat (~25 MHz) — the model rarely emits a transposed form
at T=32 (long output); headroom exists but isn't sampled (an RL/sampling target).

### Remaining build order
4. **Surrogate (Stage 3):** scale the (RTL→Fmax) dataset (more candidates ×
   Vivado), train an Fmax predictor, validate rank consistency. Then
5. **GRPO (Stage 4):** reward = oracle correctness-gate × normalised
   surrogate-Fmax, KL to the SFT model, periodic Vivado re-anchoring.
6. **Silicon validation (Stage 5):** measure the RL policy's designs on the
   PYNQ-Z2 (and optionally put the board / silicon-anchored surrogate in the loop
   for the strong "trained on silicon feedback" claim).



### Stage 4 GRPO pilot — REAL-Vivado verdict (Phase A) ✅

Provenance: `rtl/policy_cmp` (sft_v4 vs grpo_v6, in-distribution designs),
synthesized on the laptop with `run_ppa.py --period 5.0` (Vivado 2023.1,
PYNQ-Z2 part), verdict from `compare_eval.py`. Data: `rtl/policy_cmp/ppa.jsonl`
(52 designs), committed a5654e4.

Per-design REAL Fmax (freq-weighted mean of distinct-correct candidates):

| design      | SFT corr% / meanF / maxF | GRPO corr% / meanF / maxF | dMeanF |
|-------------|--------------------------|---------------------------|--------|
| fir16_8b    | 88 / 46.7 / 48           | 100 / 183.0 / 183         | +136.4 |
| fir32_8b    | 29 / 25.4 / 26           | 75 / 25.4 / 25            |  -0.0  |
| fir8_8b     | 96 / 100.2 / 302         | 100 / 301.8 / 302         | +201.7 |
| firr16      | 88 / 61.8 / 214          | 96 / 213.6 / 214          | +151.8 |
| firr8       | 96 / 106.6 / 338         | 100 / 338.4 / 338         | +231.8 |
| poly4_8b    | 75 / 104.1 / 191         | 100 / 142.2 / 191         | +38.1  |
| poly6_8b    | 100 / 64.2 / 191         | 100 / 127.6 / 191         | +63.4  |
| poly8_v3_8b | 88 / 26.6 / 27           | 96 / 26.5 / 27            |  -0.1  |

**Headline: mean real Fmax across designs SFT 66.9 → GRPO 169.8 (+102.9 MHz,
+154%), correctness held or ROSE on every design.**

Interpretation:
- The mechanism is a DISTRIBUTION SHIFT, not luck. SFT *can* emit the fast
  style but rarely (fir8 fast in 1/6 samples, firr8 1/7, firr16 1/5); GRPO emits
  it reliably (maxF == meanF on fir8/16, firr8/16 → nearly every GRPO sample is
  the fast form). This is exactly the F6-honest framing: GRPO shifts probability
  mass toward high-Fmax implementation styles.
- **F2 gaming CONFIRMED on real silicon:** poly4 surrogate maxF = inf, real
  maxF = 191. Surrogate was fooled; real Vivado caps it. Validates the clamp fix
  and gives the paper a clean case study. Re-anchor: add poly4 real labels to
  surrogate training in Phase B.
- **F4 truncation CONFIRMED:** fir32 (25→25) and poly8_v3 (27→27) flat for both
  policies — the fast transposed form is ~750 tokens, cut at the 768 cap, so it
  never appears in either policy's candidates. Fix queued: --max-tokens 1536.
- All Fmax are timing-closed Vivado numbers, not surrogate. Silicon (Stage 5)
  still pending.

**Phase A gate: PASSED.** Pilot verdict is a real-Vivado GRPO win on the
families that fit the token budget; both failure modes are the pre-diagnosed
F2/F4 flaws with fixes already queued for Phase B. Proceed to Phase B
(held-out clean experiment).

### Phase B training milestones — clean corpus + sft_v5 + surrogate_v2 ✅

Provenance: GPU server, conda env `mas`, one V100, code at 89121a6.

**Corpus regen (held-out excluded).** `gen_sft_corpus.py --holdout` →
`sft_corpus_v5.jsonl`: 358 oracle-verified pairs (0 rejected), families
fir 100 / firr 100 / poly 144 / cordic 14. Exactly 50 pairs fewer than the
408-pair full corpus = the 14 §5 held-out designs × their styles (fir/firr
{6,10,18,26} @ 4 styles = 32; poly7 v0..v5 @ 3 styles = 18). Zero held-out leak
(verified by is_holdout in the sandbox).

**SFT v5** (`sft_train_v2.py --max_length 4096`, 4 epochs, LoRA r16, ~1.8h).
Loss 0.471 → 0.009, final train_loss 0.125. F4 confirmed: log shows
`training at max_length=4096 (model supports 16384)` — the 2964>2048 line is the
harmless tokenizer-default warning, NOT truncation. Competence probe
(`probe_competence.py --adapter sft_v5_out --n 16`, oracle verdict, 1536 tokens):

| family | base | sft_v5 |
|--------|-----:|-------:|
| fir    | 9.4% | 87.5% (56/64) |
| firr   | 12.5%| 100%  (32/32) |
| poly   | 3.1% | 96.9% (31/32) |
| cordic | 0%   | 0%    (documented ceiling, out of RL) |
| OVERALL| 6.9% | 74.4% (119/160); non-cordic 93.0% (119/128) |

GATE PASSED (base 6.9% → 74.4%, +67.5pp; non-cordic 93% ≈ sft_v4). fir32 is the
soft spot (9/16 = 56%) but now PRODUCES correct candidates at all — in the
Phase-A pilot the 768-token cap truncated fir32 to 0 correct, so this confirms
the F4 fix gives GRPO a foothold on fir32 it never had. The ~10pp overall drop
vs sft_v4 (84.7%) is expected: the corpus deliberately dropped the held-out
designs, trading a little in-distribution competence for a clean held-out test.

**Surrogate v2** (`surrogate_train.py --data rtl/fmax_probe_v4 rtl/fmax_data
rtl/policy_cmp --out surrogate_v2.pt`). 203 labelled (RTL→Fmax) pairs, 35
designs, 9 text features. LODO pooled Spearman 0.965 (v1 0.959), per-design
top-1 23/25 (v1 15/17). The +52 pairs vs v1 are the Phase-A policy_cmp rows with
REAL Vivado labels — the F2 re-anchor: the surrogate has now seen poly4's real
ceiling (~191 MHz), not the +inf it once hallucinated. Held-out row filter ran
clean (0 dropped; none of the label dirs contain §5 held-out designs). Clamp to
[5,500] is applied at CONSUMPTION (grpo_oracle/eval_holdout), training stays on
real finite log-Fmax.

Next: GRPO grpo_v7 (sft_v5 + surrogate_v2, 98 train designs, frozen-SFT KL,
1536 tokens, clamp) → held-out eval (eval_holdout.py) → run_ppa.

### Second-model transfer — Qwen2.5-Coder-7B-Instruct SFT ✅ (recipe transfers)

Provenance: same clean corpus (sft_corpus_v5.jsonl, held-out excluded), same
trainer (sft_train_v2.py --max_length 4096, model supports 32768), same probe
(probe_competence --n 16, oracle verdict). Adapter: sft_qwen_out.

| probe             | RTLCoder-7B | Qwen2.5-Coder-7B |
|-------------------|------------:|-----------------:|
| base overall      | 6.9%        | 1.9%             |
| SFT overall       | 74.4%       | 68.1% (+66.2pp)  |
| SFT fir           | 87.5%       | 100% (fir32 16/16) |
| SFT firr          | 100%        | 96.9%            |
| SFT poly          | 96.9%       | 43.8%            |
| SFT cordic        | 0%          | 0%               |
| SFT non-cordic    | 93.0%       | 85.2%            |

Findings:
- The SFT recipe TRANSFERS: a second, unrelated 7B goes ~2% -> ~68% (85%
  non-cordic) with zero pipeline changes. "Method, not model."
- Complementary strengths: Qwen aces fir (100%, incl. fir32), RTLCoder aces
  poly (96.9 vs 43.8). Speculation: RTLCoder's RTL-specific pretraining helps
  the Horner recurrence; not investigated further.
- cordic = 0% on BOTH models -> the cordic ceiling replicates across
  independent 7Bs; upgraded from "RTLCoder quirk" to "7B capability-class
  limit" (strengthens the documented negative result).
Next (optional strengthener): grpo_qwen from sft_qwen_out with surrogate_v2
(text-based, model-agnostic), then Qwen row in the held-out table.

### New-family headroom vetting (IIR + median) — both GO ✅

Provenance: vet_families.py (2 hand-written styles/design, all 10 oracle-verified
I/O-equivalent at seed 3) -> laptop run_ppa (Vivado 2023.1, period 5.0) ->
vet_families.py --report. GATE: fast/slow real-Fmax ratio >= 1.5x = has the
style headroom the Fmax-RL needs.

| design | slow (ref/comb) | fast (transposed/pipe) | ratio | verdict |
|--------|----------------:|-----------------------:|------:|---------|
| iir4   | 93  | 188 | 2.03x | GO |
| iir8   | 62  | 184 | 2.99x | GO |
| iir12  | 52  | 188 | 3.62x | GO |
| med5   | 77  | 115 | 1.50x | marginal |
| med9   | 43  | 110 | 2.56x | GO |

Findings:
- IIR (order-N, real feedback y[n] deps on y[n-1],y[n-2]) has strong headroom
  that GROWS with order (2.0x@4 -> 3.6x@12), same signature as FIR: the naive
  combinational sum's critical path worsens with size while the transposed
  chain stays ~188 MHz. The style-headroom mechanism REPLICATES on a feedback
  structure -> method is not FIR-specific.
- Median (comparator sort network, ZERO multipliers) has headroom at useful
  window sizes (med9 2.56x); med5 marginal (too small to restructure). Proves
  the approach extends beyond arithmetic kernels.
- Prospective 5-family story spanning 3 circuit classes: MAC kernels
  (fir/firr/poly) + feedback filters (iir) + comparator logic (median).

NOTE: this vets HEADROOM + template correctness only. FOOTHOLD (can the 7B
LEARN these post-SFT) is UNPROVEN -- the GO verdict authorizes the catalog+SFT
investment; median (no arithmetic) is the higher-risk foothold. Next: add
iir_*/med_* generators to gen_accelerator_catalog.py + gen_sft_corpus.designs(),
regen corpus, retrain, probe.

### ★ PHASE B MONEY TABLE — held-out real-Vivado verdict (the paper's headline) ★

Provenance: eval_holdout.py (n=48/design, oracle seeds 1&2 n=1024) on server →
run_ppa (Vivado 2023.1, period 5.0, 284/285 synthesized, 1 base fir40 SYNTH
FAIL) on laptop → eval_holdout.py --report. Data: rtl/holdout_eval/ppa.jsonl
(ef2582c). All Fmax = REAL timing-closed Vivado, freq-weighted means over each
policy's distinct-correct candidates. All designs FROZEN §5 held-out (never in
SFT corpus, GRPO list, or surrogate rows).

INTERPOLATION (14 designs, in-range unseen): mean real Fmax
  base 35.1 → sft_v5 66.5 → bestof8 113.9 → grpo_v7 234.4 MHz
  grpo vs sft: +167.9 MHz (+252%); grpo vs bestof8: 2.06x
  correctness avg: sft 91.1% → grpo 94.6% (GRPO HOLDS+RISES on interp)

EXTRAPOLATION (8 designs, beyond trained range): mean real Fmax
  base 15.2 → sft_v5 52.0 → bestof8 112.2 → grpo_v7 190.1 MHz
  grpo vs sft: +138.1 MHz (+265%); grpo vs bestof8: 1.69x
  correctness avg: sft 89% → grpo 78.5% (cost concentrated in fir36 65%,
  fir40 17%, firr40 58%; poly extrap holds 98-100%)

Key rows/findings:
- Mechanism on unseen designs: SFT emits the fast form ~1-in-5..13 samples
  (fir10: one 272 in 11; firr10: ZERO fast in 13; poly7s: ~1-in-5 at 191);
  GRPO emits it near-deterministically (meanF≈maxF on most designs).
- GRPO > best-of-8 not just on cost: bestof8 (surrogate-picked from 8 sft
  samples) MISSED the fast form on fir10/fir26/poly7_v3/v4/poly8_v6/v7 —
  fast-tail sampling + surrogate ranking is strictly weaker than the shifted
  policy.
- poly verdict corrected vs the in-training read: surrogate's 460-500 claims
  were inflation (real ceiling ≈ 191-193, the pipelined Horner), BUT GRPO poly
  meanF ≈ 190 vs sft ≈ 45-60 -> the reliability win holds; only the claimed
  MAGNITUDE was gamed. Clamp contained it; Vivado exposed it. Case study stands.
- F5 honored: correctness gate = oracle seeds 1&2, n=1024 (training used seed 0).
- Extrapolation limitation (paper text): at taps far beyond training (36/40)
  the fast transposed form's correctness degrades (fir40 17%) — speed
  generalizes further than reliability; report as stated limitation.

PHASE B GATE: PASSED. Held-out table complete; GRPO gains are strong on
held-out designs in BOTH regimes → primary headline (not the best-of-N
fallback). Remaining: VerilogEval regression (running), Qwen GRPO (running),
silicon Phase C (pending, the final headline), optional iir/med family build
(vetted GO).

### Phase C smoke test — board + harness GO ✅ (silicon measurement validated)

Provenance: PYNQ-Z2 (pynq 3.1.1, kernel 6.6.10-xilinx-v2024.1), board harness
~/fmax_spike verified against repo (goldens byte-identical: fir16 0,3,13,35,76,
144,246,388,573,801; echo8b 0..9; CLI identical — checksum diffs cosmetic).
Invocation that works: `sudo -E /usr/local/share/pynq-venv/bin/python3 ...`
(non-sudo lacks /dev/dri render perms; plain sudo strips XILINX_XRT).
Sweep: system_spike.bit (fir16_8b unpipelined direct-form + echo8b canary),
60-260 MHz step 5, 3 runs, threshold 0.99.

Results (perfectly repeatable across 3 runs):
  FIR silicon Fmax   = 90.91 MHz (first fail 100.0; PLL snaps 90.9->100->111,
                       so true value in (90.9, 100.0))
  canary silicon Fmax = 250.0 MHz (never failed in range)

GATE:  1. canary margin 250.0-90.91 = 159.1 MHz  >= 20   PASS
       2. repeatability spread 0.0 MHz            <= 5    PASS
       3. silicon/STA ratio: script printed FAIL at 0.55 — but the reference
          passed (--vivado-fmax 165) was a STALE docstring constant. The DUT in
          the bitstream is the UNPIPELINED direct-form fir16 (header comment +
          399-LUT structure); our labeled Vivado data for that exact structure:
          47.56 MHz STA. Corrected ratio 90.91/47.56 = 1.91 (band 1.0-2.2,
          room-temp silicon vs worst-case signoff) -> PASS.

VERDICT: GO. The harness measures the DESIGN (canary margin proves capture path
is not the bottleneck), the measurement is deterministic, and silicon/STA is
physically plausible. Silicon Fmax measurement of the GRPO held-out designs is
cleared. TODO for the artifact: re-run sweep with --vivado-fmax 47.56 for a
clean GO printout; optionally run_ppa the exact rtl_library/fir16_8b/design.v.

Next (Phase C measurement): pick 3-5 held-out designs (suggested: fir26, firr26,
poly7_8b interp + firr36, poly8_v6 extrap), build bitstreams for SFT-median vs
GRPO-top candidates (gen_catalog_bitstream.py flow, laptop), sweep on board ->
measured silicon Fmax table (the thesis headline).

### Qwen GRPO (grpo_qwen) — trained ✅ + VerilogEval regression control ✅

**grpo_qwen** (400 steps, sft_qwen_out + surrogate_v2, frozen-SFT KL, 1536 tok):
converged with the same signature as grpo_v7 — correctness held (7-8/8 typical,
fir32 6-8/8 at end), majority flat-skips by the final quarter (policy emits the
fast style near-deterministically), kl <= 0.004, saturation at the 500 clamp on
large fir (same surrogate ceiling as RTLCoder run). Adapter -> grpo_qwen/.
Second base model completed the FULL pipeline (SFT -> GRPO) with zero code
changes. Pending: Qwen held-out eval + Vivado for its money-table row.

**VerilogEval pass@k** (run_verilogeval_passk.py, 156 problems, n=10, RTLCoder):

| policy  | compile | pass@1 | pass@5 | pass@10 |
|---------|--------:|-------:|-------:|--------:|
| base    | 64.7%   | 32.2%  | 46.2%  | 51.9%   |
| sft_v5  | 46.6%   | 16.0%  | 33.0%  | 40.4%   |
| grpo_v7 | 46.7%   | 16.7%  | 34.2%  | 41.0%   |

Findings (honest):
- **GRPO adds ZERO regression beyond SFT** — marginally better on every metric
  (16.0->16.7 pass@1). The frozen-SFT KL leash (F3) protected general ability
  through RL. The core anti-forgetting claim for the RL stage: PASSED.
- **SFT itself costs ~16pp pass@1** (specialization): 4 epochs on 358
  fixed-interface pairs pulls generations toward the corpus format; compile
  rate 65->47% indicates interface/format mismatch on foreign problems rather
  than lost Verilog competence.
- Paper framing: the policy is a DETACHABLE LoRA adapter — base model
  untouched, general capability recoverable by unloading. Report the SFT
  specialization cost + zero RL cost + adapter modularity. Mitigations
  (fewer epochs, replay mix) = future work; do not spend compute now.

### Phase C smoke test — CLEAN GO artifact ✅ (re-run with corrected STA ref)

Re-ran the spike sweep with --vivado-fmax 47.56 (the correct STA for the
unpipelined direct-form fir16 actually in the bitstream). All three gates PASS
as printed by the tool: canary margin 159.1 MHz, repeatability 0.0 MHz,
silicon/STA 90.91/47.56 = 1.91. VERDICT: GO. Artifact:
~/fmax_spike/rtl/spike/sweep_result_clean.json (board).
Note: run_ppa on rtl_library/fir16_8b/design.v needs the file COPIED to
fir16_8b.v first (run_ppa derives the top module from the filename).

### ★★ SILICON MONEY TABLE — measured on PYNQ-Z2, held-out designs ★★

Provenance: rtl/holdout_silicon bitstream (11 DUTs: 5 held-out design pairs
sft-median/grpo-top + echo8b canary, one 200MHz-constrained build, self-checked
11/11 pre-build), swept on the PYNQ-Z2 with sweep_catalog.py, 30-260 MHz,
3 runs, threshold 0.99. Board data: rtl/catalog/catalog_fmax.json (on board;
scp into repo). ALL entries spread = 0.0 MHz across 3 runs.

| held-out design | SFT silicon | GRPO silicon | speedup | gate |
|-----------------|------------:|-------------:|--------:|------|
| fir26  (interp) | 50.0  | 125.0        | 2.50x  | OK (both) |
| firr26 (interp) | 55.6  | 125.0        | 2.25x  | OK (both) |
| poly7  (interp) | 76.9  | >=200 (harness-limited) | >=2.60x | grpo at canary ceiling |
| firr36 (extrap) | 40.0  | 125.0        | 3.13x  | OK (both) |
| poly8v6(extrap) | 58.8  | >=200 (harness-limited) | >=3.40x | grpo at canary ceiling |
| echo8b canary   | 200.0 | (harness reference) | | |

HEADLINE: on real silicon, on designs never seen in training, the GRPO policy's
RTL sustains 2.3-3.4x higher measured clock than the SFT policy's typical
output — in both interpolation AND extrapolation regimes, perfectly repeatable,
canary-attributed (8/10 entries fully attributable; 2 GRPO entries exceed the
harness's own 200 MHz ceiling and are reported as >=200, honest).

Notes:
- Canary ceiling in THIS bitstream = 200 MHz (vs 250 in the 2-DUT spike): the
  11-DUT probe mux weighs on the capture path; per-bitstream canary is exactly
  why the canary rides along. DUT failures below 200 are fully attributable.
- In-context vs standalone STA: grpo fir/firr measure 125 on silicon vs
  193-228 standalone run_ppa STA. Different implementations (11-DUT shared
  200MHz-constrained build vs solo compile). The table's SFT-vs-GRPO comparison
  is same-bitstream/same-conditions = fair; standalone Vivado table is reported
  separately; do not mix columns (one methodology sentence).
- SFT silicon/STA ratios 1.56-2.37 — consistent with the smoke test's 1.91.
- Harness characterization: sweep hangs at 333 MHz (AXI/capture beyond
  validated range) -> harness validated <=250; sweeps capped at --hi 260.
- Qwen held-out eval done on server (GRPO notably FIXES Qwen's weak poly7:
  29-54% SFT -> 85-100% GRPO correctness; firr10 52%, fir36 50% dips); Fmax
  columns surrogate-saturated -> laptop run_ppa on rtl/holdout_eval_qwen next.

PHASE C GATE: PASSED. The thesis has its silicon-measured headline.

## 2026-07-13 — Phase D5 zero-GPU analyses: best-of-N curves, fir40 sample-cost, F7 area columns

`analyze_bestofn.py` (new) computes, purely from the existing
rtl/holdout_eval artifacts (fmax_manifest counts + ppa.jsonl real Fmax):

1) EXACT expected best-of-N under a PERFECT selector (closed-form order
   statistic on the empirical 48-sample distribution; incorrect samples = 0).
   This upper-bounds best-of-N + ANY reranker (surrogate top-1 included), so
   it isolates policy shift vs better sampling with zero GPU/Vivado time.

   Mean real MHz | bo1 | bo8 | bo16 | bo32 | bo48 | GRPO-bo1
   interp        | 60.7| 135.2| 171.5| 198.6| 207.8| 222.6  <- GRPO bo1 > perfect bo48
   extrap        | 47.3| 109.2| 133.8| 152.3| 159.5| 150.0  <- GRPO bo1 ~ perfect bo32

   Existence failures sampling cannot fix: firr10 SFT bo48=68.9 vs GRPO 306.8;
   fir40 SFT bo48=20.9 vs GRPO 181.8 (fast form absent from all 48 SFT samples).
   -> "RL shifts the distribution; selection cannot reach what SFT never emits."

2) fir40 sample-cost: GRPO p(correct)=8/48=0.167 -> expected 6.0 oracle-checked
   ~1s sims to first correct design at 181.8 MHz real. SFT there: p=0.75 but
   best-of-ALL-48 = 20.9 MHz. Reframes limitation #1 as a favorable trade.

3) F7 resolved: DSP/LUT/FF columns for every money-table entry
   (rtl/holdout_eval/bestofn.json). GRPO fir/firr designs use FEWER LUTs than
   SFT (fir40 1079->788) + pipeline FFs; poly maps to DSPs (5-7 -> +1 in grpo).
   No area-for-speed explosion. lut=0/1 rows = DSP-mapped multiplies.

Provenance: sandbox numpy-only, no new synthesis; all Fmax values are the
existing real-Vivado labels. Artifacts: analyze_bestofn.py,
rtl/holdout_eval/bestofn.json.

## 2026-07-13/14 — Phase D2 CODE COMPLETE: 5-family expansion (iir + med promoted)

Both vetted-GO families promoted from vet_families.py templates into the full
pipeline, all sandbox-verified with iverilog before any GPU time:

- gen_accelerator_catalog: iir_coeffs_var/iir_ref/iir_transposed/iir_spec/
  iir_golden (feedback A1=9,A2=5 >>4 fixed; B varies per variant) and
  _sort_passes/_emit_pass/med_rtl/med_comb/med_pipe/med_pipe2/med_spec/
  med_golden. Catalog main() adds iir4/8/12 + med5/9 to rtl_library (goldens
  board-ready) + 10 new accel_variants. EXISTING rtl_library entries verified
  byte-identical after regen (0 git diffs).
- oracle: iir_ref(xs,B) + med_ref(xs,W) references; build_reference handles
  iir{N}[_v{V}] and med{W} by name.
- gen_sft_corpus: FROZEN D2 split (see CLAUDE.md §5) — iir grid orders 2..14
  x v0..v3 minus interp-holdout orders {5,9}, extrap {16,20}; med grid W
  {3,5,9} (W=7 interp, W=11 extrap; med11 pipe ~2000 tok > 1536 budget is WHY
  11 is the extrap point — F4 lesson applied at design time). med3 pipe==comb
  (3-pass network) deduped. is_holdout() extended (single source of truth ->
  grpo leak-guard + surrogate row filter inherit it automatically).
- eval_holdout: +8 eval designs (30 total: 19 interp / 11 extrap); med11
  generated at 3072 tokens; --families flag to run e.g. only 'iir,med'.
- surrogate_train: v3 features n_ternary/n_cmp/nb_assign (comparator networks
  have ZERO multiplies -> old features blind on med; old n_nonblock kept
  verbatim since surrogate_v2 weights bake in its <=-conflation). extract_
  features(txt, feats) is checkpoint-aware: grpo_oracle/compare_policies/
  eval_holdout all pass ck["feat_names"], so surrogate_v2.pt (9 feats) keeps
  working while surrogate_v3 trains on 12. Sanity: med9 comb n_mult=0,
  n_ternary=72, n_cmp=89 vs fir16 ref n_mult=17, n_ternary=0.

VERIFICATION (sandbox): corpus regen --holdout = 454 oracle-verified pairs,
0 rejected (fir 100, firr 100, poly 144, cordic 14, iir 88, med 8); zero
holdout leakage; is_holdout spot-checks all pass; GRPO train list 98 -> 145
designs, no leak, no cordic; all 16 held-out new-family templates (iir5/5v1/
9/9v1/16/20 x 2 styles, med7/11 x 2) oracle-correct; med pipe2 correct at
every W.

NEXT (GPU server): git pull; python gen_sft_corpus.py --holdout --out
sft_corpus.jsonl (expect 454); sft_v6 via sft_train_v2 (same recipe as v5);
probe; gen_fmax_candidates over iir/med train designs -> laptop run_ppa ->
surrogate_v3 (12 feats) -> grpo_v8 on all 145 train designs -> extended
eval_holdout (30 designs) -> laptop Vivado -> extended money table.

## 2026-07-14 — Phase D1 HLS baseline COMPLETE (collect_hls.py, laptop Vivado)

Vitis HLS 2023.1 on 16/22 held-out designs (6 poly variants poly7_v5/poly4_v6/
poly4_v7 dropped to an intermittent Windows export cmdline-length limit even
under subst X: — redundant, the 3 poly-degree structures are covered by
poly7_v4/poly8_v6/poly8_v7). C++ kernels oracle-exact; real post-P&R clock
(export_design -flow impl); throughput = Fmax/II.

RESULT (geomean over 19 comparable designs):
  GRPO-throughput / expert-HLS-throughput = 0.96x
  -> from an NL spec the policy MATCHES hand-tuned-pragma HLS (II=1) within 4%,
     and EXCEEDS it on small designs (fir6 1.3x, firr6 1.4x).

  vs naive HLS (nopragma): 20-150x. Without pragmas HLS pipelines only the
  outer loop, so II = tap-count (fir40 II=134) or degree (poly Horner II=31-35);
  naive throughput 1.7-10.5 Msample/s. The recurrence-heavy poly is where naive
  HLS collapses hardest and the LLM's direct II=1 emission wins biggest.

  expert HLS II=1 throughput 195-258 Msample/s; GRPO II=1 181-346.

Framing (frozen): HLS input = engineer C++ + hand-placed pragmas; ours = NL
spec. "Match the HLS expert, crush the HLS novice, from natural language."
NOT "beat HLS". Artifacts: rtl/hls_baseline/hls_results.json, *_export.rpt,
collect_hls.py, gen_hls_baseline.py, analyze in RESULTS.md 2c.

Also this session: sft_v6 trained (D2, 5 families) — loss 0.51->0.005 over 4
epochs / 2h20m on the server, adapter sft_v6_out saved (33M). Held-out probe
(incl. new iir/med families) running.

## 2026-07-15 — sft_v6 probe: iir SOLVED (96.2%), med data-starved (6.2%) -> oversample fix, sft_v6b

Probe (n=16/design, corpus-format prompts, oracle verdict):
- OLD families unchanged/improved vs sft_v5: fir 90.6 (v5 87.5), firr 93.8
  (v5 100, -1 sample = noise), poly 100 (v5 96.9), cordic 0, overall 75.0
  (v5 74.4). Corpus expansion caused NO regression.
- iir (NEW): 96.2% correct (77/80; iir4 16/16, iir8 14/16, iir8_v2 16/16,
  iir12 16/16, iir14_v1 15/16) vs base 0.0%. Real-feedback recurrence learned,
  including coefficient variants. iir is DONE at the SFT stage.
- med (NEW): 6.2% (3/48) vs base 2.1% — NOT learned; even compile-rate low
  (med3 10/16). Diagnosis: data starvation, not capability — med had 8/454
  corpus pairs (1.8% of signal; no coefficient knob to make variants) vs iir 88
  and fir 100. med carries the "3 circuit classes" claim (comparator networks,
  zero multipliers), so it gets one fix cycle BEFORE grpo_v8 (SFT rerun 2.5h
  << rerunning multi-day GRPO twice).

FIX: gen_sft_corpus --oversample fam=K (duplication only; rows stay
oracle-verified verbatim). med=10 -> 80/526 rows (~15%). Sandbox-verified:
454 distinct, 526 rows. Server: regen + sft_v6b (~2.7h) + med re-probe.
GATE for grpo_v8 launch: med >= ~60% on med3/5/9. If oversampling fails,
round 2 = extra hand-written med styles (compact min/max median idioms);
if that fails, drop to 4 families / 2 classes + honest negative (the
cordic-pattern applied to data-starved comparator networks).

## 2026-07-15 — sft_v6b probe (med 35.4%) -> med_sort compact style, sft_v6c

sft_v6b (oversample med=10, 526 rows, loss 0.447->0.005, 3h03): canaries held
(fir16 93.8, poly6 93.8, iir8 93.8 — oversampling harmless); med 6.2 -> 35.4%
(med3 44%, med5 63%) BUT med9 0/16 correct, 2/16 COMPILED. Diagnosis: the
odd-even wire-network template at W=9 is 1128-1491 tokens of repetitive
boilerplate — repetition cannot teach a template too long to emit reliably.

FIX (round 2): GAC.med_sort — behavioral bubble sort, static loop bounds
(synthesis unrolls to the same comparator-network hardware class), source size
~CONSTANT in W: 130/151/172/193/215 tokens for W=3/5/7/9/11 (vs 1128-2218 for
the network forms). Oracle-verified correct at ALL five widths including
held-out med7/med11 -> also makes the held-out med evals a fair generalization
test (same source shape scales to any W). Corpus: med styles now
comb/pipe/pipe2/sort (11 distinct pairs), --oversample med=8 -> 88 rows,
457 distinct / 534 total. iir & med now equally weighted (88 each).

Server: regen + sft_v6c (~2.8h GPU 1) + probe med3/5/9 + canaries.
GATE unchanged: med >= ~60% -> grpo_v8. Failure fallback: 4 families /
2 classes + honest negative.

## 2026-07-17 — Frontier-API baseline harness (Phase D item 7, supervisor request)

gen_frontier_baseline.py: OpenAI-compatible endpoint (default DeepSeek), two
arms per held-out design — apiplain (verbatim our prompt) and apifast
(+explicit maximize-Fmax instruction; mandatory-honesty arm). Same protocol as
our models: temp 1.0, oracle seeds 1&2 n=1024, distinct-correct dedup by
norm(), .sv + fmax_manifest for laptop run_ppa, --report joins grpo columns
from rtl/holdout_eval. Resumable per design/arm; --dry-run verified (22
designs x 8 x 2 = 352 calls for the fir/firr/poly set; ~$1-3 at DeepSeek
prices). Covers all 30 held-out designs automatically once iir/med eval
exists. Ordering decision: run NOW in parallel — frontier rows are
measured-once/independent; the student-vs-frontier comparison (if D+
succeeds) joins rows measured at different times. Key hygiene: env var only.

## 2026-07-21 — sft_v6c 5-family gate PASS + Flash frontier run

**sft_v6c probe (TRAIN-family competence, n=16/design):** median W solved.
med3 14/16, med5 16/16, med9 13/16 (15/16 compiled); canaries fir16 16/16,
poly6 16/16, iir8 16/16. Aggregate: median 43/48 = **89.6%**, overall SFT
91/96 = **94.8%**, base 4/96 = 4.2%, compiled 95/96. Progression from the
compact behavioral `med_sort` style: **6.2% (sft_v6) → 35.4% (sft_v6b) →
89.6% (sft_v6c)** — confirming the earlier failure was template LENGTH, not a
capability ceiling. No FIR/poly/IIR regression. Decision: keep all 5 families /
3 circuit classes. NOTE: this is train-family competence only — NOT held-out
evidence (that comes from grpo_v8 → the 30-design frozen eval → Vivado).

**grpo_v8 sequencing (important):** grpo_v8 is NOT the immediate next step.
grpo_oracle's reward is surrogate-predicted Fmax, and surrogate_v2 was trained
on fir/firr/poly/cordic only — it has never seen IIR (feedback) or median
(comparator-network) RTL, so its predictions there are out-of-distribution and
would be gamed/mislearned (the F2 failure mode on new families, invariant #2).
Critical path: `gen_fmax_candidates.py --adapter sft_v6c_out --designs iir4
iir8 iir12 med3 med5 med9` → laptop Vivado (rtl/fmax_d2) → surrogate_v3
(12 features incl. n_ternary/n_cmp/nb_assign) → grpo_v8 (--sft sft_v6c_out
--surrogate surrogate_v3.pt, train-split design list auto-includes iir/med) →
30-design held-out eval → Vivado. Matches Phase-D item 2 in CLAUDE.md §6.

**Flash frontier run COMPLETE (correctness only):** 30 held-out designs × 8
samples × 2 arms = 480 calls, 60/60 arms, 120 distinct oracle-correct .sv in
rtl/frontier_eval. API alias deepseek-chat resolved to DeepSeek-V4-Flash
(non-thinking) @ api.deepseek.com, 2026-07-20/21. Correctness: FIRR strong
(62–100%), FIR moderate (25–37%), held-out poly/IIR/median near-zero
(poly all ~0% except poly4_v7 plain 12.5%, poly7_v4 fast 12.5%; iir5 12.5%,
med7 plain 25%). The apifast (explicit maximize-Fmax) arm did NOT improve
correctness (e.g. firr10 87.5%→37.5%). CAVEATS — do not draw conclusions yet:
(1) FAIRNESS — this is the Flash tier in non-thinking mode with a prompt tuned
to our local code models; a reviewer will (correctly) call it a handicapped
baseline. The Pro+thinking capability ladder (flash_nt / pro_nt / pro_think,
separate labels+dirs, explicit thinking + reasoning-effort control, provenance
logging — NOT a bare FRONTIER_MODEL swap) is REQUIRED before any "a frontier
model can't do this" claim. (2) NO Fmax yet — needs laptop `run_ppa.py --dir
rtl/frontier_eval`; correctness alone says nothing about the speed claim.
(3) n=8 is noisy (25% = 2/8). The frontier .sv candidates live on the GPU
server (the API run ran there) — must be git-committed from the server so the
laptop can pull them for Vivado.

## 2026-07-30 — grpo_v8 REAL VIVADO (iir/med/poly) + 1.5B STUDENT: mixed, honest

**POLY = CLEAN WIN.** SFT emits the fast ~191 MHz form only ~1-in-4..1-in-6
samples; grpo_v8 emits it near-deterministically. Per-candidate real Vivado:
poly7_8b sft {33,33,33,33,33,191} -> grpo {192,192,192}; poly7_v3 sft
{30,30,191,30,30} -> grpo {191,192,191}; poly4_v6 sft {60,192,60,192,60,60} ->
grpo {192 all}; poly8_v7 sft {28,28,192,28} -> grpo {191,191,191}. Freq-weighted
mean ~35-90 -> ~191 MHz. IMPORTANT: the poly surrogate 500-pins were NOT
gaming -- real ceiling is 191-193 MHz, so the surrogate was wrong in MAGNITUDE
but correct in RANKING (as hypothesised).

**IIR = CONSISTENCY WIN, NO CEILING CHANGE.** Both policies top out ~186-189
MHz; grpo removes the slow tail. iir5_v1 sft {146,76,76,76,146} -> grpo
{146,146,146,146}; iir9_v1 sft {61,188,185,61} -> grpo {188,188,188}; iir20 sft
{186,35,35,186} -> grpo {186,186}; iir16 sft {188,188,188} -> grpo {188,188}
(identical). So the MEAN rises, the MAX does not.

**MEDIAN = CORRECTNESS WIN, NO Fmax GAIN. The surrogate's med7 188.6 MHz was
REWARD HACKING.** Real: med7 sft max 40 -> grpo max 40 (no gain, both
38-40 MHz); med11 sft max 22 -> grpo max 34 (marginal). Correctness did improve
(med7 79.2->85.4, med11 29.2->39.6) but speed did not. This CONFIRMS the
saturation-predicts-trouble diagnostic from the correctness pass: where the
surrogate pinned at 500 on a family it had no discrimination for (median,
Spearman 0.75 after the 5-family retrain), the "gain" was illusory. REPORT
MEDIAN AS: correctness improved, Fmax unchanged, surrogate gamed -- do not
bury it. The compact behavioural med_sort style that fixed med CORRECTNESS is
fully combinational, so its critical path is long by construction; a real
median speedup needs a pipelined median template in the corpus (future work).

**MECHANISM (F6) NOW MEASURED PRECISELY on 3 families:** GRPO shifts
probability mass toward the fast implementation style SFT already emits
occasionally; it does NOT invent faster hardware. Max Fmax is set by the best
style in the corpus; GRPO changes how OFTEN you get it. This is the honest
framing for the paper and it is now backed by per-candidate real Vivado.

**1.5B STUDENT (Phase D+ step 2-3): 4 of 5 families compress, median dies.**
sft_train_v2.py on distill_corpus.jsonl (407 rows) x 4 epochs, Qwen2.5-Coder
-1.5B, **25 minutes** (vs ~3 h for the 7B), final loss 0.0395. Probe (n=16,
train-split designs): base 0/112 = 0.0%; student 55/112 = 49.1% overall, but
**55/64 = 85.9% excluding median** -- firr16 93.8%, poly6 93.8%, iir8 87.5%,
fir16 68.8%, med3/med5/med9 all 0/16 (compiled 10/4/5). CAPABILITY-SIZE
FRONTIER: median works at 7B and dies at 1.5B -- the cordic-at-7B pattern one
size class down. Both halves publishable: "silicon-quality DSP RTL for 4 of 5
families from a laptop-size model, trained in 25 min" + an honest size-limit
finding. Student adapter: student_v1_out/.

## 2026-07-28 — grpo_v8 5-FAMILY HELD-OUT EVAL (correctness done, Fmax pending)

sft_v6c vs grpo_v8_cont on the 30 frozen §5 held-out designs, n=48/design,
oracle seeds 1&2 n=1024. Run in 3 chunks (iir,med / fir,firr / poly) across two
boxes: rtl/holdout_eval_v8_{iirmed,firfirr,poly}, 85+156+105 = 346 candidates.

CORRECTNESS (sft_v6c -> grpo_v8_cont):
  MEDIAN (the doubted family) IMPROVED BOTH: med7 79.2 -> 85.4 (surrogate maxF
    41.8 -> 188.6, i.e. GRPO found a pipelined median form); med11 (extrap,
    hardest) 29.2 -> 39.6.
  IIR split: iir5 89.6 -> 89.6, iir5_v1 89.6 -> 97.9, iir9 81.2 -> 93.8;
    BUT iir9_v1 91.7 -> 58.3, iir16 41.7 -> 35.4, iir20 79.2 -> 62.5.
  FIR/FIRR mostly up: firr26 93.8 -> 100, firr36 93.8 -> 97.9, firr18 95.8 ->
    97.9, fir36 89.6 -> 91.7, fir18 100 -> 100, fir26 79.2 -> 95.8, fir6 -> 95.8,
    fir10 -> 97.9; BUT fir40 79.2 -> 52.1 and firr40 93.8 -> 83.3.
  POLY: poly7_v2/v3 100, poly7_v5 97.9, poly4_v7 97.9; dips poly7_v1 100 ->
    77.1, poly7_v4 100 -> 91.7, poly4_v6 95.8 -> 89.6, poly8_v6 100 -> 93.8,
    poly8_v7 95.8 -> 93.8.

KEY DIAGNOSTIC FINDING (new, publishable): **surrogate saturation predicts
correctness loss.** Every large correctness regression sits on a design whose
grpo surrogate score pinned at the [5,500] clamp (iir9_v1, iir16, iir20,
poly7_v1, fir40); every design where the surrogate still returned a realistic
value (iir5 135, iir5_v1 133, iir9 250, med7 84) held or IMPROVED correctness.
Saturation is therefore an observable early-warning signal for reward hacking
-> direct empirical motivation for the D3 re-anchor cycle. Corollary: MORE GRPO
steps against a saturated surrogate would degrade correctness further; the fix
is surrogate_v4 (re-anchored on real Vivado labels of these grpo candidates),
then a SHORT targeted continuation, not more blind training.

NO Fmax NUMBER HERE IS REPORTABLE — all surrogate. Real Vivado pass on the
three dirs is the next step (346 designs); recommend iirmed FIRST (new-family
evidence incl. med7). Also produced: distill_corpus.jsonl = 407 oracle-verified
correct rows from 3480 samples over 145 train-split designs (1-5 distinct per
design -> grpo_v8_cont is near-deterministic, the distribution-shift signature;
corpus size comparable to the 457-pair sft corpus). Phase D+ step 1 DONE.

INFRA LESSON (cost: one full wasted eval cycle): a container reset wiped
iverilog from the ephemeral filesystem; oracle.py's broad `except OSError`
swallowed FileNotFoundError and scored ALL 5760 candidates "incorrect",
producing a clean-looking 30-design table of 0.0% on every policy. Fixed
(ab245bd): missing simulator now RAISES. New standing rule: after ANY container
reset run `python -c "import oracle,gen_accelerator_catalog as G;
print(oracle.score(G.fir_ref('fir8_8b',G.fir_coeffs(8)),'fir8_8b',n=64)
['correct'])"` and require True BEFORE launching anything. Persistent-storage
recipe: conda env at /zeng_gk/Amine/mas/env_mas (survives resets), torch
2.4.1 + transformers 4.46.3 + peft 0.13.2 (newer transformers needs DTensor
from a newer torch than driver 550.90.12/CUDA 12.4 allows), iverilog via apt
with the Tsinghua mirror (ephemeral -> reinstall after each reset).

## 2026-07-27 — Frontier Flash baseline, real Vivado (the nuanced result)

rtl/frontier_eval + ppa.jsonl, `gen_frontier_baseline.py --report`. 30 held-out
designs x 8 samples x 2 arms, oracle seeds 1&2 n=1024, real Vivado.

APIPLAIN (identical prompt to ours): Flash maxF 20.7–155.8 MHz — the SLOW
range, same as SFT. vs grpo: fir40 8.8x, fir26 6.0x, firr10 4.4x, fir6 2.0x in
OUR favour. Finding: a frontier model does not emit fast RTL unprompted.

APIFAST (explicit maximize-Fmax): Flash BEATS grpo on peak Fmax on 10/12
fir/firr designs by 5–30% (fir26 251.5 vs 193.2; fir6 376.2 vs 317.6; firr10
369.0 vs 313.3; fir18 252.4 vs 224.2; firr36 220.2 vs 193.7; fir36 213.3 vs
187.5; fir40 205.4 vs 181.8). grpo still wins firr40 (189.3 vs 182.9) and
firr26 (227.8 vs 217.2). REPORT THIS — mandatory-honesty arm, do not bury it.

BOUNDS (all measured, all real): (1) COVERAGE — Flash poly = 0% correct on
9/10 held-out poly designs (only poly4_v7 plain 12.5% @60 MHz, poly7_v4 fast
12.5% @163.9), iir 0–12.5%, med 0–25%; our policy 94–100% on all five
families. (2) CORRECTNESS RATE — 25–87.5% even on the fast fir/firr designs,
and correctness is knowable only via OUR oracle. (3) AREA/LATENCY — apifast
buys Fmax with registers: fir6 106LUT/185FF vs our 79LUT/96FF (~2x FF for
+18%); fir40 1105LUT/1410FF vs our 788LUT/640FF (2.2x FF for +13%). Deeper
pipeline = higher latency (F7 area caveat applies).

Framing consequence: the claim is NOT "we beat the frontier on speed". It is
"same prompt -> 2–9x faster; prompted-for-speed -> the frontier matches us on
the 2 easiest families and fails the other 3; and our oracle is what makes the
comparison measurable at all." n=8/arm is noisy. Pro/pro_think rungs pending
API credit; flash_think dir exists but rung incomplete.

## 2026-07-24 — Qwen held-out MONEY TABLE (real Vivado) — method transfers

rtl/holdout_eval_qwen, real timing-closed Vivado, n=48/design, seeds 1&2
n=1024. Interp (14): base 26.0 / sft 97.6 / bestof8 153.0 / grpo **232.9**
(+139% vs sft). Extrap (8): base 20.9 / sft 62.7 / bestof8 136.5 / grpo
**190.1** (+203%). grpo > bestof8 in BOTH regimes. KEY: absolute grpo Fmax
(232.9 / 190.1) ≈ RTLCoder grpo (234.4 / 190.1) — both base models converge
to the same real-Vivado ceiling; the final speed is base-model-independent.
GRPO REPAIRS Qwen's weak poly family (poly7 corr 29–54% sft → 85–100% grpo,
and 191 MHz) — competence repair, not just speed. firr18 sft 44.6 → grpo
243.9. Honest correctness cost: firr10 92→52%, fir36 94→50% (two designs
traded correctness for speed; all others ≥94%). Provenance: laptop run_ppa
2026-07-24, ppa.jsonl committed. This is the second-model transfer evidence
(RTLCoder was model #1). Task #8 DONE.

## 2026-07-21 — D4 related-work verification (real links, per §6-D4 rule)

Verified on arXiv (all REAL, cite in the delta table): RTL-OPT
(arxiv 2601.01765, HKUST Jan-2026 — 36-design RTL-optimization benchmark:
combinational/pipelined/FSM/memory-interface pairs + automated
correctness/PPA eval); REvolution (2510.21407, POSTECH Oct-2025 —
evolutionary LLM RTL generation with dual fail/success populations for
bugfix vs PPA). Additional found in the same sweep: POET (2603.19333,
power-oriented evolutionary tuning), EvolVE (2601.18067), Dr. RTL
(2604.14989, agentic tool-grounded RTL optimization), COEVO (2604.15001,
joint correctness+PPA evolution). Our delta vs ALL of these: none report
measured silicon; none use a frozen interp/extrap held-out protocol; none
gate an RL *training* reward with an I/O-equivalence oracle (they select or
evolve at inference time / benchmark existing models). The space is crowded
and accelerating — argues for FINISHING the current rigor paper fast, not
broadening scope mid-flight. "SiliconForge"-class ideas (model-agnostic
RTL-to-RTL optimizer, formal equivalence contracts, structural surrogate,
composition holdout) recorded as the NEXT-project/thesis-chapter direction,
NOT merged into this paper's plan.

## 2026-08-09 — Proxy-validity finding, causal ablation, re-anchor, and the correction round

Session outcome: the paper's centre of gravity moved from "correctness-gated
GRPO makes fast RTL" (preempted by ChipSeek-R1 2507.04736 and PPA-RTL) to a
measurement about the reward itself. Every number below is from committed
artifacts and regenerates with the named script.

### 1. Surrogate is accurate on the behaviour policy and invalid on the optimised one
`analyze_surrogate_error.py` (held-out 30-design set, real Vivado ground truth):

  policy    surr    real     bias    MAE   spearman  clamped@500
  base     329.2    45.6   +283.6  283.6    -0.302    10/16
  sft       88.3    83.6     +4.7   20.5    +0.958     1/30
  bestof8  154.5   155.5     -1.0   35.1    +0.834     0/30
  grpo     433.6   197.7   +235.9  240.1    +0.447    25/30

Divergence between predicted and real improvement:
(433.6-88.3) - (197.7-83.6) = +231.2 MHz of proxy inflation. The real gain is
still real (83.6 -> 197.7); the proxy overstates it ~3x. Offline accuracy does
not imply validity under optimisation, and no held-out fit detects this.
Anchor in the RLHF literature: Gao, Schulman, Hilton, "Scaling Laws for Reward
Model Overoptimization", arXiv:2210.10760 / ICML 2023 — VERIFIED. Their gold
signal is a synthetic reward model; ours is Vivado and a board. That is the
delta: first measurement of the phenomenon against PHYSICAL ground truth.

Family-dependent too: on iir the surrogate is wrong even at SFT (iir16 +154.9,
iir20 +182.2, iir5 -86.1). iir and med are exactly the families where GRPO
delivered little or no Fmax gain — the method works where the proxy is valid.

### 2. Causal control: the physical reward is load-bearing (`analyze_policy_fmax.py`)
Same SFT start, same correctness gate, same KL anchor, physical term removed
(`--constant-reward`). Real Vivado, equal-sample MHz (incorrect = 0) / correct%:

  sft                     79.9 / 92.8%  61.2 / 81.6%  73.0 / 88.7%   (int/ext/all)
  correctness-only RL     52.8 / 99.1%  31.1 / 96.7%  45.3 / 98.3%
  physical-reward RL     198.7 / 93.2% 138.6 / 76.1% 176.7 / 86.9%

Correctness-only reaches the HIGHEST correctness of any policy (98.3%) and cuts
frequency 38% below SFT. Candidate level is sharper than the means: fir18 SFT
emits 34/43/224/224/43 MHz, ablation emits 43/43/43; iir9 SFT 58/58/189/189/189,
ablation 58/58/58/58. The fast style is ELIMINATED, not merely made rarer.
Surrogate predicted this policy at 49.1 vs real 46.1 — accurate because the
policy never left the SFT distribution, which is the finding predicting itself.

Update accounting (grpo_oracle now logs `update`/`n_flat`; --max-updates added):
  constant reward   159 updates / 1997 attempted (92.0% flat), KL/upd 9.2e-06
  physical reward   284 updates /  408 attempted (30.4% flat), KL/upd 3.35e-04
36x less drift per update (NOT 53x — an earlier figure compared against
grpo_v8_cont alone). A binary reward extinguishes its own gradient: with SFT
already ~94% correct, most groups come back unanimous.

### 3. Re-anchor (surrogate_v4): calibration restored, gradient largely lost
`rtl/fmax_d3/ppa.jsonl` = 43 real labels, 12 TRAIN-split designs, 22.0-338.4 MHz
(legal under invariant #3; held-out labels could not be used).
`rescore_surrogate.py` + `analyze_surrogate_error.py --pred`, identical candidates:

  clamp saturation  36/106 -> 7/106 cells
  grpo bias        +235.9 -> +30.7 MHz ; MAE 240.1 -> 71.5
  held-out rho      0.575 -> 0.638
  LODO (offline)    0.965 (v2, 203 pairs) -> 0.841 (v4, 272 pairs)

Selecting the surrogate by its OFFLINE score would have chosen the broken one.
(Not a controlled comparison — different pair sets; needs a matched-set recompute
before it becomes a headline.)

Within-design ranking (the statistic the reward actually uses — GRPO's group is
G samples of ONE design, so cross-design Spearman answers a different question):
sft 0.661 -> 0.663 (intact); grpo ~0.05 under BOTH checkpoints, but that number
is meaningless: median within-design real-Fmax spread is 0.0 MHz for grpo
(161 MHz for sft), so the ranking task on converged outputs is degenerate, not
failed. Claim "calibration restored"; do NOT claim "discrimination restored".

grpo_v9 (400 steps on surrogate_v4): 200 updates / 400 attempted (50.0% flat),
sumKL 0.0028, KL/upd 1.42e-05 — 24x less total drift than v8. Many flat groups
are `correct=8/8` with byte-identical surrogate scores: the 12 coarse text
features collapse distinct RTL onto one feature vector. NOTE GRPO z-scores
rewards per group, so reward SCALE cannot explain this; the flat rate and the
advantage-distribution shape can. Held-out eval running; three predeclared
readings: v9~v8 (remedy free), v9~SFT (proxy error was the engine — strongest
and most novel), v9 between (cost-fidelity trade). v9 is NOT update-matched to
v8 (200 vs 284) — state it or extend with --max-updates 284.

### 4. Evaluation hardening
`audit_oracle.py`, all 1529 accepted candidates, three stricter rules: 0 lost
under exact equality, 0 under warmup=0 (post-reset window compared), 0 with
latency inconsistent across seeds. The 0.999 threshold is near-exact by
construction: k = n-L-warmup, so at n=512 it admits ZERO mismatches and at
n=1024 at most ONE in 1016. Stop writing "threshold 0.999"; write the sample
counts. DEFECT FOUND: oracle keeps only decimal tokens (oracle.py:231-233), so
x/z cycles are silently dropped — 18/1529 candidates have short traces (<=7
tokens). Must reject rather than discard, then re-audit.

`analyze_bestofn.py` was hardcoded to the OLD 22-design dir. On the correct
30-design set GRPO bo1 = best-of-~22 (interp) / ~8 (extrap), NOT above
best-of-48. That claim is WITHDRAWN. What survives: 2.49x/2.27x at equal sample
count, and the perfect selector is unbuildable (needs true Fmax of all N).

`analyze_passk.py` (VerilogEval, unbiased pass@k): base 32.2 -> sft 16.0 ->
grpo 16.7 pass@1; compile-fail 35.1% -> 53.3% -> 53.3%. RL adds NO regression
beyond SFT (the control holds), but SPECIALISATION HALVES general capability.
Report the second openly — it is the concrete reason a detachable LoRA adapter
is a design property.

### 5. Defects still open (verified against the files, not asserted)
- Fmax is 1000/(period-WNS) from ONE 5 ns run (ppa_synth.tcl:78-79) — a
  WNS-derived estimate, NOT timing closure. Relabel everywhere; close a subset
  at per-family target periods (WNS >= 0) for a valid claim at the same cost.
- Silicon selection asymmetric and undisclosed: SFT median vs GRPO top on
  high-GRPO-correctness designs (gen_holdout_bitstream.py). Same flaw in the
  HLS comparison (collect_hls.py:77-81). Re-measure symmetrically.
- Silicon sweep data reaches 260 MHz, not 340 (that was the command's upper
  bound); 2 GRPO entries censored "TOO CLOSE TO CANARY".
- LODO leaks normalisation across folds (surrogate_train.py:173) — embarrassing
  in a paper about surrogate validity.
- Student has no med designs and a zero-byte ppa.jsonl: "4/5 families" is
  functional-only. Qwen eval covers only the old 22 fir/firr/poly designs.
- Correctness is NOT uniformly preserved (fir40 79->52%); 05_results.tex:101
  and 07_conclusion.tex:8 say otherwise and are false as written.
- MASTER_REFERENCE.md:376 and HANDOFF.md:277 still call ChipSeek-R1 fabricated.
  It is REAL (2507.04736). Fix before anyone reads them.
- paper/main.tex and 01/03 still say "timing-closed"; RESULTS.md:77-98 and
  05_results.tex:158-180 still carry the withdrawn best-of-48 story.

### 6. Plan (supervisor-endorsed 2026-08-09, venue TCAD primary / ICCAD 2027 backup)
Hero claim = predictor validity, NOT "RL for RTL". Figure 1 = predicted vs
measured frequency diverging over RL STEPS — requires a checkpoint trajectory
(grpo_v8*/step_*) we have not run; ~10 designs x 4 checkpoints of Vivado.
Do it: it mirrors Gao et al.'s gold-vs-proxy curves with physical ground truth.
Keep "1 RL sample = 22 supervised" OUT of the abstract (does not differentiate
against ChipSeek). PUSHED BACK on posting arXiv this week: the manuscript
contains known-false claims and v1 is permanent and diffable. Compromise =
short FOCUSED preprint on the predictor-validity finding only (clean today),
full paper after the corrections. ChipSeek head-to-head: verify code/weights
actually exist before committing; fallback is a differentiation table.

## 2026-08-10 — grpo_v9 on the re-anchored surrogate: the repair is better than free

Real Vivado, 30 held-out designs, penalised MHz (incorrect = 0) unless noted.
Reproduce: `python analyze_policy_fmax.py --dirs rtl/holdout_eval_v9`

                       v8 (surrogate_v3)   v9 (surrogate_v4)
  penalised MHz ALL             176.7               192.4
  interp                        198.7               209.3
  extrap                        138.6               163.0
  correctness                   86.9%               95.1%
  optimizer updates               284                 200

v9 wins on every axis with 30% FEWER gradient updates, so the earlier
"not update-matched" caveat now runs in v9's favour rather than against it.
SFT re-sampled in the v9 run lands at 73.2 penalised vs 73.0 in the v8 run —
the two evaluations are comparable and nothing drifted.

MECHANISM. Speed CONDITIONAL on being correct is unchanged:
  meanF(correct) interp  v8 213.2  vs  v9 213.3
  meanF(correct) extrap  v8 182.1  vs  v9 181.6
Re-anchoring did not make designs faster. It stopped the policy emitting
INCORRECT ones (86.9% -> 95.1%). The entire equal-sample gain is correctness.

This closes a loop with the trajectory data (rtl/traj_v8, surrogate_v3 scored):
  step0  corr 94.3%  proxy  82.9
  s100   corr 95.8%  proxy 218.1     (77 updates)
  s200   corr 95.3%  proxy 213.7     (138)
  s300   corr 95.3%  proxy 216.6     (205)
  s400   corr 88.0%  proxy 497.9     (276)  <- saturation AND correctness drop
The proxy sits flat for ~200 updates, then explodes to the 500 clamp between
s300 and s400, and correctness collapses at exactly the same point. v9 never
saturates and never loses correctness. THE CORRECTNESS REGRESSION AND THE PROXY
SATURATION ARE THE SAME EVENT — "correctness is not uniformly preserved" was
never a separate defect, it is the overoptimization, measured. Three
independent observations (trajectory, endpoint error, repaired endpoint) agree.

Per-family, penalised MHz:
  family      sft   v8 grpo   v9 grpo
  fir        72.3     206.5     225.2
  firr       83.1     240.5     251.1
  poly       49.6     180.3     188.9
  iir       121.8     129.2     164.6   <- +27% over v8; the family whose
  med        18.1      20.0      18.4      surrogate error was worst
iir gains most from re-anchoring, which is exactly the prediction from the
family-dependent error measurement (iir was mispredicted even at SFT).
med remains flat under both — a combinational sorting network's critical path
is not shortened by style choice; that is a template limitation, not a reward
one, and stays a reported negative result.

STATUS: the arc capability -> diagnosis -> cause -> repair -> validation is
complete with real Vivado behind every link. The "proxy error was load-bearing"
reading is REFUTED: the error was doing damage, not work. TCAD estimate raised
~55% -> ~65%.

REMAINING for the preprint: Vivado on rtl/traj_v8 (144) and rtl/traj_v9 for the
Figure-1 measured line; P1 timing closure; P2 symmetric silicon; PRE1-PRE3.

---

## 2026-08-11 — Figure 1 measured line, and three-seed replication of v9

### Trajectory: predicted vs REAL Vivado along the optimisation path

`rtl/traj_v8` (144 modules) and `rtl/traj_v9` (134) synthesised on the laptop,
0 failures. Twelve held-out fir/firr designs, n=16 per checkpoint, count-weighted
over CORRECT candidates (Eq. 5 unpenalised). Checkpoints plotted against
CUMULATIVE OPTIMIZER UPDATES, not steps: grpo_v8_cont restarts its step counter,
so step-indexing would compare runs that got different amounts of optimisation.

BASIS MATTERS HERE and I initially mixed the two. meas(correct) = weighted over
CORRECT candidates (comparable with the prediction, which only ever scores
correct ones); meas(penalised) = incorrect scored 0 MHz (the equal-sample-cost
number the money table leads with). Both, so neither can be quoted loose:

traj_v8 (original surrogate)                traj_v9 (re-anchored)
upd  pred  m(corr) m(pen) corr%         upd  pred  m(corr) m(pen) corr%
  0   82.9    81.0   76.4  94.3           0  100.9    82.4   73.3  89.1
 77  218.1   240.5  230.5  95.8          69  332.6   244.1  227.6  93.2
138  213.7   242.2  230.9  95.3         116  332.6   242.1  237.0  97.9
205  216.6   242.2  230.9  95.3         159  332.6   241.5  231.4  95.8
276  497.9   241.2  212.3  88.0         200  333.2   240.7  238.1  99.0

The v8 endpoint is the failure in one row: prediction 497.9 (clip bound 500)
against 241.2 measured. CORRECTION to my first reading of this: measured Fmax
CONDITIONAL ON CORRECTNESS does not fall at all -- it is flat at ~241 from the
first checkpoint onward, including across the jump. The 230.9 -> 212.3 fall is
on the PENALISED basis, i.e. it is 100% the correctness term (95.3 -> 88.0).

That is the sharper mechanism statement, and it agrees with the independent v8-
vs-v9 finding that meanF(correct) is identical (213.2 vs 213.3): a saturated
reward does not make designs slower, it stops penalising the ones that do not
work. Figure 1 plots the meas(correct) basis, so its caption must NOT say
measurement fell.

### The regime split — the honest, and sharper, version

Splitting on interpolation (taps 6/10/18/26) vs extrapolation (36/40):

              v8 interp        v8 extrap        v9 interp        v9 extrap
upd/ck    pred   meas      pred   meas      pred   meas      pred   meas
step0      95.1   96.6      58.3   48.8      90.9   96.7     121.0   52.8
s100      256.6  267.1     141.0  185.5     253.8  268.2     490.1  188.4
s200      253.4  266.0     134.4  188.3     253.8  267.4     490.1  188.2
s300      257.1  267.9     135.5  188.3     253.8  266.7     490.1  188.2
s400      496.9  261.5     500.0  188.8     254.5  266.7     490.4  188.1

Two findings, one of them a correction to how I was about to write the caption:

1. Re-anchoring REPAIRS the interpolation region and does NOT repair the
   extrapolation region. The 43 re-anchor labels span 4..32 taps; at 36 and 40
   the v9 predictor sits at 490 from the FIRST checkpoint and never orders
   anything. Measured extrapolation frequency is therefore identical under both
   rewards (188.8 vs 188.1) — the repair's benefit is confined to where the
   labels reach. An aggregate curve hid this; the figure now plots the split.
   Do NOT write "the re-anchored predictor stays with measurement throughout".
2. The v8 correctness collapse is CONCENTRATED where saturation is worst:
   s300 -> s400 extrapolation 92.2% -> 73.4%, interpolation 96.9% -> 95.3%.
   The damage localises to the designs whose reward went uninformative.

This is a better claim than "the repair works": a learned reward is valid only
over the support of its supervision, and offline accuracy says nothing about the
region optimisation will travel to. It also predicts the fix (label the region
you will optimise into) and states its own limit.

Figures rebuilt: `paper/preprint/figures/fig1_trajectory.tex` (four series per
panel: predicted/measured x interp/extrap), `fig3_scatter.tex`.

### Three-seed replication of grpo_v9 (TRAIN-split training logs)

grpo_v9_s1 (253 updates, 36.8% flat) and grpo_v9_s2 (272, 32.0%) finished;
original v9 was 200 updates / 50.0% flat. Flat-group rate varies a lot run to
run — report the RANGE (32-50%), not the single figure currently in the draft.

Binned over training (group size 8, TRAIN designs, surrogate reward — NOT a
result, a training diagnostic):
  v9     surrF 120 -> 169, corr 91.9% -> 96.9%
  v9_s1  surrF 159 -> 227, corr 93.5% -> 88.0%
  v9_s2  surrF 133 -> 277, corr 88.9% -> 96.8%
Seed 2 climbs highest (max group mean 468).

CORRECTED 2026-08-11 (external review, verified): I wrote "ZERO groups reached
the clip bound in ANY of the three seeds (0.0%)". That was measured on the group
MEAN and stated as though no saturation occurred at all. WRONG. Group means
never reach the clamp, but individual CLAMPED CANDIDATES appear in every seed:
  grpo_v9_log.jsonl      3 groups (lines 8, 72, 82)
  grpo_v9_s1_log.jsonl   2 groups (lines 58, 238)
  grpo_v9_s2_log.jsonl   5 groups (lines 14, 82, 160, 174, 181)
Correct wording: "no group-mean saturation, but 2-5 logged groups per seed
contain a clamped candidate." The re-anchored reward reduces saturation
sharply; it does not eliminate it, which is what the preprint's limitation
section already said about the endpoint measurement and what the training logs
say too.

PENDING for the full paper (not the preprint): eval_holdout + Vivado for
grpo_v9_s1/s2 to turn this into a held-out seed-variance row. The preprint keeps
the single-seed limitation as written and can cite the training-side replication.

### PRE2 CLOSED — oracle x/z parse defect: real, demonstrated, zero verdicts changed

DEFECT (`oracle.py`, old line 231): the trace parser was
`[int(t) for t in r.stdout.split() if t.strip().isdigit() and 0 <= int(t) < 65536]`.
iverilog renders a 16-bit value with any unknown/high-Z bit as x/z (all bits
unknown) or X/Z (some bits unknown) under %0d -- verified empirically. Those
tokens are not digits, so the sample was DELETED, not compared. Deletion
shortens the trace and shifts every later sample one place earlier; align_score
searches over latency, so the shift can be absorbed.

Two incidental findings while confirming this:
 - iverilog writes "<file>:<line>: $finish called at <t> (<unit>)" to STDOUT,
   not stderr. Its "656000" token was excluded only by the `< 65536` range
   guard, i.e. by luck, not by design. The new parser skips multi-token lines
   explicitly (a %0d value print is always exactly one token on its line).
 - The old parser was also a FALSE-NEGATIVE source: an x in the middle of a
   trace misaligned everything after it (measured 0.3813 on a design that is
   0.9821 under the corrected parser).

EXPLOIT (constructed, reproducible): fir8_8b correct except its last ~16 output
cycles are undefined.
   OLD parser: len=493  match=1.0000  ACCEPTED   <-- false positive
   NEW parser: len=512  match=0.9622  rejected
A leading-X variant (first 15 cycles undefined, warmup=8) is rejected by both,
but for the wrong reason under the old one (0.0021, pure misalignment).

FIX: keep x/z IN PLACE as X_SENTINEL = -1 in an int32 trace; -1 never equals a
16-bit reference value, so an undefined sample counts as a mismatch while the
trace keeps its length. Deliberately NOT a hard reject: an unreset pipeline is
legitimately undefined while it fills, and align_score's warmup+latency window
already excuses exactly that prefix. Hard-rejecting would have thrown away
correct designs. Non-numeric, non-x/z single-token output, or a value >= 65536,
now returns None (candidate rejected) instead of being silently skipped.

RE-AUDIT (audit_oracle.py, now scores the legacy parse alongside the fixed one
by re-deriving the legacy trace as new[new != -1], so both verdicts come from
ONE simulation): all 1,529 stored candidates, seeds 1&2, n=1024.
   accepted by the current rule ........ 1529/1529
   emit x/z on some cycle .............. 18/1529
   accepted by OLD parse, not by new ... 0     <- no false positive was realised
   accepted by new parse, not by old ... 0
   exact equality / warmup=0 / frozen latency: 1529 survive each, 0 lost
   latency inconsistent across seeds ... 0
All 18 x/z candidates have undef counts of 1, 4 or 7 falling inside the
pipeline-fill prefix (latencies 1-9); all score exactly 1.0000 under both
parsers. Mostly poly7/poly4 from the student and v8_poly evals, plus six base-
policy candidates.

Prior audit output preserved as `audit_oracle_legacyparse.jsonl` for provenance.
Preprint Sec. VII rewritten to report the defect, the constructed exploit, the
fix, and the zero-verdicts-changed re-audit. This makes the section stronger,
not weaker: the acceptance criterion is now audited by EXECUTION, and the honest
statement is "a real defect that provably could have admitted a wrong design,
and provably did not".

NOTE for whoever runs the sandbox next: iverilog was again absent from this
container (ephemeral filesystem, as warned in CLAUDE.md). `apt-get install -y
iverilog` restored it; numpy also needed `pip install numpy`.

### PRE1 CLOSED — false claims purged from the manuscripts (2026-08-11)

1. **"timing-closed" (12 sites)** — `paper/main.tex`, `paper/sections/*.tex`,
   `paper/README.md`, `RESULTS.md`. The flow (`ppa_synth.tcl:72-79`) runs
   route_design, reads WNS from ONE 5 ns run, and computes 1000/(T - WNS). That
   is a post-implementation WNS-derived ESTIMATE, not timing closure — nothing
   iterates the constraint. All sites now say "WNS-derived". `04_setup.tex`
   gained the same explicit disclaimer the preprint already carried. The
   preprint was already correct and needed no change.
2. **"Correctness is preserved in aggregate"** (`05_results.tex`) — FALSE.
   88.7% -> 86.9%, a 1.8-point DECLINE. Rewritten with the regime split, which
   is the honest and stronger version: interp flat (92.8 -> 93.2), extrap down
   5.5 points (81.6 -> 76.1). The decline sits exactly where the reward is
   saturated, so it corroborates the trajectory finding instead of being an
   unexplained cost.
3. **best-of-48 (RESULTS.md 2b, 05_results.tex sec:bestofn)** — the claim "one
   GRPO sample beats a perfect selector over 48 SFT samples" came from the old
   22-design set. On the frozen 30-design set: interp 1 GRPO sample ~ perfect
   best-of-22 (198.7 vs bo16=191.4/bo32=206.6), extrap ~ best-of-8 (138.6 vs
   bo8=137.1). GRPO does NOT exceed bo48 in either regime. `analyze_bestofn.py`
   already printed the withdrawal; the prose had not been updated.
   Two SUPPORTING examples were also wrong, in the opposite direction:
     - firr10: SFT bo48 = 313.2 BEATS grpo bo1 = 300.7 (was cited as 68.9)
     - fir40:  SFT bo48 = 181.7 BEATS grpo bo1 = 94.7  (was cited as 20.9 —
       that number is the SFT MEDIAN, not its best of 48)
   So "existence failures sampling cannot fix" is WITHDRAWN. The SFT model does
   emit the fast form on both designs, rarely. Correct framing: reallocation of
   probability mass, not creation of missing implementations — which is what
   sec:mechanism concludes independently, so the paper loses nothing.
   fir40 corrected sample-cost: sft 38/48 correct, best real 181.8; grpo 25/48,
   best real 181.8 — IDENTICAL best Fmax. fir40 is a design where GRPO buys
   nothing and costs correctness, and it lives in the saturated region.
4. **ChipSeek-R1 "fabricated"** (MASTER_REFERENCE:376, HANDOFF:277) — WRONG.
   Verified real: arXiv:2507.04736, Chen/Chang/Li/He/Chen/Li/Wang/Xu/Han/Wang;
   retitled in a later version to "ChipSeek: Optimizing Verilog Generation via
   EDA-Integrated Reinforcement Learning" (check before camera-ready). ChipMATE
   and VFlow stay on the do-not-cite list as UNVERIFIED (no public record).

### Citations verified this session (all real; authors added to refs.bib)
  RTL-OPT      arXiv:2601.01765  Lu, Liu, Zhou, Fang, Zhang, Xie (Jan 2026)
  FormalRTL    arXiv:2603.08738  Li, Li, Wen, Zhao, Wu, Huang, Xu (Feb 2026)
  ChipSeek-R1  arXiv:2507.04736  (above)
  Dr. RTL      arXiv:2604.14989  Fang, Lu, Liu, Wang, Guo, He, Tu, Xie (HKUST)
  POET         arXiv:2603.19333  Ping et al. (USC)
  presynthesis PPA estimation, Fang et al., TCAD 2024
STILL MISSING: PPA-RTL author list (DOI 10.1109/DAC63849.2025.11132897) is not
recoverable from public listings; refs.bib carries a TODO. Fill from IEEE
Xplore before submission — do NOT guess it.

Related work grew two paragraphs. (a) Tool-in-the-loop 2026 work (Dr. RTL, POET)
optimises against the real tool, so it CANNOT have our failure — its signal is
ground truth. It pays in tool invocations, which is exactly what a learned
reward exists to avoid; our result is the price of that trade. (b) Learned
pre-synthesis PPA prediction (Fang TCAD'24, Ustun'20) is evaluated with held-out
accuracy and rank correlation — our point is not that these are inaccurate
(ours is accurate by those metrics and still useless as a reward) but that the
metric is measured on a distribution deployment will not preserve.
Also noted honestly: Dr. RTL argues for industrial flows over open-source tools
and degraded designs; our WNS-derived estimates do not meet that bar, and the
related-work section now says so rather than leaving a reviewer to find it.

Other 2026 work seen while verifying, NOT yet read or cited (for the full
paper): COEVO 2604.15001, Ares 2607.27879, RTLScout 2606.06530, Alpha-RTL
2606.05253, StepPRM-RTL 2606.04246, AutoGate 2606.17461, ASPEN (MLCAD'25),
ChipVerilog 2607.13079.

### PRE3 CLOSED — LODO leak fixed; the "offline metric picks the broken one" claim FAILS

Three separate problems, one of which invalidated a headline claim.

**(a) Normalisation leak (`surrogate_train.py`).** mu/sd were fit over ALL rows
and then used inside every LODO fold, leaking the held-out design's feature
distribution into its own evaluation -- worst for designs unlike the rest, i.e.
the extreme-Fmax rows the reward depends on. Now refit per fold. CONSEQUENCE:
every LODO number produced before 2026-08-11 is suspect, including the
0.965 / 0.75-0.82 figures in `01_introduction.tex:101`, `05_results.tex:308`,
`07_conclusion.tex:39`, `RESULTS.md:157,166`. Recompute before the full paper.

**(b) `mod` is not a unique row key.** The same module name recurs across data
dirs with different RTL and different measured Fmax; keying by it collapsed 177
rows to 139. Rows now carry `key` (= <dir>/<mod>) and `src`. Anything keying
surrogate rows by module name has been silently merging distinct measurements.

**(c) The published offline comparison was TWO artifacts stacked.** The preprint
said LODO rho 0.965 -> 0.841, therefore "a practitioner selecting by
cross-validation would have kept the broken one". Reconstructing the datasets:
    surrogate_v2 = probe_v4 + data + policy_cmp            = 203 rows, 35 designs
    surrogate_v3 = v2 + fmax_d2                            = 229 rows, 41 designs  <- what grpo_v8 used
    surrogate_v4 = v3 + fmax_d3                            = 272 rows, 41 designs
So 0.965 is **v2**, not v3 -- the published before/after skipped the predictor
actually used -- AND the two figures were computed on different row sets.

MATCHED-SET RESULT (`compare_surrogate_lodo.py`, identical 229 target rows,
fold-local normalisation, 5 restarts averaged, epochs=300 = the real training
setting; NOT 4000, an early run of mine used 4000 and was both slow and
unfaithful):

  arm             rows  Spearman   top-1   mean err    MAE   >clamp
  surrogate_v3     229     0.930   25/30      +7.0    20.2        6
  surrogate_v4     229     0.919   26/30      +4.5    21.7        6
  per-metric preference for v3: spearman +0.010, top1 -0.033, bias -2.481

**INDISTINGUISHABLE.** Gap 0.010, below any reasonable noise margin, and the
metrics disagree in direction (rho/MAE lean v3; top-1/bias lean v4). The strong
claim is WITHDRAWN. The script now refuses to call a sub-0.03 difference a
preference -- its first version reported this same result as "supported", which
is exactly the kind of over-generous verdict this project keeps having to catch.

The surviving claim is cleaner and needs no assumption about which model CV
prefers: **no offline metric available at selection time separates the two**,
while under optimization they differ by an order of magnitude (bias +235.9 vs
+30.7 MHz; saturated cells 25/30 vs 2/30). Offline validity does not transfer;
the failure is INVISIBLE, not merely misleading. Preprint contribution #3 and
Sec. VI rewritten accordingly, with a new Table (tab:lodo) and an explicit
sentence retiring the earlier number.

**Incidental finding, kept in the paper.** Holding out `med3` (no near neighbour
in the training rows) makes the MLP predict log-Fmax = 3.5e6 -- exp() of that
overflows to inf and silently turned mean-err/MAE into inf in the first run.
BOTH arms do it, 6 rows each. Rank statistics absorb it without comment while
still reporting rho > 0.9. It is the same off-support blow-up the reward clamp
exists to contain, now visible inside a plain offline metric. Errors are now
reported after applying the reward's own [5, 500] MHz clamp, and rows above the
clamp are counted (`n_above_clamp`).

**Verified positively:** invariant #3 holds -- zero held-out designs appear in
the surrogate training rows under ANY combination of the five data dirs.

Sandbox notes: torch installed from default PyPI (the pytorch.org CPU index is
403 through the proxy); iverilog via apt; numpy via pip. All ephemeral.

### 2026-08-11 (later) — self-verification harness, and one error it caught in MY OWN work

`verify_claims.py` reproduces every claim-changing number of today from
committed artifacts, printing claimed-vs-computed so a disagreement is visible
without reading prose. Sections A-D are deterministic (pure numpy over
ppa.jsonl + manifests). Section E (--lodo N) reruns the UNSEEDED LODO N times.

Run: `python verify_claims.py` / `python verify_claims.py --lodo 10`
Current status: A, B, C, D all reproduce.

**Error it caught (mine).** I quoted the trajectory as "measurement DROPS
230.9 -> 212.3" while Figure 1 plots the over-CORRECT basis, on which measured
Fmax is FLAT (242.2 -> 241.2). I had mixed the penalised and over-correct bases
between the aggregate row and the regime split. Corrected everywhere; the
trajectory table above now carries BOTH columns. The corrected reading is
stronger: a saturated reward does not make correct designs slower, it stops
penalising incorrect ones -- which independently agrees with meanF(correct)
being identical across v8/v9 (213.2 vs 213.3). Preprint Tab. III gained a
measured column and a paragraph making exactly this point; Fig. 1's caption
gained the "what measurement does NOT do" sentence.

**Weakness I have NOT resolved, flagged loudly.** `surrogate_train.py` sets no
random seed, so today's 0.972 / 0.915 / 0.913 LODO figures are single draws.
The figure they replaced (0.75-0.82) was explicitly reported as a seed RANGE.
A single draw cannot refute a range. Until `verify_claims.py --lodo 10` shows
the v3 spread sitting clear of 0.75-0.82, the corrected numbers in
01_introduction.tex / 05_results.tex / 07_conclusion.tex / RESULTS.md should be
treated as PROVISIONAL. Three confounds separate them from the old figures:
fold-local vs leaked normalisation, 12 vs 9 features, and one draw vs a range.
NOTE the matched-set v3-vs-v4 comparison does NOT have this problem -- it seeds
each fold explicitly and averages 5 restarts.

Sandbox toolchain (all ephemeral, reinstall after a container reset):
  apt-get install -y iverilog
  apt-get install -y --no-install-recommends texlive-latex-recommended \
      texlive-latex-extra texlive-fonts-recommended texlive-pictures \
      texlive-publishers          # IEEEtran lives in texlive-publishers
  pip install numpy torch          # the pytorch.org CPU index 403s via the proxy;
                                   # default PyPI works
Preprint builds clean: 7 pages, 0 undefined refs, 0 overfull boxes.

### 2026-08-11 — PREPRINT DELETED at the user's instruction

`paper/preprint/` removed in full (main.tex, refs.bib, make_figs.py,
figures/fig1_trajectory.tex, figures/fig3_scatter.tex, README.md, build
artifacts). Decision: stop the preprint track, wait for the user's own
`verify_claims.py` run, then start the CCF-A paper from the beginning.

RECOVERABLE: everything is in git history. To get it back:
    git log --oneline --diff-filter=D -- paper/preprint    # find the delete commit
    git checkout <commit>^ -- paper/preprint

PRESERVED BEFORE DELETING (do not re-derive these):
 - The verified 2026-08-11 citations were merged into `paper/refs.bib`, which
   previously lacked five of them entirely: chipseek2025, fang2024presynthesis,
   formalrtl2026, gao2023scaling, ppartl2025. Two more (drrtl2026, poet2026)
   were present but author-less and have been replaced with the verified
   versions. Full-paper bib is now 25 entries. ppartl2025 still carries its
   TODO -- author list not publicly recoverable, fill from IEEE Xplore, never
   guess it.
 - `make_figs.py` is GONE with the directory. It generated Fig. 1 (predicted vs
   measured trajectory, split interp/extrap) and Fig. 3 (predicted-vs-measured
   scatter) as pgfplots fragments. Recover from git if the CCF-A paper wants
   either; the full paper has its own `paper/make_figures.py`, which is a
   different script.
 - All analysis scripts survive at repo root and are untouched:
   verify_claims.py, compare_surrogate_lodo.py, analyze_bestofn.py,
   analyze_policy_fmax.py, analyze_surrogate_error.py, analyze_passk.py,
   audit_oracle.py, rescore_surrogate.py.

STATE OF THE EVIDENCE at the moment of deletion (nothing below is affected by
removing the preprint -- these are measurements, not prose):
 - A/B/C/D of verify_claims.py reproduce. Trajectory, best-of-N, aggregate
   correctness and the oracle audit are all deterministic over committed
   artifacts.
 - PROVISIONAL and awaiting the user's `--lodo 10`: the 0.972 / 0.915 / 0.913
   LODO figures now in 01_introduction.tex, 05_results.tex, 07_conclusion.tex
   and RESULTS.md. Single unseeded draws against a figure (0.75-0.82) that was
   itself a seed range. If the v3 spread overlaps 0.75-0.82 these must revert
   to a range and my correction was wrong.
 - NOT provisional: the matched-set v3-vs-v4 comparison (0.930 vs 0.919,
   indistinguishable) seeds each fold and averages 5 restarts.

NEXT: wait for the user. Do not resume writing until they report the
verify_claims.py output.

### 2026-08-11 (verification round) — user reran verify_claims.py; two of my numbers moved

**E. LODO stability, n=10 unseeded restarts per arm (user's laptop).** The
correction to the 0.75-0.82 figure is ESTABLISHED, decisively:
    surrogate_v2 (203, 3 fam)    0.974 +/- 0.003   range .969-.978
    surrogate_v3 (229, 5 fam)    0.923 +/- 0.008   range .910-.931
    surrogate_v4 (272, re-anch)  0.905 +/- 0.009   range .890-.922
The v3 range bottoms out at 0.910 and never approaches 0.75-0.82. The old
figures died of leaky normalisation + a 9-feature extractor, not of chance.

MY SINGLE DRAWS WERE UNLUCKY IN BOTH DIRECTIONS: I quoted v3 = 0.915 (near the
bottom of its range, true mean 0.923) and v4 = 0.913 (near the TOP, true mean
0.905). Paper now carries means +/- sd, not point draws. Sections A-D of
verify_claims.py reproduced exactly on the user's machine.

**Matched-set gap, now with error bars (5 independent restart-seed bases via
`--seed-base`, 229 identical rows, 5 restarts averaged per fold each).** I added
this because a 0.011 gap quoted without a spread is not a result:

  metric        v3 (original)      v4 (re-anchored)   gap              favours v3
  Spearman      0.928 +/- 0.012    0.925 +/- 0.005    +0.004 +/- 0.012   4/5
  top-1/30      0.847 +/- 0.038    0.833 +/- 0.024    +0.013 +/- 0.045   3/5
  |bias| MHz    7.30 +/- 0.41      4.44 +/- 0.67      -2.86 +/- 1.02     0/5
  MAE MHz       19.84 +/- 1.13     21.36 +/- 1.07     +1.52 +/- 1.48     4/5
  Spearman gap per base: +0.011 +0.007 +0.015 +0.002 -0.017; t = 0.64 (df 4).

VERDICT, and note I was wrong TWICE on the way here. First I let the script call
a 0.011 gap "supported". Then, after three replicates all favoured v3, I told
the user the direction was consistent and "indistinguishable" was too strong.
The fifth replicate flipped sign. With all five: the Spearman gap is t = 0.64,
i.e. nothing. The original "indistinguishable" reading was right; my three-point
impression was a small sample fooling me exactly the way single draws fooled me
in section E. Do not report a direction for Spearman or top-1.

What DOES separate them: mean signed error, 5/5, 7.30 vs 4.44 MHz, t ~ 6.3. The
re-anchored predictor is better CALIBRATED and that is measurable offline.

**The sharper thesis this licenses (use this framing, not "offline accuracy
doesn't transfer"):** GRPO's advantage is group-relative and z-scored, so reward
SCALE is irrelevant and only WITHIN-GROUP ORDERING drives the gradient. The
offline metric that matters is therefore rank, and rank is precisely what LODO
measures -- and it reports ~0.93 for both rewards. The failure is not that the
offline metric measures the wrong quantity. It measures the RIGHT quantity on
the WRONG DISTRIBUTION: under optimization the policy moves to where the
predictor saturates (25/30 cells at the clamp, median within-design real spread
0.0 MHz), which destroys ordering exactly there, while the LODO rows -- drawn
from the pre-optimization distribution -- retain it. Calibration error catches
what rank misses only because saturation shows up as bias before it shows up as
inversion.
CAVEAT before this goes in a paper: the flat-group counts (32-50% across v9
seeds) are CONSISTENT with saturation-induced ties killing the gradient, but I
have not measured per-group reward variance at the saturating checkpoint. That
measurement is cheap and should be done before the mechanism is asserted.

`compare_surrogate_lodo.py` gained `--seed-base`. Reproduce with:
  for sb in 0 10 20 30 40; do python compare_surrogate_lodo.py \
    --a rtl/fmax_probe_v4 rtl/fmax_data rtl/policy_cmp rtl/fmax_d2 \
    --b rtl/fmax_probe_v4 rtl/fmax_data rtl/policy_cmp rtl/fmax_d2 rtl/fmax_d3 \
    --label-a v3 --label-b v4 --epochs 300 --seeds 5 --seed-base $sb \
    --out /tmp/lodo_sb$sb.json; done

### 2026-08-11 — MECHANISM HYPOTHESIS REFUTED (measured before it reached a paper)

I proposed: saturation ties the group rewards -> zero variance -> no gradient.
MEASURED from grpo_v8_log.jsonl + grpo_v8_cont_log.jsonl (284 steps), it is the
OPPOSITE. Field semantics first (grpo_oracle.py:326-327): `mean_fmax` is the mean
of rewards WHERE reward > 0, i.e. over CORRECT candidates only; `max_fmax` is the
group max. So (max - mean) measures spread among CORRECT candidates -- the
ranking question -- and is NOT the flat-group statistic (`r.std() < 1e-6` at
:295, over the full group including zeros, so a mixed correct/incorrect group is
essentially never flat; the 32-50% flat rates in v9 are all-correct-identical or
all-incorrect groups).

  step-range   mean   max    gap   %steps gap<1   %steps mean>=490
    112- 140  203.7  204.7    1.0        92.9%          0.0%
    140- 168  196.9  220.8   24.0        85.7%          0.0%
    168- 196  211.4  216.1    4.7        82.1%          0.0%
    196- 224  190.8  203.5   12.7        75.0%          0.0%
    224- 252  273.5  313.6   40.1        57.1%          7.1%
    252- 280  300.0  335.2   35.2        46.4%         17.9%

Through mid-training the reward is near-SILENT among correct candidates (gap
< 1 MHz on 75-93% of steps). During saturation the gap WIDENS (40, 35) and
flatness FALLS (57% -> 46%).

CORRECTED MECHANISM: saturation does not remove the gradient, it MANUFACTURES a
large and confident one toward distinctions that do not exist in reality. The
policy is pushed hard toward whatever lexical features trigger a ~500 MHz
prediction; correctness degrades as the side effect (95.3 -> 88.0); measured
Fmax conditional on correctness does not move (flat ~241). This is consistent
with, and explains, the earlier finding that meanF(correct) is identical across
v8/v9 while correctness differs.

Do NOT write "the reward goes quiet" or "ties kill the gradient". Write: the
reward becomes strongly opinionated about differences that are not real.

Caveat for the paper: this uses (max - mean_over_correct) as the spread proxy
because per-group reward variance was never logged. Logging r.std() per step in
grpo_oracle.py would make the claim direct and costs one line; do that before
the mechanism figure is drawn.

### 2026-08-11 — ARCHITECTURE ABLATION: the reviewer's objection is CORRECT

`surrogate_arch_ablation.py`. No GPU, no new policy run: the off-support
distribution already exists as stored artifacts. Train each predictor on the
SAME 229 v3 rows (pre-optimization distribution, held-out designs excluded by
invariant #3); test on the 345 held-out candidates the OPTIMIZED policy produced,
each carrying a real Vivado frequency. That is exactly the endpoint measurement,
run per architecture.

architecture      policy   bias MHz   saturated   rho
mlp12 (paper's)   sft         +12.4      0/30    0.794
                  grpo        +89.0      7/30    0.227
gbm12             grpo        +27.6      0/30    0.330
rf12              grpo        -13.0      0/30    0.489
knn12             grpo        -11.1      0/30    0.543
ngram_ridge       sft          +0.5      0/30    0.956
                  grpo         -0.2      0/30    0.804   <-- calibrated
ngram_gbm         grpo        -20.1      0/30    0.451

**ngram_ridge (character 3-5 grams, TF-IDF, RidgeCV -- no deep learning at all)
is essentially unbiased on the optimized policy: bias -0.2 MHz, MAE 22.5 MHz,
0/30 saturated, predicted sd 61.4 vs real sd 62.9, range 40-313 against a real
23-347.** It is NOT predicting the mean; it tracks.

CONCLUSION, and it is bad for the framing we had: the collapse is a property of
the TWELVE HAND-ENGINEERED FEATURES, not of learned physical rewards in general.
The generality claim ("learned rewards break under optimization") is NOT
supported. Every non-MLP arm is better calibrated on the optimized policy than
the paper's predictor, and the richer-representation arm is calibrated outright.

CAVEATS, all of which must be stated before this is used:
 1. My mlp12 refit gives grpo bias +89.0 / 7-of-30, while the DEPLOYED
    surrogate_v3 measured +235.9 / 25-of-30 (rescore_surrogate.py against the
    actual checkpoint). Same qualitative direction, milder. The cross-
    architecture comparison is internally consistent (identical rows, identical
    protocol) but the mlp12 absolute numbers are NOT the paper's numbers.
    Re-run the ablation scoring the deployed checkpoint as the mlp12 arm before
    publishing the table.
 2. Designs are procedurally generated (limitation F6). An n-gram model may be
    matching implementation STYLE across tap counts -- legitimate
    generalisation, but a reviewer may read it as template matching. The
    honest statement is that it generalises across the frozen held-out split,
    which is what we froze it for.
 3. Single split, single fit. Needs restarts / multiple splits for error bars.

WHAT THIS DOES TO THE PAPER. The old thesis ("learned physical rewards collapse
under optimization; offline metrics cannot see it") is not supportable as
stated. The supportable and more useful thesis:
  - The collapse is real, consequential, and measurable against silicon.
  - Its CAUSE is an impoverished feature representation, not learned reward
    modelling per se.
  - A standard richer representation, trained on identical data, is calibrated
    exactly where the hand-engineered one fails -- so the fix is cheap and does
    not require more labels.
  - Therefore: a reward model must be validated on the OPTIMIZED distribution,
    and representation capacity is the axis that matters.
That is a paper with a solution rather than only a warning.

FOLLOW-ON THAT IS NOW OBVIOUS: retrain the surrogate with n-gram features and
re-run GRPO. If reward hacking disappears and held-out Fmax improves, that is a
positive result to go with the negative one. This supersedes re-anchoring as
the recommended repair.

### 2026-08-11 — ARCHITECTURE ABLATION, deployed checkpoint, run by the user on
### the server. VERDICT: the generality claim is DEAD; the collapse is OURS.

`surrogate_arch_ablation.py --repeats 3 --ckpt surrogate_v3.pt`. Train every
predictor on the SAME 229 v3 rows; test on the 345 held-out candidates the
optimized policy produced, each with a real Vivado frequency. Reproduced
independently on the laptop (identical to 3 decimal places except the MLP arm,
which has random restarts).

architecture      grpo bias   saturated   cross-design rho   (sft bias / sat)
mlp12_deployed      +235.9      22/30          0.325           +4.7  / 0-30
mlp12_refit          +89.0       7/30          0.227          +12.3  / 0-30
gbm12                +27.1       0/30          0.326           +1.4  / 0-30
rf12                 -13.2       0/30          0.481           +4.8  / 0-30
knn12                -11.1       0/30          0.543           +6.6  / 0-30
ngram_ridge           -0.2       0/30          0.804           +0.5  / 0-30
ngram_gbm            -18.8       0/30          0.455           +1.0  / 0-30

ESTABLISHED:
 - Saturation is UNIQUE to the deployed 12-feature MLP. 22 of 30 optimized
   cells pinned at the clamp; ZERO for all five alternatives, including a
   gradient-boosted model on the SAME twelve features. So it is not even the
   feature set alone -- the MLP's unbounded extrapolation is the proximate
   cause, and richer features remove the residual bias on top of that.
 - Every architecture predicts the SUPERVISED distribution well (+0.5 to
   +12.3 MHz). The entire difference lives on the optimized distribution.
 - ngram_ridge (char 3-5 grams, TF-IDF, RidgeCV -- no deep learning) is
   unbiased there: -0.2 MHz, 0/30 saturated, cross-design rho 0.804 against
   the deployed reward's 0.325.

THEREFORE the claim "learned physical rewards collapse under optimization" is
NOT SUPPORTED. What we measured is that OUR reward did, and that several
standard alternatives trained on identical data do not. Any paper text asserting
generality over learned rewards must be rewritten. The defensible thesis:
  - the collapse is real, consequential, and silicon-validated;
  - its cause is the predictor's representation and unbounded extrapolation,
    not learned reward modelling as such;
  - the fix is cheap and needs NO new labels -- a standard richer
    representation on the same 229 rows;
  - so a reward model must be validated ON THE OPTIMIZED DISTRIBUTION, and
    representation/extrapolation behaviour is the axis that matters.
This supersedes re-anchoring (43 new labels) as the recommended repair.

NOT ANSWERABLE FROM THESE ARTIFACTS, and I initially reported it as if it were:
within-design ranking on the optimized distribution. Only 3 of 30 optimized
designs have >= 3 DISTINCT real frequencies -- the policy converges onto one
implementation, so there is nothing left to rank. My first version of the metric
required 3 distinct (pred, real) PAIRS, which let arms with more varied
predictions qualify on more designs (3 for mlp12_deployed vs 9 for ngram_ridge),
i.e. the arms were averaged over DIFFERENT design subsets and were never
comparable. Eligibility now depends on the real values only. The column is
retained but is underpowered by construction on the optimized policy; do not use
it to separate architectures. Answering the question needs candidates with
genuine within-design diversity, which these evals do not contain.

REMAINING CAVEAT: designs are procedurally generated (F6). An n-gram model may
be recognising implementation STYLE across tap counts. That is legitimate
generalisation across the frozen held-out split -- which is what the split was
frozen for -- but a reviewer may read it as template matching, and the paper
should say so before they do.

OBVIOUS FOLLOW-ON: retrain the surrogate with n-gram features and re-run GRPO.
If reward hacking disappears and held-out Fmax improves, the paper gains a
positive result to sit beside the negative one.

### 2026-08-11 — external review, adjudicated

Three claims checked against the files. Two upheld, one superseded.

1. UPHELD, and it was my error. "Zero groups reached the clamp" was measured on
   the group MEAN. Individual clamped candidates appear in every seed (2-5
   groups each). Corrected in place above, with line numbers.

2. UPHELD, and it is the sharpest point anyone has made about the ablation.
   **The n-gram model was chosen by looking at the optimized distribution.**
   Six architectures were scored on the 345 post-optimization candidates and
   the best one was reported. That is selection on the test set. What the
   ablation licenses is "a richer representation WOULD HAVE predicted this
   optimized distribution well", NOT "a richer representation prevents the
   collapse". The latter requires using it as the reward and running GRPO.
   Until then, do not write that n-grams fix anything.
   Note the recursion, which is the interesting part: an n-gram reward fitted
   on the same 229 rows has UNKNOWN validity on the distribution that n-gram-
   guided GRPO would create. The paper's own thesis says you cannot know in
   advance. So both outcomes are publishable -- no collapse means
   representation is the actionable axis; a collapse at a different rate means
   the deeper claim (any learned reward is eventually exploited; representation
   changes only how fast) survives and is stronger.

3. SUPERSEDED. "Documentation drift: knn12 GRPO rho documented 0.543 but
   committed 0.604." The reviewer read commit b76f540, the LAPTOP run, before
   the server run (cb5981b) replaced it. The current committed file has 0.543
   and MASTER_REFERENCE matches it.
   BUT a real issue hides underneath: knn12 is deterministic, and the laptop
   produced 0.604 where the sandbox and server both produced 0.543. Same data,
   same code, different sklearn/numpy build. Pick ONE canonical environment for
   every number that reaches the paper and record its versions; do not mix
   machines within a table.

Also upheld and already known: the seed pushes are TRAINING LOGS only -- no
seed-specific candidates, oracle summaries, manifests or Vivado results, so
they are not outcome replications; and the current manuscript still presents
correctness-gated GRPO as the central contribution and contains none of the
trajectory, re-anchoring, seed or ablation work.

### 2026-08-11 — THE REWARD HACK, OBSERVED. Layout channel, verified in source.

The invariance gate said the deployed reward is vulnerable to line count. The
TRAJECTORY says the policy USED it. Both verified here against committed files.

rtl/traj_v8, 12 held-out fir/firr designs, count-weighted per checkpoint:

  ckpt    lines  nb_assign  tokens  blank  cmt   real Fmax   surrogate
  step0    32.3       17.2   494.8   0.00 0.00        81.0        82.9
  s100     36.2       24.2   515.2   0.00 0.00       240.5       218.1
  s200     36.0       24.0   509.7   0.00 0.00       242.2       213.7
  s300     36.4       24.4   520.5   0.00 0.00       242.2       216.6
  s400     56.5       44.4   496.9   0.00 0.00       241.2       497.9

s300 -> s400: lines +20.1, nb_assign +20.0 (tracks lines almost exactly),
TOKENS -23.6 (the code got SMALLER), surrogate +281.3, real -1.0.
Zero blank lines and zero comments at every checkpoint, so the literal
blank-line attack from the gate was NOT the channel.

MECHANISM, visible in the source (fir18_8b, same design, consecutive ckpts):
  s300 (33 lines): a0 <= 24'd0; a1 <= 24'd0; a2 <= 24'd0; a3 <= 24'd0; ...
  s400 (51 lines): a0 <= 24'd0;
                   a1 <= 24'd0;
                   a2 <= 24'd0;
`nb_assign` = re.findall(r"^\s*\w+(?:\[[^\]]*\])?\s*<=", txt, MULTILINE)
counts assignments that BEGIN A LINE. Packed: 1. Split: 18. Same hardware.
The policy learned that pressing Enter raises the reward.

THIS IS THE PAPER'S CENTRAL FIGURE. It is a reward hack with real Vivado
measurements on both sides, a mechanism visible in two lines of source, and a
feature definition that explains it exactly.

THE TWO-PHASE STORY, which is stronger than either previous framing:
  phase 1 (to ~step 100): the physical reward teaches genuinely faster RTL.
    81.0 -> 240.5 MHz REAL. This is the positive result and it is unaffected.
  phase 2 (~step 300-400): continued optimization discovers a layout channel.
    surrogate +281 MHz, real -1 MHz, correctness 95.3% -> 88.0%.
"The reward was useful early and hacked late" -- not "it worked" and not "it
failed".

CREDIT: the layout hypothesis came from the external reviewer, who derived it
from the line/token/nb_assign drift before we had looked. Verified independently
here.

CAVEATS carried forward:
 - trace equality certifies the SAMPLED mutants (40 candidates x 2 seeds x 256
   vectors), not equivalence for all inputs. For comments/whitespace the
   unchanged token stream is the stronger argument.
 - the gate's "operational" groups are reconstructed (policy, design) sets of
   deduplicated eval candidates, NOT the actual 8-sample training groups. They
   are counterfactual decision-sensitivity metrics. The prospective run must log
   real training groups and compute advantage directly.

NEXT: analyze_reflow_attribution.py re-scores every trajectory candidate under a
layout-canonical form (comments stripped, one statement per line) and reports
what share of the s300->s400 jump disappears, plus token-identical cross-
checkpoint pairs (same tokens, same hardware, different reward). Then STOP
diagnosing v8.

### 2026-08-11 — ATTRIBUTION CLOSED. The late reward jump is 100% layout.

`analyze_reflow_attribution.py --ckpt surrogate_v3.pt`, 144 stored v8 trajectory
candidates, canonicalisation verified LOSSLESS (0/144 token streams changed).

ckpt   upd  raw pred  canon pred    real   lines  nb_raw  nb_can  tokens
step0    0      83.3       201.8    81.0    32.3    17.2    25.8   430.8
s100    77     219.5       494.2   240.5    36.2    24.2    46.3   424.9
s200   138     217.3       496.5   242.2    36.0    24.0    46.0   419.8
s300   205     218.0       497.5   242.2    36.4    24.4    46.8   429.5
s400   276     497.7       494.1   241.2    56.5    44.4    44.4   411.1

  s300 -> s400 reward jump, RAW layout        +279.7 MHz
  s300 -> s400 reward jump, CANONICAL layout    -3.4 MHz
  s300 -> s400 real Vivado change               -1.0 MHz
  share of the jump removed by canonicalisation: 101.2%

Under a uniform layout the late "gain" is -3.4 MHz, which matches the measured
-1.0 MHz. The entire +279.7 was formatting.

THE CLEANEST STATEMENT OF THE HACK, straight from the table:
  nb_CANON is essentially FLAT across s100/s200/s300/s400: 46.3, 46.0, 46.8,
  44.4 -- the design has ~46 nonblocking assignments the whole time.
  nb_RAW goes 24.2, 24.0, 24.4 -> 44.4. The policy did not add assignments; it
  moved them onto their own lines so the line-anchored regex would count them.
  At s400, nb_raw == nb_can == 44.4: the policy had converged ONTO the canonical
  layout, which is why canonicalisation changes nothing there and everything at
  s300.

NULL RESULT, reported: zero token-identical cross-checkpoint pairs. The policy
changed tokens as well as layout between checkpoints, so the "same tokens,
different reward" figure does not exist in these artifacts. The attribution
number carries the claim instead.

CAVEAT THAT MUST TRAVEL WITH THE 101.2% -- do not drop it. The canonical scores
sit at 494-497 for every checkpoint from s100 on, i.e. AT THE 500 MHz CLAMP.
The existing predictor was trained on raw-layout rows where nb_assign has a
different distribution, so feeding it canonical text saturates it. This is
therefore an ATTRIBUTION DIAGNOSTIC, not a demonstration that canonicalisation
yields a working reward. Applying canonical form to the deployed predictor
would replace one broken reward with another. The repair requires RETRAINING on
canonical representations -- the rf_struct plan -- and its success is an open
question this analysis does not answer.

YOSYS: conda create -p /tmp/yosys_test -c conda-forge yosys SUCCEEDS.
Yosys 0.68+ available. The structural canonicalisation path is open; the lexical
fallback is no longer needed as the primary route. Install into the persistent
env (-p /zeng_gk/Amine/mas/env_mas) before relying on it -- /tmp is ephemeral.

### 2026-08-11 — canonicalize.py v1.0.0 built; lexical backend PASSES the contract

`canonicalize.py --backend lexical` over 490 stored candidates
(holdout_eval_v8_* + traj_v8):

  contract PASSED     489/490
  rejected              1/490  (base__fir26_8b__g2.sv, explicit refusal:
                                macro/function/task/generate/multi-module)
  equivalence merges     91    (same design, different spelling -- CORRECT)
  collisions              0    (different designs, same canonical form)

Contract clauses all verified per candidate: idempotence C(C(x))==C(x); bytewise
equality of C(x) and C(m(x)) for m in {comments, blanklines, whitespace, reflow,
pack, rename}; explicit rejection of unsupported syntax; identical structural
features across the whole suite. `reflow` is the OBSERVED attack (one statement
per line) and `pack` its inverse, so the exploited channel is in the suite by
construction.

STRUCTURAL FEATURES (STRUCT_FEATURES) deliberately differ from the deployed 12:
  n_lines    DELETED -- it is the exploited channel and has no hardware meaning
  nb_assign  was line-anchored `^\s*\w+...<=`; now a statement-level token count
  accum      was `\b[a-z]+\d` i.e. it read SIGNAL NAMES; now a token-shape match

ERROR I MADE AND CAUGHT: the first collision audit counted "different raw token
streams -> same canonical form" as a failure and reported 91 collisions. That is
the canonicaliser WORKING -- alpha-renaming exists so that `acc0` and `a0`
collapse. All 91 groups are within a single design. The audit now defines a
collision as DIFFERENT DESIGNS sharing a canonical form (different reference
models => different hardware), which is 0. The rigorous version compares oracle
traces and belongs in the frozen pre-registration run.

YOSYS BACKEND IS UNTESTED. It is written (read_verilog -> proc; opt_clean ->
write_rtlil, src/hdlname attributes stripped, autogen ids renumbered) but no
yosys exists in the sandbox. It must be contract-tested on the server before it
is preferred over lexical; until then the honest claim is LEXICAL invariance.

OPEN, and a genuine go/no-go before any GPU time (Check A): does canonicalising
the 229 labelled training rows COLLAPSE their feature diversity? Rows that
become feature-identical with different real Fmax are label noise rf_struct
cannot resolve. If diversity collapses, rf_struct is a weak reward before it
ever meets a policy.
Second pre-registered risk (Check B): a bounded RF cannot extrapolate. Off
support it returns a leaf mean and supplies NO gradient. That is the failure
mode which replaces saturation, and "canonical GRPO barely moves" must be
called in advance rather than discovered.

### 2026-08-11 — canonicaliser v1.5.0; Check A GO (conditional on traces)

CONTRACT (server, v1.4.1, lexical, 490 candidates): 484 passed, 1 rejected,
0 collisions, **5 TRACE FAILURES**. The five are an OPEN BLOCKER: the go rule is
zero unsafe semantic merges, and a trace failure means the canonicaliser changed
a design. They must be diagnosed and the check re-run at v1.5.0, whose canonical
output differs from v1.4.1.

CHECK A (sandbox, v1.5.0, 229 training rows, held-out already excluded):
  material within-design pairs .......... 389
  unorderable (identical features) ...... 5  (1.3%)
  family rates: fir 0.0  firr 0.0  poly 0.0  iir 0.0  other 0.0  med 21.7%
  unsafe semantic merges ................ 0
  rejection rate ........................ 0.00%
  VERDICT: GO  (all four preregistered thresholds met)
NOTE: med at 21.7% is a MARGINAL pass against a 25% ceiling, on the one family
GRPO already gains nothing on. Report it as marginal; do not present 1.3% alone.

TWO DEFECTS CHECK A CAUGHT, both fixed before any freeze:
 1. `for (i = 0; i < 5; i = i + 1)` contains semicolons, and the statement
    splitter broke on EVERY `;`, shredding loop headers into three pseudo-
    statements. Both the canonical emitter and the feature extractor now split
    only at parenthesis depth 0.
 2. No feature saw loop TRIP COUNTS. Two med5 candidates differing only in
    `n6 < 5` vs `n6 < 4` -- i.e. in how many comparator stages the loop unrolls
    into -- measured 60.4 and 38.3 MHz with byte-identical feature vectors.
    Added n_loops, loop_bound_max, loop_bound_sum. A loop bound determines the
    synthesised hardware and cannot be altered by any layout change, so this is
    a structural feature, not a fitted one.

PROVENANCE OF THAT FIX, stated because it matters: the loop features were added
AFTER seeing Check A fail, on TRAINING data only, before the freeze, and the
external review explicitly directs "fix the representation" on a NO-GO. It is
not tuning against v8 outputs or the sealed split, neither of which was
consulted. med moved 30.4% -> 21.7%; the threshold was not moved.

ALSO FIXED at v1.4.2: the v1.3.0 classifier rewrite had silently dropped
n_regs / n_wires / n_ternary from the feature dict. check_a raised KeyError
before they could reach a frozen vector.

BACKEND DECISION, LOCKED: lexical. Yosys reached 33/60 on the byte contract and
would additionally need an RTLIL-specific feature extractor -- the current
features count Verilog tokens (`<=`, `posedge`, `*`) that `proc; opt_clean` no
longer represents -- plus its own Check A. It is the TCAD extension. The claim
we make is LEXICAL invariance.

### 2026-08-11 — the 5 trace failures: SystemVerilog unsized fill literal. FIXED.

The trace check (which exists because byte-level metamorphic equality cannot
prove the canonical form is the same circuit) found 5 of 490 canonical forms
that DO NOT COMPILE. Originals all simulate; the defect was entirely ours.

CAUSE, one token:
    original   a0 <= '0;
    canonical  n0 <= ' 0 ;          <- invalid
`'0` is the SystemVerilog UNSIZED FILL literal. The tokenizer's number pattern
required a base letter (`'d`, `'h`, `'b`), so `'0` never matched as one token;
it split into `'` + `0` and space-joining produced `' 0`. Only candidates using
`'0` broke, which is why it was exactly 5 and why it appeared in fir40/firr18/
firr6 (their reset blocks use `'0`).

FIX (v1.5.1): added `'[01xXzZ](?![A-Za-z0-9_])` to the number alternation,
placed AFTER the based-literal alternative so `8'd1` still matches whole.

WHY THIS MATTERS BEYOND THE BUG. Nothing else would have caught it. The
contract passed 489/490 WITH this defect present: idempotence held (the broken
output is stable), metamorphic equality held (all spellings produce the same
broken output), features matched, and there were no collisions. A canonicaliser
can be perfectly self-consistent and still emit garbage. Only running the
output through a simulator found it. Keep --check-traces in the frozen protocol
and never treat the byte contract as sufficient.

SECOND FIX, same commit: `trace_equal` returned "simulation failed" whenever
EITHER side failed to simulate, which hid whether the input or the canonicaliser
was at fault -- I initially guessed the inputs were broken and was wrong. It now
returns None ("original does not simulate -- not evaluable", excluded from the
denominator) versus False ("CANONICAL FORM DOES NOT SIMULATE", a defect).

State after v1.5.1 (sandbox): self-test PASSED; contract 489/490, 1 explicit
rejection, 0 collisions, 91 equivalence merges; Check A GO (389 material pairs,
5 unorderable = 1.3%, med 21.7% marginal, 0 unsafe merges, 0.00% rejection).
AWAITING: the server re-run of --check-traces at v1.5.1. The blocker closes only
when that reads 0 canonical-compile failures.

### 2026-08-11 — canonicaliser v1.6.1. Two tokenizer gaps, and a guard that failed.

TRACE CHECK (server, v1.5.1): 5 canonical-compile failures -> 1. The remaining
one was `base__firr18__g1.sv`:
    original   y <= {12'b0, $signed($signed({3'b0, tap[0]}) * 1)} + ...
    canonical  y <= { 12'b0 , $ signed ( $ signed ( ...     <- invalid
The `ident` pattern is `[A-Za-z_][A-Za-z0-9_$]*`, which does not allow a LEADING
`$`, so `$signed` split into `$` + `signed` and space-joining broke it. Fixed in
v1.6.0 with a `systask` token group: `\$[A-Za-z_][A-Za-z0-9_$]*`.

THIS WAS THE SECOND GAP OF THE SAME SHAPE (`'0` was the first). I added a
token-count guard intended to catch the class systemically, then TESTED IT by
synthetically removing the `'0` rule. **IT DID NOT FIRE.** Input `'0` tokenises
as `'` + `0` (2 tokens); output `' 0` re-tokenises as `'` + `0` (2 tokens).
Same count, same sequence, invalid Verilog.

NO TOKEN-LEVEL CHECK CAN CATCH A TOKENIZER GAP. The tokenizer does not know the
two pieces had to stay adjacent, so nothing computed from its output can notice
they were separated. Both gaps also passed the ENTIRE byte-level contract --
idempotence, metamorphic equality, feature equality -- because a consistently
broken output is still perfectly consistent with itself.

THE ONLY SUFFICIENT DETECTOR IS COMPILING THE OUTPUT.
=> `--check-traces` over the full corpus is MANDATORY in the frozen protocol,
   and must be re-run whenever the corpus or the tokenizer changes.
=> A passing contract is NOT evidence that the canonical form is well formed.
The guard is kept for the narrower class it does catch (a construct vanishing)
and its limitation is documented in the code so nobody re-derives false comfort.

STATE (sandbox, v1.6.1): self-test PASSED; contract 489/490, 1 explicit
rejection, 0 collisions, 91 equivalence merges; Check A GO (389 material pairs,
5 unorderable = 1.3%, med 21.7% marginal, 0 unsafe merges, 0.00% rejection).
AWAITING the server trace re-run at v1.6.1; the blocker closes at 0.

### 2026-08-13 — BLOCKER CLOSED. preregistration.json FROZEN (revision 1).

Server, canonicaliser v1.6.1, lexical backend, 490 candidates:
  contract passed .............. 489/490 (1 explicit rejection)
  collisions ................... 0
  failures ..................... {} (empty)
  CANONICAL-COMPILE/TRACE ...... 0     <- the go criterion, met
Check A (server, same version): GO. 389 material pairs, 5 unorderable (1.3%),
0 unsafe merges, 0.00% rejection. Family: fir/firr/poly/iir/other all 0.0%,
med 21.7% (MARGINAL against the 25% ceiling -- always report it as marginal,
never quote the 1.3% overall alone).

`preregistration.json` written and frozen. It pins: environment (canonical
machine + library versions, because knn12 rho differed 0.543 vs 0.604 across
machines on deterministic code); sha256 of all seven load-bearing scripts;
canonicaliser version/backend/contract result; the rf_struct feature list with
its provenance; the training-row manifest; the selection rule (design-blocked
nested CV, training rows only) with an explicit disclosure that RandomForest was
noticed while inspecting v8; Check A thresholds and result; Check B's
reward-resolution-failure definition; the sealed-split spec (20 designs, seed
20260813, unopened) with its honest limitation; the three training arms x two
seeds matched on non-flat updates; the per-group logging requirement; the
evaluation protocol; the five success criteria; and the stop rules.

DO NOT EDIT IT after the sealed split is opened. To change anything: bump
`revision`, record the reason in `amendments`, and say in the paper that the
change came after freeze.

NEXT, in order: (1) generate + seal the 20-design split from seed 20260813,
unopened; (2) extend grpo_oracle.py with the per-group logging the
preregistration requires; (3) train three arms x two seeds; (4) Vivado once;
(5) stop and write. Manuscript drafting runs in parallel starting now.

### Preregistration revision 2 (2026-08-14) — pre-outcome implementation amendment

External review approved the science and blocked the artifact: revision 1
declared procedures that were **not yet executable or not yet numerically
defined**. Revision 2 fixes exactly that and nothing else. No sealed design
existed, none was viewed, and no arm had trained when it was written, so nothing
in it is informed by an outcome. Approved as-is: canonicaliser v1.6.1, Check A
GO, the RandomForest disclosure, and the 20-design split.

What was not executable, and what closes it:

1. **The sealed split had no generator.** `gen_accelerator_catalog.py` emits
   fixed grids and has no seed-driven selection, so seed 20260813 alone
   determined nothing — a reader could not have reconstructed the split, which
   is the whole point of naming it. `gen_sealed_split.py` is that determinism,
   hashed before it runs. Two things it forced into the open:
   - The trained grid covers **every** fir/firr tap count in 4..32, so "an
     unseen tap count inside the trained range" does not exist. Interpolation
     designs come from a coefficient axis (`fir_coeffs_var`, `firr_coeffs_var`,
     matching the existing poly/iir variant axes); firr variants stay affine in
     the tap index so the family keeps its no-coefficient-table property.
   - **med's interpolation pool is provably empty** — a median is defined by its
     window width alone and every width inside the trained range is consumed by
     the train grid {3,5,9} or the held-out set {7,11}. Its two slots are
     reallocated by a declared rule (interp = fir 3, firr 3, poly 2, iir 2,
     med 0; extrap = 2 each). 20 designs, 10 per regime, all five families.
2. **`grpo_oracle.py` could not run the experiment**: no rf_struct reward, no
   flat-group or raw-candidate logging, checkpoints indexed by attempted step
   rather than optimizer update. All three implemented. Checkpoint indexing
   matters because arms are matched on non-flat updates — a step-indexed
   checkpoint compares different amounts of learning across arms.
3. **Vague terms operationalized.** "Substantial part" → high retention ≥50% of
   the prospective original-MLP improvement, and a *modifier* on success rather
   than part of the gate, so an unexpected MLP failure cannot make the repaired
   reward unclassifiable. "Late divergence" → reward up materially from update
   138 to 276 while equal-sample real Fmax falls materially, max(5 MHz, 2%);
   it requires the mid checkpoint (8 samples/design/seed at update 138),
   without which only the weaker endpoint sign-disagreement claim is available.
4. **The conjunctive success criterion is gone.** Five must-all-hold conditions
   made a partial result — the likelier outcome — classifiable only after the
   fact. Replaced by an eight-label taxonomy assigned by `analyze_sealed.py`,
   frozen before the data exists.
5. **Identities.** Full SHA-256 for the model, adapter, reward artifact and
   labelled rows, not just 16-char script prefixes. Hash basis stated exactly:
   LF-normalised content for text, raw bytes for binaries, path-sorted manifest
   digest for directories — **not** git blob hashes (git prepends
   `blob <len>\0`, giving a different digest).

**Wording correction, and it is the paper's own thesis again.** Compilation was
sufficient to catch the two tokenizer defects, but compilation is not
*generally* sufficient: a canonicaliser can emit valid Verilog that behaves
differently — a rename merging two signals would compile cleanly. The frozen
statement is: *token-level self-checks cannot generally certify source
preservation; compilation detects syntactic corruption; sampled full-trace
equality supplies stronger semantic evidence, though not formal equivalence.*
The trace audit is pinned at **256 vectors under seeds 1 and 2** — sampled, not
exhaustive.

Also frozen: reward-time gates (raw RTL passes the oracle; canonical form
compiles; unsupported or canonical-invalid → reward 0 **and logged with a
reason**, so each rate is reportable rather than an invisible loss of gradient);
a pre-open mutation contract over every distinct rf_struct-arm training
candidate, whose failure classifies the experiment `invalid_repair` under the
existing stop rule rather than triggering a repair; med retained as a
predeclared high-risk stratum at equal weight; and a corrected budget cut order
— if six runs are unaffordable the cut is **grpo_mlp_original seed 2**, because
the correctness-only arm answers the causal objection and cannot be inferred
from history, while the MLP already has the measured v8 trajectory.

Power, recorded before the fact: 10 independent designs per regime, paired
design SD ≈ 66 MHz (interp) / 59 MHz (extrap), 80%-power detectable effect
≈ 60–65 MHz. Adequate for effects like the prior 77–119 MHz gains, underpowered
below ~40 MHz. Two designs per family × regime do **not** support inferential
family claims; family results are descriptive.

`canonicalize.py` gained an additive `compiles()` helper for the reward gate.
Canonicalisation behaviour is unchanged (version stays 1.6.1) but the file hash
moved, so the byte contract and Check A are re-run at the new hash to confirm
the reported results still hold. If either differs, revision 2 is void and the
difference is reported.

NEXT, in order: (1) re-verify contract + Check A at the new hashes; (2) train
the rf_struct reward artifact; (3) generate + seal the split; (4) freeze hashes;
(5) train the arms; (6) Vivado once; (7) stop and write. Manuscript drafting
runs in parallel starting now.

### rf_struct reward trained (2026-08-14) — recorded BEFORE any arm ran

`train_rf_struct.py` on the canonical machine, iverilog 12.0, sklearn 1.7.2:
229 rows kept, 0 dropped, 41 designs, 15 canonical features.

Descriptive leave-one-design-out (selects nothing; the architecture is fixed by
the preregistration):
```
pooled Spearman rho        0.885
within-design rho  mean    0.555   over 30 designs with >=3 rows and spread
within-design rho  median  0.816
worst designs   sft__poly8_v3_8b -1.00, med3 -1.00, sft__fir32_8b -0.87,
                fir32_8b -0.61, med5 -0.12
```

Feature importances: `n_mult` 0.267, `accum_struct` 0.264,
`pipe_ratio_struct` 0.241, `n_regs` 0.084, `n_nonblock` 0.060, everything else
below 0.04.

**Two predictions recorded now, before the sealed split exists and before any
arm trains.** They are stated so they cannot later be offered as post-hoc
explanation.

1. **The loop features contribute almost nothing to the fitted model.**
   `loop_bound_max` 0.0063, `loop_bound_sum` 0.0049, `n_loops` 0.0001. They were
   added to repair med's orderability after Check A failed at 30.4%, and they
   did what they were added to do — Check A measures whether feature VECTORS
   differ, and med moved to 21.7% — but making two candidates *distinguishable*
   is not the same as the fitted model *ordering them correctly*. Both facts can
   hold at once, and here they do.
2. **med is the family most likely to underperform**, and `med3` at rho = -1.00
   plus `med5` at -0.12 is the same weakness Check A flagged at 21.7%, seen
   through a different instrument. This is consistent with med's predeclared
   high-risk status. It is NOT grounds to remove med: the stop rules forbid it,
   and dropping the hard family after seeing the diagnostic is precisely the
   move this preregistration exists to prevent.

Within-design ranking is what a GRPO reward actually needs — only the ORDER
inside a sampled group drives the gradient. A within-design mean of 0.555 with
several strongly negative designs is a real risk to the prospective run, and the
preregistration already names the outcome it would produce: `stable_null`, or
`reward_resolution_failure` if fewer than 20% of eligible groups resolve.

### Correction (2026-08-14): four overstated claims in the narrative prompt

An external audit of `reviewer_prompt_story.md` (reviewer pulled at `ccb8beb`)
found four claims that the repository does not support. All four were verified
against the committed record and all four were wrong. They are corrected in the
file and recorded here so the false versions do not resurface again.

1. **"One GRPO sample ≈ perfect-selector best-of-48."** WITHDRAWN 2026-08-11
   (RESULTS.md §2b) — computed on the old 22-design set. On the frozen 30-design
   5-family set the honest figure is ≈ **22** perfectly-selected samples in
   interpolation, ≈8 in extrapolation, and GRPO bo1 at 198.7 MHz **loses** to a
   perfect best-of-48 at 210.3. The withdrawn version was reintroduced from
   memory.
2. **"Token-identical cross-checkpoint pairs with different rewards."** These do
   not exist. `MASTER_REFERENCE.md:2672` records **zero pairs** as an explicit
   NULL RESULT. `analyze_reflow_attribution.py` was built to find them; it found
   none. The prompt described the script's intent as though it were its output,
   and called it "the whole claim with no statistics in it." The load-bearing
   evidence is instead that canonical `nb_assign` is flat across checkpoints
   (46.3, 46.0, 46.8) while raw `nb_assign` climbs ~20.
3. **"LODO Spearman 0.959, top-1 15/17" attributed to the exploited reward.**
   Those are **v1** diagnostics on a smaller dataset. The deployed
   `surrogate_v3` is **0.923 ± 0.008** (229 rows, 5 families). Old diagnostics
   were attached to a different artifact.
4. **101.2% presented as attribution with its caveat dropped.** The committed
   text says "CAVEAT THAT MUST TRAVEL WITH THE 101.2% -- do not drop it":
   canonical scores sit at 494–497 from s100 on, i.e. AT the 500 MHz clamp,
   because the predictor was trained on raw-layout rows and saturates on
   canonical text. It is an ATTRIBUTION DIAGNOSTIC, not a demonstration that
   canonicalisation yields a working reward.

Also accepted from the audit: do not call the protocol a "gold standard"
(sampled equivalence, one FPGA, template-generated specs); and the silicon
2.3–3.4× figures are selected demonstrations with asymmetric candidate selection
and two harness-censored results, not policy-level causal estimates.

**This is the paper's own thesis, committed by its authors, inside the document
arguing for it.** Every one of the four passed an internal check — they were
consistent with recollection, with the narrative, and with each other. Only
reading the committed record caught them. The corrective is procedural, not
attitudinal: no number enters a manuscript, prompt, or figure without a
`verify_claims.py`-style pointer to the artifact that produced it.

### Capability-paper recovery and fail-closed manuscript pipeline (2026-08-17)

User-authorized recovery returned the paper to the frozen `grpo_v8` capability
result and removed the later reward-repair study from the submission's critical
path. No new policy experiment was run. `analyze_main_results.py` is now the
only generator for headline result tables. It requires exactly the three frozen
five-family chunks, exactly 30 designs (19 interpolation, 11 extrapolation),
both SFT and GRPO, `n=48` for every policy/design, and a PPA row for every
manifest candidate. The primary endpoint is per-design equal-sample real
post-route Fmax: every incorrect sample and implementation failure scores zero.

Recomputed from the committed manifests and `ppa.jsonl` files:

```
regime          SFT      GRPO     paired gain    95% paired-design bootstrap
interpolation   79.9     198.7      +118.8        [88.5, 146.6] MHz   18/19 improve
extrapolation   61.2     138.6       +77.5        [43.5, 109.2] MHz    9/11 improve
overall         73.0     176.7      +103.7        [80.1, 126.1] MHz   27/30 improve
```

Bootstrap intervals are explicitly post-hoc descriptive uncertainty, with
fixed seed 20260817 and 100,000 paired-design resamples. They are not a
preregistered confirmatory test. Exact empirical perfect-selector curves from
the same script put one GRPO draw at approximately 21 SFT draws under
interpolation and 8 under extrapolation. GRPO does not beat perfect SFT
best-of-48 in either regime.

The script generates `paper/generated/{claims.tex,claims.json,
claim_provenance.md,main_results.json,table_*.tex}` plus the two headline
figures. Every claim record contains its method and artifact `file:line` ranges.
`verify_claims.py` now recomputes the generated outputs, validates every source
pointer, recursively resolves manuscript inputs, rejects unknown claim IDs, and
fails if any raw numeric literal appears in authored manuscript prose. The
current recovery draft passes: 100 ledger claims, 89 used claim IDs, zero raw
numeric literals. The draft now leads with the penalized endpoint and limits the
reward-hacking story to the measured `traj_v8` diagnostic: step0 to s100 is a
real gain (76.4 to 230.5 MHz penalized), whereas s300 to s400 raises proxy reward
216.6 to 497.9 MHz while conditional measured Fmax is flat (242.2 to 241.2 MHz),
correctness falls 95.3% to 88.0%, and penalized Fmax falls 230.9 to 212.3 MHz.

#### Symmetric board rerun: prepared, not measured

`gen_symmetric_holdout_bitstream.py` retains the historical five post-hoc design
picks but removes the policy-side asymmetry. For both policies it selects the
upper count-weighted median real-Vivado Fmax among functional manifest
candidates with a compiled PPA row; exact-Fmax ties use larger count then lexical
module name. `rtl/holdout_silicon_symmetric/selection_manifest.json` records the
post-hoc-design warning, source hashes, PPA file:line pointers, copied-RTL and
golden hashes, and frozen board sweep plan. All ten DUTs plus the echo canary
matched their goldens at 1.0000 under the Icarus preflight.

The laptop build did **not** complete. Standard Vivado run-manager execution
hung at child launch; after termination, a bounded in-process diagnostic reached
RTL elaboration but failed because generated `system_la0_0.v` could not resolve
`la_axi_fast` (`Synth 8-439`, cascading `Synth 8-6156` / `Common 17-69`). The
PYNQ board at the recorded address also timed out on ping and SSH. Therefore no
final bitstream/HWH pair and no
`rtl/holdout_silicon_symmetric/catalog_fmax.json` exist. The recovery draft
reports no symmetric silicon number and does not reuse the historical
asymmetric table. `sweep_catalog.py` was extended so a future successful live
sweep records raw runs, bitstream/HWH/selection hashes, environment provenance,
per-entry Vivado references, and explicit no-pass rows.

### Strongest-paper integration after the recovery checkpoint (2026-08-17)

The capability paper now restores the strongest independently checkable
secondary results without promoting them to the primary causal claim.
`analyze_main_results.py` remains the sole fail-closed paper generator and now
validates all of the following artifacts before emitting any manuscript number:

1. the frozen 30-design, five-family `grpo_v8` primary comparison;
2. the complete raw-base correctness rows on that same universe;
3. the earlier Qwen second-backbone replication on 22 designs and three
   families;
4. candidate-level concentration and implementation-diversity diagnostics;
5. the stored same-task API baseline, VerilogEval control, selected HLS
   comparison, reflow-attribution diagnostic, and evaluation-protocol source;
6. the symmetric-board selection manifest, while continuing to reject any live
   silicon claim unless the missing catalog artifact exists.

The restored results and their evidentiary roles are:

```
primary raw base, same 30 tasks       2.8% correct; 1.8 MHz penalized Fmax
Qwen replication, 22 tasks           64.9 -> 200.5 MHz; +135.6 [122.7,147.3]; 22/22
dominant correct-candidate mass       43.5% -> 72.6% (SFT -> GRPO)
effective correct implementations    2.88 -> 1.74
SFT support contains >= GRPO mean     25/30 designs
stored API, same prompt               14.3 MHz penalized; 27.1% correct
stored API, timing prompt             55.0 MHz penalized; 22.9% correct
VerilogEval pass@1                    base 32.2%; SFT 16.0%; GRPO 16.7%
selected fastest GRPO / pragma HLS    0.96x geometric mean over 19 valid designs
selected fastest GRPO / plain HLS     46.0x geometric mean, range 18.3x--108.3x
```

These tiers must not be collapsed. The primary result is the equal-sample
policy comparison. Qwen is a narrower earlier replication. Candidate
concentration is a mechanism diagnostic. The API run is one stored prompt/API
configuration, not a general frontier-model comparison. The HLS table compares
the selected fastest GRPO implementation with engineer-written C++ baselines,
not policy-average samples. VerilogEval shows a large specialization cost from
the base model to SFT and no material additional loss from SFT to GRPO. The
reflow study remains a bounded diagnostic: canonical rescoring removes 101.2%
of the raw late jump, but its scores are clamp-saturated and there are zero
token-identical cross-checkpoint pairs.

The generated paper now includes `table_replication.tex`, `table_context.tex`,
and `fig_mechanism_verified.{pdf,png}`. Deterministic figure metadata makes all
six generated figure files byte-stable across consecutive runs. The claim
ledger currently contains 171 validated claims, of which the manuscript uses
150. `verify_claims.py` resolves every included TeX file, checks each artifact
`file:line` pointer, rejects unknown claim IDs, and rejects raw numeric literals
in authored prose. The final local audit passed all correctness, best-of-N,
trajectory, oracle, manuscript-provenance, and symmetric-board checks.

Citation metadata was re-audited against primary records. In particular, the
previous PPA-RTL title was false: the record is *Hardware Generation with High
Flexibility using Reinforcement Learning Enhanced LLMs* by Zhao, Fu, Li, Hu,
Guo, and Jin. VeriReason, POET, EvolVE, and COEVO author lists were corrected,
and Alpha-RTL was added to the test-time policy-adaptation discussion.

Still missing before calling the paper submission-ready: a real LaTeX build and
page-layout pass (no TeX distribution is installed on this laptop), human prose
and citation review, and preferably additional independent primary seeds. A
successful symmetric board build and live sweep would strengthen the paper but
does not exist yet. The strongest current framing is therefore a reproducible
capability paper with a bounded reward-overoptimization subplot, not a silicon
paper and not a completed reward-repair paper.

### TCAD-first manuscript conversion (2026-08-17)

After the supervisor's journal recommendation was confirmed by the user, the
submission target changed from a DAC-first plan to **IEEE TCAD first**. This is
consistent with the earlier supervisor-endorsed venue record at line 1870 of
this file. The same work must not be submitted concurrently to DAC or another
venue.

No experiment or empirical value changed during the conversion. The paper now
uses `\documentclass[journal]{IEEEtran}` and the standard journal author form.
The obsolete ICCAD length comments and conference-only balancing were removed.
Current TCAD instructions allow a 14-page regular-paper submission, require
IEEE two-column format, and require a generative-AI-use acknowledgment. The
official instructions explicitly list a missing AI disclosure, inadequate
related work, insufficient state-of-the-art comparison, and insufficient new
results as possible desk-rejection grounds:
https://ieee-ceda.org/publications/tcad/tcad-paper-submissions

The disclosure is intentionally specific and must not be weakened: OpenAI
Codex assisted repository auditing, analysis-code development, LaTeX drafting,
and prose editing; the author remains responsible for all code, analysis,
figures, citations, and text. `paper/TCAD_SUBMISSION.md` records the remaining
human-only decisions: final authorship, ORCIDs, prior-submission history,
Associate Editor conflicts, and Traditional-versus-Open-Access choice.

Journal hardening added only derivations and literature-grounded positioning:

- the exact standardized group advantage and frozen-SFT KL estimator used by
  `grpo_oracle.py`;
- the identity decomposing penalized Fmax into correctness and
  conditional-on-correct frequency, clarifying why neither conditional speed
  nor distinct-candidate averaging is the primary endpoint;
- paired-design uncertainty and candidate-concentration definitions;
- a protocol-level comparison with VeriSeek, PPA-RTL, ChipSeek, Alpha-RTL, and
  RTL-OPT, without manufacturing a numeric leaderboard across incompatible
  technology/process/evaluation settings; and
- an artifact-traceability section linking the frozen manifests, RTL,
  multiplicities, PPA rows, generator, figures, and claim ledger.

The full post-conversion audit passed unchanged: 171 claim records with valid
artifact line pointers, 150 claim IDs used in rendered manuscript sources, zero
raw numeric literals in authored prose, all primary/replication/context outputs
current, and no symmetric live-silicon artifact. A rendered PDF and page count
remain blocked only by the absence of a TeX installation on this laptop.

### TCAD strengthening start: sealed-study revision 3 + primary PPA accounting (2026-08-18)

The user authorized the strengthening plan and required every new result to be
recorded in this master record. No new policy, sealed-set, Vivado, or live-board
measurement was produced in this step. The prospective sealed split remains
unopened in the repository. A read-only audit of the GPU server was attempted
before stating that the amendment was pre-outcome, but the SSH endpoint closed
the connection; the launch workflow therefore also refuses every pre-existing
arm output on the server rather than assuming it is absent.

**Revision-3 pre-outcome workflow repair.** The revision-2 preregistration
named an evaluator that could only consume the historical 30-design split and
provided no executable way to audit the actual RF-arm training candidates.
It also retained an analyzer that could omit zero-correct designs, accept
partial PPA data, accept manually supplied gate/diagnostic values, and encoded
the pre-amendment correctness-arm seed count. Before any sealed output was
generated, `preregistration.json` was advanced to revision 3 with no change to
the split, reward, endpoint, thresholds, training hyperparameters, synthesis
target, bootstrap, or outcome taxonomy. The executable chain is now:

1. `run_arm.sh`: only RF seeds 1/2, MLP seeds 1/2, and correctness seed 1;
   exact 276 non-flat updates and checkpoints 138/276; stale outputs refused;
   pinned hashes, CUDA, Icarus, VVP, and an oracle canary checked before launch.
2. `verify_sealed_training.py`: requires all five exact run configurations,
   consecutive eight-candidate groups, unique updates 1..276, matching summary
   counts, and both checkpoints before sealed generation.
3. `materialize_rf_candidates.py` + `canonicalize.py --check-traces`: materialize
   every distinct non-empty RTL candidate in the two actual RF group logs with
   source-row/content hashes, then run the frozen compilation/trace gate before
   opening the split.
4. `eval_sealed.py` + `run_sealed_server_stage.sh`: consume the stored frozen
   prompts and per-design token budgets; preserve the full sample denominator,
   including zero-correct designs; use SFT n=48, two-seed endpoints n=24/seed,
   correctness n=48 for its single training seed, and RF midpoint n=8/seed.
5. `run_sealed_laptop_ppa.ps1` + `verify_sealed_ppa.py`: run the identical
   Zynq-7020 5 ns flow and require one explicit PPA row for every emitted
   candidate. An interrupted batch is incomplete, not silently scored zero.
6. `analyze_sealed_v3.py` + `run_sealed_analysis.sh`: derive the frozen endpoint,
   diagnostics, validity gate, and outcome label only from the evaluation,
   training-log, contract, and PPA artifacts.

`freeze_hashes.py --verify` was also repaired: it now fails on dependencies
required by the current identity set but missing from the old `hashes.json`.
Previously it compared only keys already present in that file, so a newly added
required script could remain silently unpinned. Seven GPU-free regression
tests pass, covering multiplicity/failure accounting, zero-correct retention,
missing zero-correct denominators, stale-output refusal, distinct-candidate
materialization, explicit one-row-per-candidate PPA coverage, and unique
optimizer-update accounting. Python compilation, JSON validation, PowerShell
parsing, and Bash syntax checks also pass. The next server action is to
regenerate and verify the complete revision-3 hashes on the canonical server;
no arm may start until that succeeds.

**New primary PPA diagnostic from existing real-Vivado rows (no new run).**
`analyze_main_results.py` now validates LUT, FF, DSP, BRAM, and vectorless-power
fields for every compiled primary candidate and generates
`paper/generated/table_ppa.tex`. Assigning zero area to an incorrect or failed
sample would perversely reward failure, so resource values are explicitly
conditioned on oracle-correct, successfully implemented samples: multiplicity-
weighted within each design, then averaged equally over the 30 designs. This
is secondary to the unchanged failure-penalized Fmax endpoint.

```
metric                              SFT         GRPO       GRPO/SFT
conditional LUTs                  272.34       289.19        1.0619
conditional flip-flops           133.65       195.91        1.4658
conditional DSP blocks             4.045        2.167       0.5356
conditional vectorless power (W)   0.12282      0.12194     0.9929
```

Seventeen of 30 designs have higher GRPO penalized Fmax with no increase in
conditional mean LUT count; seventeen also improve with no increase in
conditional mean DSP count. The honest interpretation is a specific trade-off:
about 6% more LUTs and 47% more registers (consistent with deeper pipelining),
about 46% fewer DSPs, and no measured increase in Vivado's vectorless power
estimate. It is not an activity-based power claim and no arbitrary composite
"area" proxy is used.

After regeneration, the canonical 30-design result remains exactly unchanged:
73.0 -> 176.7 MHz overall penalized equal-sample Fmax, +103.7 MHz with the
post-hoc descriptive interval [80.1, 126.1], and 27/30 designs improved.
`verify_claims.py` now validates 185 source-backed claim records, 164 used claim
IDs, zero hand-copied manuscript numbers, and the absent live-board artifact.

During the final pre-commit audit, remote commit `6b14d32` introduced a second,
smaller `regen_tables.py` calculation path. It was not used to change or select
any result. To preserve one source of truth, that filename is now only a thin
compatibility entry point to the stricter `analyze_main_results.py`; it contains
no independent metric implementation. Both `python regen_tables.py --check`
and the canonical generator therefore validate the same 30-design artifacts.

### Sealed-study execution recovery and preregistration revision 4 (2026-08-19)

Access was restored through two replacement GPU-container ports after the
revision-3 commit. The shared checkout was still at `3110c88`, with one complete
untracked training run and three incomplete active runs. No sealed evaluation
directory or sealed outcome existed or was inspected. The running processes
were mapped by exact process group before termination:

- V100-SXM2 box: incomplete `grpo_rf_s2` and `grpo_mlp_s1`;
- V100S-PCIe box: incomplete `grpo_corr_s1`;
- all four GPUs were verified afterward at 1 MiB, 0% utilization, with no
  compute application remaining.

The three incomplete process trees were stopped and their directories, update
logs, and stdout logs moved recoverably to
`abandoned_runs/pre_rev3_stopped_20260819/`. They will not be resumed, merged,
or analysed. This follows the frozen crash policy exactly.

The server also contained a completed `grpo_rf_s1` run from 2026-08-17. It was
not discarded merely because it was discovered late. A launch-time audit found
exactly 276 non-flat updates, 419 attempted groups, 143 flat groups, checkpoint
directories 138 and 276, the intended completion status, and the exact frozen
training configuration. Its revision-2 `hashes.json` independently passed on
the canonical server: 27 pinned artifacts, zero changed, zero missing. The
training implementation, oracle, candidate catalogue, SFT corpus logic, RF
reward artifact, SFT adapter, and base model are byte-identical between launch
commit `3110c88` and the revision-3 code. Its launch hash manifest,
preregistration, and runner were copied beside the checkpoint before the shared
checkout was updated.

This is a training-completion/provenance fact, not a sealed efficacy result.
No reward trajectory or sealed performance outcome was used to make the
decision. Preregistration revision 4 prospectively retains this valid RF seed-1
checkpoint, archives and restarts the three incomplete arms from update zero,
and balances the remaining allocation across boxes: RF seed 2 and MLP seed 2
on V100S-PCIe; MLP seed 1 and correctness seed 1 on V100-SXM2. Each two-seed
reward arm therefore spans both GPU types. No scientific endpoint, threshold,
split, reward, model, optimizer setting, evaluation sample count, synthesis
flow, bootstrap rule, or outcome label changed.

Because the containers could not reach GitHub, a verified complete Git bundle
was transferred from the laptop. The shared server checkout was fast-forwarded
without resetting or deleting historical artifacts and now matches `88bfe36`.

**Revision-4 freeze and launch.** After the revision-4 disclosure was committed,
the canonical server regenerated `hashes.json` over the complete identity set.
The independent write-then-verify pass reported 37 pinned artifacts, zero
changed, zero missing, and zero required-but-unpinned. The resulting identity
commit is `8b71cbcc605a496fd1a1970d24281d2ebabb1887`, transferred back to the
laptop by a verified Git bundle and pushed to GitHub before progress was
reported.

The four remaining runs were then launched from update zero in detached,
per-job process groups with the preregistered commands and balanced allocation:

- V100-SXM2 GPU 0: `grpo_mlp_s1`;
- V100-SXM2 GPU 1: `grpo_corr_s1`;
- V100S-PCIe GPU 0: `grpo_rf_s2`;
- V100S-PCIe GPU 1: `grpo_mlp_s2`.

Every job independently passed the 37-artifact hash check and functional-oracle
canary, loaded the intended 6.77B-parameter model, and completed its first
eight-candidate group and first optimizer update. At that confirmation point,
all four canonical group logs contained eight rows, all update logs contained
one row, and every assigned GPU was actively computing. These are execution
health checks only; no sealed evaluation has been generated or inspected and
no efficacy conclusion is drawn from first-group training rewards.

### Correctness-control L40S relocation: isolated environment and revision 5 (2026-08-19)

The correctness-only seed-1 run is the long pole because its binary reward is
flat for most eight-candidate groups. A scheduling snapshot of the active
V100-SXM2 run showed 84 attempted groups and 22 non-flat optimizer updates. No
sealed-policy evaluation exists, and no sealed candidate, Fmax, resource, or
power result was generated or inspected. The attempted/update counts were read
only to estimate completion time; this partial run will be archived and will
contribute no study result.

The user authorised physical GPUs 4--7 on the eight-L40S host and restricted
all changes there to `/home/adam/mas/mas`. Existing environments were not used:
with user-site packages disabled they were either missing core dependencies or
had incompatible major package versions. A fresh isolated environment was
therefore created at `/home/adam/mas/mas/env_fpga`, with every Conda, package,
cache, temporary, repository, model, and output path kept below the authorised
directory and `PYTHONNOUSERSITE=1`. Its study-relevant versions are:

```
Python             3.10.20
torch              2.4.1+cu121
transformers       4.46.3
peft               0.13.2
accelerate         1.0.1
numpy              2.2.6
scipy              1.15.3
scikit-learn       1.7.2
joblib              1.5.3
iverilog / vvp     12.0
```

CUDA 12.1 in that environment detects the L40S (compute capability 8.9), and
Icarus compilation/simulation passes. Because GitHub SSH was unavailable from
the host, commit `a757bd37` was transferred in a verified Git bundle. The base
model and SFT adapter were copied directly between the authorised servers and
then checked by the same directory-manifest hash used by `freeze_hashes.py`:

```
artifact       source digest                                                    L40S digest
base model     c29348b7a8ee7fbd73a31a215942d51d5490574d080305a15ca12f7fd396e256  identical
sft_v6c_out    9ce91891c911b73f3f636b21ffb9f1769ce2b7ef2fbe40a8d1d68a874d56e2e8  identical
```

All other 37 revision-4 artifact digests matched as well, and the functional
oracle canary passed. Two explicitly non-study canaries tested the new machine:
seed 999 completed one FP16 inference group in 25 seconds, and seed 998 reached
a real non-flat update on attempted group 13 and successfully executed backward,
optimizer, and checkpoint saving without an out-of-memory error. These outputs
(`l40_fp16_canary_seed999` and `l40_fp16_update_canary_seed998`) are operational
tests only. Their undeclared seeds and candidates are not study arms, are not
opened for efficacy analysis, and cannot enter a paper table.

The key reproducibility hazard found during this check was dtype: the old
automatic rule selects FP16 on V100 but BF16 on L40S. Revision 5 therefore
passes `--dtype fp16` explicitly for every arm, makes
`verify_sealed_training.py` reject any non-FP16 run, allows only the declared
L40S physical GPU 4 in addition to the two V100 indices, and permits an explicit
environment-bin path while disabling user-site packages. The correctness arm
will move only after this amendment is committed, transferred, re-hashed on the
L40S host, and independently verified. It will then be archived on V100 and
restarted from update zero on L40S GPU 4 with the same seed, model content,
adapter, prompts, reward, optimizer, hyperparameters, ceilings, and checkpoints.
No endpoint, threshold, evaluation sample count, or scientific decision rule is
changed; the relocation changes hardware and expected wall-clock time only.

**Revision-5 freeze, archive, and actual launch.** The amendment was committed
and pushed as `9c293a68`, then transferred to the L40S host by a verified Git
bundle. On that host, `freeze_hashes.py` regenerated `hashes.json` using the
content-identical model at its new absolute path and immediately verified the
result: 37 pinned artifacts, zero changed, zero missing, and zero required-but-
unpinned. Seven GPU-free workflow regression tests, preregistration JSON parsing,
and Bash syntax validation also passed. The resulting identity commit is
`c08027b06efd6c05fbe09c4b0087290b706fa95b`; it was transferred back by a
second verified bundle and pushed to GitHub before the old run was touched.

The V100 correctness process group was then resolved exactly as PGID 8724 and
terminated. Its final group log contains 856 rows: 107 consecutive complete
eight-candidate groups, 31 non-flat updates, and 76 flat groups, with maximum
update 31. The directory and all three external logs were moved recoverably to
`abandoned_runs/rev4_corr_relocated_l40_20260819/`. Nothing from this partial
run is resumed, merged, evaluated, or reported as a study result. V100-SXM2 GPU
1 was verified idle afterward; GPU 0 continues the independent MLP seed-1 job.

Correctness seed 1 restarted from update zero at 2026-08-18 18:06:41 UTC on
physical L40S GPU 4, process group 3194802, from identity commit `c08027b0`:

```
FPGA_ENV_BIN=/home/adam/mas/mas/env_fpga/bin \
RTLCODER_PATH=/home/adam/mas/mas/rtlcoder \
PYTHONNOUSERSITE=1 ./run_arm.sh correctness 1 4
```

The launch independently passed all 37 hashes and the functional-oracle canary,
loaded the intended 6.77B-parameter model, and recorded reward `correctness`,
seed 1, `torch.float16`, group 8, 1,536 tokens, target 276 updates, ceiling 4,500
groups, checkpoints 138/276, temperature 1.0, learning rate 1e-5, and KL
coefficient 0.1 in `run_config.json`. At the post-launch health check it had
completed seven full groups and four optimizer updates and GPU 4 was actively
computing. These counts establish execution health only; they are not sealed
efficacy evidence and no endpoint has been generated or inspected.

### Four of five sealed training arms complete (2026-08-19)

The three remaining physical-reward jobs completed normally and wrote their
frozen update-276 checkpoints and `run_summary.json` files. Combined with the
previously retained RF seed-1 run, four of the five preregistered training arms
are now complete:

```
arm / seed       attempted groups   non-flat updates   flat groups   ended
rf_struct / 1                 419                276           143   target updates reached (276)
rf_struct / 2                 465                276           189   target updates reached (276)
mlp / 1                       414                276           138   target updates reached (276)
mlp / 2                       497                276           221   target updates reached (276)
```

Every completed run reports checkpoints 138 and 276 with an empty
`missed_checkpoints` list. At the same read-only status check, the L40S
correctness seed-1 process remained active at 835 complete attempted groups and
113 non-flat updates. No sealed-policy generation or evaluation has started;
these are training-completion and execution-progress facts, not efficacy
results. The full fail-closed `verify_sealed_training.py` audit remains blocked
by design until correctness seed 1 reaches its declared stopping condition.

### Historical generated-RTL token-length audit (2026-08-19)

`audit_generated_token_lengths.py` measures output length using the exact frozen
RTLCoder tokenizer rather than whitespace or a generic lexical proxy. Its
machine-readable output is `token_length_audit_v8.json`, generated from the
committed `rtl/holdout_eval_v8_{firfirr,iirmed,poly}` manifests and candidate
RTL. The output records the tokenizer-file hashes and a combined SHA-256 over
every input manifest, summary, and retained RTL file.

The historical v8 evaluator retained only oracle-correct candidates, so this
audit is explicitly **conditional on correctness**. It cannot recover the token
lengths of incorrect or extraction-failed draws and must not be described as an
all-generation mean. With candidate multiplicity preserved, each policy had
1,440 total draws and the retained correct RTL had these tokenizer lengths:

```
policy   retained correct draws   mean tokens   median tokens
base                         41         455.76             387
SFT                       1,277         503.07             394
GRPO                      1,252         689.67             662
```

Thus the historical GRPO model did **not** produce shorter correct code: its
mean was 1.371 times SFT and 1.513 times base. Base had correct retained outputs
for only 16 of 30 designs, but restricting the design-balanced comparison to
those 16 common designs gives the same ordering: 483.36 base, 521.17 SFT, and
667.28 GRPO tokens. This is an LLM inference-cost/verbosity diagnostic, not a
hardware-area result: all policies use the same 6.77B backbone and prompt, while
FPGA resources and Fmax depend on the synthesized circuit rather than source
token count. The new sealed RF/MLP/correctness policies require their own frozen
evaluation before any current-model token-length claim is made.

### Post-correctness pipeline staged without opening the sealed split (2026-08-19)

The four completed physical-reward runs were copied from the V100 host into the
authorised L40S study checkout before the correctness run finished. This was a
byte-for-byte operational relocation only; no candidate efficacy was inspected.
Directory manifests computed independently at the source and destination
matched exactly:

```
run          files  directory-manifest SHA-256
grpo_rf_s1      18  c2109c91cf969f51ef555cd9525db0ed2f627c1d7c2e4795cff918e89985c3be
grpo_rf_s2      15  7b3be67365c8284cab01db5d51288243b5df02b7b0ac1ac8f29aa99104719fae
grpo_mlp_s1     15  6a763688187109e6e54a8f5044be1a2971aad431eb210e4b0132c2bc315ed80f
grpo_mlp_s2     15  f28fab4dab237be78567cd50ea1c893b95d030aa50cc0b1f113c1471d21411df
```

All four staged runs pass the frozen `verify_sealed_training.audit_run` checks.
Their group-log SHA-256 values are, respectively,
`609b5fd0a98cec67bb7281e9fde6a881f37fc40f297936627e54bccac6fe8a04`,
`b4737450595e5ab38b5d8852d18ade27d81ebd2386cad2ac3fb892262ae84979`,
`5fe011edb634cf280674597d1d482686d52e4d48221d597d83b4591e62c20053`,
and `32198a1c28f84f33c1ddba4bd71a590fb18b2fa24eb8e24d1003892878f4b631`.
The L40S checkout still verifies all 37 frozen pre-outcome hashes with zero
changed, missing, or unpinned artifacts. It had 44 GiB free, and all eight
sealed evaluation destinations were absent.

`/home/adam/mas/mas/start_sealed_after_correctness.sh` is an operational,
non-study launcher installed outside the frozen checkout. It invokes the exact
hashed `run_sealed_server_stage.sh` on physical L40S GPU 4 and refuses to start
unless the correctness summary ends exactly with target update 276, process
group 3194802 has exited, the checkout is identity `c08027b0`, every sealed
destination and launch log is absent, GPU 4 is idle, and at least 10 GiB is
free. A pre-completion dry invocation refused with no output or log side
effects. The exact post-notification command is:

```
ssh adam40 /home/adam/mas/mas/start_sealed_after_correctness.sh
```

The frozen server evaluator remains serial on one GPU. Its scheduling was not
silently rewritten to use four GPUs during an active preregistered study.
`run_sealed_handoff.ps1` makes the later boundaries one-command and fail-closed:
`-Stage Fetch` requires the remote completion marker, downloads the eight
evaluation directories plus audit manifests through a temporary directory,
and compares a full remote/local SHA-256 manifest before installing anything;
`-Stage Ppa` invokes the unchanged `run_sealed_laptop_ppa.ps1`; and
`-Stage ReturnAndAnalyze` refuses pre-existing remote PPA/results, returns the
eight complete PPA files, invokes the frozen analysis, and retrieves its sole
result. PowerShell parsing passed, and a live dry test before server completion
refused with no staging residue or local transfer artifact.

At 2026-08-19 07:38:47 UTC, the still-blind correctness run was healthy at
1,428 complete groups and 144 updates, leaving 132 updates before target or
3,072 groups before the ceiling. Non-flat rates were 6/100, 14/200, 16/350,
29/500, and 46/800 most-recent groups; the remaining run needs 4.2969%. GPU 4
was active at 61% sampled utilization with 14,841 MiB allocated. These are
execution-progress values only, not policy-efficacy results.

### Symmetric PYNQ build repaired and staged; live sweep still pending (2026-08-19)

The symmetric five-pair board selection was regenerated and all ten DUTs plus
the echo canary again passed the Icarus/golden self-check at 1.0000. The prior
same-process Vivado failure was isolated: after block-design module-reference
generation, Vivado 2023.1 could leave `la_axi_fast.v` auto-disabled for direct
top synthesis even though it appeared in the project. Reopening the generated
project restored the source to the synthesis compile order. The generator and
its emitted Tcl now enforce that close/reopen/update-order boundary. An
existing-project probe then synthesized with zero errors, zero critical
warnings, and no black boxes. The first clean-build attempt encountered a
transient Vivado design-assist `rules.tcl` read/initialisation error before block
design creation; one immediate clean retry completed synthesis, placement,
routing, and bitstream generation.

The resulting local generated pair is:

```
artifact                                                        bytes    SHA-256
rtl/holdout_silicon_symmetric/out/system_holdout_symmetric.bit  4045674  f8502d94d988308caf13f018477f45ff16b6dfc078f9ec7ca55aac76432d8605
rtl/holdout_silicon_symmetric/out/system_holdout_symmetric.hwh    142044  25125897a74874dc51579ce2a134039da70e856cdf342f91f8352bd9ef246834
```

All 7,184 routable nets are fully routed and none has a routing error
(`rtl/holdout_silicon_symmetric/out/route_status.rpt:9-10`). This is **not** a
200 MHz timing-closure claim: routed WNS is -38.448 ns
(`rtl/holdout_silicon_symmetric/out/timing_summary_routed.rpt:140`) because the
image deliberately includes slow SFT candidates and the live protocol lowers
and sweeps FCLK0 from 20 through 260 MHz. A separate exact-flow laptop canary
completed in about 136 seconds and reproduced 70.8014726706 MHz, 199 LUTs,
96 FFs, 0 DSPs, 0 BRAMs, and 0.111 W
(`rtl/holdout_eval_v8_firfirr/ppa.jsonl:1`), establishing that the laptop Vivado
PPA path is operational; it is not a sealed outcome.

`run_symmetric_board_handoff.ps1` now checks the bit/HWH, selection manifest,
eleven design-derived goldens, and board scripts; refuses pre-existing local or
remote results; uploads the fixed bundle; runs the declared 3 x 20--260 MHz
sweep; retrieves `catalog_fmax.json`; and verifies its schema plus bitstream,
HWH, selection, and manifest hashes. Its parser test passed and, with the board
offline, its live dry test timed out fail-closed without creating a false result.
The PYNQ-Z2 at 192.168.2.99 still does not answer ping or SSH, so there is still
no live symmetric-silicon artifact or board claim. The exact bit/HWH pair and
the routed timing, utilization, and route-status reports are retained in Git;
the much larger regenerable Vivado project and checkpoints remain ignored.

### Correctness ceiling failure preserved; revision 6 frozen (2026-08-20)

The revision-5 correctness seed-1 run ended normally at its preregistered
4,500-attempt ceiling without reaching the matched update target. This is a
compute-feasibility failure, not a sealed efficacy result: no sealed-policy RTL
has been generated, evaluated, synthesised, or viewed. A new deterministic
audit reads the complete server artifacts rather than transcribing counters by
hand. It verifies 36,000 candidate rows in exactly 4,500 consecutive groups,
215 unique non-flat updates numbered 1 through 215, 4,285 flat groups,
checkpoint 138 present, checkpoint 276 absent, and the last update at group
4,484. The run reported `steps exhausted` and no CUDA or runtime error.

The non-flat rate fell during training. In the final 1,500 groups there were
25 updates (1.6667%); in the final 1,000, 16 (1.6%); and in the final 500,
7 (1.4%). These exact values and every 250-group bin are in
`failed_training_runs/rev5_corr_ceiling4500.json`, whose raw SHA-256 is
`6109d4c98a4312933be2d77a742c495fe47b5162edb497a0bc37371e41b60c50`.
That artifact also records raw SHA-256 and byte counts for the run directory,
all external logs, and the revision-5 launch identity.

The complete 182 MiB failed run was moved recoverably, not deleted, to
`/home/adam/mas/mas/failed_runs/rev5_corr_ceiling4500_20260820/`. It is never
resumed, merged, evaluated as an endpoint, or pooled with a later run.

Preregistration revision 6 discloses this post-training but pre-sealed-outcome
change. Only correctness seed 1's safety ceiling changes, from 4,500 to 15,000
attempted groups. The arm restarts from the frozen SFT adapter at update zero
with the same seed, reward, model, FP16 dtype, optimizer, learning rate, KL,
group size, temperature, token budget, target of 276 updates, checkpoints, and
crash policy, and it still stops immediately at update 276. If 15,000 attempts
are insufficient, the failure is reported and there is no further extension.
Physical L40S GPU 7 was prospectively assigned at the user's direction and all
eight L40S GPUs, including GPU 7, were verified idle before the revision was
frozen. A synchronization regression test now fails if the preregistration,
launcher, and completion auditor disagree on the ceiling; all eight workflow
tests pass locally.

The revision-6 identity was frozen and pushed as commit `bb9d6811`. On the L40
host, `freeze_hashes.py --verify` recomputed the 13 GB base-model manifest plus
all code, adapter, reward, split, and failure-audit identities: 39 pinned,
0 changed, 0 missing, and 0 required-but-unpinned. The same eight workflow tests
passed in the isolated L40 environment, the tracked checkout was clean, and the
launch-time machine checks found 41 GiB free and physical GPU 7 idle at 19 MiB
with no compute process.

Correctness seed 1 then started from update zero at
2026-08-20 11:22:58 UTC on physical L40S GPU 7, process group 3696880:

```
FPGA_ENV_BIN=/home/adam/mas/mas/env_fpga/bin \
RTLCODER_PATH=/home/adam/mas/mas/rtlcoder \
PYTHONNOUSERSITE=1 ./run_arm.sh correctness 1 7
```

The emitted `run_config.json` independently records correctness reward, seed 1,
group 8, temperature 1.0, 1,536 tokens, learning rate 1e-5, KL 0.1, FP16,
target 276 updates, checkpoints 138/276, and the sole amended value: a maximum
of 15,000 groups. The launcher again passed all 39 hashes and the functional
oracle canary before loading 6.77B parameters. The first complete group was
7/8 correct, non-flat, and produced update 1 in 60 seconds; GPU 7 was then
active at 27.9 GiB, 97% utilisation, and 222.83 W. This establishes launch
health only and is not sealed efficacy evidence.

A detached completion monitor is active outside the tracked study checkout. It
sends the already-tested iPhone notification on correctness success or failure.
Only after a clean `276|target updates reached (276)` summary and process-group
exit will its fail-closed launcher verify the frozen Git identity, clean tracked
state, absent sealed outputs, free disk, and idle GPU 7, then invoke the hashed
`run_sealed_server_stage.sh` unchanged on that GPU. It also notifies when the
server evaluation starts and when it succeeds or fails. A pre-completion dry
invocation refused without creating a sealed log, status, or output artifact.

### Exploratory CPU completion-risk sensitivity analysis (2026-08-20)

`exploratory_correctness_completion_risk.py` ran on the L40 host's CPU with
`CUDA_VISIBLE_DEVICES` empty, one million Monte Carlo draws, and seed 20260820.
The active revision-6 GPU-7 process remained healthy at 96% utilisation during
the analysis. This diagnostic is explicitly outside the frozen primary
workflow: it consumes only aggregate 250-group counts from the archived
revision-5 audit, never candidate RTL or sealed efficacy output, and cannot
change the active run, its 15,000-group ceiling, or any reporting rule.

The input audit SHA-256 is
`6109d4c98a4312933be2d77a742c495fe47b5162edb497a0bc37371e41b60c50`,
the diagnostic script SHA-256 is
`b103acc252212183eef0f8745a97c4838868ab489345795e95dd642e159a8289`,
and the complete machine-readable output `exploratory_correctness_completion_risk.json`
has SHA-256
`de40c245576b8eaa1f2e942a244a4c63dd4efd2a42e9350d71b08239d9d6982f`.

After the archived stop, 61 further updates are required within 10,500 groups,
so the break-even expected non-flat rate is 0.58095%. The final six observed
250-group bins contain `[5, 4, 6, 3, 3, 4]` updates. A binomial logistic slope
test over those bins gives an odds ratio of 0.92591 per bin and p=0.51562: these
six bins do not establish continuing late decline, although this does not prove
stationarity.

The result is intentionally a sensitivity table, not one invented probability:

```
future assumption                                      completion result
final-1500 rate (1.6667%) remains fixed                exact failure 3.65e-24
stationary Jeffreys uncertainty from final 1500        999,978 / 1,000,000 complete
resample the last six 250-group rates                  1,000,000 / 1,000,000 complete
one more 0.5814 rate-ratio drop, then plateau          99.99952% complete
halve the final-500 rate to 0.7%, then plateau         93.94265% complete
break-even 0.58095% fixed rate                         51.71766% complete
fixed 0.5% rate                                        13.50419% complete
repeat the 0.5814 decay every future 1500 groups       17 / 1,000,000 complete
```

Thus recent-rate and plateau models say the new ceiling is ample, and the late
bins contain no statistically detected continuing slope. The run can still fail
under a harsh compounding-saturation model, which expects only 33.94 of the 61
needed future updates. Since one non-stationary trajectory cannot identify
which future model is true, no unconditional success probability is claimed.
The scientifically valid decision remains to leave revision 6 untouched and
report its actual stopping condition.

### Correctness control completed; frozen pre-open contract stopped the repair study (2026-08-24)

The revision-6 correctness-only control reached its frozen target normally at
2026-08-24 17:23 China time. The server `run_summary.json` records exactly 276
optimizer updates in 12,054 attempted groups, 11,778 flat groups, checkpoints
138 and 276 present, no missed checkpoint, and `target updates reached (276)`.
Its SHA-256 is
`444d5e15218ca30d4107423ac74a25422a79f7fa45e7f1cea87c4df4c1c9183b`.
This completes all five declared training arms; it is still a training-
completion fact, not an efficacy result.

The first automatic sealed-stage handoff then failed operationally with exit
126 because the untracked wrapper executed tracked
`run_sealed_server_stage.sh` directly even though Git records that file as mode
100644. The failed wrapper and log/status were preserved under
`/home/adam/mas/mas/failed_handoffs/rev6_permission_20260824T172435/`.
Only the untracked wrapper was changed to invoke the byte-identical frozen
script through `bash`; the tracked checkout remained clean at frozen identity
`bb9d68115555317ba968c62f96308ec321606918`. This operational repair did not
open the sealed split or alter any study code, model, checkpoint, reward, or
decision rule.

On the repaired launch, all 39 frozen hashes matched and
`verify_sealed_training.py` passed all five runs. Materialisation then produced
1,217 distinct non-empty RF-training candidates from 7,047 logged occurrences.
The mandatory pre-open canonicalisation/compilation/trace contract stopped on
exactly one candidate before any sealed evaluation began:

```
file: rtl/sealed_rf_training_candidates/
      rftrain__iir6_v3__a5194f1b83f187c5.sv
source: grpo_rf_s2/group_log.jsonl:3083
training location: group 386, candidate 2, update 244
oracle/reward: incorrect, reward 0.0, structural features not evaluated
exception: Unsupported: ambiguous statement: multiple top-level '<='
           (cannot separate assignment from comparison)
```

The emitted candidate SHA-256 is
`296772a50469a79ef709c6273c1547ec1c5fc7c6412a6a40bb286b9f08cb358c`.
Its reset branch places eight nonblocking assignments on one source line; the
candidate is also malformed later by an incomplete ternary. An independent
read-only pass over all 1,217 materialised files found this one exception and
no other `verify_contract` exception. The candidate had already been rejected
by the functional gate during training, which is why its structural reward was
never read. Nevertheless, the frozen preregistration deliberately requires the
mutation contract over **every distinct RF-arm training candidate**, and says
that any new failure classifies the experiment `invalid_repair` and must not be
patched and rerun. That conservative rule cannot be weakened after observing
this failure merely because the offending candidate was incorrect.

The contract process exited before writing `rf_training_contract.json` and
before the first `eval_sealed.py` command. All eight efficacy destinations
(`sealed_sft`, RF endpoints and midpoints, MLP controls, and correctness
control) remain absent, GPU 7 is idle, and no sealed member, candidate, oracle
result, or PPA outcome has been generated or inspected. Therefore the sealed
efficacy split remains unopened, but this preregistered repair attempt has met
its frozen `invalid_repair` stop condition. Any later evaluation would have to
be labelled exploratory or preregistered as a new study; it cannot be presented
as continuation of this confirmatory attempt.

Additional preserved remote hashes:

```
sealed_training_audit.json     106ab3b73ae8b3e8b369a741d1d1feb04cbb236f6b5dc8f7dfec22f75cd13ff7
rf_training_candidates.json    49f16cf5ce31bd8c5661697418c1b41b9088b441246cb397991ff45351257828
RF seed-2 group log            b4737450595e5ab38b5d8852d18ade27d81ebd2386cad2ac3fb892262ae84979
failed pre-open launch log     d8868795b699b4459d7b3e3f368e43436581f7214b6a8769472e548bc459f7b2
```

### Separate reward-eligible Study 2 frozen before sealed efficacy (2026-08-24)

Study 1 remains `invalid_repair` under its frozen all-candidate rule. It is not
renamed, amended, or erased. Because it stopped before any sealed generation,
a separately labelled Study 2 was frozen at 2026-08-24 10:57:53 UTC to test the
already-trained checkpoints on the still-unopened efficacy split. This is a
prospective efficacy test, but not an independent validation of the gate scope:
the reward-eligible scope was specified after diagnosing the Study 1 failure,
and the paper must say so.

The Study 2 gate follows the causal training path. Every row whose functional
oracle allowed the RF structural reward to be used must have non-empty RTL,
`correct=true`, `gate="ok"`, a finite positive reward, a canonical hash, and a
structural-feature dictionary. Every correct row must satisfy all of those
conditions. Every non-correct row must retain reward 0.0 and is counted by its
exclusion reason rather than deleted. A distinct RTL string may not mix design
or eligibility identities. Thus the malformed incorrect candidate at RF seed-2
line 3083 remains visible in the exclusion ledger but cannot invalidate a
structural-reward implementation path that it never entered.

The training-log facts observed during the Study 1 diagnosis, and frozen before
any efficacy output, are 7,072 total rows, 7,047 non-empty RTL occurrences,
6,534 reward-eligible occurrences, and 801 distinct reward-eligible RTL
contents. All 801 must pass the lexical mutation contract, reproduce the exact
reward-time canonical hash and feature vector, compile, match original versus
canonical traces under both oracle seeds with 256 vectors, and have zero
cross-design canonical collisions. A count mismatch or any failure stops Study
2 before sealed generation, with no patch-and-rerun.

The frozen scientific declaration is `preregistration_study2.json`. The
implementation is `audit_rf_reward_eligible.py`, with separate server, laptop
Vivado, handoff, and final-analysis wrappers carrying the `_study2` suffix.
`analyze_sealed_v3.py` retains the Study 1 all-nonempty scope as its default and
requires an explicit `--mutation-scope reward_eligible` for Study 2. Local
GPU-free regression tests cover malformed incorrect exclusion, missing metadata
failure, structured contract exceptions, and analyzer fail-closed handling;
all 12 tests pass. At this freeze point no sealed efficacy directory or result
exists. The complete byte identity is recorded separately in
`hashes_study2.json` before the Study 2 gate is executed.

The identity manifest was generated on the L40 host against commit `0749a7e2`
and resolves all 45 entries with zero missing objects. Its raw-file SHA-256 is
`ae6eba02b205c3b628ce1fa0025b7071c1a3b973a427a93f256c4fb2ca08b623`.
All 41 ordinary file entries independently match the laptop checkout; the four
remaining entries are the server-only SFT-adapter and base-model manifest
digests/file counts. The pinned base-model digest is
`c29348b7a8ee7fbd73a31a215942d51d5490574d080305a15ca12f7fd396e256`,
and the pinned SFT-adapter digest is
`9ce91891c911b73f3f636b21ffb9f1769ce2b7ef2fbe40a8d1d68a874d56e2e8`.

The frozen Study 2 pre-open gate then passed exactly. The repeated training
audit again passed all five arms. The reward-eligible ledger contains the
frozen 7,072 rows: 6,534 eligible occurrences, 513 non-empty oracle-incorrect
occurrences, and 25 no-module occurrences, yielding exactly 801 distinct
eligible RTL contents. All 801 passed the mutation, reward-time hash/feature,
compile, and two-seed trace checks; there were zero rejects, zero contract
failures, zero pre-contract errors, and zero cross-design collisions. This is a
validity result, not an efficacy result.

Preserved Study 2 gate hashes:

```
sealed_training_audit_study2.json          106ab3b73ae8b3e8b369a741d1d1feb04cbb236f6b5dc8f7dfec22f75cd13ff7
rf_reward_eligible_manifest_study2.json    eb14e0ef867723b8caafb45009c8791a305393dedca4723354220a3ac2c1cd66
rf_reward_eligible_contract_study2.json    6582cc0ee8f5ce4d5970891f47e1fff5a21d8484578e0b56ad638b85ed3c4aca
```

Only after that exact pass did the runner invoke the first sealed command,
the frozen 48-sample-per-design SFT evaluation. At the time this entry was
written the SFT generation was still running and no policy-level efficacy or
PPA result had been inspected.

### Study 2 sealed efficacy outcome (2026-08-26)

The server stage completed without error, and the frozen laptop Vivado audit
then covered all eight arms. The per-arm audit contains 112, 39, 51, 24, 29,
103, 64, and 67 candidate rows; 488 synthesized and the single explicit
failure was retained for penalized scoring
(`sealed_ppa_audit_study2.json:14-72`). The audit is marked complete and pins
the unchanged `run_ppa.py` and `ppa_synth.tcl` hashes
(`sealed_ppa_audit_study2.json:3-7`).

On the preregistered primary penalized equal-sample endpoint over all 20 sealed
designs, RF raised mean Fmax from 35.3752 to 93.0133 MHz: a +57.6382 MHz paired
effect with 95% stratified-bootstrap CI [+37.6927, +77.2049]
(`sealed_results_study2.json:803-813`). Both independent training seeds were
positive overall, at +49.5161 and +65.7603 MHz
(`sealed_results_study2.json:817-827`). The interpolation effect was +77.8878
MHz [48.3661, 107.1789], and the extrapolation effect was +37.3886 MHz
[13.8897, 60.8875] (`sealed_results_study2.json:773-799`).

Correctness did not collapse: combined RF correctness was 0.5385 versus 0.5625
for SFT (`sealed_results_study2.json:810-813`). The original MLP-reward control
also improved over SFT, but its all-design point estimate was 66.1401 MHz and
its SFT-relative effect was +30.7650 MHz, below RF's 93.0133 MHz point estimate
(`sealed_results_study2.json:803-808`,
`sealed_results_study2.json:864-869`). This output does not contain a direct
RF-minus-MLP confidence interval, so direct statistical superiority must not be
claimed from these point estimates alone.

The correctness-only control increased all-design correctness to 0.6740 but
reduced penalized Fmax by 10.6969 MHz relative to SFT
(`sealed_results_study2.json:925-935`). This separates the hardware-grounded
physical-quality effect from merely optimizing functional pass rate. The RF
midpoint-to-end check found no late divergence: interpolation stayed 125.4967
to 125.3674 MHz while extrapolation rose 51.9107 to 60.6593 MHz
(`sealed_results_study2.json:1008-1025`).

The reward-eligible mutation/trace contract remained 801/801 with zero
rejections and collisions (`sealed_results_study2.json:975-986`), and reward
resolution was 114/147 eligible groups, or 0.7755
(`sealed_results_study2.json:948-952`). The frozen final classification is
`full_two_regime_repair`, because both seeds improved in both regimes and both
combined confidence intervals excluded zero
(`sealed_results_study2.json:1030-1031`). The complete result artifact has raw
SHA-256 `03c746a87de291613cc1c32a867ab40fce512af50eb40fd39c0b76ce441802f9`.

This is the main sealed efficacy result. It does not by itself complete the
separately planned resource/power summary or PYNQ-Z2 board confirmation; those
must remain bounded follow-up evidence and must not change this frozen outcome.

### Bounded Study 2 secondary closure (2026-08-26)

After the primary outcome was opened, a secondary-analysis specification was
frozen before calculating the direct RF--MLP interval or aggregate resource
trade-offs. It forbids new generation, checkpoint selection, sample changes,
or any change to the `full_two_regime_repair` primary classification
(`study2_secondary_analysis_spec.json:1-45`). These analyses are explicitly
post-primary secondary evidence, not a retroactive preregistration
(`study2_secondary_results.json:2-10`).

The direct paired comparison reuses the exact primary family-by-regime
bootstrap resamples. RF exceeds MLP by +27.4368 MHz [20.7440, 34.4775] under
interpolation, +26.3096 MHz [6.0028, 46.6165] under extrapolation, and +26.8732
MHz [16.2151, 37.4835] across all 20 designs
(`study2_secondary_results.json:108-153`). Thus the direct interval excludes
zero in each frozen scope; unlike the earlier point-estimate-only comparison,
statistical superiority over MLP is supported for this sealed evaluation.

All three endpoint arms contribute 960 samples across the 20 designs. SFT, RF,
and MLP correctness are 0.5625, 0.5385, and 0.4990; their implementation rates
are 0.5625, 0.5385, and 0.4979, respectively
(`study2_secondary_results.json:81-106`). The complete PPA audit remains
489 rows, 488 successful implementations, and one explicit failure
(`study2_secondary_results.json:11-14`).

Resource and power values condition on compiled oracle-correct draws and use
the 15 designs with such support in SFT, RF, and MLP; designs are then weighted
equally (`study2_secondary_results.json:155-176`). Relative to SFT on this
common support, RF averages 754.93 versus 689.23 LUTs, a +65.70 difference
[47.25, 84.15] (`study2_secondary_results.json:231-250`), and 236.20 versus
161.45 flip-flops, a +74.75 difference [66.15, 83.36]
(`study2_secondary_results.json:305-324`). Conversely, RF averages 2.73 versus
5.00 DSP blocks, a -2.26 difference [-2.82, -1.70]
(`study2_secondary_results.json:379-398`). BRAM use is zero in all three arms
on this support (`study2_secondary_results.json:453-472`).

Vivado vectorless power is 0.16225 W for RF versus 0.15968 W for SFT, a
+0.00257 W paired difference [0.00170, 0.00345]
(`study2_secondary_results.json:527-546`). This is an estimated-power trade-off,
not measured board power. The defensible paper statement is therefore that RF
buys much higher penalized Fmax with more LUT/FF use and a small vectorless
power increase, while using substantially fewer DSPs; it is not a free PPA
improvement in every dimension.

`analyze_study2_secondary.py` is the sole generator for the secondary JSON,
claim ledger, and two Study 2 TeX tables. `verify_claims.py` independently
checks that the primary outcome is unchanged, all three direct comparisons use
the frozen resample-plan hashes, the 489-row PPA totals agree, all 59 secondary
claim pointers resolve, and every generated table macro names a ledger claim.
The complete secondary result has raw SHA-256
`db65bced7c7a1052101764f221eec67407c85f3cba4f56d215a4493c94b31d15`.

### Study 2 live PYNQ-Z2 confirmation (2026-08-26)

This is the new Study 2 board result, not the older asymmetric historical
comparison. The original outcome-independent family hash stopped before
creating any board output because it selected `firr18_v5`, for which SFT and
both RF seeds had zero oracle-correct candidates. That failure remains recorded
with its three source summaries in
`study2_board_protocol_amendment.json:9-22`; it was not hidden or replaced
silently. The amended feasibility rule requires at least one correct candidate
in each paired arm, then applies the same design hash without using reward,
Fmax, area, resource, or power values. Consequently this board subset is
descriptive supporting evidence, not an independently selected confirmation
(`study2_board_results.json:3-5`).

After selection and before any upload or live result, the frozen sweep floor
was lowered symmetrically from 20 to 5 MHz because already-sealed Vivado rows
put valid selected DUTs below the old floor. The high end, step, three repeats,
trace depth, scoring threshold, and canary margin were unchanged, and no
silicon outcome had been observed (`study2_board_protocol_amendment.json:41-62`).
All ten selected DUTs plus the echo canary passed their Icarus/golden self-check
at 1.0000 before the fresh Vivado build.

The live PYNQ-Z2 sweep contains 52 frequency points for each entry in each of
three complete runs (`study2_board_results.json:21-35`). Every boundary was
recomputed from the raw scores, no trace returned to passing after its first
failure, and every DUT/canary Fmax spread was 0 MHz
(`study2_board_results.json:31-48`). The echo canary was 200.0 MHz; the minimum
canary-to-DUT margin was 57.14 MHz, so all ten DUT gates passed
(`study2_board_results.json:50-53`).

The paired live-silicon medians were:

| Family/design | SFT [MHz] | RF [MHz] | RF--SFT [MHz] |
|---|---:|---:|---:|
| FIR / `fir34_v1_8b` | 40.00 | 125.00 | +85.00 |
| FIRR / `firr20_v6` | 58.82 | 142.86 | +84.04 |
| polynomial / `poly16_v13_8b` | 30.30 | 30.30 | 0.00 |
| IIR / `iir18_v7` | 125.00 | 125.00 | 0.00 |
| median / `med19` | 40.00 | 30.30 | -9.70 |

These rows are generated from `study2_board_results.json:55-110`, not copied
into the paper by hand. Across the five pairs, RF has two wins, two exact ties,
and one loss; the descriptive means are 58.824 MHz for SFT and 90.692 MHz for
RF, a +31.868 MHz mean paired difference, while the median difference is 0 MHz
(`study2_board_results.json:112-121`). Therefore the honest silicon conclusion
is heterogeneous directional support: two large FIR-family gains, no change
on polynomial and IIR, and a median-filter regression. Five amended pairs do
not justify a population CI or a claim that RF wins every family.

The raw live artifact is
`rtl/sealed_study2_board/catalog_fmax.json` (SHA-256
`0bf79d8ba9393622e813f85a4068d27e2e19a105131ec70f9b82501aac4e1443`).
It identifies itself as `live_pynq_clock_sweep` and binds the exact bitstream,
HWH, selector map, and selection-manifest hashes
(`rtl/sealed_study2_board/catalog_fmax.json:3-33`). The exact committed
bitstream SHA-256 is
`eca6ea6dde9f855d4f1c058827fbcdf45a2c80e16223dd9ab8e9ceeba66cb91f`.
`analyze_study2_board.py` is the sole generator for the descriptive board JSON,
27-claim ledger, and TeX table. `verify_claims.py` independently checks all raw
boundaries, hashes, repetitions, canary gates, scope language, source pointers,
and generated table macros.

### Strongest-paper evidence consolidation (2026-08-26)

`STRONGEST_PAPER_EVIDENCE_MAP.md` is now the single pre-writing map for the
strongest paper supported by this record. It inventories the sealed primary
result, matched controls, repaired-reward checks, physical-cost trade-offs,
live board support, historical breadth, Qwen replication, mechanism, sampling
efficiency, contextual controls, mandatory caveats, and evidence that must stay
excluded. It does not draft or modify manuscript prose. Numerical authority
remains with the generated claim ledgers and their artifact pointers; if the
map ever disagrees with a generated claim, the generated claim wins.

### Verified pre-writing figure and table package (2026-08-26)

The canonical visual package is inventoried in
`paper/FIGURE_TABLE_PACKAGE.md`. `paper/make_verified_figures.py` produces the
five quantitative figure composites plus the locked method export as matching
PDF/PNG files, with exact plotted arrays, frozen input hashes, output hashes,
factual caption skeletons, and file:line provenance recorded under
`paper/generated/`. Its `--check` mode independently regenerated all six
figures and confirmed byte-identical outputs. The final visual audit repaired
annotation collisions and retained zero-valued designs, both board ties, the
board loss, the median-family counterexample, and the amended board-study scope
warning.

`analyze_study2_secondary.py` also generates a compact four-arm headline table,
a separate two-seed replication table, a regime/direct-control table, and the
conditional-PPA table entirely through claim macros. The legacy breadth,
family, Qwen replication, and trajectory tables remain generated supporting
assets. `verify_claims.py` checks every Study 2 table macro against the
provenance ledger. This package is complete enough to begin drafting; no
manuscript prose was changed during visual preparation.

### Full TCAD manuscript draft and rendered audit (2026-08-26)

The strongest-paper evidence map has now been converted into a complete IEEE
TCAD regular-paper draft under `paper/`. The manuscript leads with the frozen
20-design repaired-RF versus SFT endpoint, reports both independent RF seeds,
then presents the correctness-only and original-MLP controls, conditional PPA,
the explicitly amended descriptive PYNQ-Z2 study, earlier five-family breadth,
Qwen2.5-Coder transfer, probability-reallocation mechanism, perfect-selector
bound, and bounded historical reward-failure trajectory. It does not pool the
historical and sealed studies or promote the amended board subset to
independent confirmation.

The generated PDF is `paper/build/main.pdf`: 12 US-letter IEEE two-column pages
with a 214-word abstract, six index terms, six canonical figures, five headline
tables, a dedicated generative-AI-use section, and 24 bibliography entries.
Every rendered manuscript number remains claim-ledger backed; static checks
found no undefined citations, references, duplicate labels, or structural TeX
errors. All 12 rendered pages were visually inspected. The remaining
submission tasks are human-author decisions---supervisor review, author order,
ORCIDs, prior-version/concurrent-submission disclosure, and final approval---not
missing empirical analysis.

### Post-primary artifact-only mechanism and sampling-cost extension (2026-08-27)

Before launching any new training or timing-closure experiment, a deterministic
post-primary analysis was added without changing the completed Study 2 outcome,
samples, checkpoints, oracle decisions, or Vivado rows. The exact endpoint
decomposition verifies `F = q * mu`: SFT has correctness 0.562500, conditional
Fmax 62.889157 MHz, and penalized Fmax 35.375151 MHz; repaired RF has
0.538542, 172.713370 MHz, and 93.013346 MHz; original MLP has 0.498958,
132.556431 MHz, and 66.140136 MHz; correctness-only has 0.673958,
36.616941 MHz, and 24.678293 MHz
(`artifact_extension_results.json:13-34`,
`artifact_extension_results.json:282-304`,
`artifact_extension_results.json:542-564`,
`artifact_extension_results.json:802-824`). Thus the correctness-only arm's
higher functional yield coexists with a much lower quality conditional on a
correct draw; this is stronger and more precise than saying only that its
penalized endpoint fell.

The structural analysis retains multiplicity within design and then weights
the 16 common-support designs equally. Relative to SFT, correctness-only RTL
raises the mean maximum multiplications per statement from 8.7758 to 17.3349,
reduces the structural accumulation score from 2.8871 to 0.2478, reduces the
pipeline-ratio feature from 0.1447 to 0.0242, and raises the maximum loop bound
from 9.9950 to 12.5830
(`artifact_extension_results.json:1070-1186`). The deterministic largest
conditional-Fmax loss is `iir18_v7`, 126.9468 to 40.1027 MHz; its representative
correctness-only implementation places all 21 multiplications in one statement
and has zero structural pipeline ratio
(`artifact_extension_results.json:2350-2437`). These lexical aggregates
support the bounded interpretation "larger, less-pipelined arithmetic
expressions and loops"; they do not prove that every correctness-only output is
a wide combinational `always` block or establish a unique causal mechanism.

The sealed perfect-selector analysis also corrects the sampling-efficiency
claim for Study 2. One repaired-RF draw (93.0133 MHz) lies between SFT
best-of-17 (92.4707 MHz) and best-of-18 (93.6642 MHz), with an interpolated
equivalent of 17.45 draws (`artifact_extension_results.json:2443-2530`). At
best-of-18, the distinct cost axes are 18 LLM draws, 36 oracle simulation
streams, an expected 10.125 raw correct implementation attempts, and 3.078
content-deduplicated implementations per design. These are workload counts,
not reconstructed GPU seconds or token totals. The older best-of-21 statement
must not be transferred into this sealed study.

`analyze_artifact_extension.py` is the sole generator of
`artifact_extension_results.json` and `artifact_extension_provenance.md`.
`verify_artifact_extension.py` independently checks all input hashes,
decomposition identities, selection rules, structural aggregates, cost axes,
and generated-file freshness. Five extension tests plus the twelve original
sealed-workflow tests pass. All frequencies in this extension remain the
original single-5-ns WNS-derived values until the separately preregistered
timing-closure gate reports its outcome.

### Timing-closure infrastructure gate status (2026-08-28)

The preregistered timing-closure validation has not yet produced a Study-2
candidate result. V1 was aborted after Vivado intermittently failed to read
four different Tcl files from its own installation. Two completed candidate
measurements are retained only as aborted-protocol diagnostics and are not
used in any paper endpoint. The frozen v1 manifest SHA-256 is
`2e0674f96c57be3864a6fab7683b0edc76f732762f78547d5e6a3e8efc17e194`.

V2 introduced raw dependency guards and required 12 consecutive synthetic
first-attempt implementations before exposing any candidate. It produced nine
valid runs, then failed on run 10 when Vivado could not read its own generated
`.Xil/.../realtime/timing_gate_v2_stability_probe.tcl`; that file was present
in the retained failed directory and both dependency guards passed. The v2
FAIL attestation SHA-256 is
`10625e4104341efcdfb21efd3b2983d5e12ba537cb33743bc95dc8196e061ed0`.
No Study-2 candidate RTL ran in v2, and the failure is classified as host/tool
working-file instability rather than RTL timing performance.

V3 moved every Vivado process to a unique short working directory and supplied
an explicit short `-tempDir` under `C:\VGT3S001`, while leaving the device,
Vivado version, closure Tcl, constraints, candidate selection, search rule,
failure scoring, and pilot thresholds unchanged. All 20 required fresh
synthetic synth/place/route processes passed on their first attempt. Every run
compiled and implemented, reported one clock and 51 setup paths, had zero
unconstrained paths, clean routing, and WNS 7.501 ns at the synthetic 10 ns
request. All pre/post raw dependency guards matched and no retry was used.

The frozen v3 package manifest SHA-256 is
`a1d7308b26ee8e8a0081da83dac53b4db6bad2335bd91dcac661ec81c2177271`;
the v3 PASS attestation SHA-256 is
`bdddfb76499011dd0492b4560ac2bba9277f874400663e63cb11dea4da8a829c`.
The full raw logs, per-run result JSON files, launcher status, and attestation
are committed in `timing_closure_gate_v3/stability_campaign_001/` (commit
`816778cc`). This PASS authorizes freezing and running the separate ten-candidate
closure package; it does not validate the manuscript's WNS-derived Fmax proxy
by itself, and no manuscript frequency should yet be relabeled timing-closed.

### L40S GPU-0 exclusion and VerilogEval pre-result boundary (2026-08-29)

Physical GPU index 0 on `ubuntu-SYS-420GP-TNR` is permanently excluded from
future CUDA work by explicit user instruction. During the prospective matched
VerilogEval extension, the SFT process assigned to GPU 0 stopped on its first
problem with a CUDA illegal-memory error before publishing any problem shard.
The RF seed-1 and seed-2 processes on GPUs 2 and 4 were unaffected and
continued. This zero-shard SFT attempt is infrastructure evidence, not a model
correctness result; it must never enter the policy comparison. The failed
remote attempt is retained under
`/home/adam/mas/mas/verilogeval_rf_v3_20260829/sft`, and a fresh SFT run may use
only a nonzero validated L40S GPU after one becomes free. The permanent local
operational rule is recorded in `EXECUTION_HOST_POLICY.md`.

### Real-candidate closure V3 and single-thread infrastructure V4 (2026-08-29)

The separately frozen real-candidate V3 package ran all ten predeclared
candidates from scratch after the V3 synthetic PASS. Nine candidates produced
complete constrained closure brackets. Candidate
`c02_fir_rf_fir42_v6_8b` received the preregistered zero after two consecutive
Vivado synthesis processes at the same bisection period reported two different
existing installation Tcl files as missing. The formal V3 verdict is FAIL:
completeness is false and pooled Spearman is 0.8159509202, below the frozen
0.90 threshold. Median sMAPE is 0.0231660 and the representative paired RF-SFT
mean remains +86.5879 MHz, but those favorable secondary values do not override
the failed gate (`timing_closure_candidate_v3/results/pilot_gate.json`). No
historical WNS-derived manuscript value may be relabeled timing-closed from V3.

V4 prospectively tested the concrete infrastructure hypothesis that Vivado's
multithreaded synthesis helper caused the internal-file failures. Its frozen
manifest is
`0abb91093bb073b483dbe0e09d1863004eed3b468174ca66259055014cbd72e1`.
The wrapper set `general.maxThreads=1` before sourcing the byte-identical V1
closure flow, and the raw dependency guard was expanded from
`scripts/rt/data/**/*.tcl` to the complete `scripts/rt/**/*.tcl` tree. Eighteen
fresh synthetic implementations passed. Run 19 then failed when Vivado still
launched its helper and reported the existing
`scripts/rt/data/unimacro/unimacro_vhdl.tcl` unreadable, while all before/after
raw dependency hashes matched. V4 therefore froze FAIL without a retry and
without exposing any Study-2 candidate. Its attestation SHA-256 is
`77d34c36ca081176732286170b81bdc2a7b52dd5647a188bfc0e714731b304d3`
(`timing_closure_gate_v4/stability_campaign_001/stability_attestation.json`).

The current scientific boundary is that the laptop's Vivado installation/host
is not reliable enough for the preregistered repeated fresh-process closure
gate. This is infrastructure evidence, not evidence that candidate RTL failed
timing. The V4 candidate package remains NO-GO, the extra-seed package's frozen
timing prerequisite remains unsatisfied, and proxy-dependent PPA-RTL labeling
must not launch. Repair requires a validated Vivado reinstall/other licensed
Vivado host or a newly justified prospective execution architecture; repeated
retries until PASS are prohibited.

### Minimal Vivado synthesis reproducer and host diagnosis (2026-08-30)

The V4 infrastructure fault was reproduced without candidate RTL, placement,
routing, or timing analysis. A trivial registered 32-bit module failed during
out-of-context synthesis when Vivado 2023.1 falsely reported different existing
realtime Tcl files as missing. Direct file I/O was stable: PowerShell completed
10,000 SHA-256 reads, one parent Vivado Tcl process completed 20,000 binary
reads, and five fresh parent Vivado processes completed 100 reads each with
zero failures. In contrast, the nine retained minimal helper-enabled synthesis
runs produced four passes and five internal-file-read failures. A byte-identical
short-path copy did not eliminate the fault.

A diagnostic-only copy of `rtSynthParallelPrep.tcl` disabled the parallel
helper without modifying the Vivado installation. Six of seven retained runs
then passed, but the seventh still falsely reported the existing `common.tcl`
as missing. The helper therefore amplifies the fault but is not its root cause.
The installation files remained byte-stable, ACL-readable, and repeatedly
hashable; C: reported Healthy/OK, and no contemporaneous storage, Defender, or
resource-exhaustion event explained the failures.

The host is Windows 11 25H2 build 26200.9168, while AMD's Vivado 2023.1 support
matrix lists only Windows 11 21H2 and 22H2. The established proximate cause is
the Vivado synthesis/realtime runtime's intermittent file-I/O failure on this
host; the leading underlying hypothesis is the unsupported tool/OS combination,
not candidate RTL. Full scripts, bounded raw logs, and the post-restart decision
rule are retained in `vivado_diagnostics/`. No frozen study was amended and no
paper endpoint was produced.

### First post-restart Vivado probe (2026-08-30)

The prescribed first post-restart ordinary helper-enabled minimal synthesis
passed once: 106 cells, zero synthesis errors, empty stderr, and exit code 0.
The raw stdout confirms that Vivado launched its synthesis helper, so the trial
exercised the previously implicated runtime path
(`vivado_diagnostics/evidence/postrestart_20260830__r01/`). This is encouraging
host-diagnostic evidence, but it is not a stability PASS: four of nine retained
pre-restart helper-enabled trials also passed. No paper experiment or candidate
closure run was launched, and the existing V1--V4 scientific boundary is
unchanged.

### Post-restart and persistent-parent Vivado gates V5--V6 (2026-08-30)

V5 prospectively tested the reboot hypothesis with forty required fresh
first-attempt synthetic implementations, using the unchanged V4 single-thread
closure wrapper and no Study-2 candidate RTL.  Runs 1--6 were valid.  Run 7
then launched the synthesis helper and falsely reported the existing
`scripts/rt/data/unimacro/unimacro_vhdl.tcl` file unreadable (`No error`).  The
complete raw dependency guards before and after the process matched.  V5 is an
immutable FAIL; its attestation SHA-256 is
`6dcb03bf4ec0ba575f4d2908d991f3d6a65d4bccb9c9a8340a9f9847e71a46e6`
(`timing_closure_gate_v5/`).  Restarting Windows therefore did not repair the
runtime fault.

The only locally justified alternative architecture was then tested before
candidate exposure.  A diagnostic showed that two isolated in-memory projects
could synthesize in one Vivado parent with clean project boundaries and one
helper launch.  V6 prospectively required forty such isolated projects, each
running the unchanged pre-synthesis XDC plus synth/opt/place/route sequence.
Its first project was fully valid (WNS 7.501 ns, 51 setup paths, zero
unconstrained paths, clean routing and isolation).  During synthesis of project
2, however, ABC failed to open an internal realtime `genlib` temporary path and
the parent exited with code 3.  The dependency guards again matched.  V6 is an
immutable FAIL; its attestation SHA-256 is
`de502c2e9d6e7832f222a5555986a9eddabf442a87ed4e1f8c562bd501339eca`
(`timing_closure_gate_v6/`).

Consequently no real V4--V6 candidate, extra-seed timing-dependent extension,
or PPA-RTL physical-label job was authorized.  The local execution alternatives
are exhausted without modifying unsupported Vivado internals.  Completion of
that timing-dependent branch now requires a licensed Vivado environment on a
supported OS (or another prospectively justified external environment); this
is an infrastructure boundary, not candidate timing evidence.

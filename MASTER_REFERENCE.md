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

### FABRICATED citations to NEVER use
ChipMATE, VFlow, ChipSeek-R1 (do not cite; they don't exist). Verify every SOTA
number against the original paper before quoting.

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

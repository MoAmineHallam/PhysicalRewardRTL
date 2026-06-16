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

## 0. TL;DR — what exists and what it's worth

| Thing | State | Headline result |
|---|---|---|
| MAS (design+verification agents) | works (server) | self-correcting RTL gen + sim verify, retries |
| MAS (synthesis→deploy loop) | **coded, never run end-to-end** | no MAS bitstream ever produced (no Vivado on server) |
| Hardware golden capture (966 designs) | **done, validated** | 966 designs bit-exact vs silicon, 0 mismatch |
| RL dataset | done | 9,660 candidates scored vs silicon golden |
| GRPO fine-tune (grpo_v3) | done | VerilogEval pass@1 +2.2, compile +1.4 vs base |
| Sim/silicon gap study | **in progress** | tier-1 measured; tier-2 capture running on board |
| PPA / silicon-Fmax reward | not started (idea) | clock-sweep confirmed feasible on Z2 |

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

## 8. WHAT'S LEFT (priority order)
1. **Finish gap study tier-2:** board capture (running) → `analyze_gap.py` → the number.
2. If gap is real: write it up as the core contribution.
3. Wire `grpo_v3` adapter into the MAS Design Agent (cheap integration win).
4. 2nd base model (generality).
5. Catalog expansion (FSM/combinational families).
6. Silicon-Fmax / PPA reward (Lever 3, = supervisor's RL-PPA on the generation side).
7. Supervisor conversation: reconcile the two tracks into one story.

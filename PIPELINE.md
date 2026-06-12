# Scaled Dataset Pipeline (1000+ designs, hardware reward)

Goal: a GRPO training dataset of **1000+ diverse RTL designs**, each scored
against a **real hardware golden waveform** captured on the PYNQ-Z2. The whole
flow is automated so you only push a button per stage — no per-design manual
Vivado work.

## Why this shape

The reward is NOT "synthesize each LLM candidate on the board" (impossible:
RL needs thousands of rollouts, synthesis takes minutes). Instead:

1. Capture a **golden hardware waveform once per design** (on the board).
2. Score every LLM candidate **in simulation** (iverilog) against that golden.

So "1000 designs" = 1000 golden captures, done once, batched into bitstreams.

## Stages

### 1. Generate the catalog  (done, repeatable)
```
python gen_designs.py
```
Emits `rtl_library/<name>/{design.v,golden.py,spec.txt}` for ~1004 designs
across 42 families (counters, arithmetic, shifters, logic, sequential, FSM-ish,
bit manipulation, datapath) plus `rtl_library/manifest.json` — the single source
of truth (per design: inputs, probe packing, mask, period, golden_body).

### 2. Verify correctness  (done — gate before any Vivado)
```
python verify_manifest.py --jobs 8
```
Compiles every `design.v` with iverilog and checks it matches its golden_body.
**1004/1004 PASS.** Only designs that pass here go to hardware.

### 3. Generate batched bitstream sources  (done)
```
python gen_bitstream.py --batch 64
```
Splits the catalog into 16 batches (a Zynq-7020 can't hold 1000 DUTs + a
1000-way mux). For each batch K:
- `rtl/batches/dut_top_b{K}.v` — 64 DUTs, per-instance wire renaming, 6-bit
  local sel mux (verified: all 16 elaborate with all DUTs, no collisions)
- `rtl/batches/build_b{K}.tcl` — headless Vivado build template
- `rtl/batches/batch_manifest.json` — global sel <-> design map

Use `rtl/la_axi_wide.v` (6-bit sel) instead of `la_axi.v` (3-bit) for batches.

### 4. Build bitstreams headlessly  (one command per batch, no GUI)

Runs on the **laptop** (Vivado lives there; the server has no Vivado and no link
to the board). The build Tcl is self-contained — it builds the Zynq PS7 +
AXI-Lite -> la_axi_wide -> dut_top block design inline (no external BD_TCL) and
derives all paths from its own location, so it works as-is on Windows.

Linux/macOS:
```
for k in $(seq 0 15); do vivado -mode batch -source rtl/batches/build_b$k.tcl; done
```
Windows (cmd):
```
for /L %k in (0,1,15) do vivado -mode batch -source rtl\batches\build_b%k.tcl
```
Each batch K writes `rtl/batches/out_bK/system_bK.bit` + `system_bK.hwh`.

### 5. Capture hardware goldens  (done — on the board, automated)
```
sudo python3 capture_waveforms.py --bit-dir rtl/batches \
     --manifest rtl/batches/batch_manifest.json --rtl-lib rtl_library
```
Loads each bitstream, sweeps sel, reads the LA buffer, writes
`rtl_library/<name>/waveform.npy`. Adjust `--la-base` to your AXI address map.
**1004/1004 captured.**

### 6. Validate hardware vs golden  (done — gate before trusting reward)
```
python validate_hw.py --report hw_bad.json
```
The stimulus counter free-runs (not reset on arm), so each capture is an
exact window of the golden sequence at an unknown phase; validation searches
the window inside a long golden (see validate_hw.py docstring).
**Result: 966 exact match, 0 mismatch, 38 long-period.** The 38 (wide
add/sub/cmp/satadd, true periods 4M-4G cycles) are excluded because a 32768-
sample capture at unknown phase cannot be verified against them — not because
they failed. Training pool = 966 hardware-validated designs (hw_bad.json:
use "good", exclude "bad" + "long_period").

### 7. Build the RL dataset  (on the GPU box — in progress)
```
cd /zeng_gk/Amine/mas
python fpga/build_dataset.py --n 10 --out fpga/dataset.jsonl
python fpga/analyze_dataset.py fpga/dataset.jsonl --weights fpga/design_weights.json
```
build_dataset.py and score_candidate.py are manifest-driven (all 966 good
designs, hw_bad.json consumed, append+resume). The scorer never trusts the
manifest `period` field (it understates the state period for acc/mac); it
compares fixed-cycle sims against golden_from_body directly — stage 6 proved
that sequence bit-identical to silicon for every "good" design.
analyze_dataset.py turns the JSONL into per-design sampling weights
(proportional to within-design reward std: saturated families contribute no
GRPO gradient and are down-weighted to a floor).

### 8. GRPO-v3 + evaluate
```
python fpga/grpo_train_v3.py --steps 600 --group_size 8
```
Trains a fresh LoRA on the 966-design pool: variance-weighted design
sampling (design_weights.json), batched group generation, in-process
hardware-grounded reward, KL-to-base via adapter-disable, fp16+GradScaler
on V100 / bf16 on Ampere (auto). Then run VerilogEval (156) with
run_verilogeval_ft.py under conditions identical to the baseline run.

## Topology (resolved)

- **Server** (`/zeng_gk/Amine/mas`): GPU box. Generates the catalog, verifies
  with iverilog, generates batched sources + build Tcl, trains GRPO. No Vivado,
  no link to the board.
- **Laptop** (`C:\Users\Amine\mas\fpga`): has Vivado **and** the PYNQ-Z2 (board
  connects to the laptop only). Builds bitstreams (stage 4) and captures
  waveforms from the board (stage 5).
- **Bridge**: git (or zip) moves files server <-> laptop.

`PART = xc7z020clg400-1` is confirmed (matches the project's own synth flow).
The block design is built inline by each `build_bK.tcl` — nothing left to fill
in. After build, the laptop pushes `system_bK.bit`/`.hwh` to the board and runs
`capture_waveforms.py` there (board is reachable from the laptop at the address
the existing deployment flow uses).

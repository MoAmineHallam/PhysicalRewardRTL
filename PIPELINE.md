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
```
for k in $(seq 0 15); do vivado -mode batch -source rtl/batches/build_b$k.tcl; done
```
First fill in at the top of each `build_b{K}.tcl`: `PART` and `BD_TCL` (your
Zynq PS + AXI + la_axi_wide block design hook). See "What I need from you".

### 5. Capture hardware goldens  (on the board, automated)
```
sudo python3 capture_waveforms.py --bit-dir rtl/batches \
     --manifest rtl/batches/batch_manifest.json --rtl-lib rtl_library
```
Loads each bitstream, sweeps sel, reads the LA buffer, writes
`rtl_library/<name>/waveform.npy`. Adjust `--la-base` to your AXI address map.

### 6. Validate hardware vs golden  (gate before trusting reward)
```
python validate_hw.py --report hw_bad.json
```
Excludes any design whose silicon capture disagrees with the golden RTL.

### 7. Build the RL dataset  (on the GPU box)
Generate N candidates per design with RTLCoder, score each (sim vs hw golden),
write JSONL — manifest-driven so it scales to all designs.

### 8. GRPO-v3 + evaluate
Train on the 1000-design pool (weighted sampling), then run VerilogEval (156)
vs the 35.9% baseline.

## What I need from you to finish full automation of stage 4

The Vivado Tcl template is complete except for project specifics I can't infer:
1. **PART** — confirm `xc7z020clg400-1` (PYNQ-Z2).
2. **Block design** — the Tcl/path that builds your Zynq PS + AXI interconnect
   + la_axi_wide instance + top wrapper (`BD_TCL`). If you share your existing
   project's `*.tcl` export I'll wire it in so the build is truly one command.
3. **LA AXI base address** + **buffer DEPTH** actually deployed (la_axi_wide
   defaults DEPTH=32768; the old notes mentioned 1024 — confirm).

With those three, stage 4 becomes a single loop with zero manual steps.

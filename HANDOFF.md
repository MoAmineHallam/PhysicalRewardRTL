# Project Handoff — Amine FPGA + RL Research

## What this project is

Two-track research:

**Track 1 (MAS paper):** A multi-agent system (MAS) that takes natural-language hardware specs through Verilog RTL generation → simulation → Vivado synthesis → deployment to a PYNQ-Z2 board. Novelty: closes the loop on real silicon, which prior work doesn't do. The MAS is functionally stable (counter passes end-to-end). Benchmark baseline measured: RTLCoder scores 68.6% compile / 37.2% functional pass on 156 VerilogEval spec-to-rtl problems. This is the number to beat.

**Track 2 (RL paper — current priority, supervisor-directed):** Fine-tune an RTL LLM using real FPGA waveform feedback from the PYNQ-Z2. Every prior RL-for-IC paper uses a simulator for rewards. This project's novelty is hardware-in-the-loop reward signals from real silicon. Done = fine-tuned model beats 37.2% baseline.

---

## Environment

**GPU server (China):**
- SSH: `ssh root@10.251.171.18 -p 30324`
- Conda env: `mas`
- Project root: `/zeng_gk/Amine/mas/`
- VerilogEval: `/zeng_gk/Amine/verilog-eval/`
- Run A results: `/zeng_gk/Amine/verilog-eval/run_A_rtlcoder/results.csv`
- iverilog: `/usr/bin/iverilog`, always use `-g2012`
- Models: RTLCoder at `/zeng_gk/Amine/mas/rtlcoder/`, Qwen2.5-Coder-7B-Instruct to be downloaded

**Windows PC:**
- Vivado 2023.1 (no PYNQ-Z2 board preset installed — configure Zynq PS manually)
- Project: `C:/Users/Amine/la_project/la_pynq/`
- RTL source: `C:/Users/Amine/la_project/la_axi.v`
- Bitstream: `C:/Users/Amine/la_project/la_pynq/la_pynq.runs/impl_1/la_bd_wrapper.bit`
- HWH: `C:/Users/Amine/la_project/la_pynq/la_pynq.gen/sources_1/bd/la_bd/hw_handoff/la_bd.hwh`

**PYNQ-Z2 board:**
- IP: `192.168.2.99`, user: `xilinx`, pass: `xilinx`
- Part: `xc7z020clg400-1`
- Jupyter: `http://192.168.2.99`
- Files on board: `/home/xilinx/jupyter_notebooks/la_bd_wrapper.bit` + `la_bd_wrapper.hwh`
- PYNQ pairs `.bit` + `.hwh` by EXACT matching filename — both must be `la_bd_wrapper.*`

**Critical rules:**
- Never use heredocs or echo for Verilog/long base64 on server — terminal line-length splits them
- Always transfer files via Python writer script: generate base64 of a Python script that calls `pathlib.Path.write_text()`, decode and run it
- Always verify ASCII-clean before base64 encoding: `assert all(x < 128 for x in content.encode())`
- Vivado Tcl Console has no grep/unix tools — use Tcl `string match` or `file open/read`
- Wrapper file is in `.gen` not `.srcs`: `la_pynq.gen/sources_1/bd/la_bd/hdl/la_bd_wrapper.v`

---

## What is DONE

### Phase 0: Logic Analyzer (COMPLETE ✅)

Built and deployed a hardware logic analyzer on the PYNQ-Z2.

**RTL:** `/zeng_gk/Amine/mas/la_axi.v`
- Module: `la_axi`, params: DW=16, DEPTH=32768, AW=15
- AXI-Lite slave interface
- FSM states: IDLE → ARMED → CAPTURING → DONE
- Register map:
  - `0x00 CTRL`: bit0=arm/start, bit1=trigger_mode (0=sw-start, 1=edge-trigger)
  - `0x04 STATUS`: bit0=done, bit1=armed (waiting for trigger)
  - `0x08 RADDR`: buffer read index
  - `0x0C RDATA`: buffer[RADDR]
- Edge trigger: rising edge on probe[0]

**Verified in simulation:** iverilog -g2012, SIMULATION_PASS

**Vivado block design (la_pynq project):**
- Zynq PS (processing_system7, M_AXI_GP0, FCLK_CLK0=100MHz)
- AXI Interconnect
- la_axi_0 (RTL module)
- c_counter_binary (16-bit, feeds probe for self-test)
- proc_sys_reset
- Address: 0x40000000

**Confirmed on real silicon:**
- SW-start: 32768 samples captured, all diffs = 1 ✅
- Edge trigger: first sample bit0=1 (edge fired), all diffs = 1 ✅

**PYNQ Python driver:**
```python
from pynq import Overlay
ol = Overlay('/home/xilinx/jupyter_notebooks/la_bd_wrapper.bit')
la = ol.la_axi_0

# SW-start
la.write(0x00, 0x1)

# Edge trigger
la.write(0x00, 0x3)

# Poll done
import time
for _ in range(100000):
    if la.read(0x04) & 1:
        break
    time.sleep(0.0001)

# Read buffer
for i in range(N):
    la.write(0x08, i)
    sample = la.read(0x0C)
```

---

### MAS Baseline (COMPLETE)

- VerilogEval run A: RTLCoder raw = **68.6% compile, 37.2% functional pass** on 156 problems
- Runner: `/zeng_gk/Amine/verilog-eval/run_verilogeval.py`
- Results: `/zeng_gk/Amine/verilog-eval/run_A_rtlcoder/results.csv`
- Run B (MAS-wrapped) written but paused — MAS prompt hurts simple combinational designs
- Known failure categories from run A: arithmetic/logic (10), combinational/always (6), vector/bit-manipulation (5), FSM/sequential (5), edge detection (4)

---

## What is IN PROGRESS

### Phase 3: Build RL Dataset (NEXT)

See phases section below.

---

## What is DONE (continued)

### Phase 1: RTL Design Library (COMPLETE ✅)

7 golden reference designs written, compile-checked (iverilog -g2012), and committed to repo under `rtl_library/`:
- edge_detector, alu_mux, comb_always, bcd_counter, bit_manip, dff_array, shift_reg
- Each has: `design.v`, `stimulus.txt`, `golden.py` (counter-driven, 32768 samples)

### Phase 2: Hardware Waveform Capture (COMPLETE ✅)

**Vivado block design (la_pynq project) — updated:**
- Replaced c_counter_binary with `dut_top` (instantiates all 7 DUTs, free-running 32-bit counter as stimulus)
- Added `axi_gpio_0` (3-bit output) at `0x41200000` — Python writes sel[0-6] to select active DUT
- `la_axi_0` at `0x40000000` unchanged
- New RTL sources: `rtl/la_axi.v`, `rtl/dut_top.v`, `rtl_library/*/design.v`
- New bitstream deployed to PYNQ: `la_bd_wrapper.bit` + `la_bd_wrapper.hwh`

**Hardware waveforms captured — all 7 DUTs, 32768 samples each:**
- Location on server: `/zeng_gk/Amine/mas/rtl_library/<design>/waveform.npy`
- Verified correct: BCD 79→80 wrap confirmed, shift_reg 0x55/0xAA pattern, bit_manip reversal+popcount ✅

**PYNQ capture driver:**
```python
from pynq import Overlay
import numpy as np, time
ol = Overlay('/home/xilinx/jupyter_notebooks/la_bd_wrapper.bit')
la   = ol.la_axi_0
gpio = ol.axi_gpio_0

def capture(sel_id):
    gpio.write(0x00, sel_id)
    time.sleep(0.001)
    la.write(0x00, 0x1)
    for _ in range(500000):
        if la.read(0x04) & 1: break
    data = []
    for i in range(32768):
        la.write(0x08, i)
        data.append(la.read(0x0C) & 0xFFFF)
    return np.array(data, dtype=np.uint16)
# sel: 0=edge_detector 1=alu_mux 2=comb_always 3=bcd_counter
#      4=bit_manip 5=dff_array 6=shift_reg
```

**Probe packing per sel (matches golden.py):**
- 0: {14'b0, cnt[8], rise}
- 1: {12'b0, result[3:0]}
- 2: {12'b0, valid, out[2:0]}
- 3: {8'b0, tens[3:0], ones[3:0]}
- 4: {4'b0, reversed[7:0], popcount[3:0]}
- 5: {8'b0, q[7:0]}
- 6: {8'b0, q[7:0]}

---

### Phase 1: RTL Design Library (COMPLETE ✅) — original entry below

Building a set of hand-written, known-correct golden reference designs. These are the **measuring instrument** — the model never sees them. The MAS generates candidates, the LA captures waveforms, and these golden references define what "correct hardware behavior" looks like.

**Why hand-written:** The golden references must be trusted ground truth. The MAS output is what you're training, not what you're training *with*.

**Design choices are evidence-driven** from run A failure data. Priority order (most failures first):

1. **Edge detector** — 4 failures (edgedetect, edgedetect2, edgecapture, dualedge). Output goes high for 1 cycle on rising edge of input. FIRST TO BUILD.
2. **ALU with mux** — covers arithmetic/logic failures (m2014, ece241 series)
3. **Combinational always block** — covers alwaysblock, always_if, conditional, kmap failures
4. **BCD counter** — covers countbcd, FSM/sequential failures
5. **Bit-reversal / popcount** — covers vector manipulation failures
6. **D flip-flop array** — covers dff, dff8 failures
7. **Shift register** — general sequential, broadly useful

**Important design principle:** Bias toward sequential designs. Combinational designs settle instantly — their waveform is weak. Sequential designs (counter, FSM, shift register) produce rich time-varying waveforms that exercise the LA meaningfully and strengthen the hardware-grounded novelty claim.

**Directory structure:**
```
/zeng_gk/Amine/mas/rtl_library/
  <design_name>/
    design.v        # golden RTL (hand-written, correct)
    stimulus.txt    # input stimulus sequence
    golden.py       # Python that computes expected output waveform
    waveform.npy    # (Phase 2) captured hardware waveform
```

**Scale strategy:** You write ~7-10 golden references by hand (one time). The hundreds/thousands of training variants come from: (a) MAS-generated candidates on the same specs, both correct and buggy, and (b) VerilogEval's 156 problems run through the MAS. The LA scores all of them automatically against the golden references.

**IMMEDIATE NEXT STEP:** Create the library directory and write `edge_detector/design.v`.

---

## What comes NEXT (phases)

### Phase 2: Capture hardware waveforms
For each golden design:
1. Instantiate design alongside LA in Vivado block design (mux approach: one bitstream, AXI SEL register at 0x10 selects which DUT feeds the probe)
2. Deploy bitstream to PYNQ-Z2
3. Run stimulus, capture LA waveform
4. Save as `waveform.npy`

**Open decision:** One bitstream per design vs. one muxed bitstream. For 7 designs, the mux approach (one synth run, software switches) is clearly better.

### Phase 3: Build RL dataset
Each training example is a JSONL record:
```json
{
  "rtl": "<verilog code string>",
  "stimulus": [...],
  "hw_waveform": [...],
  "golden_waveform": [...],
  "reward": 0.0-1.0
}
```
Reward = waveform similarity score (e.g. normalized Hamming distance between hw_waveform and golden_waveform). Dense reward from waveform closeness is better than sparse pass/fail.

Sources of RTL candidates:
- MAS generating candidates from specs (correct + buggy)
- VerilogEval 156 problems run through RTLCoder (you already have run A results)

### Phase 4: Fine-tune and evaluate
- Fine-tune RTLCoder (or Qwen2.5-Coder-7B) using RL (PPO or DPO) on the dataset
- Evaluate against 37.2% baseline on VerilogEval
- Paper result = fine-tuned model beats baseline

---

## Deferred (not forgotten)

- **MAS board deployment**: MAS generates RTL → MAS synthesizes → MAS deploys to board. This is a separate milestone that demonstrates the full MAS pipeline. To be done AFTER Phase 1.
- **Run B (MAS-wrapped VerilogEval)**: Paused because MAS prompt hurts simple combinational designs. Root cause: different system prompts between run A and B. Fix before resuming: align prompts so A and B use identical generation conditions. Then run B properly.
- **Qwen2.5-Coder-7B-Instruct download**: Replace Qwen3.6-35b (vision model, wrong class, drop it) with Qwen2.5-Coder-7B-Instruct (~15GB bf16, fits alongside RTLCoder in 64GB VRAM). Update `reasoning_call` in `llm.py` to load via transformers, mirroring `coder_call`.

---

## Key decisions already made (don't re-litigate)

- No Ollama — all models via HuggingFace transformers
- RTLCoder 2048-token context limit constrains it to small designs only
- Field ceiling ~30% on real Verilog is the thesis, not a bug
- GEMM oracle abandoned (AXI read-latency bug in reference, iverilog hierarchical access issues)
- "Done" for the paper = fine-tuned model beats 37.2% baseline on VerilogEval, NOT when the first small design works
- LA is a tool (instrument), not the research novelty — don't spend paper novelty budget on it
- Rewards from real silicon is the novelty — every prior RL-for-IC paper uses simulation

---

## Literature (verified real, safe to cite)

- MAGE: arXiv 2412.07822
- RTLCoder: arXiv 2312.08617 (published 41.6%/62.2%, our reproduction 37.2%/68.6%)
- VerilogEval: arXiv 2309.07544
- RTLLM and RTLLM2.0: Lu et al. 2024, Liu et al. 2024
- ResBench: arXiv 2503.08823 (closest prior — does synthesis but not board)
- CVDP: arXiv 2506.14074 (783 problems, SOTA ≤34% pass@1 — confirms 37.2% is competitive)
- RL-in-ICs survey: Integration journal 2025 (good for related-work, confirms every prior RL work uses simulation not real hardware)

**UNVERIFIED (do not cite):** ChipMATE, VFlow — no public record found.
**CORRECTED 2026-08-11:** ChipSeek-R1 was on this list in error. It is REAL
(arXiv:2507.04736) and is cited in the preprint. See MASTER_REFERENCE.md.

---

## Communication preferences

- One command block at a time, wait for pasted output before next step
- Diagnose only from actual output, never guess from errors
- Direct pushback when over-explaining or drifting into premature optimization
- Shorter is better
- Don't declare victory prematurely — the paper isn't done until fine-tuned model beats baseline

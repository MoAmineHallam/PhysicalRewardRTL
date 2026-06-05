#!/usr/bin/env python3
"""
build_dataset.py  -  Phase 3 RL training dataset builder.

Generates RTL candidates for all 7 designs using RTLCoder (temperature
sampling for diversity), scores each against real FPGA hardware waveforms
using score_candidate.py, and writes JSONL dataset.

Usage:
    python build_dataset.py [--sel SEL_ID] [--n N] [--out OUT.jsonl]

    --sel   which design to generate for (0-6, default: all)
    --n     candidates per design (default: 50)
    --out   output file (default: dataset.jsonl)
    --temp  sampling temperature (default: 0.9)
    --score_script  path to score_candidate.py
"""

import sys
import os
import argparse
import json
import subprocess
import tempfile
import re
import time

# ── paths ──────────────────────────────────────────────────────────────────────
SCORE_SCRIPT = os.path.join(os.path.dirname(__file__), "score_candidate.py")
LLM_DIR      = "/zeng_gk/Amine/mas"
sys.path.insert(0, LLM_DIR)

DESIGN_NAMES = [
    "edge_detector",  # 0
    "alu_mux",        # 1
    "comb_always",    # 2
    "bcd_counter",    # 3
    "bit_manip",      # 4
    "dff_array",      # 5
    "shift_reg",      # 6
]

# Natural-language specs tuned for RTLCoder (≤2048 tok context).
# Format matches RTLCoder's VerilogEval prompt style.
SPECS = {
    0: """\
Please write a Verilog module named `edge_detector` that detects rising edges.

Ports:
  input  clk    - clock
  input  rst_n  - active-low synchronous reset
  input  in     - single-bit signal to monitor
  output rise   - goes high for exactly one clock cycle on each 0→1 transition of `in`

Behavior:
  - Registered (clocked) design; all outputs update on posedge clk.
  - On !rst_n: rise <= 0.
  - rise is 1 when in==1 and the previous registered value of in==0, else 0.
""",

    1: """\
Please write a Verilog module named `alu_mux` implementing a registered ALU with op-select mux.

Ports:
  input  clk         - clock
  input  rst_n       - active-low synchronous reset
  input  [3:0] a     - operand A
  input  [3:0] b     - operand B
  input  [2:0] op    - operation select
  output reg [3:0] result

Operations (op):
  0 → result = a + b   (4-bit addition, truncated)
  1 → result = ~a      (bitwise NOT of a)
  2 → result = a       (pass A)
  3 → result = b       (pass B)
  4 → result = a ^ b   (XOR)
  5 → result = ~a
  6 → result = a
  7 → result = b

Behavior:
  - Registered: result updates on posedge clk.
  - On !rst_n: result <= 0.
""",

    2: """\
Please write a Verilog module named `comb_always` that implements a priority encoder.

Ports:
  input  clk         - clock
  input  rst_n       - active-low synchronous reset
  input  [7:0] in    - 8-bit input
  output [2:0] out   - index of highest set bit (priority: bit 7 > bit 0)
  output valid       - 1 if any bit of `in` is set, else 0

Behavior:
  - Registered: out and valid update on posedge clk.
  - On !rst_n: out <= 0, valid <= 0.
  - Priority: highest-index set bit wins.
    in[7]=1 → out=7; in[7]=0, in[6]=1 → out=6; ... in[0]=1 only → out=0.
  - valid=1 iff in != 0.
""",

    3: """\
Please write a Verilog module named `bcd_counter` that counts 0–99 in BCD.

Ports:
  input  clk         - clock
  input  rst_n       - active-low synchronous reset
  input  en          - count enable (count only when en=1)
  output [3:0] ones  - BCD ones digit (0–9)
  output [3:0] tens  - BCD tens digit (0–9)

Behavior:
  - Registered: ones and tens update on posedge clk.
  - On !rst_n: ones <= 0, tens <= 0.
  - When en=1: increment; ones wraps 9→0 and tens increments; at 99→00.
  - When en=0: hold current value.
""",

    4: """\
Please write a Verilog module named `bit_manip` that reverses bits and counts population.

Ports:
  input  clk           - clock
  input  rst_n         - active-low synchronous reset
  input  [7:0] in      - 8-bit input
  output [7:0] reversed  - bit-reversed version of in (in[0]→reversed[7], etc.)
  output [3:0] popcount  - number of 1-bits in `in` (0–8)

Behavior:
  - Registered: reversed and popcount update on posedge clk.
  - On !rst_n: reversed <= 0, popcount <= 0.
  - reversed[i] = in[7-i] for i in 0..7.
  - popcount = in[0]+in[1]+...+in[7].
""",

    5: """\
Please write a Verilog module named `dff_array` implementing an 8-bit enabled D flip-flop array.

Ports:
  input  clk       - clock
  input  rst_n     - active-low synchronous reset
  input  en        - write enable
  input  [7:0] d   - data input
  output [7:0] q   - registered output

Behavior:
  - Registered: q updates on posedge clk.
  - On !rst_n: q <= 0.
  - When en=1: q <= d.
  - When en=0: q holds its current value.
""",

    6: """\
Please write a Verilog module named `shift_reg` implementing an 8-bit serial-in parallel-out shift register.

Ports:
  input  clk       - clock
  input  rst_n     - active-low synchronous reset
  input  en        - shift enable
  input  sin       - serial input (shifted into MSB or LSB)
  output [7:0] q   - parallel output

Behavior:
  - Registered: q updates on posedge clk.
  - On !rst_n: q <= 0.
  - When en=1: shift left by 1, sin enters at LSB: q <= {q[6:0], sin}.
  - When en=0: q holds.
""",
}


def extract_verilog(text: str, module_name: str) -> str | None:
    """Extract first complete Verilog module from LLM output."""
    # Try to find module...endmodule block
    pattern = rf'(?s)(module\s+{re.escape(module_name)}\b.*?endmodule)'
    m = re.search(pattern, text)
    if m:
        return m.group(1)
    # Fallback: any module...endmodule
    m = re.search(r'(?s)(module\s+\w+\b.*?endmodule)', text)
    if m:
        return m.group(1)
    return None


def score_verilog(verilog_src: str, sel_id: int, score_script: str) -> float | None:
    """Write verilog to temp file, run score_candidate.py, return float or None."""
    with tempfile.NamedTemporaryFile(suffix='.v', mode='w', delete=False) as f:
        f.write(verilog_src)
        tmp_path = f.name
    try:
        cp = subprocess.run(
            [sys.executable, score_script, tmp_path, str(sel_id)],
            capture_output=True, text=True, timeout=180
        )
        if cp.returncode == 0:
            return float(cp.stdout.strip())
        return None
    except Exception:
        return None
    finally:
        os.unlink(tmp_path)


def generate_candidates(sel_id: int, n: int, temperature: float):
    """Yield (rtl_src, raw_output) for n candidates using RTLCoder."""
    try:
        from llm import coder_call
    except ImportError as e:
        print(f"[ERROR] Cannot import llm.coder_call: {e}", file=sys.stderr)
        return

    spec = SPECS[sel_id]
    design_name = DESIGN_NAMES[sel_id]

    for i in range(n):
        try:
            raw = coder_call(spec, temperature=temperature)
        except TypeError:
            # coder_call may not accept temperature kwarg — try without
            try:
                raw = coder_call(spec)
            except Exception as e2:
                print(f"  [gen {i}] call failed: {e2}", file=sys.stderr)
                continue
        except Exception as e:
            print(f"  [gen {i}] call failed: {e}", file=sys.stderr)
            continue

        verilog = extract_verilog(raw, design_name)
        if verilog is None:
            print(f"  [gen {i}] no module extracted", file=sys.stderr)
            continue

        # ensure ASCII clean
        try:
            verilog.encode('ascii')
        except UnicodeEncodeError:
            verilog = verilog.encode('ascii', errors='replace').decode('ascii')

        yield verilog, raw


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--sel', type=int, default=-1,
                        help='Design sel_id (0-6), -1 = all')
    parser.add_argument('--n', type=int, default=50,
                        help='Candidates per design')
    parser.add_argument('--out', default='dataset.jsonl',
                        help='Output JSONL path')
    parser.add_argument('--temp', type=float, default=0.9,
                        help='Sampling temperature')
    parser.add_argument('--score_script', default=SCORE_SCRIPT,
                        help='Path to score_candidate.py')
    args = parser.parse_args()

    sel_ids = list(range(7)) if args.sel == -1 else [args.sel]

    out_path = args.out
    # append mode so we can resume
    with open(out_path, 'a') as fout:
        for sel_id in sel_ids:
            design_name = DESIGN_NAMES[sel_id]
            print(f"\n=== {design_name} (sel={sel_id}) — generating {args.n} candidates ===")
            scored = 0
            for idx, (verilog, _raw) in enumerate(
                    generate_candidates(sel_id, args.n, args.temp)):
                reward = score_verilog(verilog, sel_id, args.score_script)
                if reward is None:
                    print(f"  [{idx:3d}] score FAIL")
                    # still record with reward=-1 so we know it compiled/sim failed
                    reward = -1.0

                record = {
                    "sel_id":      sel_id,
                    "design_name": design_name,
                    "reward":      reward,
                    "rtl":         verilog,
                }
                fout.write(json.dumps(record) + '\n')
                fout.flush()
                scored += 1
                print(f"  [{idx:3d}] reward={reward:.4f}")

            print(f"  → {scored} records written for {design_name}")

    print(f"\nDone. Dataset: {out_path}")


if __name__ == "__main__":
    main()

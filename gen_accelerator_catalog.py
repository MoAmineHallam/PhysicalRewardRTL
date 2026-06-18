#!/usr/bin/env python3
"""
gen_accelerator_catalog.py  -  Phase-1 accelerator-block catalog.

Phase 0 validated that we can measure real silicon Fmax on the PYNQ-Z2 for
designs in the ~80-200 MHz window (fir16_8b = 90.9 MHz, harness good >200 MHz).
This generates a catalog of accelerator designs that (a) land in that window and
(b) admit functionally-equivalent implementations with DIFFERENT Fmax -- the
headroom the silicon-Fmax RL will later optimise.

Two families, both with EXACT integer goldens and a single counter-driven input
x = cnt[7:0] (so the golden is a deterministic function of the cycle index, and
the dut_top wires .x(cnt[7:0])):

  FIR<T>_8b   : T-tap direct-form FIR, 8-bit samples, fixed symmetric coeffs.
                Reference = unpipelined MAC cone (slow); the LLM can pipeline it.
  POLY<D>_8b  : degree-D Horner polynomial  (((c0*x+c1)*x+c2)...)  mod 2^16.
                Reference = full combinational mult-add chain (slow).

Per design it writes (matching the existing rtl_library/<name>/ layout):
  rtl_library/<name>/design.v   reference (unpipelined) implementation
  rtl_library/<name>/golden.py  Python reference (same coeffs) -> 16-bit stream
  rtl_library/<name>/spec.txt   natural-language prompt for the LLM

For the Phase-1 Fmax-SPREAD gate it also writes functionally-equivalent stylistic
variants (unpipelined v0 + pipelined v1) so run_ppa can show the Fmax range:
  rtl/accel_variants/<name>__v{0,1}.sv   (module renamed to match the filename)
  rtl/accel_variants/accel_manifest.json  module -> {design, family, style}

Usage (anywhere with the repo):
    python gen_accelerator_catalog.py
Then the Phase-1 gate (laptop, Vivado):
    python run_ppa.py --dir rtl/accel_variants --out rtl/accel_variants/ppa.jsonl \
        --clk clk --period 5.0
    # expect: every design's v0/v1 in [80,250] MHz with a clear v0->v1 spread
"""

import os
import json

HERE = os.path.dirname(os.path.abspath(__file__))
RTL_LIB = os.path.join(HERE, "rtl_library")
VAR_DIR = os.path.join(HERE, "rtl", "accel_variants")

# 8-bit symmetric triangular FIR coefficients (all < 64 so products fit 16 bits).
def fir_coeffs(taps):
    if taps == 16:   # keep the silicon-validated fir16_8b coefficients exactly
        return [3, 7, 12, 19, 27, 34, 40, 43, 43, 40, 34, 27, 19, 12, 7, 3]
    return [(min(i, taps - 1 - i) + 1) * 2 + 1 for i in range(taps)]


def poly_coeffs(deg):
    # small odd constants c0..c_deg
    return [2 * k + 1 for k in range(deg + 1)]


# ---------------------------------------------------------------- goldens
def fir_golden(coeffs):
    return f'''"""Golden for a {len(coeffs)}-tap direct-form FIR (family=fir), 8-bit samples
x[c]=c&0xFF, fixed coefficients {coeffs}. Output {{y[15:0]}} mask=0xFFFF.
Hardware output is this stream delayed by pipeline latency; the sweep/score
two-sided registration shift absorbs that, so this is the un-delayed ideal."""
import numpy as np

H = {coeffs}


def compute_golden(n_cycles: int = 32768) -> np.ndarray:
    out = []
    xline = [0] * {len(coeffs)}
    for c in range(n_cycles):
        x = c & 0xFF
        xline = [x] + xline[:{len(coeffs) - 1}]
        out.append(sum(H[k] * xline[k] for k in range({len(coeffs)})) & 0xFFFF)
    return np.array(out, dtype=np.uint16)


if __name__ == "__main__":
    g = compute_golden()
    for i in range(min(20, len(g))):
        print(f"{{i:4d}}  {{g[i]:#06x}}  {{g[i]}}")
    np.save("golden_waveform.npy", g)
'''


def poly_golden(coeffs):
    return f'''"""Golden for a degree-{len(coeffs) - 1} Horner polynomial (family=poly), mod 2^16.
x[c]=c&0xFF, coefficients {coeffs}: y = (((c0*x+c1)*x+c2)...+cD) & 0xFFFF.
Output {{y[15:0]}} mask=0xFFFF. Pipeline latency absorbed by the score shift."""
import numpy as np

C = {coeffs}


def compute_golden(n_cycles: int = 32768) -> np.ndarray:
    out = []
    for c in range(n_cycles):
        x = c & 0xFF
        acc = C[0]
        for k in range(1, len(C)):
            acc = (acc * x + C[k]) & 0xFFFF
        out.append(acc & 0xFFFF)
    return np.array(out, dtype=np.uint16)


if __name__ == "__main__":
    g = compute_golden()
    for i in range(min(20, len(g))):
        print(f"{{i:4d}}  {{g[i]:#06x}}  {{g[i]}}")
    np.save("golden_waveform.npy", g)
'''


# ---------------------------------------------------------------- FIR verilog
def fir_ref(mod, coeffs):
    T = len(coeffs)
    prods = " + ".join(f"8'd{coeffs[k]} * xs[{k}]" for k in range(T))
    return f'''// {T}-tap direct-form FIR, 8-bit samples, unpipelined MAC cone (the long
// register-to-register path -> lower Fmax; pipeline it to go faster).
module {mod} (
    input  wire        clk,
    input  wire        rst_n,
    input  wire [7:0]  x,
    output reg  [15:0] y
);
    reg  [7:0]  xs [0:{T - 1}];
    integer     i;
    reg  [23:0] acc;
    always @(*) acc = {prods};
    always @(posedge clk) begin
        if (!rst_n) begin
            for (i = 0; i < {T}; i = i + 1) xs[i] <= 8'd0;
            y <= 16'd0;
        end else begin
            xs[0] <= x;
            for (i = 1; i < {T}; i = i + 1) xs[i] <= xs[i-1];
            y <= acc[15:0];
        end
    end
endmodule
'''


def fir_pipe(mod, coeffs):
    T = len(coeffs)
    prod_assigns = "\n            ".join(
        f"p[{k}] <= 8'd{coeffs[k]} * xs[{k}];" for k in range(T))
    psum = " + ".join(f"p[{k}]" for k in range(T))
    return f'''// {T}-tap direct-form FIR, 8-bit samples, PIPELINED: products registered in
// stage 1, summed in stage 2 -> shorter register-to-register path, higher Fmax.
// Functionally identical to the reference up to a fixed extra latency.
module {mod} (
    input  wire        clk,
    input  wire        rst_n,
    input  wire [7:0]  x,
    output reg  [15:0] y
);
    reg  [7:0]  xs [0:{T - 1}];
    reg  [15:0] p  [0:{T - 1}];
    integer     i;
    always @(posedge clk) begin
        if (!rst_n) begin
            for (i = 0; i < {T}; i = i + 1) begin xs[i] <= 8'd0; p[i] <= 16'd0; end
            y <= 16'd0;
        end else begin
            xs[0] <= x;
            for (i = 1; i < {T}; i = i + 1) xs[i] <= xs[i-1];
            {prod_assigns}
            y <= {psum};
        end
    end
endmodule
'''


# ---------------------------------------------------------------- POLY verilog
def poly_ref(mod, coeffs):
    D = len(coeffs) - 1
    lines = [f"    wire [15:0] t0 = 16'd{coeffs[0]};"]
    for k in range(1, D + 1):
        lines.append(f"    wire [15:0] t{k} = t{k-1} * x + 16'd{coeffs[k]};")
    chain = "\n".join(lines)
    return f'''// Degree-{D} Horner polynomial, mod 2^16, FULL combinational mult-add chain
// (the long path -> lower Fmax; pipeline the stages to go faster).
module {mod} (
    input  wire        clk,
    input  wire        rst_n,
    input  wire [7:0]  x,
    output reg  [15:0] y
);
{chain}
    always @(posedge clk) begin
        if (!rst_n) y <= 16'd0;
        else        y <= t{D};
    end
endmodule
'''


def poly_pipe(mod, coeffs):
    D = len(coeffs) - 1
    # one pipeline register per Horner stage: r[k] = r[k-1]*x_d[k-1] + c[k]
    # x must be delayed alongside so each stage multiplies by the same-era x.
    decls = "\n    ".join([f"reg [15:0] r{k};" for k in range(D + 1)] +
                          [f"reg [7:0] xd{k};" for k in range(1, D + 1)])
    rst = " ".join([f"r{k} <= 16'd0;" for k in range(D + 1)] +
                   [f"xd{k} <= 8'd0;" for k in range(1, D + 1)])
    body = [f"r0 <= 16'd{coeffs[0]};", "xd1 <= x;"]
    for k in range(1, D + 1):
        xin = f"xd{k}"
        body.append(f"r{k} <= r{k-1} * {xin} + 16'd{coeffs[k]};")
        if k + 1 <= D:
            body.append(f"xd{k+1} <= {xin};")
    body_s = "\n            ".join(body)
    return f'''// Degree-{D} Horner polynomial, mod 2^16, FULLY PIPELINED (one register per
// stage, with the input delayed alongside) -> short per-stage path, higher Fmax.
// Functionally identical to the reference up to a fixed extra latency.
module {mod} (
    input  wire        clk,
    input  wire        rst_n,
    input  wire [7:0]  x,
    output reg  [15:0] y
);
    {decls}
    always @(posedge clk) begin
        if (!rst_n) begin {rst} y <= 16'd0; end
        else begin
            {body_s}
            y <= r{D};
        end
    end
endmodule
'''


def fir_spec(name, T):
    return (f"Write a Verilog module named `{name}`, a {T}-tap direct-form FIR "
            f"filter with inputs `clk`, active-low `rst_n`, an 8-bit unsigned "
            f"sample input `x`, and a 16-bit registered output `y`. Keep a "
            f"{T}-element delay line of past samples and each cycle output the "
            f"low 16 bits of the sum of products of the taps with the fixed "
            f"coefficients {fir_coeffs(T)}. Clear state to 0 on `!rst_n`.\n")


def poly_spec(name, D, coeffs):
    return (f"Write a Verilog module named `{name}` with inputs `clk`, active-low "
            f"`rst_n`, an 8-bit input `x`, and a 16-bit registered output `y`. "
            f"Evaluate the degree-{D} polynomial with coefficients {coeffs} "
            f"(c0 first) at `x` using Horner's method, keeping only the low 16 "
            f"bits (mod 2^16), and register the result into `y`. Clear `y` to 0 "
            f"on `!rst_n`.\n")


def main():
    os.makedirs(VAR_DIR, exist_ok=True)
    designs = []
    for T in (8, 16, 32):
        c = fir_coeffs(T)
        designs.append((f"fir{T}_8b", "fir", fir_golden(c),
                        fir_ref(f"fir{T}_8b", c), fir_spec(f"fir{T}_8b", T),
                        fir_ref, fir_pipe, c))
    for D in (4, 6):
        c = poly_coeffs(D)
        designs.append((f"poly{D}_8b", "poly", poly_golden(c),
                        poly_ref(f"poly{D}_8b", c), poly_spec(f"poly{D}_8b", D, c),
                        poly_ref, poly_pipe, c))

    mani = {}
    for name, fam, golden, ref_v, spec, ref_fn, pipe_fn, coeffs in designs:
        d = os.path.join(RTL_LIB, name)
        os.makedirs(d, exist_ok=True)
        open(os.path.join(d, "design.v"), "w").write(ref_v)
        open(os.path.join(d, "golden.py"), "w").write(golden)
        open(os.path.join(d, "spec.txt"), "w").write(spec)
        # variants for the Fmax-spread gate (module renamed to file stem)
        for k, fn in ((0, ref_fn), (1, pipe_fn)):
            mod = f"{name}__v{k}"
            open(os.path.join(VAR_DIR, mod + ".sv"), "w").write(fn(mod, coeffs))
            mani[mod] = {"design": name, "family": fam,
                         "style": "unpipelined" if k == 0 else "pipelined"}
        print(f"  {name:10s} ({fam})  + v0/v1 variants")

    json.dump(mani, open(os.path.join(VAR_DIR, "accel_manifest.json"), "w"),
              indent=1)
    print(f"\n{len(designs)} designs -> rtl_library/<name>/, "
          f"{len(mani)} variants -> rtl/accel_variants/")
    print("Phase-1 gate (laptop, Vivado):")
    print("  python run_ppa.py --dir rtl/accel_variants "
          "--out rtl/accel_variants/ppa.jsonl --clk clk --period 5.0")
    print("  -> expect every v0/v1 in [80,250] MHz with a clear v0->v1 Fmax spread")


if __name__ == "__main__":
    main()

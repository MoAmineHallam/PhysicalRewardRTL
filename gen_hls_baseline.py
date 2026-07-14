#!/usr/bin/env python3
"""
gen_hls_baseline.py  -  Phase D1: the commercial-HLS baseline (reviewer BLOCKER).

Question this answers: "why not just write 3 lines of C++ and let Vitis HLS
generate the RTL?" For every §5 held-out design this emits a C++ kernel with
the EXACT integer semantics of the oracle reference (mod 2^16, same tap/Horner
recurrences), in TWO variants:

  nopragma : plain C loop, no directives (what a naive user gets)
  pragma   : #pragma HLS pipeline II=1 + full unroll + array_partition
             (what an HLS-literate user gets; II=1 makes throughput directly
             comparable to our one-sample-per-cycle RTL)

plus a self-checking C testbench per design (stimulus = the oracle's directed+
random vectors, golden = the oracle reference), used BOTH by g++ in the sandbox
(pre-flight verification, zero Vivado time wasted on wrong kernels) and by
Vitis HLS csim. run_hls.tcl batch-runs csim + csynth + export_design -flow impl
(real Vivado place-and-route, NOT the optimistic HLS estimate) for all
designs x variants; collect_hls.py parses the reports into hls_results.json and
prints the HLS-vs-GRPO comparison table using the existing held-out ppa.jsonl.

  sandbox : python gen_hls_baseline.py          # generate + g++ verify
  laptop  : vitis_hls -f rtl/hls_baseline/run_hls.tcl   (2-4 h, resumable)
  anywhere: python collect_hls.py               # the comparison table
"""

import os
import re
import subprocess
import numpy as np

import gen_accelerator_catalog as GAC
import gen_sft_corpus as GSC
import oracle

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "rtl", "hls_baseline")
N_TB = 256          # testbench vectors (small header, plenty of coverage)
PERIOD = "5.0"      # 200 MHz target, same as run_ppa

# the 22 frozen §5 held-out designs: (name, kind, params)
def holdout_list():
    ds = []
    for T in sorted(GSC.HOLDOUT_FIR_TAPS) + sorted(GSC.HOLDOUT_EXTRAP_TAPS):
        ds.append((f"fir{T}_8b", "fir", GAC.fir_coeffs(T)))
        ds.append((f"firr{T}", "fir", [k + 1 for k in range(T)]))
    for v in range(6):
        nm = "poly7_8b" if v == 0 else f"poly7_v{v}_8b"
        ds.append((nm, "poly", GAC.poly_coeffs_var(7, v)))
    for D in (4, 8):
        for v in sorted(GSC.HOLDOUT_EXTRAP_POLY_VARS):
            ds.append((f"poly{D}_v{v}_8b", "poly", GAC.poly_coeffs_var(D, v)))
    assert all(GSC.is_holdout(n) for n, _, _ in ds) and len(ds) == 22
    return ds


def fir_cpp(name, H):
    T = len(H)
    coef = ", ".join(str(c) for c in H)
    return f"""// {name}: {T}-tap FIR, y = (sum H[k]*x[n-k]) mod 2^16 (oracle-exact).
#include <stdint.h>

void {name}(uint8_t x, uint16_t *y) {{
#pragma HLS INTERFACE ap_ctrl_none port=return
#ifndef NO_PRAGMA
#pragma HLS pipeline II=1
#endif
    static uint8_t line[{T}] = {{0}};
#ifndef NO_PRAGMA
#pragma HLS array_partition variable=line complete
#endif
    static const uint16_t H[{T}] = {{{coef}}};
    for (int k = {T - 1}; k > 0; k--) {{
#ifndef NO_PRAGMA
#pragma HLS unroll
#endif
        line[k] = line[k - 1];
    }}
    line[0] = x;
    uint32_t acc = 0;
    for (int k = 0; k < {T}; k++) {{
#ifndef NO_PRAGMA
#pragma HLS unroll
#endif
        acc += (uint32_t)H[k] * line[k];
    }}
    *y = (uint16_t)acc;
}}
"""


def poly_cpp(name, C):
    coef = ", ".join(str(c) for c in C)
    D = len(C) - 1
    return f"""// {name}: degree-{D} Horner polynomial mod 2^16 (oracle-exact).
#include <stdint.h>

void {name}(uint8_t x, uint16_t *y) {{
#pragma HLS INTERFACE ap_ctrl_none port=return
#ifndef NO_PRAGMA
#pragma HLS pipeline II=1
#endif
    static const uint16_t C[{D + 1}] = {{{coef}}};
    uint16_t acc = C[0];
    for (int k = 1; k <= {D}; k++) {{
#ifndef NO_PRAGMA
#pragma HLS unroll
#endif
        acc = (uint16_t)(acc * x + C[k]);
    }}
    *y = acc;
}}
"""


def tb_cpp(name):
    return f"""// self-checking TB for {name} (g++ pre-flight AND Vitis HLS csim).
#include <stdio.h>
#include <stdint.h>
#include "{name}_golden.h"

void {name}(uint8_t x, uint16_t *y);

int main() {{
    int bad = 0;
    for (int i = 0; i < GOLDEN_N; i++) {{
        uint16_t y;
        {name}(STIM[i], &y);
        if (y != GOLDEN[i]) {{
            if (bad < 5)
                printf("MISMATCH @%d: x=%u got=%u want=%u\\n",
                       i, (unsigned)STIM[i], (unsigned)y, (unsigned)GOLDEN[i]);
            bad++;
        }}
    }}
    printf("%s: %s (%d/%d)\\n", "{name}", bad ? "FAIL" : "PASS",
           GOLDEN_N - bad, GOLDEN_N);
    return bad ? 1 : 0;
}}
"""


def golden_h(name, kind, coeffs, stim):
    ref = oracle.fir_ref(stim, coeffs) if kind == "fir" else \
          oracle.poly_ref(stim, coeffs)
    fmt = lambda a: ",".join(str(int(v)) for v in a)
    return (f"// auto-generated golden for {name} (oracle reference, seed 5)\n"
            f"#define GOLDEN_N {len(stim)}\n"
            f"static const unsigned char STIM[GOLDEN_N] = {{{fmt(stim)}}};\n"
            f"static const unsigned short GOLDEN[GOLDEN_N] = {{{fmt(ref)}}};\n")


def main():
    os.makedirs(OUT, exist_ok=True)
    designs = holdout_list()
    stim = oracle.gen_stimulus(N_TB, 8, seed=5)

    names = []
    for name, kind, coeffs in designs:
        cpp = fir_cpp(name, coeffs) if kind == "fir" else poly_cpp(name, coeffs)
        open(os.path.join(OUT, f"{name}.cpp"), "w").write(cpp)
        open(os.path.join(OUT, f"{name}_tb.cpp"), "w").write(tb_cpp(name))
        open(os.path.join(OUT, f"{name}_golden.h"), "w").write(
            golden_h(name, kind, coeffs, stim))
        names.append(name)

    # ---- Vitis HLS batch tcl: (design x variant) -> csim + csynth + impl ----
    body = "\n".join(f'lappend DESIGNS "{n}"' for n in names)
    tcl = f"""# Auto-generated - Phase D1 HLS baseline batch (Vitis HLS).
# Run from a SHORT path (Windows 260-char/8191-char-cmdline limit trips
# export_design on the larger designs). Recommended on the laptop:
#   subst X: C:\\Users\\Amine\\mas\\fpga-repo\\rtl\\hls_baseline
#   cd /d X:\\
#   vitis_hls -f run_hls.tcl
# Resumable: solutions that already have an export report are skipped, and a
# failed export is caught so ONE failure never aborts the whole batch.
set PART   "xc7z020clg400-1"
set PERIOD {PERIOD}
set DESIGNS [list]
{body}

set FAILED [list]
foreach d $DESIGNS {{
    foreach variant {{pragma nopragma}} {{
        set proj "proj_${{d}}_${{variant}}"
        set rpt  "$proj/sol1/impl/report/verilog/${{d}}_export.rpt"
        if {{[file exists $rpt]}} {{
            puts "SKIP $d/$variant (already done)"
            continue
        }}
        puts ">>> $d / $variant"
        open_project -reset $proj
        set_top $d
        if {{$variant eq "nopragma"}} {{
            add_files "$d.cpp" -cflags "-DNO_PRAGMA"
        }} else {{
            add_files "$d.cpp"
        }}
        add_files -tb "$d\\_tb.cpp"
        open_solution -reset "sol1"
        set_part $PART
        create_clock -period $PERIOD
        csim_design
        csynth_design
        # catch so a single Windows cmdline-length export failure logs and the
        # batch keeps going instead of aborting mid-sweep
        if {{[catch {{export_design -flow impl -rtl verilog}} emsg]}} {{
            puts "EXPORT-FAIL $d/$variant : $emsg"
            lappend FAILED "$d/$variant"
        }}
        close_project
    }}
}}
puts "HLS BASELINE BATCH DONE"
if {{[llength $FAILED]}} {{
    puts "EXPORTS THAT FAILED (rerun after `subst` to a short path): $FAILED"
}}
exit
"""
    open(os.path.join(OUT, "run_hls.tcl"), "w").write(tcl)
    open(os.path.join(OUT, ".gitignore"), "w").write("proj_*/\n*.log\n")

    # ---- g++ pre-flight: every kernel (BOTH variants) vs oracle golden ----
    print(f"generated {len(names)} designs x2 variants -> {OUT}")
    print("\ng++ pre-flight (kernel vs oracle golden):")
    bad = 0
    for name in names:
        for flag, tag in (([], "pragma "), (["-DNO_PRAGMA"], "nopragma")):
            exe = f"/tmp/hlstest_{name}"
            r = subprocess.run(
                ["g++", "-O2", "-o", exe, *flag,
                 os.path.join(OUT, f"{name}.cpp"),
                 os.path.join(OUT, f"{name}_tb.cpp"), "-I", OUT],
                capture_output=True, text=True)
            if r.returncode != 0:
                print(f"  {name:14s} [{tag}] COMPILE FAIL\n{r.stderr[:300]}")
                bad += 1
                continue
            t = subprocess.run([exe], capture_output=True, text=True)
            ok = t.returncode == 0
            bad += (not ok)
            if not ok or tag.strip() == "pragma":
                print(f"  {t.stdout.strip()}  [{tag.strip()}]"
                      + ("" if ok else "  ** FAIL **"))
            os.path.exists(exe) and os.remove(exe)
    if bad:
        raise SystemExit(f"\n{bad} kernel checks FAILED -- fix before Vitis HLS")
    print("\nall kernels oracle-exact (both variants). next (laptop):\n"
          "  cd rtl\\hls_baseline && vitis_hls -f run_hls.tcl\n"
          "  (then) python ..\\..\\collect_hls.py")


if __name__ == "__main__":
    main()

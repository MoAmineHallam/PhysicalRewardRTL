#!/usr/bin/env python3
"""
oracle.py  -  V2 reward oracle (Stage 0 of the proper method, see MASTER_REFERENCE §10).

Fixes the three reward flaws of V1 (score_candidate.py):
  1. V1 drove a free-running COUNTER -> coverage = "whatever the counter hits".
     Here: a deterministic mix of DIRECTED + RANDOM input vectors (seeded, so the
     exact same stimulus can be replayed on the board for a real silicon reward).
  2. V1 compared bit-Hamming to ONE captured trajectory (a copy-this-design task,
     partial credit to wrong designs). Here: I/O-EQUIVALENCE to a reference model
     under that stimulus -> a clean correct/incorrect signal that accepts ANY
     implementation (pipelined / retimed / restructured) up to a latency offset.
  3. V1 reference assumed counter inputs. Here the reference is f(input_stream) ->
     output_stream, so the stimulus and the reference are decoupled.

Scope (v1 of the oracle): the single-input streaming accelerator families
(fir/firr/poly/cordic), interface (clk, rst_n, x[7:0], y[15:0]). Reference params
are derived from the design name via gen_accelerator_catalog helpers (DRY).

This is simulation-backed for now (iverilog), but the design is board-ready: the
stimulus is a plain seeded vector sequence; a board "vector player" (Stage 2)
streams the same vectors to the DUT and the SAME align/score logic compares the
captured outputs. The functional reward then becomes genuinely board-measured.

CLI:  python oracle.py --design firr16 --file rtl_library/firr16/design.v
"""

import os
import re
import json
import argparse
import tempfile
import subprocess

import numpy as np

import gen_accelerator_catalog as GAC

HERE = os.path.dirname(os.path.abspath(__file__))
RTL_LIB = os.path.join(HERE, "rtl_library")
OUT_MASK = 0xFFFF


# ---------------------------------------------------------------- stimulus
def gen_stimulus(n, width=8, seed=0):
    """Deterministic DIRECTED + RANDOM input vectors (board-replayable).

    Directed prefix exercises corners (0, max, 1, max-1, alternating bit
    patterns, walking ones/zeros, small ramp); the rest is uniform random.
    """
    hi = (1 << width) - 1
    directed = [0, hi, 1, hi - 1, 0x55 & hi, 0xAA & hi, hi >> 1, (hi >> 1) + 1, 0, hi]
    directed += [1 << b for b in range(width)]                 # walking ones
    directed += [hi ^ (1 << b) for b in range(width)]          # walking zeros
    directed += list(range(0, min(hi + 1, 16)))                # small ramp
    rng = np.random.default_rng(seed)
    if n > len(directed):
        rand = rng.integers(0, hi + 1, size=n - len(directed), dtype=np.int64)
        seq = np.array(directed[:n] + rand.tolist(), dtype=np.int64)
    else:
        seq = np.array(directed[:n], dtype=np.int64)
    return seq.astype(np.uint16)


# ---------------------------------------------------------------- references
# Each maps an arbitrary input stream -> output stream (16-bit), matching the
# exact integer semantics of the corresponding design family.
def fir_ref(xs, H):
    T = len(H)
    out, line = [], [0] * T
    for x in xs:
        line = [int(x)] + line[:T - 1]
        out.append(sum(H[k] * line[k] for k in range(T)) & OUT_MASK)
    return np.array(out, dtype=np.uint16)


def poly_ref(xs, C):
    out = []
    for x in xs:
        acc = C[0]
        for k in range(1, len(C)):
            acc = (acc * int(x) + C[k]) & OUT_MASK
        out.append(acc & OUT_MASK)
    return np.array(out, dtype=np.uint16)


def iir_ref(xs, B):
    """Order-N IIR: y[n] = (sum B_k x[n-k] + ((9*y1)>>4) + ((5*y2)>>4)) mod 2^16."""
    order = len(B) - 1
    xd = [0] * order
    y1 = y2 = 0
    out = []
    for x in xs:
        acc = B[0] * int(x) + sum(B[k] * xd[k - 1] for k in range(1, order + 1))
        acc += (GAC.IIR_A1 * y1) >> 4
        acc += (GAC.IIR_A2 * y2) >> 4
        ynew = acc & OUT_MASK
        y2, y1 = y1, ynew
        xd = [int(x)] + xd[:-1]
        out.append(ynew)
    return np.array(out, dtype=np.uint16)


def med_ref(xs, W):
    """Streaming median-of-W: window = current sample + previous W-1 (init 0)."""
    win = [0] * W
    out = []
    for x in xs:
        win = [int(x)] + win[:-1]
        out.append(sorted(win)[W // 2])
    return np.array(out, dtype=np.uint16)


def cordic_ref(xs, atan, x0, n):
    out = []
    for xin in xs:
        x, y, z = x0, 0, int(xin)
        for i in range(n):
            dx, dy = x >> i, y >> i
            if z >= 0:
                x, y, z = x - dy, y + dx, z - atan[i]
            else:
                x, y, z = x + dy, y - dx, z + atan[i]
        out.append(x & OUT_MASK)
    return np.array(out, dtype=np.uint16)


def build_reference(design):
    """design name -> (reference callable, input width). Params via GAC (DRY)."""
    # coefficient-variant forms (sealed split, prereg rev 2) are matched FIRST;
    # the v0 patterns below are anchored so they cannot swallow a _v{n} name.
    m = re.match(r"fir(\d+)_v(\d+)_8b$", design)
    if m:
        H = GAC.fir_coeffs_var(int(m.group(1)), int(m.group(2)))
        return (lambda xs: fir_ref(xs, H)), 8
    m = re.match(r"firr(\d+)_v(\d+)$", design)
    if m:
        H = GAC.firr_coeffs_var(int(m.group(1)), int(m.group(2)))
        return (lambda xs: fir_ref(xs, H)), 8
    m = re.match(r"fir(\d+)_8b$", design)
    if m:
        H = GAC.fir_coeffs(int(m.group(1)))
        return (lambda xs: fir_ref(xs, H)), 8
    m = re.match(r"firr(\d+)$", design)
    if m:
        H = [k + 1 for k in range(int(m.group(1)))]
        return (lambda xs: fir_ref(xs, H)), 8
    m = re.match(r"poly(\d+)_v(\d+)_8b$", design)
    if m:
        C = GAC.poly_coeffs_var(int(m.group(1)), int(m.group(2)))
        return (lambda xs: poly_ref(xs, C)), 8
    m = re.match(r"poly(\d+)_8b$", design)
    if m:
        C = GAC.poly_coeffs(int(m.group(1)))
        return (lambda xs: poly_ref(xs, C)), 8
    m = re.match(r"cordic(\d+)$", design)
    if m:
        N = int(m.group(1)); atan, x0 = GAC.cordic_tables(N)
        return (lambda xs: cordic_ref(xs, atan, x0, N)), 8
    m = re.match(r"iir(\d+)(?:_v(\d+))?$", design)
    if m:
        B = GAC.iir_coeffs_var(int(m.group(1)), int(m.group(2) or 0))
        return (lambda xs: iir_ref(xs, B)), 8
    m = re.match(r"med(\d+)$", design)
    if m:
        W = int(m.group(1))
        return (lambda xs: med_ref(xs, W)), 8
    raise ValueError(f"no reference for design '{design}' (oracle = fir/firr/"
                     f"poly/cordic/iir/med single-input families)")


# ---------------------------------------------------------------- DUT sim
def _tb(module, n, in_w):
    return f"""`timescale 1ns/1ps
module tb;
  reg clk=0, rst_n=0; reg [{in_w-1}:0] x; wire [15:0] y;
  reg [{in_w-1}:0] stim [0:{n-1}]; integer i;
  {module} dut (.clk(clk), .rst_n(rst_n), .x(x), .y(y));
  always #5 clk = ~clk;
  initial begin
    $readmemh("stim.hex", stim);
    rst_n = 0; x = 0; @(posedge clk); @(posedge clk); rst_n = 1;
    for (i = 0; i < {n}; i = i + 1) begin
      x = stim[i]; @(posedge clk); #1; $display("%0d", y);
    end
    $finish;
  end
endmodule
"""


try:
    import resource

    def _cap_mem():
        """preexec_fn: cap a sim child's address space (RLIMIT_AS) so a
        pathological candidate (e.g. a huge memory decl that makes iverilog/vvp
        balloon to tens of GB) dies as an INDIVIDUAL failed sim -> scored
        incorrect, instead of tripping the cgroup OOM killer and taking down the
        whole run (observed: vvp at 65 GB OOM-killed grpo_v8 at step 107)."""
        lim = 4 * 1024 ** 3          # 4 GB; normal sims here use < 200 MB
        resource.setrlimit(resource.RLIMIT_AS, (lim, lim))
except ImportError:                  # non-POSIX (Windows laptop never sims)
    _cap_mem = None


def run_dut(rtl_text, design, stim, in_w):
    """Compile candidate + vector-player TB, drive `stim`, return y stream.
    Returns None on compile/sim failure or wrong/missing module name."""
    if not re.search(r"\bmodule\s+" + re.escape(design) + r"\b", rtl_text):
        return None
    with tempfile.TemporaryDirectory() as wd:
        cand = os.path.join(wd, "cand.v")
        tb = os.path.join(wd, "tb.v")
        hexf = os.path.join(wd, "stim.hex")
        vvp = os.path.join(wd, "a.vvp")
        open(cand, "w").write(rtl_text)
        open(tb, "w").write(_tb(design, len(stim), in_w))
        open(hexf, "w").write("\n".join(f"{int(v):x}" for v in stim) + "\n")
        try:
            c = subprocess.run(["iverilog", "-g2012", "-o", vvp, cand, tb],
                               capture_output=True, text=True, timeout=60,
                               preexec_fn=_cap_mem)
            if c.returncode != 0:
                return None
            r = subprocess.run(["vvp", vvp], capture_output=True, text=True,
                               cwd=wd, timeout=60, preexec_fn=_cap_mem)
        except FileNotFoundError as e:
            # The SIMULATOR ITSELF is missing -- an environment fault, NOT a
            # wrong candidate. Never silently score this "incorrect": that
            # produced a full eval of 0.0% on every policy (2026-07-27, after a
            # container reset wiped iverilog from the ephemeral filesystem).
            raise RuntimeError(
                f"iverilog/vvp not found ({e}) -- the oracle cannot score "
                "anything. Install iverilog (conda install -c conda-forge "
                "iverilog) before running any eval/training.") from e
        except (subprocess.TimeoutExpired, OSError, MemoryError):
            # pathological candidate (runaway elaboration/sim or memory bomb):
            # score it INCORRECT, never let it OOM/hang the whole GRPO run.
            return None
        vals = _parse_trace(r.stdout)
    return vals if vals is not None and len(vals) >= 32 else None


# a value print from _tb's $display("%0d", y) is always a line holding exactly
# one token; anything else on stdout is simulator chatter (iverilog puts
# "<file>:<line>: $finish called at <t> (<unit>)" there, not on stderr).
_CHATTER = re.compile(r"\s")

X_SENTINEL = -1          # never equal to any 16-bit reference value


def _parse_trace(stdout):
    """Turn a vvp stdout into the DUT's output stream, or None if unparseable.

    iverilog renders an output with any unknown or high-impedance bit as
    'x'/'z' (all bits unknown) or 'X'/'Z' (some bits unknown) under %0d. The
    previous filter kept only decimal tokens, which DROPPED those samples: the
    trace silently got shorter, every later sample shifted one place earlier,
    and a candidate whose output is undefined on some cycles was compared as if
    those cycles had never been driven. Two candidates could differ in exactly
    the cycles that vanished and still compare equal.

    Undefined output is wrong output, so an x/z sample is kept IN PLACE as a
    sentinel that cannot equal any reference value. Keeping it positional
    rather than rejecting the candidate outright matters: an unreset pipeline
    is legitimately undefined while it fills, and align_score's warmup/latency
    window already excuses exactly that prefix. A candidate undefined after the
    window now fails, which is the intended behaviour; one undefined only
    during fill still passes, as it did before.
    """
    vals = []
    for line in stdout.splitlines():
        t = line.strip()
        if not t or _CHATTER.search(t):
            continue
        if t.isdigit():
            v = int(t)
            if v >= 65536:               # not a 16-bit y print
                return None
            vals.append(v)
        elif t in ("x", "X", "z", "Z"):
            vals.append(X_SENTINEL)
        else:
            return None                  # unexpected single-token output
    return np.array(vals, dtype=np.int32) if vals else None


# ---------------------------------------------------------------- score
def align_score(y_dut, y_ref, max_lat=40, warmup=8):
    """Best I/O-equivalence over a latency offset (DUT may be pipelined).
    Returns (best_match_fraction, best_latency)."""
    if y_dut is None:
        return 0.0, -1
    best, best_L = 0.0, -1
    for L in range(max_lat + 1):
        a = y_dut[L + warmup:]
        b = y_ref[warmup:warmup + len(a)]
        k = min(len(a), len(b))
        if k < 32:
            continue
        frac = float(np.mean(a[:k] == b[:k]))
        if frac > best:
            best, best_L = frac, L
    return best, best_L


def score(rtl_text, design, n=512, seed=0, pass_thresh=0.999):
    ref_fn, in_w = build_reference(design)
    stim = gen_stimulus(n, in_w, seed)
    y_ref = ref_fn(stim)
    y_dut = run_dut(rtl_text, design, stim, in_w)
    frac, lat = align_score(y_dut, y_ref)
    return {"design": design, "compiled": y_dut is not None,
            "match": round(frac, 4), "latency": lat,
            "correct": bool(frac >= pass_thresh), "n": n, "seed": seed}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--design", required=True)
    ap.add_argument("--file", required=True)
    ap.add_argument("--n", type=int, default=512)
    ap.add_argument("--seed", type=int, default=0)
    args = ap.parse_args()
    print(json.dumps(score(open(args.file).read(), args.design, args.n, args.seed)))


if __name__ == "__main__":
    main()

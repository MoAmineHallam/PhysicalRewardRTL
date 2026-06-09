#!/usr/bin/env python3
"""
gen_designs.py  -  Programmatic generator for 1000+ counter-driven RTL designs.

Each generated design satisfies the board harness contract:
  - all inputs are slices of a free-running 32-bit counter `cnt`
  - all outputs are packed into a single 16-bit `probe`
  - a known period (for FFT phase alignment / N_COMPARE)

For every design it writes:
  rtl_library/<name>/design.v    golden synthesizable RTL
  rtl_library/<name>/golden.py   self-contained reference (compute_golden + main)
  rtl_library/<name>/spec.txt    natural-language spec (LLM prompt)

and appends one record to rtl_library/manifest.json, the single source of truth
consumed by verify_designs.py, gen_bitstream.py, and score_candidate.py.

Designs are correct-by-construction: the Verilog and the Python golden are
emitted from the same parameters. verify_designs.py then proves sim-equivalence
before anything reaches Vivado.

Usage:
    python gen_designs.py            # generate the full catalog
    python gen_designs.py --limit 50 # generate only the first 50 (smoke test)
"""

import os
import json
import argparse
import math

RTL_LIB = os.path.join(os.path.dirname(os.path.abspath(__file__)), "rtl_library")

# Accumulates manifest records as designs are emitted.
MANIFEST = []
_SEEN = set()   # guard against duplicate names from overlapping parameter sweeps


def clog2(n):
    return max(1, math.ceil(math.log2(n))) if n > 1 else 1


def pack(sig, width):
    """Pack a `width`-bit signal into the 16-bit probe, zero-padding the top.
    Avoids an illegal zero-width '{0'b0, ...}' when width == 16."""
    pad = 16 - width
    return sig if pad <= 0 else "{%d'b0, %s}" % (pad, sig)


def emit(name, family, verilog, golden_body, inputs, outwires, ports,
         probe, probe_mask, period, spec, golden_doc=""):
    """Write one design's three files and record its manifest entry.

    golden_body: Python source computing `val` (the 16-bit probe value) from
                 integer counter value `c`. Used verbatim in golden.py and
                 exec'd by verify_designs.py -- the single source of truth for
                 the reference behavior.
    """
    if name in _SEEN:
        return   # skip duplicate (parameter values collided)
    _SEEN.add(name)

    d = os.path.join(RTL_LIB, name)
    os.makedirs(d, exist_ok=True)

    with open(os.path.join(d, "design.v"), "w") as f:
        f.write(verilog)

    golden_py = f'''"""
Golden reference for {name} (family={family}).
{golden_doc}
Probe packing: {probe}   mask={probe_mask:#06x}   period={period}
Counter-driven: inputs are slices of free-running cnt.
"""
import numpy as np


def compute_golden(n_cycles: int = 32768) -> np.ndarray:
    out = []
    for c in range(n_cycles):
{golden_body}
        out.append(val & 0xFFFF)
    return np.array(out, dtype=np.uint16)


if __name__ == "__main__":
    g = compute_golden()
    for i in range(min(20, len(g))):
        print(f"{{i:4d}}  {{g[i]:#06x}}  {{g[i]}}")
    np.save("golden_waveform.npy", g)
    print(f"Saved golden_waveform.npy ({{len(g)}} samples)")
'''
    with open(os.path.join(d, "golden.py"), "w") as f:
        f.write(golden_py)

    with open(os.path.join(d, "spec.txt"), "w") as f:
        f.write(spec)

    MANIFEST.append({
        "name": name,
        "family": family,
        "inputs": inputs,        # list of [port, cnt_slice]
        "outwires": outwires,    # list of verilog wire decls (for tb)
        "ports": ports,          # DUT port connections (excl clk/rst_n)
        "probe": probe,          # verilog probe packing expression
        "probe_mask": probe_mask,
        "period": period,
        "golden_body": golden_body,
    })


# ----------------------------------------------------------------------------
# Family generators
# ----------------------------------------------------------------------------

def gen_mod_counters():
    """Free-running modulo-N counters of varying modulus."""
    # spread, not every value -- diversity over near-duplicates
    moduli = list(range(2, 97)) + list(range(98, 200, 2)) + \
        [208, 224, 240, 250, 256]
    for n in moduli:
        w = clog2(n)
        name = f"mod{n}_counter"
        verilog = f"""// Modulo-{n} free-running counter (width {w}).
module {name} (
    input  wire clk,
    input  wire rst_n,
    output reg  [{w-1}:0] count
);
    always @(posedge clk) begin
        if (!rst_n)              count <= {w}'d0;
        else if (count == {w}'d{n-1}) count <= {w}'d0;
        else                     count <= count + {w}'d1;
    end
endmodule
"""
        golden = (
            "        # mod-N free-running counter\n"
            f"        val = c % {n}"
        )
        emit(
            name=name, family="mod_counter", verilog=verilog,
            golden_body=golden,
            inputs=[], outwires=[f"wire [{w-1}:0] count;"],
            ports=".count(count)",
            probe="{%d'b0, count}" % (16 - w),
            probe_mask=(1 << w) - 1, period=n,
            spec=(f"Write a Verilog module named `{name}` that is a free-running "
                  f"modulo-{n} counter.\n\nPorts:\n  input  clk\n  input  rst_n   "
                  f"active-low synchronous reset\n  output [{w-1}:0] count\n\n"
                  f"Behavior:\n  - Registered on posedge clk.\n  - On !rst_n: "
                  f"count <= 0.\n  - Counts 0,1,...,{n-1},0,... wrapping at {n}.\n"),
            golden_doc=f"Modulo-{n} counter, period {n}.",
        )


def gen_width_counters():
    """Plain binary up-counters of varying bit width (period = 2^w)."""
    for w in range(2, 17):
        period = 1 << w
        name = f"counter{w}b"
        pw = min(w, 16)
        verilog = f"""// {w}-bit binary up-counter.
module {name} (
    input  wire clk,
    input  wire rst_n,
    output reg  [{w-1}:0] count
);
    always @(posedge clk) begin
        if (!rst_n) count <= {w}'d0;
        else        count <= count + {w}'d1;
    end
endmodule
"""
        golden = f"        val = c & {(1<<pw)-1}"
        emit(
            name=name, family="counter", verilog=verilog, golden_body=golden,
            inputs=[], outwires=[f"wire [{w-1}:0] count;"],
            ports=".count(count)",
            probe=("count" if w >= 16 else "{%d'b0, count}" % (16 - w)),
            probe_mask=(1 << pw) - 1, period=period,
            spec=(f"Write a Verilog module named `{name}`, a {w}-bit free-running "
                  f"binary up-counter.\n\nPorts:\n  input clk\n  input rst_n "
                  f"(active-low sync reset)\n  output [{w-1}:0] count\n\nBehavior:\n"
                  f"  - Registered. On !rst_n count<=0. Else count<=count+1 "
                  f"(wraps at 2^{w}).\n"),
            golden_doc=f"{w}-bit up-counter.",
        )


def gen_updown_counters():
    """Up/down counters; direction toggles via a counter bit."""
    for w in range(3, 16):
        name = f"updown{w}b"
        # dir from cnt[12] so it stays constant over a full 2^w sweep, then flips.
        dir_bit = w + 2
        period = 1 << (dir_bit + 1)
        verilog = f"""// {w}-bit up/down counter. dir=0 up, dir=1 down.
module {name} (
    input  wire clk,
    input  wire rst_n,
    input  wire dir,
    output reg  [{w-1}:0] count
);
    always @(posedge clk) begin
        if (!rst_n)   count <= {w}'d0;
        else if (dir) count <= count - {w}'d1;
        else          count <= count + {w}'d1;
    end
endmodule
"""
        golden = (
            "        # up/down counter; replay state from reset\n"
            "        pass\n"
            "        # handled below via stateful fallback"
        )
        # up/down needs state replay -> use a stateful golden body.
        golden_body = (
            f"        if c == 0:\n"
            f"            st = 0\n"
            f"        d = (c >> {dir_bit}) & 1\n"
            f"        val = st & {(1<<w)-1}\n"
            f"        st = (st - 1) if d else (st + 1)\n"
            f"        st &= {(1<<w)-1}"
        )
        emit(
            name=name, family="updown", verilog=verilog,
            golden_body=golden_body,
            inputs=[["dir", f"cnt[{dir_bit}]"]],
            outwires=[f"wire [{w-1}:0] count;"],
            ports=f".dir(cnt[{dir_bit}]), .count(count)",
            probe="{%d'b0, count}" % (16 - w),
            probe_mask=(1 << w) - 1, period=period,
            spec=(f"Write a Verilog module named `{name}`, a {w}-bit up/down "
                  f"counter.\n\nPorts:\n  input clk, rst_n\n  input dir (0=up, "
                  f"1=down)\n  output [{w-1}:0] count\n\nBehavior:\n  - Registered. "
                  f"On !rst_n count<=0. dir=0: +1, dir=1: -1.\n"),
            golden_doc=f"{w}-bit up/down counter (dir=cnt[{dir_bit}]).",
        )


def gen_multipliers():
    """Unsigned multipliers a*b of varying widths."""
    for wa in range(2, 9):
        for wb in range(2, 9):
            if wa + wb > 15:        # 15-bit product still fits the 16-bit probe
                continue
            ow = wa + wb
            name = f"mul{wa}x{wb}"
            if name == "mult4x4":   # avoid clobbering existing hand-authored design
                name = "mul4x4g"
            verilog = f"""// {wa}x{wb} unsigned multiplier (registered).
module {name} (
    input  wire clk,
    input  wire rst_n,
    input  wire [{wa-1}:0] a,
    input  wire [{wb-1}:0] b,
    output reg  [{ow-1}:0] product
);
    always @(posedge clk) begin
        if (!rst_n) product <= {ow}'d0;
        else        product <= a * b;
    end
endmodule
"""
            golden = (
                f"        a = c & {(1<<wa)-1}\n"
                f"        b = (c >> {wa}) & {(1<<wb)-1}\n"
                f"        val = a * b"
            )
            emit(
                name=name, family="mul", verilog=verilog, golden_body=golden,
                inputs=[["a", f"cnt[{wa-1}:0]"], ["b", f"cnt[{wa+wb-1}:{wa}]"]],
                outwires=[f"wire [{ow-1}:0] product;"],
                ports=f".a(cnt[{wa-1}:0]), .b(cnt[{wa+wb-1}:{wa}]), .product(product)",
                probe="{%d'b0, product}" % (16 - ow),
                probe_mask=(1 << ow) - 1, period=1 << (wa + wb),
                spec=(f"Write a Verilog module named `{name}`, a registered "
                      f"{wa}-bit x {wb}-bit unsigned multiplier.\n\nPorts:\n  input "
                      f"clk, rst_n\n  input [{wa-1}:0] a\n  input [{wb-1}:0] b\n  "
                      f"output [{ow-1}:0] product\n\nBehavior: product <= a*b on "
                      f"posedge clk; 0 on !rst_n.\n"),
                golden_doc=f"{wa}x{wb} unsigned multiply.",
            )


def gen_addsub():
    """Adders / subtractors / add-sub of varying width."""
    for w in range(2, 16):
        for mode in ("add", "sub", "addsub"):
            ow = w + 1
            base = f"{mode}{w}b"
            if mode == "addsub":
                name = base
                sub_in = f", .sub(cnt[{2*w}])"
                inputs = [["a", f"cnt[{w-1}:0]"], ["b", f"cnt[{2*w-1}:{w}]"],
                          ["sub", f"cnt[{2*w}]"]]
                ports = f".a(cnt[{w-1}:0]), .b(cnt[{2*w-1}:{w}]), .sub(cnt[{2*w}]), .result(result)"
                opline = ("        else if (sub) result <= {1'b0, a} - {1'b0, b};\n"
                          "        else          result <= {1'b0, a} + {1'b0, b};")
                decl = "    input  wire sub,\n"
                golden = (
                    f"        a = c & {(1<<w)-1}\n"
                    f"        b = (c >> {w}) & {(1<<w)-1}\n"
                    f"        s = (c >> {2*w}) & 1\n"
                    f"        val = ((a - b) if s else (a + b)) & {(1<<ow)-1}"
                )
                period = 1 << (2 * w + 1)
            else:
                name = base
                decl = ""
                inputs = [["a", f"cnt[{w-1}:0]"], ["b", f"cnt[{2*w-1}:{w}]"]]
                ports = f".a(cnt[{w-1}:0]), .b(cnt[{2*w-1}:{w}]), .result(result)"
                if mode == "add":
                    opline = "        else result <= {1'b0, a} + {1'b0, b};"
                    golden = (
                        f"        a = c & {(1<<w)-1}\n"
                        f"        b = (c >> {w}) & {(1<<w)-1}\n"
                        f"        val = (a + b) & {(1<<ow)-1}"
                    )
                else:
                    opline = "        else result <= {1'b0, a} - {1'b0, b};"
                    golden = (
                        f"        a = c & {(1<<w)-1}\n"
                        f"        b = (c >> {w}) & {(1<<w)-1}\n"
                        f"        val = (a - b) & {(1<<ow)-1}"
                    )
                period = 1 << (2 * w)
            verilog = f"""// {w}-bit {mode} with carry/borrow out (registered).
module {name} (
    input  wire clk,
    input  wire rst_n,
    input  wire [{w-1}:0] a,
    input  wire [{w-1}:0] b,
{decl}    output reg  [{ow-1}:0] result
);
    always @(posedge clk) begin
        if (!rst_n) result <= {ow}'d0;
{opline}
    end
endmodule
"""
            verb = {"add": "adds", "sub": "subtracts",
                    "addsub": "adds or subtracts (sub input selects)"}[mode]
            emit(
                name=name, family=mode, verilog=verilog, golden_body=golden,
                inputs=inputs, outwires=[f"wire [{ow-1}:0] result;"],
                ports=ports, probe=pack("result", ow),
                probe_mask=(1 << ow) - 1, period=period,
                spec=(f"Write a Verilog module named `{name}` that {verb} two "
                      f"{w}-bit unsigned numbers, registered, with a {ow}-bit "
                      f"result (top bit = carry/borrow).\n\nPorts:\n  input clk, "
                      f"rst_n\n  input [{w-1}:0] a, b\n" +
                      ("  input sub (0=add,1=sub)\n" if mode == "addsub" else "") +
                      f"  output [{ow-1}:0] result\n"),
                golden_doc=f"{w}-bit {mode}.",
            )


def gen_shifters():
    """Barrel shifters and rotators."""
    for w in (4, 5, 6, 7, 8, 10, 12, 16):
        sw = clog2(w)
        for direction in ("left", "right"):
            for kind in ("logical", "rotate"):
                # barrel rotate only well-defined when shamt range == width,
                # i.e. width is a power of two (else shamt can exceed w).
                if kind == "rotate" and (w & (w - 1)) != 0:
                    continue
                name = f"{kind}_{direction[0]}sh{w}"
                if direction == "left":
                    if kind == "logical":
                        op = "data << shamt"
                        gexpr = f"(d << s) & {(1<<w)-1}"
                    else:
                        op = "(data << shamt) | (data >> (%d - shamt))" % w
                        gexpr = f"((d << s) | (d >> ({w}-s))) & {(1<<w)-1} if s else d"
                else:
                    if kind == "logical":
                        op = "data >> shamt"
                        gexpr = f"d >> s"
                    else:
                        op = "(data >> shamt) | (data << (%d - shamt))" % w
                        gexpr = f"((d >> s) | (d << ({w}-s))) & {(1<<w)-1} if s else d"
                # rotate by 0 special-cased to avoid >>w undefined; guard in verilog
                if kind == "rotate":
                    op = f"(shamt == 0) ? data : ({op})"
                verilog = f"""// {w}-bit {direction} {kind} shift (registered). shamt {sw} bits.
module {name} (
    input  wire clk,
    input  wire rst_n,
    input  wire [{w-1}:0] data,
    input  wire [{sw-1}:0] shamt,
    output reg  [{w-1}:0] out
);
    always @(posedge clk) begin
        if (!rst_n) out <= {w}'d0;
        else        out <= {op};
    end
endmodule
"""
                golden = (
                    f"        d = c & {(1<<w)-1}\n"
                    f"        s = (c >> {w}) & {(1<<sw)-1}\n"
                    f"        val = ({gexpr}) & {(1<<w)-1}"
                )
                emit(
                    name=name, family="shift", verilog=verilog,
                    golden_body=golden,
                    inputs=[["data", f"cnt[{w-1}:0]"],
                            ["shamt", f"cnt[{w+sw-1}:{w}]"]],
                    outwires=[f"wire [{w-1}:0] out;"],
                    ports=f".data(cnt[{w-1}:0]), .shamt(cnt[{w+sw-1}:{w}]), .out(out)",
                    probe=("out" if w >= 16 else "{%d'b0, out}" % (16 - w)),
                    probe_mask=(1 << w) - 1, period=1 << (w + sw),
                    spec=(f"Write a Verilog module named `{name}`, a registered "
                          f"{w}-bit {direction} {kind} "
                          f"{'shifter' if kind=='logical' else 'rotator'}.\n\n"
                          f"Ports:\n  input clk, rst_n\n  input [{w-1}:0] data\n  "
                          f"input [{sw-1}:0] shamt\n  output [{w-1}:0] out\n\n"
                          f"Behavior: out <= data {direction}-{kind} by shamt.\n"),
                    golden_doc=f"{w}-bit {direction} {kind} shift.",
                )


def gen_comparators():
    for w in range(2, 17):
        name = f"cmp{w}b"
        verilog = f"""// {w}-bit magnitude comparator (registered): gt, eq, lt.
module {name} (
    input  wire clk,
    input  wire rst_n,
    input  wire [{w-1}:0] a,
    input  wire [{w-1}:0] b,
    output reg  gt, eq, lt
);
    always @(posedge clk) begin
        if (!rst_n) begin gt<=0; eq<=0; lt<=0; end
        else begin
            gt <= (a > b);
            eq <= (a == b);
            lt <= (a < b);
        end
    end
endmodule
"""
        golden = (
            f"        a = c & {(1<<w)-1}\n"
            f"        b = (c >> {w}) & {(1<<w)-1}\n"
            f"        val = ((1 if a>b else 0)<<2)|((1 if a==b else 0)<<1)|(1 if a<b else 0)"
        )
        emit(
            name=name, family="cmp", verilog=verilog, golden_body=golden,
            inputs=[["a", f"cnt[{w-1}:0]"], ["b", f"cnt[{2*w-1}:{w}]"]],
            outwires=["wire gt, eq, lt;"],
            ports=f".a(cnt[{w-1}:0]), .b(cnt[{2*w-1}:{w}]), .gt(gt), .eq(eq), .lt(lt)",
            probe="{13'b0, gt, eq, lt}", probe_mask=0x7, period=1 << (2 * w),
            spec=(f"Write a Verilog module named `{name}`, a registered {w}-bit "
                  f"magnitude comparator.\n\nPorts:\n  input clk, rst_n\n  input "
                  f"[{w-1}:0] a, b\n  output gt, eq, lt\n\nBehavior: gt=(a>b), "
                  f"eq=(a==b), lt=(a<b), all registered.\n"),
            golden_doc=f"{w}-bit comparator -> {{gt,eq,lt}}.",
        )


def gen_bitops():
    """Combinational bit functions over a w-bit input: parity, popcount,
    reverse, gray, leading-zeros."""
    for w in (3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16):
        iw = min(w, 16)
        # parity
        name = f"parity{w}"
        verilog = f"""// {w}-bit parity (registered): even = ^in.
module {name} (
    input  wire clk, rst_n,
    input  wire [{w-1}:0] in,
    output reg  even, odd
);
    always @(posedge clk) begin
        if (!rst_n) begin even<=0; odd<=1; end
        else begin even <= ^in; odd <= ~(^in); end
    end
endmodule
"""
        golden = (
            f"        x = c & {(1<<iw)-1}\n"
            f"        e = bin(x).count('1') & 1\n"
            f"        val = (e<<1)|(1-e)"
        )
        emit(name, "parity", verilog, golden,
             inputs=[["in", f"cnt[{w-1}:0]"]], outwires=["wire even, odd;"],
             ports=f".in(cnt[{w-1}:0]), .even(even), .odd(odd)",
             probe="{14'b0, even, odd}", probe_mask=0x3, period=1 << iw,
             spec=(f"Write a Verilog module named `{name}` computing even/odd "
                   f"parity of a {w}-bit input (registered). even=^in, odd=~even.\n"),
             golden_doc=f"{w}-bit parity.")

        # popcount
        ow = clog2(w + 1)
        name = f"popcount{w}"
        verilog = f"""// {w}-bit population count (registered).
module {name} (
    input  wire clk, rst_n,
    input  wire [{w-1}:0] in,
    output reg  [{ow-1}:0] count
);
    integer k;
    always @(posedge clk) begin
        if (!rst_n) count <= 0;
        else begin
            count = 0;
            for (k=0;k<{w};k=k+1) count = count + in[k];
        end
    end
endmodule
"""
        golden = (f"        x = c & {(1<<iw)-1}\n"
                  f"        val = bin(x).count('1')")
        emit(name, "popcount", verilog, golden,
             inputs=[["in", f"cnt[{w-1}:0]"]],
             outwires=[f"wire [{ow-1}:0] count;"],
             ports=f".in(cnt[{w-1}:0]), .count(count)",
             probe="{%d'b0, count}" % (16 - ow),
             probe_mask=(1 << ow) - 1, period=1 << iw,
             spec=(f"Write a Verilog module named `{name}` that counts the number "
                   f"of 1 bits in a {w}-bit input (registered), output "
                   f"[{ow-1}:0] count.\n"),
             golden_doc=f"{w}-bit popcount.")

        # bit reverse
        rw = min(w, 16)
        name = f"reverse{w}"
        verilog = f"""// {w}-bit bit-reverse (registered).
module {name} (
    input  wire clk, rst_n,
    input  wire [{w-1}:0] in,
    output reg  [{w-1}:0] out
);
    integer k;
    always @(posedge clk) begin
        if (!rst_n) out <= 0;
        else for (k=0;k<{w};k=k+1) out[k] <= in[{w-1}-k];
    end
endmodule
"""
        golden = (f"        x = c & {(1<<rw)-1}\n"
                  f"        val = int(format(x, '0{w}b')[::-1], 2)")
        emit(name, "reverse", verilog, golden,
             inputs=[["in", f"cnt[{w-1}:0]"]],
             outwires=[f"wire [{w-1}:0] out;"],
             ports=f".in(cnt[{w-1}:0]), .out(out)",
             probe=("out" if w >= 16 else "{%d'b0, out}" % (16 - w)),
             probe_mask=(1 << rw) - 1, period=1 << rw,
             spec=(f"Write a Verilog module named `{name}` that bit-reverses a "
                   f"{w}-bit input (registered), output [{w-1}:0] out.\n"),
             golden_doc=f"{w}-bit reverse.")

        # gray code
        gw = min(w, 16)
        name = f"gray{w}"
        verilog = f"""// {w}-bit binary->Gray (registered).
module {name} (
    input  wire clk, rst_n,
    input  wire [{w-1}:0] bin,
    output reg  [{w-1}:0] gray
);
    always @(posedge clk) begin
        if (!rst_n) gray <= 0;
        else        gray <= bin ^ (bin >> 1);
    end
endmodule
"""
        golden = (f"        x = c & {(1<<gw)-1}\n"
                  f"        val = x ^ (x >> 1)")
        emit(name, "gray", verilog, golden,
             inputs=[["bin", f"cnt[{w-1}:0]"]],
             outwires=[f"wire [{w-1}:0] gray;"],
             ports=f".bin(cnt[{w-1}:0]), .gray(gray)",
             probe=("gray" if w >= 16 else "{%d'b0, gray}" % (16 - w)),
             probe_mask=(1 << gw) - 1, period=1 << gw,
             spec=(f"Write a Verilog module named `{name}` converting a {w}-bit "
                   f"binary value to Gray code (registered): gray=bin^(bin>>1).\n"),
             golden_doc=f"{w}-bit gray encode.")


def gen_priority_encoders():
    for w in range(2, 17):
        ow = clog2(w)
        name = f"prienc{w}"
        chain = "\n".join(
            [f"            {'if' if i==w-1 else 'else if'} (req[{i}]) enc <= {ow}'d{i};"
             for i in range(w - 1, 0, -1)]
        ) + f"\n            else enc <= {ow}'d0;"
        verilog = f"""// {w}-to-{ow} priority encoder (registered). MSB highest priority.
module {name} (
    input  wire clk, rst_n,
    input  wire [{w-1}:0] req,
    output reg  [{ow-1}:0] enc,
    output reg  valid
);
    always @(posedge clk) begin
        if (!rst_n) begin enc<=0; valid<=0; end
        else begin
            valid <= |req;
{chain}
        end
    end
endmodule
"""
        golden = (
            f"        req = c & {(1<<w)-1}\n"
            f"        enc = 0\n"
            f"        for i in range({w-1}, -1, -1):\n"
            f"            if req & (1<<i):\n"
            f"                enc = i; break\n"
            f"        val = ((1 if req else 0)<<{ow})|enc"
        )
        emit(name, "prienc", verilog, golden,
             inputs=[["req", f"cnt[{w-1}:0]"]],
             outwires=[f"wire [{ow-1}:0] enc;", "wire valid;"],
             ports=f".req(cnt[{w-1}:0]), .enc(enc), .valid(valid)",
             probe="{%d'b0, valid, enc}" % (16 - ow - 1),
             probe_mask=(1 << (ow + 1)) - 1, period=1 << w,
             spec=(f"Write a Verilog module named `{name}`, a {w}-input priority "
                   f"encoder (registered). MSB has highest priority. Outputs "
                   f"[{ow-1}:0] enc and valid=|req.\n"),
             golden_doc=f"{w}-input priority encoder.")


def gen_decoders():
    for w in (2, 3, 4):
        ow = 1 << w
        if ow > 16:
            continue
        name = f"decoder{w}to{ow}"
        verilog = f"""// {w}-to-{ow} one-hot decoder (registered).
module {name} (
    input  wire clk, rst_n,
    input  wire [{w-1}:0] sel,
    output reg  [{ow-1}:0] out
);
    always @(posedge clk) begin
        if (!rst_n) out <= 0;
        else        out <= ({ow}'d1 << sel);
    end
endmodule
"""
        golden = (f"        s = c & {(1<<w)-1}\n"
                  f"        val = 1 << s")
        emit(name, "decoder", verilog, golden,
             inputs=[["sel", f"cnt[{w-1}:0]"]],
             outwires=[f"wire [{ow-1}:0] out;"],
             ports=f".sel(cnt[{w-1}:0]), .out(out)",
             probe=("out" if ow >= 16 else "{%d'b0, out}" % (16 - ow)),
             probe_mask=(1 << ow) - 1 if ow < 16 else 0xFFFF, period=1 << w,
             spec=(f"Write a Verilog module named `{name}`, a {w}-to-{ow} one-hot "
                   f"decoder (registered): out = 1<<sel.\n"),
             golden_doc=f"{w}-to-{ow} decoder.")


def gen_lfsrs():
    """Galois LFSRs with various widths and feedback polynomials."""
    # (width, tap_mask, seed) tuples -- maximal/standard polynomials.
    cfgs = [
        (4, 0x9, 0xF), (5, 0x12, 0x1F), (6, 0x21, 0x3F), (7, 0x41, 0x7F),
        (8, 0x8E, 0xAC), (8, 0x95, 0x01), (8, 0xB8, 0xFF),
        (9, 0x110, 0x1AA), (10, 0x240, 0x3FF), (11, 0x500, 0x7AB),
        (12, 0x829, 0xABC), (13, 0x100D, 0x1FFF), (14, 0x2015, 0x2ABC),
        (15, 0x6000, 0x7FFF), (16, 0xB400, 0xACE1),
    ]
    for idx, (w, taps, seed) in enumerate(cfgs):
        name = f"lfsr{w}_{idx}"
        verilog = f"""// {w}-bit Galois LFSR. taps={taps:#x} seed={seed:#x}.
module {name} (
    input  wire clk, rst_n,
    output reg  [{w-1}:0] state
);
    always @(posedge clk) begin
        if (!rst_n) state <= {w}'h{seed:x};
        else        state <= state[0] ? (({{1'b0, state[{w-1}:1]}}) ^ {w}'h{taps:x})
                                       :  ({{1'b0, state[{w-1}:1]}});
    end
endmodule
"""
        golden = (
            "        if c == 0:\n"
            f"            st = {seed}\n"
            "        val = st\n"
            "        fb = st & 1\n"
            "        st = st >> 1\n"
            f"        if fb: st ^= {taps}\n"
            f"        st &= {(1<<w)-1}"
        )
        pw = min(w, 16)
        emit(name, "lfsr", verilog, golden,
             inputs=[], outwires=[f"wire [{w-1}:0] state;"],
             ports=".state(state)",
             probe=("state" if w >= 16 else "{%d'b0, state}" % (16 - w)),
             probe_mask=(1 << pw) - 1, period=(1 << w) - 1,
             spec=(f"Write a Verilog module named `{name}`, a {w}-bit Galois LFSR "
                   f"with feedback tap mask {taps:#x} and seed {seed:#x} (on "
                   f"!rst_n). Each cycle: shift right; if outgoing LSB is 1, XOR "
                   f"the shifted value with the tap mask. Output [{w-1}:0] state.\n"),
             golden_doc=f"{w}-bit LFSR taps={taps:#x}.")


def gen_accumulators():
    """Accumulators: acc += data each cycle, varying widths."""
    for w in (2, 3, 4, 5, 6, 7, 8):
        for aw in (8, 10, 12, 14, 16):
            if aw < w:
                continue
            name = f"acc{w}to{aw}"
            verilog = f"""// {aw}-bit accumulator of {w}-bit input (registered, wraps).
module {name} (
    input  wire clk, rst_n,
    input  wire [{w-1}:0] data,
    output reg  [{aw-1}:0] acc
);
    always @(posedge clk) begin
        if (!rst_n) acc <= 0;
        else        acc <= acc + data;
    end
endmodule
"""
            golden = (
                "        if c == 0:\n"
                "            st = 0\n"
                f"        val = st & {(1<<min(aw,16))-1}\n"
                f"        st = (st + (c & {(1<<w)-1})) & {(1<<aw)-1}"
            )
            emit(name, "accum", verilog, golden,
                 inputs=[["data", f"cnt[{w-1}:0]"]],
                 outwires=[f"wire [{aw-1}:0] acc;"],
                 ports=f".data(cnt[{w-1}:0]), .acc(acc)",
                 probe=("acc[15:0]" if aw >= 16 else "{%d'b0, acc}" % (16 - aw)),
                 probe_mask=(1 << min(aw, 16)) - 1, period=1 << (w + 4),
                 spec=(f"Write a Verilog module named `{name}`, an {aw}-bit "
                       f"accumulator. Each cycle acc <= acc + data ({w}-bit "
                       f"input); 0 on !rst_n.\n"),
                 golden_doc=f"{aw}-bit accumulator of {w}-bit data.")


def gen_step_counters():
    """Counters that increment by a constant step K each cycle."""
    for w in range(4, 15):
        for k in (2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 15):
            name = f"step{k}_cnt{w}b"
            verilog = f"""// {w}-bit counter, increments by {k} each cycle.
module {name} (
    input  wire clk, rst_n,
    output reg  [{w-1}:0] count
);
    always @(posedge clk) begin
        if (!rst_n) count <= {w}'d0;
        else        count <= count + {w}'d{k};
    end
endmodule
"""
            golden = (
                "        if c == 0:\n"
                "            st = 0\n"
                f"        val = st\n"
                f"        st = (st + {k}) & {(1<<w)-1}"
            )
            emit(name, "step_counter", verilog, golden,
                 inputs=[], outwires=[f"wire [{w-1}:0] count;"],
                 ports=".count(count)",
                 probe="{%d'b0, count}" % (16 - w),
                 probe_mask=(1 << w) - 1, period=(1 << w),
                 spec=(f"Write a Verilog module named `{name}`, a {w}-bit counter "
                       f"that increments by {k} each cycle (wraps). 0 on !rst_n.\n"),
                 golden_doc=f"{w}-bit step-{k} counter.")


def gen_down_counters():
    for w in range(2, 17):
        name = f"downcnt{w}b"
        verilog = f"""// {w}-bit down-counter.
module {name} (
    input  wire clk, rst_n,
    output reg  [{w-1}:0] count
);
    always @(posedge clk) begin
        if (!rst_n) count <= {{{w}{{1'b1}}}};
        else        count <= count - {w}'d1;
    end
endmodule
"""
        golden = (
            "        if c == 0:\n"
            f"            st = {(1<<w)-1}\n"
            "        val = st\n"
            f"        st = (st - 1) & {(1<<w)-1}"
        )
        emit(name, "down_counter", verilog, golden,
             inputs=[], outwires=[f"wire [{w-1}:0] count;"],
             ports=".count(count)",
             probe=("count" if w >= 16 else "{%d'b0, count}" % (16 - w)),
             probe_mask=(1 << w) - 1, period=1 << w,
             spec=(f"Write a Verilog module named `{name}`, a {w}-bit down-counter "
                   f"that starts at all-ones on reset and decrements each cycle.\n"),
             golden_doc=f"{w}-bit down-counter.")


def gen_muxes():
    """n-to-1 multiplexers with d-bit data paths, counter-driven."""
    for n in (2, 4, 8, 16):
        sw = clog2(n)
        for d in (1, 2, 3, 4):
            if sw + n * d > 30:
                continue
            name = f"mux{n}x{d}b"
            decls = ", ".join(f"input wire [{d-1}:0] d{i}" for i in range(n))
            cases = "\n".join(
                f"            {sw}'d{i}: out <= d{i};" for i in range(n))
            # bit assignments: sel=cnt[sw-1:0], di = cnt[sw+(i+1)*d-1 : sw+i*d]
            conns = [f".sel(cnt[{sw-1}:0])"]
            for i in range(n):
                lo = sw + i * d
                hi = lo + d - 1
                conns.append(f".d{i}(cnt[{hi}:{lo}])")
            conns.append(".out(out)")
            verilog = f"""// {n}-to-1 mux, {d}-bit data (registered).
module {name} (
    input  wire clk, rst_n,
    input  wire [{sw-1}:0] sel,
    {decls},
    output reg  [{d-1}:0] out
);
    always @(posedge clk) begin
        if (!rst_n) out <= 0;
        else case (sel)
{cases}
            default: out <= 0;
        endcase
    end
endmodule
"""
            gbody = ["        sel = c & %d" % ((1 << sw) - 1)]
            for i in range(n):
                lo = sw + i * d
                gbody.append(f"        d{i} = (c >> {lo}) & {(1<<d)-1}")
            gbody.append("        val = [%s][sel]" %
                         ", ".join(f"d{i}" for i in range(n)))
            golden = "\n".join(gbody)
            emit(name, "mux", verilog, golden,
                 inputs=[["sel", f"cnt[{sw-1}:0]"]],
                 outwires=[f"wire [{d-1}:0] out;"],
                 ports=", ".join(conns),
                 probe="{%d'b0, out}" % (16 - d),
                 probe_mask=(1 << d) - 1, period=1 << (sw + n * d),
                 spec=(f"Write a Verilog module named `{name}`, a registered "
                       f"{n}-to-1 multiplexer with {d}-bit data inputs d0..d{n-1} "
                       f"and a {sw}-bit sel. out <= d[sel].\n"),
                 golden_doc=f"{n}-to-1 mux, {d}-bit.")


def gen_minmax():
    for w in range(2, 17):
        for kind in ("min", "max"):
            name = f"{kind}{w}b"
            op = "<" if kind == "min" else ">"
            verilog = f"""// {w}-bit {kind} of two inputs (registered).
module {name} (
    input  wire clk, rst_n,
    input  wire [{w-1}:0] a,
    input  wire [{w-1}:0] b,
    output reg  [{w-1}:0] out
);
    always @(posedge clk) begin
        if (!rst_n) out <= 0;
        else        out <= (a {op} b) ? a : b;
    end
endmodule
"""
            pyop = "min" if kind == "min" else "max"
            golden = (
                f"        a = c & {(1<<w)-1}\n"
                f"        b = (c >> {w}) & {(1<<w)-1}\n"
                f"        val = {pyop}(a, b)"
            )
            emit(name, kind, verilog, golden,
                 inputs=[["a", f"cnt[{w-1}:0]"], ["b", f"cnt[{2*w-1}:{w}]"]],
                 outwires=[f"wire [{w-1}:0] out;"],
                 ports=f".a(cnt[{w-1}:0]), .b(cnt[{2*w-1}:{w}]), .out(out)",
                 probe=pack("out", w),
                 probe_mask=(1 << w) - 1, period=1 << (2 * w),
                 spec=(f"Write a Verilog module named `{name}` outputting the "
                       f"{kind} of two {w}-bit unsigned inputs a, b (registered).\n"),
                 golden_doc=f"{w}-bit {kind}.")


def gen_alus():
    """Multi-operation ALUs with varying width and op repertoire."""
    OPS = [
        ("add", "a + b",      "(a + b)"),
        ("sub", "a - b",      "(a - b)"),
        ("and", "a & b",      "(a & b)"),
        ("or",  "a | b",      "(a | b)"),
        ("xor", "a ^ b",      "(a ^ b)"),
        ("nota","~a",         "(~a)"),
        ("shl", "a << 1",     "(a << 1)"),
        ("shr", "a >> 1",     "(a >> 1)"),
    ]
    for w in (4, 5, 6, 7, 8, 10, 12):
        for nops in (2, 3, 4, 5, 6, 7, 8):
            ops = OPS[:nops]
            ow = clog2(nops)
            name = f"alu{w}_{nops}op"
            cases = "\n".join(
                f"            {ow}'d{i}: result <= {expr};"
                for i, (_, expr, _) in enumerate(ops))
            verilog = f"""// {w}-bit ALU, {nops} ops selected by op[{ow-1}:0] (registered).
module {name} (
    input  wire clk, rst_n,
    input  wire [{w-1}:0] a,
    input  wire [{w-1}:0] b,
    input  wire [{ow-1}:0] op,
    output reg  [{w-1}:0] result
);
    always @(posedge clk) begin
        if (!rst_n) result <= 0;
        else case (op)
{cases}
            default: result <= 0;
        endcase
    end
endmodule
"""
            mask = (1 << w) - 1
            gcases = "\n".join(
                f"            {i}: val = {pe} & {mask}"
                for i, (_, _, pe) in enumerate(ops))
            golden = (
                f"        a = c & {(1<<w)-1}\n"
                f"        b = (c >> {w}) & {(1<<w)-1}\n"
                f"        op = (c >> {2*w}) & {(1<<ow)-1}\n"
                f"        val = 0\n"
                f"        if False:\n            pass\n" +
                "\n".join(
                    f"        elif op == {i}: val = {pe} & {mask}"
                    for i, (_, _, pe) in enumerate(ops))
            )
            emit(name, "alu", verilog, golden,
                 inputs=[["a", f"cnt[{w-1}:0]"], ["b", f"cnt[{2*w-1}:{w}]"],
                         ["op", f"cnt[{2*w+ow-1}:{2*w}]"]],
                 outwires=[f"wire [{w-1}:0] result;"],
                 ports=(f".a(cnt[{w-1}:0]), .b(cnt[{2*w-1}:{w}]), "
                        f".op(cnt[{2*w+ow-1}:{2*w}]), .result(result)"),
                 probe="{%d'b0, result}" % (16 - w),
                 probe_mask=(1 << w) - 1, period=1 << (2 * w + ow),
                 spec=(f"Write a Verilog module named `{name}`, a registered "
                       f"{w}-bit ALU with {nops} operations selected by op:\n" +
                       "".join(f"  op={i}: result = {expr}\n"
                               for i, (_, expr, _) in enumerate(ops)) +
                       f"Ports: clk, rst_n, [{w-1}:0] a, b, [{ow-1}:0] op, "
                       f"[{w-1}:0] result.\n"),
                 golden_doc=f"{w}-bit {nops}-op ALU.")


def gen_signed_mul():
    for w in (2, 3, 4, 5, 6, 7):
        ow = 2 * w
        name = f"smul{w}x{w}"
        verilog = f"""// signed {w}x{w} multiplier (registered).
module {name} (
    input  wire clk, rst_n,
    input  wire signed [{w-1}:0] a,
    input  wire signed [{w-1}:0] b,
    output reg  signed [{ow-1}:0] product
);
    always @(posedge clk) begin
        if (!rst_n) product <= 0;
        else        product <= a * b;
    end
endmodule
"""
        golden = (
            f"        a = c & {(1<<w)-1}\n"
            f"        b = (c >> {w}) & {(1<<w)-1}\n"
            f"        a = a - {1<<w} if a >= {1<<(w-1)} else a\n"
            f"        b = b - {1<<w} if b >= {1<<(w-1)} else b\n"
            f"        val = (a * b) & {(1<<ow)-1}"
        )
        emit(name, "smul", verilog, golden,
             inputs=[["a", f"cnt[{w-1}:0]"], ["b", f"cnt[{2*w-1}:{w}]"]],
             outwires=[f"wire signed [{ow-1}:0] product;"],
             ports=f".a(cnt[{w-1}:0]), .b(cnt[{2*w-1}:{w}]), .product(product)",
             probe="{%d'b0, product}" % (16 - ow),
             probe_mask=(1 << ow) - 1, period=1 << (2 * w),
             spec=(f"Write a Verilog module named `{name}`, a registered signed "
                   f"{w}-bit x {w}-bit multiplier with {ow}-bit signed product.\n"),
             golden_doc=f"signed {w}x{w} multiply.")


def gen_saturating_add():
    for w in range(3, 16):
        name = f"satadd{w}b"
        maxv = (1 << w) - 1
        verilog = f"""// {w}-bit unsigned saturating adder (registered).
module {name} (
    input  wire clk, rst_n,
    input  wire [{w-1}:0] a,
    input  wire [{w-1}:0] b,
    output reg  [{w-1}:0] sum
);
    wire [{w}:0] full = a + b;
    always @(posedge clk) begin
        if (!rst_n) sum <= 0;
        else        sum <= full[{w}] ? {w}'d{maxv} : full[{w-1}:0];
    end
endmodule
"""
        golden = (
            f"        a = c & {(1<<w)-1}\n"
            f"        b = (c >> {w}) & {(1<<w)-1}\n"
            f"        s = a + b\n"
            f"        val = {maxv} if s > {maxv} else s"
        )
        emit(name, "satadd", verilog, golden,
             inputs=[["a", f"cnt[{w-1}:0]"], ["b", f"cnt[{2*w-1}:{w}]"]],
             outwires=[f"wire [{w-1}:0] sum;"],
             ports=f".a(cnt[{w-1}:0]), .b(cnt[{2*w-1}:{w}]), .sum(sum)",
             probe="{%d'b0, sum}" % (16 - w),
             probe_mask=(1 << w) - 1, period=1 << (2 * w),
             spec=(f"Write a Verilog module named `{name}`, a {w}-bit unsigned "
                   f"saturating adder: sum=a+b clamped to {maxv} on overflow "
                   f"(registered).\n"),
             golden_doc=f"{w}-bit saturating add.")


def gen_mac():
    """Multiply-accumulate: acc += a*b each cycle."""
    for w in (2, 3, 4, 5, 6, 7, 8):
        for aw in (8, 10, 12, 14, 16):
            if aw < 2 * w:
                continue
            name = f"mac{w}_{aw}b"
            verilog = f"""// {aw}-bit MAC: acc <= acc + a*b ({w}-bit operands).
module {name} (
    input  wire clk, rst_n,
    input  wire [{w-1}:0] a,
    input  wire [{w-1}:0] b,
    output reg  [{aw-1}:0] acc
);
    always @(posedge clk) begin
        if (!rst_n) acc <= 0;
        else        acc <= acc + a * b;
    end
endmodule
"""
            golden = (
                "        if c == 0:\n"
                "            st = 0\n"
                f"        val = st & {(1<<min(aw,16))-1}\n"
                f"        a = c & {(1<<w)-1}\n"
                f"        b = (c >> {w}) & {(1<<w)-1}\n"
                f"        st = (st + a * b) & {(1<<aw)-1}"
            )
            emit(name, "mac", verilog, golden,
                 inputs=[["a", f"cnt[{w-1}:0]"], ["b", f"cnt[{2*w-1}:{w}]"]],
                 outwires=[f"wire [{aw-1}:0] acc;"],
                 ports=f".a(cnt[{w-1}:0]), .b(cnt[{2*w-1}:{w}]), .acc(acc)",
                 probe=("acc[15:0]" if aw >= 16 else "{%d'b0, acc}" % (16 - aw)),
                 probe_mask=(1 << min(aw, 16)) - 1, period=1 << (2 * w + 4),
                 spec=(f"Write a Verilog module named `{name}`, an {aw}-bit "
                       f"multiply-accumulate: acc <= acc + a*b each cycle, with "
                       f"{w}-bit operands a, b. 0 on !rst_n.\n"),
                 golden_doc=f"{aw}-bit MAC, {w}-bit operands.")


def gen_gray_counters():
    """Counters whose output sequence is Gray code (state is binary count)."""
    for w in range(3, 17):
        name = f"graycnt{w}b"
        verilog = f"""// {w}-bit Gray-code counter (output is Gray of internal binary count).
module {name} (
    input  wire clk, rst_n,
    output reg  [{w-1}:0] gray
);
    reg [{w-1}:0] bin;
    always @(posedge clk) begin
        if (!rst_n) begin bin <= 0; gray <= 0; end
        else begin
            bin  <= bin + 1'b1;
            gray <= (bin + 1'b1) ^ ((bin + 1'b1) >> 1);
        end
    end
endmodule
"""
        golden = (f"        b = c & {(1<<w)-1}\n"
                  f"        val = b ^ (b >> 1)")
        emit(name, "gray_counter", verilog, golden,
             inputs=[], outwires=[f"wire [{w-1}:0] gray;"],
             ports=".gray(gray)",
             probe=pack("gray", w),
             probe_mask=(1 << w) - 1, period=1 << w,
             spec=(f"Write a Verilog module named `{name}`, a free-running {w}-bit "
                   f"Gray-code counter: its output steps through Gray code order.\n"),
             golden_doc=f"{w}-bit gray counter.")


def gen_negate():
    for w in range(3, 17):
        for kind in ("twos", "ones"):
            name = f"neg_{kind}{w}b"
            if kind == "twos":
                op = "(~in + 1'b1)"
                gexpr = f"(-x) & {(1<<w)-1}"
                desc = "two's complement negation (-in)"
            else:
                op = "~in"
                gexpr = f"(~x) & {(1<<w)-1}"
                desc = "one's complement (~in)"
            verilog = f"""// {w}-bit {desc} (registered).
module {name} (
    input  wire clk, rst_n,
    input  wire [{w-1}:0] in,
    output reg  [{w-1}:0] out
);
    always @(posedge clk) begin
        if (!rst_n) out <= 0;
        else        out <= {op};
    end
endmodule
"""
            golden = (f"        x = c & {(1<<w)-1}\n"
                      f"        val = {gexpr}")
            emit(name, "negate", verilog, golden,
                 inputs=[["in", f"cnt[{w-1}:0]"]],
                 outwires=[f"wire [{w-1}:0] out;"],
                 ports=f".in(cnt[{w-1}:0]), .out(out)",
                 probe=pack("out", w),
                 probe_mask=(1 << w) - 1, period=1 << w,
                 spec=(f"Write a Verilog module named `{name}` computing the "
                       f"{desc} of a {w}-bit input (registered).\n"),
                 golden_doc=f"{w}-bit {kind} negate.")


def gen_abs():
    for w in range(3, 13):
        name = f"abs{w}b"
        verilog = f"""// {w}-bit two's complement absolute value (registered).
module {name} (
    input  wire clk, rst_n,
    input  wire [{w-1}:0] in,
    output reg  [{w-1}:0] out
);
    always @(posedge clk) begin
        if (!rst_n)     out <= 0;
        else if (in[{w-1}]) out <= (~in + 1'b1);
        else            out <= in;
    end
endmodule
"""
        golden = (
            f"        x = c & {(1<<w)-1}\n"
            f"        val = ((~x + 1) & {(1<<w)-1}) if (x >> {w-1}) & 1 else x"
        )
        emit(name, "abs", verilog, golden,
             inputs=[["in", f"cnt[{w-1}:0]"]],
             outwires=[f"wire [{w-1}:0] out;"],
             ports=f".in(cnt[{w-1}:0]), .out(out)",
             probe="{%d'b0, out}" % (16 - w),
             probe_mask=(1 << w) - 1, period=1 << w,
             spec=(f"Write a Verilog module named `{name}` computing the absolute "
                   f"value of a {w}-bit two's complement input (registered).\n"),
             golden_doc=f"{w}-bit abs.")


def gen_window_cmp():
    """Output 1 if lo <= x <= hi for fixed lo/hi thresholds."""
    for w in (4, 5, 6, 7, 8):
        span = 1 << w
        for lo, hi in ((span // 4, 3 * span // 4), (1, span // 2),
                       (span // 3, 2 * span // 3), (span // 8, span // 2),
                       (span // 4, span - 1)):
            name = f"window{w}_{lo}_{hi}"
            verilog = f"""// {w}-bit window comparator: in_range = ({lo} <= x <= {hi}).
module {name} (
    input  wire clk, rst_n,
    input  wire [{w-1}:0] x,
    output reg  in_range
);
    always @(posedge clk) begin
        if (!rst_n) in_range <= 0;
        else        in_range <= (x >= {w}'d{lo}) && (x <= {w}'d{hi});
    end
endmodule
"""
            golden = (f"        x = c & {(1<<w)-1}\n"
                      f"        val = 1 if ({lo} <= x <= {hi}) else 0")
            emit(name, "window", verilog, golden,
                 inputs=[["x", f"cnt[{w-1}:0]"]], outwires=["wire in_range;"],
                 ports=f".x(cnt[{w-1}:0]), .in_range(in_range)",
                 probe="{15'b0, in_range}", probe_mask=0x1, period=1 << w,
                 spec=(f"Write a Verilog module named `{name}` that asserts "
                       f"in_range when a {w}-bit input x is within [{lo}, {hi}] "
                       f"inclusive (registered).\n"),
                 golden_doc=f"{w}-bit window [{lo},{hi}].")


def gen_clamp():
    """Clamp x to [0, hi] (saturate above hi)."""
    for w in (4, 5, 6, 7, 8):
        for hi in ((1 << w) - (1 << (w - 2)), (1 << (w - 1)) + 1,
                   (1 << (w - 1)), (1 << w) - 2):
            name = f"clamp{w}_{hi}"
            verilog = f"""// {w}-bit clamp to max {hi} (registered).
module {name} (
    input  wire clk, rst_n,
    input  wire [{w-1}:0] x,
    output reg  [{w-1}:0] out
);
    always @(posedge clk) begin
        if (!rst_n) out <= 0;
        else        out <= (x > {w}'d{hi}) ? {w}'d{hi} : x;
    end
endmodule
"""
            golden = (f"        x = c & {(1<<w)-1}\n"
                      f"        val = {hi} if x > {hi} else x")
            emit(name, "clamp", verilog, golden,
                 inputs=[["x", f"cnt[{w-1}:0]"]],
                 outwires=[f"wire [{w-1}:0] out;"],
                 ports=f".x(cnt[{w-1}:0]), .out(out)",
                 probe="{%d'b0, out}" % (16 - w),
                 probe_mask=(1 << w) - 1, period=1 << w,
                 spec=(f"Write a Verilog module named `{name}` that clamps a "
                       f"{w}-bit input to a maximum of {hi} (registered).\n"),
                 golden_doc=f"{w}-bit clamp to {hi}.")


def gen_swaps():
    """Nibble / half swaps of a w-bit word."""
    for w in (4, 6, 8, 10, 12, 14, 16):
        h = w // 2
        name = f"halfswap{w}"
        verilog = f"""// {w}-bit half-swap: out = {{lo, hi}} (registered).
module {name} (
    input  wire clk, rst_n,
    input  wire [{w-1}:0] in,
    output reg  [{w-1}:0] out
);
    always @(posedge clk) begin
        if (!rst_n) out <= 0;
        else        out <= {{in[{h-1}:0], in[{w-1}:{h}]}};
    end
endmodule
"""
        golden = (
            f"        x = c & {(1<<w)-1}\n"
            f"        hi = (x >> {h}) & {(1<<h)-1}\n"
            f"        lo = x & {(1<<h)-1}\n"
            f"        val = (lo << {h}) | hi"
        )
        emit(name, "swap", verilog, golden,
             inputs=[["in", f"cnt[{w-1}:0]"]],
             outwires=[f"wire [{w-1}:0] out;"],
             ports=f".in(cnt[{w-1}:0]), .out(out)",
             probe=("out" if w >= 16 else "{%d'b0, out}" % (16 - w)),
             probe_mask=(1 << min(w, 16)) - 1, period=1 << min(w, 16),
             spec=(f"Write a Verilog module named `{name}` that swaps the upper "
                   f"and lower halves of a {w}-bit input (registered).\n"),
             golden_doc=f"{w}-bit half swap.")


def gen_rotate_const():
    """Rotate-by-constant designs."""
    for w in (4, 6, 8, 10, 12, 16):
        for r in (1, 2, 3, w // 4, w // 2, w - 1):
            r = r % w
            if r == 0:
                continue
            name = f"rotl{w}_{r}"
            verilog = f"""// {w}-bit rotate-left by {r} (registered).
module {name} (
    input  wire clk, rst_n,
    input  wire [{w-1}:0] in,
    output reg  [{w-1}:0] out
);
    always @(posedge clk) begin
        if (!rst_n) out <= 0;
        else        out <= {{in[{w-1-r}:0], in[{w-1}:{w-r}]}};
    end
endmodule
"""
            golden = (
                f"        x = c & {(1<<w)-1}\n"
                f"        val = ((x << {r}) | (x >> {w-r})) & {(1<<w)-1}"
            )
            emit(name, "rotate_const", verilog, golden,
                 inputs=[["in", f"cnt[{w-1}:0]"]],
                 outwires=[f"wire [{w-1}:0] out;"],
                 ports=f".in(cnt[{w-1}:0]), .out(out)",
                 probe=("out" if w >= 16 else "{%d'b0, out}" % (16 - w)),
                 probe_mask=(1 << min(w, 16)) - 1, period=1 << min(w, 16),
                 spec=(f"Write a Verilog module named `{name}` that rotates a "
                       f"{w}-bit input left by {r} bits (registered).\n"),
                 golden_doc=f"{w}-bit rotate-left {r}.")


def gen_ring_johnson():
    for w in (3, 4, 5, 6, 7, 8, 9, 10, 12, 16):
        # ring
        name = f"ring{w}"
        verilog = f"""// {w}-bit ring counter (one-hot, rotates).
module {name} (
    input  wire clk, rst_n,
    output reg  [{w-1}:0] count
);
    always @(posedge clk) begin
        if (!rst_n) count <= {w}'b1;
        else        count <= {{count[{w-2}:0], count[{w-1}]}};
    end
endmodule
"""
        golden = (
            "        if c == 0:\n"
            "            st = 1\n"
            "        val = st\n"
            f"        st = ((st << 1) | (st >> {w-1})) & {(1<<w)-1}"
        )
        emit(name, "ring", verilog, golden,
             inputs=[], outwires=[f"wire [{w-1}:0] count;"],
             ports=".count(count)",
             probe=pack("count", w),
             probe_mask=(1 << w) - 1, period=w,
             spec=(f"Write a Verilog module named `{name}`, a {w}-bit ring counter "
                   f"that resets to one-hot 1 and rotates left each cycle.\n"),
             golden_doc=f"{w}-bit ring counter.")
        # johnson
        name = f"johnson{w}"
        verilog = f"""// {w}-bit Johnson (twisted-ring) counter.
module {name} (
    input  wire clk, rst_n,
    output reg  [{w-1}:0] count
);
    always @(posedge clk) begin
        if (!rst_n) count <= {w}'b0;
        else        count <= {{count[{w-2}:0], ~count[{w-1}]}};
    end
endmodule
"""
        golden = (
            "        if c == 0:\n"
            "            st = 0\n"
            "        val = st\n"
            f"        st = ((st << 1) | (1 - ((st >> {w-1}) & 1))) & {(1<<w)-1}"
        )
        emit(name, "johnson", verilog, golden,
             inputs=[], outwires=[f"wire [{w-1}:0] count;"],
             ports=".count(count)",
             probe=pack("count", w),
             probe_mask=(1 << w) - 1, period=2 * w,
             spec=(f"Write a Verilog module named `{name}`, a {w}-bit Johnson "
                   f"(twisted ring) counter: shift left, feed inverted MSB into "
                   f"LSB. Resets to 0.\n"),
             golden_doc=f"{w}-bit johnson counter.")


def gen_gray2bin():
    for w in range(3, 17):
        name = f"gray2bin{w}"
        xors = " ^ ".join(f"(gray >> {i})" for i in range(w))
        verilog = f"""// {w}-bit Gray-to-binary decoder (registered).
module {name} (
    input  wire clk, rst_n,
    input  wire [{w-1}:0] gray,
    output reg  [{w-1}:0] bin
);
    always @(posedge clk) begin
        if (!rst_n) bin <= 0;
        else        bin <= {xors};
    end
endmodule
"""
        golden = (
            f"        g = c & {(1<<w)-1}\n"
            f"        b = 0\n"
            f"        for i in range({w-1}, -1, -1):\n"
            f"            b ^= (g >> i)\n"
            f"        val = b & {(1<<w)-1}"
        )
        emit(name, "gray2bin", verilog, golden,
             inputs=[["gray", f"cnt[{w-1}:0]"]],
             outwires=[f"wire [{w-1}:0] bin;"],
             ports=f".gray(cnt[{w-1}:0]), .bin(bin)",
             probe=pack("bin", w),
             probe_mask=(1 << w) - 1, period=1 << w,
             spec=(f"Write a Verilog module named `{name}` converting a {w}-bit "
                   f"Gray code input to binary (registered).\n"),
             golden_doc=f"{w}-bit gray->binary.")


def gen_terminal_counters():
    """Counter with a terminal-count flag at a fixed value."""
    for w in (4, 5, 6, 7, 8):
        tc = (1 << w) - 1
        for top in (tc, (1 << w) // 2, (1 << w) // 3, (1 << w) // 4,
                    (3 * (1 << w)) // 4):
            name = f"tccnt{w}_{top}"
            verilog = f"""// {w}-bit counter wrapping at {top}, tc pulses at top.
module {name} (
    input  wire clk, rst_n,
    output reg  [{w-1}:0] count,
    output reg  tc
);
    always @(posedge clk) begin
        if (!rst_n) begin count <= 0; tc <= 0; end
        else begin
            tc <= (count == {w}'d{top});
            count <= (count == {w}'d{top}) ? {w}'d0 : count + 1'b1;
        end
    end
endmodule
"""
            ow = w
            golden = (
                "        if c == 0:\n"
                "            st = 0; prev = 0\n"
                f"        val = (st & {(1<<ow)-1}) | ((1 if prev == {top} else 0) << {ow})\n"
                f"        prev = st\n"
                f"        st = 0 if st == {top} else (st + 1)"
            )
            emit(name, "terminal_counter", verilog, golden,
                 inputs=[], outwires=[f"wire [{w-1}:0] count;", "wire tc;"],
                 ports=".count(count), .tc(tc)",
                 probe="{%d'b0, tc, count}" % (16 - w - 1),
                 probe_mask=(1 << (w + 1)) - 1, period=top + 1,
                 spec=(f"Write a Verilog module named `{name}`, a {w}-bit counter "
                       f"that wraps at {top} and asserts tc for one cycle when it "
                       f"reaches {top} (both registered).\n"),
                 golden_doc=f"{w}-bit counter wrap {top} + tc.")


def gen_threshold():
    for w in (4, 5, 6, 7, 8):
        for t in ((1 << (w - 1)), (1 << w) - (1 << (w - 2)), (1 << (w - 2)),
                  (1 << w) - 2, (1 << (w - 1)) + (1 << (w - 2))):
            name = f"thresh{w}_{t}"
            verilog = f"""// {w}-bit threshold detector: above = (x > {t}) (registered).
module {name} (
    input  wire clk, rst_n,
    input  wire [{w-1}:0] x,
    output reg  above
);
    always @(posedge clk) begin
        if (!rst_n) above <= 0;
        else        above <= (x > {w}'d{t});
    end
endmodule
"""
            golden = (f"        x = c & {(1<<w)-1}\n"
                      f"        val = 1 if x > {t} else 0")
            emit(name, "threshold", verilog, golden,
                 inputs=[["x", f"cnt[{w-1}:0]"]], outwires=["wire above;"],
                 ports=f".x(cnt[{w-1}:0]), .above(above)",
                 probe="{15'b0, above}", probe_mask=0x1, period=1 << w,
                 spec=(f"Write a Verilog module named `{name}` asserting `above` "
                       f"when a {w}-bit input exceeds {t} (registered).\n"),
                 golden_doc=f"{w}-bit threshold > {t}.")


def gen_running_minmax():
    """Sequential running min/max of the input stream since reset."""
    for w in (4, 5, 6, 7, 8, 10, 12):
        for kind in ("rmax", "rmin"):
            name = f"{kind}{w}b"
            if kind == "rmax":
                init = "0"
                cond = "x > acc"
                pyinit = "0"
                pycmp = "x if x > st else st"
            else:
                init = "{%d{1'b1}}" % w
                cond = "x < acc"
                pyinit = str((1 << w) - 1)
                pycmp = "x if x < st else st"
            verilog = f"""// {w}-bit running {('maximum' if kind=='rmax' else 'minimum')} since reset.
module {name} (
    input  wire clk, rst_n,
    input  wire [{w-1}:0] x,
    output reg  [{w-1}:0] acc
);
    always @(posedge clk) begin
        if (!rst_n) acc <= {init};
        else if ({cond}) acc <= x;
    end
endmodule
"""
            golden = (
                "        if c == 0:\n"
                f"            st = {pyinit}\n"
                f"        val = st\n"
                f"        x = c & {(1<<w)-1}\n"
                f"        st = {pycmp}"
            )
            emit(name, kind, verilog, golden,
                 inputs=[["x", f"cnt[{w-1}:0]"]],
                 outwires=[f"wire [{w-1}:0] acc;"],
                 ports=f".x(cnt[{w-1}:0]), .acc(acc)",
                 probe="{%d'b0, acc}" % (16 - w),
                 probe_mask=(1 << w) - 1, period=1 << w,
                 spec=(f"Write a Verilog module named `{name}` tracking the "
                       f"running {'maximum' if kind=='rmax' else 'minimum'} of a "
                       f"{w}-bit input stream since reset (registered).\n"),
                 golden_doc=f"{w}-bit running {kind}.")


def gen_shiftregs():
    """Serial-in shift registers (SIPO), both directions, varying width."""
    for w in range(3, 17):
        for direction in ("left", "right"):
            name = f"sipo_{direction[0]}{w}b"
            if direction == "left":
                op = f"{{q[{w-2}:0], sin}}"
                gshift = f"((st << 1) | sin) & {(1<<w)-1}"
            else:
                op = f"{{sin, q[{w-1}:1]}}"
                gshift = f"((st >> 1) | (sin << {w-1})) & {(1<<w)-1}"
            verilog = f"""// {w}-bit serial-in parallel-out shift register ({direction}).
module {name} (
    input  wire clk, rst_n,
    input  wire sin,
    output reg  [{w-1}:0] q
);
    always @(posedge clk) begin
        if (!rst_n) q <= 0;
        else        q <= {op};
    end
endmodule
"""
            golden = (
                "        if c == 0:\n"
                "            st = 0\n"
                f"        val = st & {(1<<min(w,16))-1}\n"
                f"        sin = c & 1\n"
                f"        st = {gshift}"
            )
            emit(name, "shiftreg", verilog, golden,
                 inputs=[["sin", "cnt[0]"]],
                 outwires=[f"wire [{w-1}:0] q;"],
                 ports=".sin(cnt[0]), .q(q)",
                 probe=("q" if w >= 16 else "{%d'b0, q}" % (16 - w)),
                 probe_mask=(1 << min(w, 16)) - 1, period=1 << min(w + 1, 16),
                 spec=(f"Write a Verilog module named `{name}`, a {w}-bit "
                       f"serial-in parallel-out shift register shifting "
                       f"{direction} (sin enters each cycle). 0 on !rst_n.\n"),
                 golden_doc=f"{w}-bit SIPO {direction}.")


def gen_demux():
    """1-to-n demultiplexer: routes a data bit to one of n outputs."""
    for n in (2, 4, 8, 16):
        sw = clog2(n)
        if n > 16:
            continue
        name = f"demux1to{n}"
        verilog = f"""// 1-to-{n} demux: out[sel] = din, others 0 (registered).
module {name} (
    input  wire clk, rst_n,
    input  wire din,
    input  wire [{sw-1}:0] sel,
    output reg  [{n-1}:0] out
);
    always @(posedge clk) begin
        if (!rst_n) out <= 0;
        else        out <= din ? ({n}'d1 << sel) : {n}'d0;
    end
endmodule
"""
        golden = (
            f"        din = c & 1\n"
            f"        sel = (c >> 1) & {(1<<sw)-1}\n"
            f"        val = (1 << sel) if din else 0"
        )
        emit(name, "demux", verilog, golden,
             inputs=[["din", "cnt[0]"], ["sel", f"cnt[{sw}:1]"]],
             outwires=[f"wire [{n-1}:0] out;"],
             ports=f".din(cnt[0]), .sel(cnt[{sw}:1]), .out(out)",
             probe=("out" if n >= 16 else "{%d'b0, out}" % (16 - n)),
             probe_mask=(1 << n) - 1 if n < 16 else 0xFFFF, period=1 << (sw + 1),
             spec=(f"Write a Verilog module named `{name}`, a 1-to-{n} "
                   f"demultiplexer routing din to out[sel] ({sw}-bit sel), other "
                   f"outputs 0 (registered).\n"),
             golden_doc=f"1-to-{n} demux.")


def gen_bitwise():
    """Two-input bitwise logic gates over w-bit words."""
    OPS = [("and", "a & b", "a & b"), ("or", "a | b", "a | b"),
           ("xor", "a ^ b", "a ^ b"), ("nand", "~(a & b)", "~(a & b)"),
           ("nor", "~(a | b)", "~(a | b)"), ("xnor", "~(a ^ b)", "~(a ^ b)")]
    for w in (2, 4, 6, 8):
        for op, vexpr, pexpr in OPS:
            name = f"bit{op}{w}b"
            verilog = f"""// {w}-bit bitwise {op.upper()} of two inputs (registered).
module {name} (
    input  wire clk, rst_n,
    input  wire [{w-1}:0] a,
    input  wire [{w-1}:0] b,
    output reg  [{w-1}:0] out
);
    always @(posedge clk) begin
        if (!rst_n) out <= 0;
        else        out <= {vexpr};
    end
endmodule
"""
            golden = (
                f"        a = c & {(1<<w)-1}\n"
                f"        b = (c >> {w}) & {(1<<w)-1}\n"
                f"        val = ({pexpr}) & {(1<<w)-1}"
            )
            emit(name, "bitwise", verilog, golden,
                 inputs=[["a", f"cnt[{w-1}:0]"], ["b", f"cnt[{2*w-1}:{w}]"]],
                 outwires=[f"wire [{w-1}:0] out;"],
                 ports=f".a(cnt[{w-1}:0]), .b(cnt[{2*w-1}:{w}]), .out(out)",
                 probe=pack("out", w), probe_mask=(1 << w) - 1, period=1 << (2 * w),
                 spec=(f"Write a Verilog module named `{name}` computing the "
                       f"bitwise {op.upper()} of two {w}-bit inputs a, b "
                       f"(registered).\n"),
                 golden_doc=f"{w}-bit bitwise {op}.")


GENERATORS = [
    gen_bitwise,
    gen_mod_counters, gen_width_counters, gen_updown_counters,
    gen_step_counters, gen_down_counters, gen_gray_counters,
    gen_ring_johnson, gen_terminal_counters, gen_shiftregs,
    gen_multipliers, gen_signed_mul, gen_addsub, gen_saturating_add,
    gen_shifters, gen_rotate_const, gen_comparators, gen_minmax,
    gen_window_cmp, gen_clamp, gen_threshold,
    gen_bitops, gen_negate, gen_abs, gen_swaps,
    gen_priority_encoders, gen_decoders, gen_muxes, gen_demux,
    gen_gray2bin, gen_alus, gen_lfsrs, gen_accumulators, gen_mac,
    gen_running_minmax,
]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--limit", type=int, default=0,
                    help="only emit the first N designs (smoke test)")
    args = ap.parse_args()

    for g in GENERATORS:
        g()

    if args.limit:
        del MANIFEST[args.limit:]

    # assign sel ids in catalog order
    for i, rec in enumerate(MANIFEST):
        rec["sel"] = i

    os.makedirs(RTL_LIB, exist_ok=True)
    with open(os.path.join(RTL_LIB, "manifest.json"), "w") as f:
        json.dump(MANIFEST, f, indent=1)

    # family histogram
    from collections import Counter
    hist = Counter(r["family"] for r in MANIFEST)
    print(f"Generated {len(MANIFEST)} designs into {RTL_LIB}")
    for fam, n in sorted(hist.items(), key=lambda x: -x[1]):
        print(f"  {fam:12s} {n}")
    print(f"\nmanifest.json written ({len(MANIFEST)} records).")


if __name__ == "__main__":
    main()

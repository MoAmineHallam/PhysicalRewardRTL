"""Explicit simulation contract shared by every newly compared policy."""
from __future__ import annotations

import re
import shutil
import subprocess
import tempfile
from pathlib import Path
import numpy as np
import oracle

N = 1024
LATENCY = 40
WARMUP = 8


def testbench(module, width):
    return f'''`timescale 1ns/1ps
module tb;
reg clk=0, rst_n=0; reg [{width-1}:0] x=0; wire [15:0] y;
reg [{width-1}:0] stim[0:{N-1}]; integer i,e;
{module} dut(.clk(clk),.rst_n(rst_n),.x(x),.y(y));
always #5 clk=~clk;
initial begin
 $readmemh("stim.hex",stim);
 for(e=0;e<2;e=e+1) begin
  @(negedge clk); rst_n=0; x=0;
  repeat(2) begin @(posedge clk); #1; $display("RESET %0d",y); end
  for(i=0;i<{N+LATENCY};i=i+1) begin
   @(negedge clk); rst_n=1;
   if(i<{N}) x=stim[i]; else x=0;
   @(posedge clk); #1; $display("TRACE %0d %0d",e,y);
  end
 end
 $finish;
end
endmodule
'''


def inspect_trace(stdout, golden):
    resets = re.findall(r"^RESET (\S+)\s*$", stdout, re.M)
    traces = [re.findall(rf"^TRACE {e} (\S+)\s*$", stdout, re.M) for e in (0, 1)]
    reset_ok = len(resets) == 4 and all(v == "0" for v in resets)
    valid_latencies = []
    for trace in traces:
        if len(trace) != N + LATENCY:
            valid_latencies.append([])
            continue
        values = np.array([int(x) if x.isdigit() and int(x) < 65536 else -1
                           for x in trace], dtype=np.int64)
        valid_latencies.append([lat for lat in range(LATENCY+1)
                                if np.array_equal(values[lat+WARMUP:lat+N], golden[WARMUP:N])])
    shared = sorted(set(valid_latencies[0]).intersection(valid_latencies[1]))
    return dict(correct=bool(reset_ok and shared), reset_zero=reset_ok,
                reset_values=resets, trace_lengths=[len(t) for t in traces],
                valid_latencies=shared, compared_per_episode=N-WARMUP)


def check(rtl, design, scratch=None):
    for tool in ("iverilog", "vvp"):
        if not shutil.which(tool):
            raise RuntimeError("Missing simulator: " + tool)
    reference, width = oracle.build_reference(design)
    with tempfile.TemporaryDirectory(prefix="cmp-sim-", dir=scratch) as tmp:
        wd = Path(tmp)
        (wd/"dut.sv").write_text(rtl, encoding="utf-8")
        (wd/"tb.sv").write_text(testbench(design, width), encoding="ascii")
        try:
            comp = subprocess.run(["iverilog", "-g2012", "-s", "tb", "-o", "sim.vvp",
                                   "dut.sv", "tb.sv"], cwd=wd, capture_output=True,
                                  text=True, timeout=60)
        except subprocess.TimeoutExpired:
            return dict(correct=False, reason="compile_timeout", checks=[])
        if comp.returncode:
            return dict(correct=False, reason="compile_failure", stderr=comp.stderr, checks=[])
        checks = []
        for seed in (1, 2):
            stimulus = oracle.gen_stimulus(N, width, seed)
            (wd/"stim.hex").write_text("\n".join(f"{int(v):x}" for v in stimulus)+"\n")
            try:
                sim = subprocess.run(["vvp", "sim.vvp"], cwd=wd, capture_output=True,
                                     text=True, timeout=60)
                value = inspect_trace(sim.stdout, reference(stimulus))
                value.update(seed=seed, returncode=sim.returncode,
                             stdout=sim.stdout, stderr=sim.stderr)
                value["correct"] = value["correct"] and sim.returncode == 0
            except subprocess.TimeoutExpired:
                value = dict(seed=seed, correct=False, reason="simulation_timeout")
            checks.append(value)
        shared = set(range(LATENCY+1))
        for value in checks:
            shared.intersection_update(value.get("valid_latencies", []))
        return dict(correct=all(v["correct"] for v in checks) and bool(shared),
                    checks=checks, valid_latencies=sorted(shared),
                    compile_stderr=comp.stderr)

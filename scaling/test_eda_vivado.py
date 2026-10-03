"""CPU checks for the parallel Vivado runner and its calibration rule (fake Vivado)."""

from __future__ import annotations

import json
import os
import stat
import tempfile
import unittest

from scaling import eda_vivado as ev

# Stand-in for run_ppa.py: same run_one signature and command line as the real one.
FAKE_RUN_PPA = '''
import json, os, subprocess, tempfile
def run_one(vivado, vfile, top, clk, period):
    with tempfile.TemporaryDirectory() as wd:
        outj = os.path.join(wd, "ppa.json")
        subprocess.run([vivado, "-mode", "batch", "-nojournal", "-nolog", "-source", "x.tcl",
                        "-tclargs", vfile, top, clk, str(period), outj], capture_output=True, text=True)
        if os.path.exists(outj):
            return json.load(open(outj))
        return {"compiled": 0, "error": ""}
'''

# Fake Vivado: fmax from the file length, failure if the RTL contains "BROKEN".
FAKE_VIVADO = '''#!/usr/bin/env python3
import json, os, sys
vfile, top, clk, period, outj = sys.argv[-5:]
rtl = open(vfile).read()
assert os.path.isdir(".") and not os.getcwd().startswith(os.path.dirname(vfile))
if "BROKEN" in rtl:
    sys.exit(0)
json.dump({"compiled": 1, "wns": 0.0, "fmax_mhz": 100.0 + len(rtl), "lut": len(rtl) % 7,
           "ff": 3, "dsp": 0, "bram": 0, "power_w": 0.1}, open(outj, "w"))
'''


def fake_root(tmp):
    root = os.path.join(tmp, "fpga")
    os.makedirs(root)
    with open(os.path.join(root, "run_ppa.py"), "w") as h:
        h.write(FAKE_RUN_PPA)
    with open(os.path.join(root, "ppa_synth.tcl"), "w") as h:
        h.write("# tcl\n")
    vivado = os.path.join(tmp, "vivado")
    with open(vivado, "w") as h:
        h.write(FAKE_VIVADO)
    os.chmod(vivado, os.stat(vivado).st_mode | stat.S_IEXEC)
    return root, vivado


def write_circuits(directory, bodies):
    os.makedirs(directory, exist_ok=True)
    for name, body in bodies.items():
        with open(os.path.join(directory, name + ".sv"), "w") as h:
            h.write(f"module {name}(input clk); {body} endmodule\n")


class EdaVivadoTest(unittest.TestCase):
    def test_parallel_run_is_resumable_and_records_failures(self):
        with tempfile.TemporaryDirectory() as tmp:
            root, vivado = fake_root(tmp)
            circ = os.path.join(tmp, "circ")
            write_circuits(circ, {"a": "x", "b": "xx", "c": "BROKEN"})
            out = os.path.join(tmp, "res", "ppa.jsonl")
            meta = ev.run_parallel(ev.list_circuits(circ), out, vivado, root, jobs=2)
            self.assertEqual((meta["n_run"], meta["n_ok"], meta["n_fail"]), (3, 2, 1))
            recs = ev.load_records(out)
            self.assertEqual(set(recs), {"a", "b", "c"})
            self.assertEqual(recs["c"]["compiled"], 0)
            self.assertIn("wall_s", recs["a"])
            meta2 = ev.run_parallel(ev.list_circuits(circ), out, vivado, root, jobs=2)
            self.assertEqual((meta2["n_run"], meta2["n_skipped"]), (0, 3))
            with open(out) as h:
                self.assertEqual(len(h.readlines()), 3)

    def test_sample_is_hash_ordered_and_limited_to_reference(self):
        ref = {f"m{i}": {"compiled": 1} for i in range(30)}
        available = [f"m{i}" for i in range(40)]
        s = ev.calibration_sample(ref, available, 20)
        self.assertEqual(len(s), 20)
        self.assertTrue(all(m in ref for m in s))
        self.assertEqual(s, ev.calibration_sample(ref, list(reversed(available)), 20))

    def test_compare_rule(self):
        mods = [f"m{i}" for i in range(20)]
        ref = {m: {"compiled": 1, "fmax_mhz": 100.0, "lut": 5, "ff": 3, "dsp": 0, "bram": 0} for m in mods}
        same = {m: dict(r) for m, r in ref.items()}
        self.assertTrue(ev.compare(ref, same, mods)["pass"])
        near = {m: dict(r, fmax_mhz=100.5) for m, r in ref.items()}
        self.assertTrue(ev.compare(ref, near, mods)["pass"])
        two_off = dict(same, m0=dict(ref["m0"], fmax_mhz=102.0), m1=dict(ref["m1"], fmax_mhz=98.0))
        self.assertTrue(ev.compare(ref, two_off, mods)["pass"])
        three_off = dict(two_off, m2=dict(ref["m2"], fmax_mhz=102.0))
        self.assertFalse(ev.compare(ref, three_off, mods)["pass"])
        big = dict(same, m0=dict(ref["m0"], fmax_mhz=104.0))
        self.assertFalse(ev.compare(ref, big, mods)["pass"])
        res = dict(same, m0=dict(ref["m0"], lut=6), m1=dict(ref["m1"], lut=6))
        self.assertFalse(ev.compare(ref, res, mods)["pass"])
        failed = dict(same, m0={"compiled": 0})
        self.assertFalse(ev.compare(ref, failed, mods)["pass"])
        missing = {m: r for m, r in same.items() if m != "m0"}
        self.assertFalse(ev.compare(ref, missing, mods)["pass"])


if __name__ == "__main__":
    unittest.main()

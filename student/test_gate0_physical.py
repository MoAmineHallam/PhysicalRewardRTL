"""CPU checks for Gate 0 collection and the frozen analysis."""

from __future__ import annotations

import json
import os
import tempfile
import unittest

from student import gate0_physical as gp


def write_run(work, run_id, designs):
    """designs: {design: (n, [(rtl_body, count), ...])}"""
    out = os.path.join(work, "runs", run_id)
    os.makedirs(out)
    manifest, summary = {}, {}
    for design, (n, cands) in designs.items():
        family = "fir" if design.startswith("fir") else "poly"
        summary[design] = {"n": n, "n_correct": sum(c for _b, c in cands),
                           "family": family, "regime": "interp"}
        for i, (body, count) in enumerate(cands):
            module = f"{run_id}__{design}__g{i}"
            with open(os.path.join(out, module + ".sv"), "w") as handle:
                handle.write(f"module {module}(input clk); {body} endmodule\n")
            manifest[module] = {"design": design, "family": family, "regime": "interp",
                                "count": count, "source_sha256": f"{run_id}{design}{i}"}
    json.dump(manifest, open(os.path.join(out, "fmax_manifest.json"), "w"))
    json.dump({run_id: summary}, open(os.path.join(out, "holdout_summary.json"), "w"))
    json.dump({}, open(os.path.join(out, "generation_config.json"), "w"))
    return {"id": run_id, "policy": run_id.split("_")[0], "arm": run_id.split("_")[1],
            "out_dir": out}


class PhysicalTest(unittest.TestCase):
    def test_collect_dedupes_and_analysis_matches_hand_computation(self):
        with tempfile.TemporaryDirectory() as work:
            gp.WORK = work
            fast, slow = "assign y = a;", "assign   y = b;"
            runs = [
                write_run(work, "p_fp16", {"fir1": (4, [(fast, 2), (slow, 2)]),
                                           "poly1": (4, [(fast, 4)])}),
                write_run(work, "p_gptq4", {"fir1": (4, [(slow, 3)]),
                                            "poly1": (4, [(fast + " ", 1)])}),
            ]
            json.dump({"runs": runs}, open(os.path.join(work, "plan.json"), "w"))
            vivado = os.path.join(work, "vivado")
            gp.main(["collect", "--out", vivado])
            cmap = json.load(open(os.path.join(vivado, "candidate_map.json")))
            # fir1 fast, fir1 slow, poly1 fast (whitespace variant merged)
            self.assertEqual(len(cmap), 3)
            with open(os.path.join(vivado, "ppa.jsonl"), "w") as handle:
                for stem, entry in cmap.items():
                    is_fast = "y = a" in open(os.path.join(vivado, stem + ".sv")).read()
                    handle.write(json.dumps({"module": stem, "compiled": 1,
                                             "fmax_mhz": 200.0 if is_fast else 50.0}) + "\n")
            gp.main(["analyze", "--vivado", vivado])
            report = json.load(open(os.path.join(vivado, "gate0_analysis.json")))
            (c,) = report["contrasts"]
            # fir1: ref mu = (2*200+2*50)/4 = 125, arm mu = 50; poly1: 200 vs 200
            self.assertAlmostEqual(c["mu"]["diff"], (-75 + 0) / 2)
            self.assertAlmostEqual(c["mu"]["relative_loss"], 37.5 / 162.5)
            # F: fir1 ref 125 arm 37.5; poly1 ref 200 arm 50
            self.assertAlmostEqual(c["F"]["diff"], ((37.5 - 125) + (50 - 200)) / 2)
            self.assertAlmostEqual(c["q"]["diff"], ((0.75 - 1.0) + (0.25 - 1.0)) / 2)
            lo, hi = c["mu"]["ci"]
            self.assertLessEqual(lo, c["mu"]["diff"])
            self.assertGreaterEqual(hi, c["mu"]["diff"])
            # fir1 majority tie broken deterministically; poly1 arm all on the majority form
            self.assertIsNotNone(c["off_fp16_majority_share"])
            # one design per stratum: the stratified interval has no spread, so A;
            # the unstratified sensitivity interval shows the real uncertainty
            self.assertEqual(report["decision"]["outcome"], "A")
            self.assertEqual(c["mu"]["ci"], [-37.5, -37.5])
            u_lo, u_hi = c["mu"]["ci_unstratified"]
            self.assertLess(u_lo, u_hi)

    def test_missing_vivado_result_stops(self):
        with tempfile.TemporaryDirectory() as work:
            gp.WORK = work
            runs = [write_run(work, "p_fp16", {"fir1": (2, [("assign y = a;", 1)])})]
            json.dump({"runs": runs}, open(os.path.join(work, "plan.json"), "w"))
            vivado = os.path.join(work, "vivado")
            gp.main(["collect", "--out", vivado])
            open(os.path.join(vivado, "ppa.jsonl"), "w").close()
            with self.assertRaises(SystemExit):
                gp.main(["analyze", "--vivado", vivado])

    def test_decision_rule(self):
        def r(run, arm, ci_hi, loss, q_ref=0.8, q_arm=0.8):
            return {"run": run, "arm": arm, "mu": {"ci": [-50, ci_hi], "relative_loss": loss},
                    "q": {"ref": q_ref, "arm": q_arm}}
        self.assertEqual(gp.decide([r("stu_gptq4", "gptq4", -1, 0.2)])["outcome"], "A")
        self.assertTrue(gp.decide([r("stu_rtn3", "rtn3", -1, 0.3),
                                   r("stu_gptq4", "gptq4", 5, 0.01)])["outcome"].startswith("A-prime"))
        self.assertEqual(gp.decide([r("stu_gptq4", "gptq4", 5, 0.01)])["outcome"], "B")
        self.assertEqual(gp.decide([r("stu_gptq4", "gptq4", 5, 0.07)])["outcome"], "inconclusive")
        self.assertTrue(gp.decide([r("stu_gptq4", "gptq4", 5, 0.01, 0.8, 0.3)])
                        ["C_student_gptq4_correctness_collapse"])

    def test_bootstrap_degenerate_and_ordered(self):
        lo, hi = gp.stratified_bootstrap({"a": 1.0, "b": 1.0}, {"a": "s", "b": "s"}, n=200)
        self.assertEqual((lo, hi), (1.0, 1.0))
        lo, hi = gp.stratified_bootstrap({"a": -3.0, "b": 1.0, "c": 2.0},
                                         {"a": "s", "b": "s", "c": "t"}, n=500)
        self.assertLessEqual(lo, hi)


if __name__ == "__main__":
    unittest.main()

"""CPU checks for the K1 queue, learning-rate selection and decision rule."""

from __future__ import annotations

import json
import os
import random
import tempfile
import unittest

from scaling import k1
from scaling import sft


def corpus_rows():
    rows = []
    for fam, n_designs in (("fir", 20), ("poly", 10), ("med", 2)):
        for i in range(n_designs):
            for style in ("ref", "pipe"):
                rows.append({"design": f"{fam}{i}", "family": fam, "style": style,
                             "prompt": "p", "completion": "c"})
    return rows


def row(correct, f, family="fir", regime="interp", n=24):
    return {"n": n, "correct": correct, "sum_cF": correct * f, "family": family,
            "regime": regime, "forms": ({"k": correct} if correct else {})}


def make_table(spec, designs=12, seed=0):
    """spec[size] = (q, f, seed_noise) -> table keyed by run id, plus a plan with runs."""
    rng = random.Random(seed)
    table, runs = {}, []
    for size, (q, f, noise) in spec.items():
        for s in k1.SEEDS[size]:
            rid = f"k1_{k1.tag(size)}_s{s}"
            runs.append({"id": rid, "size": size, "seed": s})
            rows = {}
            for d in range(designs):
                fam = "fir" if d % 2 else "poly"
                qq = min(1.0, max(0.0, q + rng.uniform(-noise, noise)))
                c = round(24 * qq)
                rows[f"d{d}"] = row(c, f + rng.uniform(-noise * 50, noise * 50), family=fam)
            table[rid] = rows
    return {"runs": runs}, table


class K1Test(unittest.TestCase):
    def test_validation_split_holds_out_whole_designs_deterministically(self):
        rows = corpus_rows()
        train, val, held = k1.split_validation(rows)
        self.assertEqual(held, k1.split_validation(list(reversed(rows)))[2])
        self.assertFalse({r["design"] for r in train} & {r["design"] for r in val})
        fams = {r["family"] for r in val}
        self.assertEqual(fams, {"fir", "poly"})  # med has fewer than 3 designs
        self.assertEqual(sum(1 for d in held if d.startswith("fir")), 3)
        self.assertEqual(len(train) + len(val), len(rows))

    def test_leak_check(self):
        with tempfile.TemporaryDirectory() as tmp:
            split = os.path.join(tmp, "s.json")
            json.dump({"designs": [{"design": "zzz", "family": "fir"}]}, open(split, "w"))
            k1.leak_check(corpus_rows(), [split])
            json.dump({"designs": [{"design": "fir3", "family": "fir"}]}, open(split, "w"))
            with self.assertRaises(SystemExit):
                k1.leak_check(corpus_rows(), [split])

    def test_job_graph(self):
        jobs = k1.build_jobs("/w", ["fir", "poly"])
        stages = [j["stage"] for j in jobs]
        self.assertEqual(stages.count("sweep"), 12)
        self.assertEqual(stages.count("final"), 10)
        self.assertEqual(stages.count("eval"), 10)
        self.assertEqual(len({j["id"] for j in jobs}), len(jobs))
        self.assertEqual(jobs[0]["size"], "7B")
        for j in jobs:
            if j["stage"] == "eval":
                self.assertRegex(j["id"], r"^[a-z][a-z0-9_]*$")

    def test_lr_selection_and_dependencies(self):
        with tempfile.TemporaryDirectory() as work:
            k1.WORK = work
            plan = {"jobs": k1.build_jobs(work, ["fir"])}
            final = next(j for j in plan["jobs"] if j["stage"] == "final")
            ev = next(j for j in plan["jobs"] if j["stage"] == "eval"
                      and j["size"] == final["size"] and j["seed"] == final["seed"])
            self.assertEqual(k1.dependency_state(final, plan), "waiting")
            self.assertIsNone(k1.select_learning_rates(plan))
            nll = {5e-5: 0.30, 1e-4: 0.20, 2e-4: 0.20}
            for j in plan["jobs"]:
                if j["stage"] == "sweep":
                    os.makedirs(j["out_dir"])
                    json.dump({"nll_per_token": nll[j["lr"]]}, open(os.path.join(j["out_dir"], j["marker"]), "w"))
            choice = k1.select_learning_rates(plan)
            self.assertEqual(set(choice["lr"].values()), {1e-4})  # tie -> smaller lr
            self.assertEqual(k1.dependency_state(final, plan), "ready")
            self.assertEqual(k1.dependency_state(ev, plan), "waiting")
            os.makedirs(os.path.join(work, "failures"))
            json.dump({}, open(os.path.join(work, "failures", f"{final['id']}-x.json"), "w"))
            self.assertEqual(k1.dependency_state(ev, plan), "blocked")
            # a second selection never overwrites the first
            for j in plan["jobs"]:
                if j["stage"] == "sweep":
                    json.dump({"nll_per_token": 0.0 if j["lr"] == 5e-5 else 1.0},
                              open(os.path.join(j["out_dir"], j["marker"]), "w"))
            self.assertEqual(set(k1.select_learning_rates(plan)["lr"].values()), {1e-4})

    def test_trend_rule(self):
        sizes = ["a", "b", "c", "d"]
        cis = {"d - a": [1, 5], "b - a": [-1, 2], "c - b": [-2, 1], "d - c": [0.5, 3]}
        self.assertTrue(k1.trend_holds({"a": 1, "b": 2, "c": 3, "d": 4}, cis, sizes))
        self.assertTrue(k1.trend_holds({"a": 1, "b": 2, "c": 1.5, "d": 4}, cis, sizes))
        self.assertFalse(k1.trend_holds({"a": 1, "b": 0.5, "c": 0.4, "d": 4}, cis, sizes))
        self.assertFalse(k1.trend_holds({"a": 1, "b": 2, "c": 3, "d": 4}, dict(cis, **{"d - a": [-1, 5]}), sizes))
        bad = dict(cis, **{"c - b": [-3, -1]})
        self.assertFalse(k1.trend_holds({"a": 1, "b": 2, "c": 1.5, "d": 4}, bad, sizes))

    def test_decisions_on_synthetic_tables(self):
        k1.RESAMPLES = 400
        trend_plan, trend = make_table({"0.5B": (0.3, 100, 0.02), "1.5B": (0.5, 100, 0.02),
                                        "3B": (0.7, 100, 0.02), "7B": (0.9, 100, 0.02)})
        res = k1.analyze_table(trend_plan, trend)
        self.assertEqual(res["decision"]["outcome"], "trend")
        self.assertTrue(res["decision"]["mu_flat_descriptive"])
        sat_plan, sat = make_table({s: (0.99, 100, 0.0) for s in ("0.5B", "1.5B", "3B", "7B")})
        self.assertEqual(k1.analyze_table(sat_plan, sat)["decision"]["outcome"], "saturated")
        flat_plan, flat = make_table({s: (0.5, 100, 0.3) for s in ("0.5B", "1.5B", "3B", "7B")}, seed=3)
        self.assertIn(k1.analyze_table(flat_plan, flat)["decision"]["outcome"],
                      ("no signal", "inconclusive"))

    def test_seeded_training_arguments(self):
        seen = {}
        def original(**kwargs):
            seen.update(kwargs)
            return kwargs
        make = sft.seeded_training_arguments(original, 7)
        make(output_dir="x", seed=42)
        self.assertEqual((seen["seed"], seen["data_seed"], seen["output_dir"]), (7, 7, "x"))


if __name__ == "__main__":
    unittest.main()

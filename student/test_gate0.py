"""CPU checks for the Gate 0 launcher: run matrix, GPU assignment and locking."""

from __future__ import annotations

import os
import tempfile
import unittest

from student import gate0


class Gate0PlanTest(unittest.TestCase):
    def setUp(self):
        self.runs = gate0.build_runs(gate0.POLICIES, "/root", "/w/split.json", "/w/keep.json",
                                     "/w", {"distill_corpus.jsonl": "/c/d.jsonl",
                                            "sft_corpus_v5.jsonl": "/c/v5.jsonl"})
        self.by_id = {r["id"]: r for r in self.runs}

    def test_run_matrix(self):
        self.assertEqual(len(self.runs), 8 + 5 + 5)
        self.assertEqual(len(self.by_id), len(self.runs))
        for run in self.runs:
            args = run["args"]
            self.assertEqual(args[args.index("--n") + 1], "24")
            self.assertEqual(args[args.index("--generation-seed") + 1], "1001")
            self.assertEqual(args[args.index("--policy") + 1], run["id"])

    def test_arm_arguments(self):
        trimmed = self.by_id["stu_gptq4t"]["args"]
        self.assertIn("/w/keep.json", trimmed)
        self.assertEqual(trimmed[trimmed.index("--method") + 1], "gptq")
        self.assertEqual(trimmed[trimmed.index("--calib") + 1], "/c/d.jsonl")
        fp16 = self.by_id["qsft_fp16"]["args"]
        self.assertNotIn("--method", fp16)
        self.assertNotIn("--keep-vocab", fp16)
        rtn = self.by_id["qgrpo_rtn3"]["args"]
        self.assertEqual(rtn[rtn.index("--bits") + 1], "3")
        self.assertNotIn("--calib", rtn)
        fam = self.by_id["qsft_gptq3"]["args"]
        self.assertEqual(fam[fam.index("--families") + 1: fam.index("--out-dir")],
                         ["fir", "firr", "poly"])
        self.assertEqual(fam[fam.index("--calib") + 1], "/c/v5.jsonl")

    def test_workers(self):
        workers = {r["id"]: r["worker"] for r in self.runs}
        self.assertTrue(all(w == "v100a-0" for i, w in workers.items() if i.startswith("qsft")))
        self.assertTrue(all(w == "v100a-1" for i, w in workers.items() if i.startswith("qgrpo")))
        student = [w for i, w in workers.items() if i.startswith("stu")]
        self.assertEqual(student.count("v100b-0"), 4)
        self.assertEqual(student.count("v100b-1"), 4)

    def test_lock_is_exclusive_and_stale_locks_clear(self):
        with tempfile.TemporaryDirectory() as tmp:
            lock = os.path.join(tmp, "run.lock")
            self.assertTrue(gate0.acquire(lock))
            self.assertFalse(gate0.acquire(lock))
            host = open(lock).read().split()[0]
            with open(lock, "w") as handle:
                handle.write(f"{host} 999999999 20260101T000000Z\n")
            self.assertTrue(gate0.acquire(lock))

    def test_unknown_arm_rejected(self):
        with self.assertRaises(ValueError):
            gate0.arm_args("int4")


if __name__ == "__main__":
    unittest.main()

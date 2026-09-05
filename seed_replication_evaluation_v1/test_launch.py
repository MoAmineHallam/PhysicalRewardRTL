import unittest
import json
import tempfile
from pathlib import Path
from seed_replication_evaluation_v1 import launch


class ContractTests(unittest.TestCase):
    def test_all_four_budgets(self):
        for run, n, seed in [("rf_s3", 24, 103), ("rf_s4", 24, 104),
                             ("correctness_s2", 48, 102), ("correctness_s3", 48, 103)]:
            command = launch.command(run)
            self.assertEqual(command[command.index("--n") + 1], str(n))
            self.assertEqual(command[command.index("--generation-seed") + 1], str(seed))
            self.assertIn("upd_276", command[command.index("--adapter") + 1])
            self.assertEqual("--score-rf" in command, run.startswith("rf_"))

    def test_unknown_run_rejected(self):
        with self.assertRaises(RuntimeError):
            launch.command("sft")

    def test_complete_split(self):
        split = launch.evaluator.load_split(str(launch.ROOT / "sealed_split.json"))
        self.assertEqual(len(split), 20)

    def test_dependencies_present(self):
        self.assertEqual(len(launch.hashes()), len(launch.FILES))

    def fixture(self, directory):
        split = launch.evaluator.load_split(str(launch.ROOT / "sealed_split.json"))
        summary = {"rf_s3": {r["design"]: dict(n=24, n_correct=0, n_compiled=0,
            n_distinct_correct=0, **{k: r[k] for k in ("family", "regime", "max_tokens")}) for r in split}}
        generation = dict(policy="rf_s3", training_seed=3, generation_seed=103,
            n_per_design=24, temperature=1.0, gen_batch=4, oracle_n=1024,
            oracle_seeds=[1, 2], score_rf=True,
            sealed_split_sha256=launch.evaluator.sha256_file(str(launch.ROOT / "sealed_split.json")),
            eval_script_sha256=launch.evaluator.sha256_file(str(launch.ROOT / "eval_sealed.py")))
        for name, data in [("fmax_manifest.json", {}), ("holdout_summary.json", summary),
                           ("generation_config.json", generation)]:
            (directory / name).write_text(json.dumps(data))
        return summary

    def test_zero_correct_designs_retained(self):
        with tempfile.TemporaryDirectory() as temporary:
            directory = Path(temporary)
            self.fixture(directory)
            result = launch.validate_output("rf_s3", directory, check_adapter=False)
            self.assertEqual(result["n_draws"], 480)
            self.assertEqual(result["n_emitted"], 0)

    def test_missing_design_rejected(self):
        with tempfile.TemporaryDirectory() as temporary:
            directory = Path(temporary)
            summary = self.fixture(directory)
            summary["rf_s3"].pop(next(iter(summary["rf_s3"])))
            (directory / "holdout_summary.json").write_text(json.dumps(summary))
            with self.assertRaisesRegex(RuntimeError, "Incomplete design"):
                launch.validate_output("rf_s3", directory, check_adapter=False)

    def test_lost_multiplicity_rejected(self):
        with tempfile.TemporaryDirectory() as temporary:
            directory = Path(temporary)
            summary = self.fixture(directory)
            first = next(iter(summary["rf_s3"].values()))
            first.update(n_correct=1, n_compiled=1)
            (directory / "holdout_summary.json").write_text(json.dumps(summary))
            with self.assertRaisesRegex(RuntimeError, "Multiplicity"):
                launch.validate_output("rf_s3", directory, check_adapter=False)


if __name__ == "__main__":
    unittest.main()

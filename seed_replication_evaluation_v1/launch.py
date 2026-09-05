"""Hash-frozen, completion-gated endpoint generation on idle assigned V100s."""
import argparse
import hashlib
import json
import os
import platform
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
sys.path.insert(0, str(ROOT))
import eval_sealed as evaluator

FILES = ["seed_replication_evaluation_v1/launch.py",
         "seed_replication_evaluation_v1/PROTOCOL.md",
         "seed_replication_evaluation_v1/test_launch.py",
         "eval_sealed.py", "grpo_oracle.py", "oracle.py", "build_dataset.py",
         "canonicalize.py", "gen_sft_corpus.py", "gen_accelerator_catalog.py",
         "sealed_split.json", "seed_replication_extension_v1/config.json",
         "seed_replication_extension_v1/PROTOCOL.md",
         "seed_replication_extension_v1/validate.py",
         "seed_replication_extension_v2/config.json",
         "seed_replication_extension_v2/PROTOCOL.md",
         "seed_replication_extension_v2/validate.py"]


def now():
    return datetime.now(timezone.utc).isoformat()


def write(path, data, exclusive=False):
    with path.open("x" if exclusive else "w", encoding="utf-8", newline="\n") as f:
        json.dump(data, f, indent=2)
        f.write("\n")


def check(condition, message):
    if not condition:
        raise RuntimeError(message)


def hashes():
    return {p: evaluator.sha256_file(str(ROOT / p)) for p in FILES}


def verify():
    frozen = json.loads((HERE / "freeze.json").read_text())
    check(frozen["files"] == hashes(), "Frozen evaluation dependencies changed")
    return evaluator.sha256_file(str(HERE / "freeze.json"))


def settings(run_id):
    config = json.loads((ROOT / "seed_replication_extension_v2/config.json").read_text())
    found = [r for r in config["runs"] if r["run_id"] == run_id]
    check(len(found) == 1, "Unknown run id")
    run = found[0]
    parent = json.loads((ROOT / "seed_replication_extension_v1/config.json").read_text())
    contract = parent["prospective_evaluation_contract_not_launched_here"]
    n = contract["rf_samples_per_design_per_seed" if run["reward"] == "rf_struct"
                 else "correctness_samples_per_design_per_seed"]
    return config, run, n


def command(run_id):
    config, run, n = settings(run_id)
    return [config["remote_execution"]["python"], "-u", str(ROOT / "eval_sealed.py"),
            "--base", config["remote_execution"]["base_model"], "--adapter",
            str(ROOT / run["output_dir"] / "upd_276"), "--policy", run_id,
            "--training-seed", str(run["training_seed"]), "--generation-seed",
            str(100 + run["training_seed"]), "--n", str(n), "--temp", "1.0",
            "--gen-batch", "4", "--n-stim", "1024", "--out-dir",
            str(HERE / "outputs" / run_id)] + (["--score-rf"] if run["reward"] == "rf_struct" else [])


def idle(config, run):
    check(platform.node().split(".")[0] == run["hostname"], "Wrong execution host")
    from seed_replication_extension_v2 import validate
    for index in range(2):
        validate.base.gpu_snapshot(run["physical_gpu"], config["remote_execution"]["gpu_idle"])
        if index == 0:
            time.sleep(2)


def validate_output(run_id, directory=None, check_adapter=True):
    config, run, n = settings(run_id)
    directory = directory or HERE / "outputs" / run_id
    manifest = json.loads((directory / "fmax_manifest.json").read_text())
    summary = json.loads((directory / "holdout_summary.json").read_text())
    generation = json.loads((directory / "generation_config.json").read_text())
    split = evaluator.load_split(str(ROOT / "sealed_split.json"))
    check(set(summary) == {run_id}, "Summary policy mismatch")
    check(set(summary[run_id]) == {r["design"] for r in split}, "Incomplete design coverage")
    for key, expected in {"policy": run_id, "training_seed": run["training_seed"],
            "generation_seed": 100 + run["training_seed"], "n_per_design": n,
            "temperature": 1.0, "gen_batch": 4, "oracle_n": 1024,
            "oracle_seeds": [1, 2], "score_rf": run["reward"] == "rf_struct",
            "sealed_split_sha256": evaluator.sha256_file(str(ROOT / "sealed_split.json")),
            "eval_script_sha256": evaluator.sha256_file(str(ROOT / "eval_sealed.py"))}.items():
        check(generation.get(key) == expected, f"Generation config mismatch: {key}")
    check(set(p.stem for p in directory.glob("*.sv")) == set(manifest), "RTL file inventory mismatch")
    for module, row in manifest.items():
        check(row["design"] in summary[run_id], "Unknown candidate design")
        check(module.startswith(run_id + "__" + row["design"] + "__g"), "Module identity mismatch")
        check(row["policy"] == run_id and row["n"] == n and type(row["count"]) is int
              and 0 < row["count"] <= n, "Candidate accounting mismatch")
        check(row["generation_seed"] == 100 + run["training_seed"] and
              row["oracle_seeds"] == [1, 2] and row["oracle_n"] == 1024, "Candidate oracle mismatch")
        check(evaluator.sha256_file(str(directory / (module + ".sv"))) == row["emitted_sha256"],
              "Emitted RTL changed")
    for split_row in split:
        row = summary[run_id][split_row["design"]]
        selected = [r for r in manifest.values() if r["design"] == split_row["design"]]
        check(row["n"] == n and 0 <= row["n_correct"] <= row["n_compiled"] <= n,
              "Design denominator/functional count mismatch")
        check(sum(r["count"] for r in selected) == row["n_correct"] and
              len(selected) == row["n_distinct_correct"], "Multiplicity mismatch")
        for key in ("family", "regime", "max_tokens"):
            check(row[key] == split_row[key], f"Split metadata mismatch: {key}")
    if check_adapter:
        adapter = ROOT / run["output_dir"] / "upd_276"
        check(generation["adapter"] == str(adapter) and
              generation["adapter_sha256"] == evaluator.sha256_dir(str(adapter)), "Adapter identity changed")
    return {"n_designs": len(split), "n_draws": len(split) * n, "n_emitted": len(manifest),
            "files": {p.name: evaluator.sha256_file(str(p)) for p in sorted(directory.iterdir()) if p.is_file()}}


def worker(run_id):
    state = HERE / "state" / run_id
    status = {"run_id": run_id, "started_utc": now(), "status": "PREFLIGHT"}
    try:
        status["freeze_sha256"] = verify()
        write(state / "status.json", status)
        config, run, _ = settings(run_id)
        check(ROOT.as_posix() == config["remote_execution"]["repo_root"], "Wrong remote worktree")
        subprocess.run([sys.executable, "seed_replication_extension_v2/validate.py", "--mode", "completed",
            "--run-id", run_id, "--out", str(state / "training_completion_audit.json")], cwd=ROOT, check=True)
        from transformers import GenerationConfig
        gc = GenerationConfig.from_pretrained(config["remote_execution"]["base_model"])
        check(gc.top_p == 1.0, "Inherited top-p differs from frozen contract")
        write(state / "inherited_generation_config.json", gc.to_dict(), exclusive=True)
        idle(config, run)
        verify()
        status.update(status="RUNNING", command=command(run_id), generation_started_utc=now())
        write(state / "status.json", status)
        subprocess.run(command(run_id), cwd=ROOT, check=True)
        verify()
        audit = validate_output(run_id)
        write(state / "generation_completion_audit.json", audit, exclusive=True)
        status.update(status="COMPLETE", completed_utc=now(), **{k: audit[k] for k in ("n_designs", "n_draws", "n_emitted")})
    except Exception as exc:
        status.update(status="FAILED", failed_utc=now(), error=f"{type(exc).__name__}: {exc}")
        raise
    finally:
        write(state / "status.json", status)


def launch(run_id):
    verify()
    config, run, _ = settings(run_id)
    idle(config, run)
    check(not (HERE / "outputs" / run_id).exists(), "Evaluation output already exists")
    state = HERE / "state" / run_id
    state.mkdir(parents=True, exist_ok=False)
    env = dict(os.environ, CUDA_VISIBLE_DEVICES=str(run["physical_gpu"]),
               PYTHONNOUSERSITE="1", HF_HUB_OFFLINE="1", TOKENIZERS_PARALLELISM="false",
               PATH=config["remote_execution"]["environment_bin"] + os.pathsep + os.environ["PATH"])
    with (state / "stdout.log").open("x") as log:
        process = subprocess.Popen([config["remote_execution"]["python"], "-u", str(__file__),
            "--work", run_id], cwd=ROOT, env=env, stdin=subprocess.DEVNULL,
            stdout=log, stderr=subprocess.STDOUT, start_new_session=True)
    write(state / "launcher.json", {"pid": process.pid, "launched_utc": now(), "run_id": run_id}, exclusive=True)
    print(f"Started completion-gated worker: {run_id} PID {process.pid}")


def main():
    parser = argparse.ArgumentParser()
    modes = parser.add_mutually_exclusive_group(required=True)
    modes.add_argument("--freeze", action="store_true")
    modes.add_argument("--check", action="store_true")
    modes.add_argument("--launch")
    modes.add_argument("--work")
    modes.add_argument("--validate-output")
    args = parser.parse_args()
    if args.freeze:
        check(not (HERE / "state").exists() and not (HERE / "outputs").exists(), "Cannot freeze after launch")
        write(HERE / "freeze.json", {"frozen_utc": now(), "hash_basis": "SHA256 LF-normalized text",
              "files": hashes()}, exclusive=True)
    elif args.check:
        print("PASS: frozen evaluation package " + verify())
    elif args.launch:
        launch(args.launch)
    elif args.work:
        worker(args.work)
    else:
        verify()
        print(json.dumps(validate_output(args.validate_output), indent=2))


if __name__ == "__main__":
    main()

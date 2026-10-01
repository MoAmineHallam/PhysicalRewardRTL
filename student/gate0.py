#!/usr/bin/env python3
"""Gate 0 orchestration on the two V100 boxes (shared filesystem).

    python student/gate0.py prepare                 # once, on V100a
    python student/gate0.py work --worker v100a-0   # one per GPU, on its box
    python student/gate0.py status                  # anywhere

``prepare`` selects the previous-project checkout whose evaluator files match
the frozen GitHub version, runs the oracle self-check, draws the development
split, freezes the kept vocabulary, and writes ``gate0/plan.json``.  Workers
only read that plan.  Each run is one ``eval_compressed.py`` invocation in a
fresh directory; a failed run is moved aside, never resumed or merged.
"""

from __future__ import annotations

import argparse
import datetime as _dt
import hashlib
import json
import os
import socket
import subprocess
import sys
from typing import Dict, List, Optional, Sequence

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(HERE)
WORK = os.path.join(REPO, "gate0")
EVAL = os.path.join(HERE, "eval_compressed.py")

MAS = "/zeng_gk/Amine/mas"
CANDIDATE_ROOTS = [f"{MAS}/fpga", f"{MAS}/fpga-v100-v2", f"{MAS}/fpga-comparison-v3-20260915"]
QWEN15 = f"{MAS}/models/Qwen/Qwen2___5-Coder-1___5B"
QWEN7 = f"{MAS}/qwen2.5-coder-7b-instruct"

# sha256 of the previous project's files at GitHub commit 40acc78
# (moaminehallam/fpga, branch claude/amazing-hopper-ytsbvr).
EXPECTED = {
    "eval_sealed.py": "17c889bdd3062d3ace7e64f1a054b2dc5482ee4eb8aeb98f8b7688c533c4769a",
    "oracle.py": "afd3138ff30cee45a02f3c841c445f29dfda3fea44f3c4e2401d0be2ee4de8c5",
    "grpo_oracle.py": "808834839a44d5daf7a99e73d13824ed2d3179c05b8ed264e51d7d261b258020",
    "build_dataset.py": "b6796a2c08880ecc1f7b84b9a8196a1bfb74a161f50f7648b18aad318579c9c6",
    "gen_sealed_split.py": "a4e1f1a652a33753115ebad54e1f6151b92cb0dc339089f3db13c9b5a6e38b9c",
    "gen_sft_corpus.py": "4e12315bbd27700efd2db07f011543eef2870ab49e7a1518e39a3e6fb6c429e0",
    "gen_accelerator_catalog.py": "2226fae084baf358b3002a669fb66c2ce497815335aaba3b535c146b12e8f7ad",
    "canonicalize.py": "36577ed72d1e64f32bd950f6887e59c7393614c60dedb6c1ff89ae6ceb7aae9f",
    "score_candidate.py": "6f03ad03a6b3584979d1b8311d03f79b983769be1d32ecb22344e87339f1e47c",
}

# Each policy is evaluated only on the families it was trained on (fixed from
# the training records before any Gate 0 draw): the Qwen-7B pair saw
# fir/firr/poly only; the 1.5B student scores 0% on median at FP16.
POLICIES: Dict[str, dict] = {
    "stu": {"base": QWEN15, "adapter": f"{MAS}/fpga/student_v1_out", "box": "v100b",
            "families": ["fir", "firr", "poly", "iir"], "calib": ["distill_corpus.jsonl"],
            "arms": ["fp16", "rtn8", "rtn4", "rtn3", "gptq4", "gptq3", "fp16t", "gptq4t"]},
    "qsft": {"base": QWEN7, "adapter": f"{MAS}/fpga/sft_qwen_out", "box": "v100a",
             "families": ["fir", "firr", "poly"], "calib": ["sft_corpus_v5.jsonl"],
             "arms": ["fp16", "rtn4", "rtn3", "gptq4", "gptq3"]},
    "qgrpo": {"base": QWEN7, "adapter": f"{MAS}/fpga/grpo_qwen", "box": "v100a",
              "families": ["fir", "firr", "poly"], "calib": ["sft_corpus_v5.jsonl"],
              "arms": ["fp16", "rtn4", "rtn3", "gptq4", "gptq3"]},
}
KEEP_VOCAB_CORPORA = ["sft_corpus.jsonl", "sft_corpus_v5.jsonl", "distill_corpus.jsonl"]
GENERATION_SEED = 1001
N_DRAWS = 24
BOXES = {"v100a": 2, "v100b": 2}


def sha256_file(path: str) -> str:
    with open(path, "rb") as handle:
        return hashlib.sha256(handle.read()).hexdigest()


def now() -> str:
    return _dt.datetime.now(_dt.timezone.utc).strftime("%Y%m%dT%H%M%SZ")


def arm_args(arm: str) -> List[str]:
    """Translate an arm name into eval_compressed.py arguments."""
    trimmed = arm.endswith("t")
    core = arm[:-1] if trimmed else arm
    if core == "fp16":
        args = ["--bits", "16"]
    elif core.startswith("rtn"):
        args = ["--bits", core[3:], "--method", "rtn"]
    elif core.startswith("gptq"):
        args = ["--bits", core[4:], "--method", "gptq"]
    else:
        raise ValueError(f"unknown arm {arm}")
    return args + (["--keep-vocab", "@KEEP"] if trimmed else [])


def assign_workers(policies: Dict[str, dict]) -> Dict[tuple, str]:
    """One policy per GPU when a box holds as many policies as GPUs, else round robin."""
    workers = {}
    for box, n_gpu in BOXES.items():
        names = [name for name, spec in policies.items() if spec["box"] == box]
        if len(names) == n_gpu:
            for gpu, name in enumerate(names):
                for arm in policies[name]["arms"]:
                    workers[(name, arm)] = f"{box}-{gpu}"
        else:
            index = 0
            for name in names:
                for arm in policies[name]["arms"]:
                    workers[(name, arm)] = f"{box}-{index % n_gpu}"
                    index += 1
    return workers


def build_runs(policies: Dict[str, dict], root: str, split: str, keep: str,
               work: str, corpus_paths: Dict[str, str]) -> List[dict]:
    workers = assign_workers(policies)
    runs = []
    for name, spec in policies.items():
        for arm in spec["arms"]:
            run_id = f"{name}_{arm}"
            args = [a.replace("@KEEP", keep) for a in arm_args(arm)]
            if "--method" in args and args[args.index("--method") + 1] == "gptq":
                args += ["--calib"] + [corpus_paths[c] for c in spec["calib"]]
                args += ["--calib-n", "128", "--calib-len", "2048", "--calib-seed", "0"]
            out_dir = os.path.join(work, "runs", run_id)
            runs.append({
                "id": run_id, "policy": name, "arm": arm,
                "worker": workers[(name, arm)], "out_dir": out_dir,
                "args": ["--fpga-root", root, "--base", spec["base"],
                         "--adapter", spec["adapter"], "--split", split,
                         "--policy", run_id, "--generation-seed", str(GENERATION_SEED),
                         "--n", str(N_DRAWS), "--families", *spec["families"],
                         "--out-dir", out_dir, *args],
            })
    return runs


def evaluator_matches(root: str) -> Dict[str, Optional[bool]]:
    result = {}
    for name, expected in EXPECTED.items():
        path = os.path.join(root, name)
        result[name] = sha256_file(path) == expected if os.path.isfile(path) else None
    return result


def choose_root(requested: str) -> str:
    candidates = CANDIDATE_ROOTS if requested == "auto" else [requested]
    table = {root: evaluator_matches(root) for root in candidates if os.path.isdir(root)}
    for root, matches in table.items():
        if all(matches.values()):
            return root
    print("No checkout matches the frozen GitHub evaluator. Per-file match:")
    for root, matches in table.items():
        print(f"  {root}")
        for name, ok in matches.items():
            print(f"    {name:28s} {'match' if ok else 'MISSING' if ok is None else 'DIFFERS'}")
    raise SystemExit("stop: paste this table back before running Gate 0")


def oracle_self_check(root: str) -> None:
    code = ("import oracle,gen_accelerator_catalog as G;"
            "print(oracle.score(G.fir_ref('fir8_8b',G.fir_coeffs(8)),'fir8_8b',n=64)['correct'])")
    out = subprocess.run([sys.executable, "-c", code], cwd=root, capture_output=True, text=True)
    if out.returncode != 0 or out.stdout.strip().splitlines()[-1:] != ["True"]:
        raise SystemExit(f"oracle self-check failed in {root}:\n{out.stdout}\n{out.stderr}")
    print("oracle self-check: True")


def resolve_corpus(name: str, root: str) -> str:
    for base in [root] + [r for r in CANDIDATE_ROOTS if r != root]:
        path = os.path.join(base, name)
        if os.path.isfile(path):
            return path
    raise SystemExit(f"corpus {name} not found in {root} or the other checkouts")


def prepare(args: argparse.Namespace) -> None:
    os.makedirs(os.path.join(WORK, "logs"), exist_ok=True)
    root = choose_root(args.fpga_root)
    print(f"frozen evaluator checkout: {root}")
    oracle_self_check(root)
    for name, spec in POLICIES.items():
        for key in ("base", "adapter"):
            if not os.path.isdir(spec[key]):
                raise SystemExit(f"{name}: {key} directory missing: {spec[key]}")
    corpora = sorted(set(KEEP_VOCAB_CORPORA) | {c for s in POLICIES.values() for c in s["calib"]})
    corpus_paths = {c: resolve_corpus(c, root) for c in corpora}

    split = os.path.join(WORK, "dev_split.json")
    if not os.path.isfile(split):
        others = [r for r in CANDIDATE_ROOTS if r != root and os.path.isdir(r)]
        subprocess.run([sys.executable, os.path.join(HERE, "make_dev_split.py"),
                        "--fpga-root", root, "--tokenizer", QWEN15, "--out", split,
                        "--also-exclude-from", *others], check=True)
    keep = os.path.join(WORK, "keep_vocab_qwen.json")
    if not os.path.isfile(keep):
        subprocess.run([sys.executable, os.path.join(HERE, "make_keep_vocab.py"),
                        "--tokenizer", QWEN15, "--exclude-split", split, "--out", keep,
                        "--corpus", *[corpus_paths[c] for c in KEEP_VOCAB_CORPORA]],
                       check=True)

    with open(split, encoding="utf-8") as handle:
        designs = json.load(handle)["designs"]
    families = {d["family"] for d in designs}
    for name, spec in POLICIES.items():
        missing = set(spec["families"]) - families
        if missing:
            raise SystemExit(f"{name}: families {sorted(missing)} absent from the split")
    plan = {
        "schema": "gate0_plan/1",
        "fpga_root": root,
        "python": sys.executable,
        "split": split, "split_sha256": sha256_file(split),
        "keep_vocab": keep, "keep_vocab_sha256": sha256_file(keep),
        "corpora": {c: {"path": p, "sha256": sha256_file(p)} for c, p in corpus_paths.items()},
        "evaluator_sha256": EXPECTED,
        "generation_seed": GENERATION_SEED, "n_draws": N_DRAWS,
        "runs": build_runs(POLICIES, root, split, keep, WORK, corpus_paths),
    }
    path = os.path.join(WORK, "plan.json")
    if os.path.isfile(path):
        with open(path, encoding="utf-8") as handle:
            old = json.load(handle)
        if old["runs"] != plan["runs"] or old["split_sha256"] != plan["split_sha256"]:
            raise SystemExit(f"{path} exists with a different plan; never change a running campaign")
        print("plan.json already present and identical")
    else:
        with open(path, "w", encoding="utf-8", newline="\n") as handle:
            json.dump(plan, handle, indent=1)
            handle.write("\n")
    by_family: Dict[str, int] = {}
    for d in designs:
        by_family[d["family"]] = by_family.get(d["family"], 0) + 1
    print(f"dev split: {len(designs)} designs {by_family}")
    for worker in sorted({r["worker"] for r in plan["runs"]}):
        ids = [r["id"] for r in plan["runs"] if r["worker"] == worker]
        print(f"  {worker}: {', '.join(ids)}")
    print(f"plan written: {path}")


def load_plan() -> dict:
    path = os.path.join(WORK, "plan.json")
    if not os.path.isfile(path):
        raise SystemExit("gate0/plan.json missing: run `gate0.py prepare` on V100a first")
    with open(path, encoding="utf-8") as handle:
        return json.load(handle)


def is_complete(out_dir: str) -> bool:
    return os.path.isfile(os.path.join(out_dir, "generation_config.json"))


def acquire(lock: str) -> bool:
    record = f"{socket.gethostname()} {os.getpid()} {now()}\n"
    try:
        fd = os.open(lock, os.O_CREAT | os.O_EXCL | os.O_WRONLY)
    except FileExistsError:
        try:
            host, pid, _ = open(lock).read().split()
        except (OSError, ValueError):
            return False
        if host == socket.gethostname() and not os.path.exists(f"/proc/{pid}"):
            os.remove(lock)  # stale lock from a dead worker on this host
            return acquire(lock)
        return False
    with os.fdopen(fd, "w") as handle:
        handle.write(record)
    return True


def work(args: argparse.Namespace) -> None:
    plan = load_plan()
    box, gpu = args.worker.split("-")
    mine = [r for r in plan["runs"] if r["worker"] == args.worker]
    if not mine:
        raise SystemExit(f"no runs assigned to {args.worker}")
    os.makedirs(os.path.join(WORK, "logs"), exist_ok=True)
    os.makedirs(os.path.join(WORK, "failures"), exist_ok=True)
    env = dict(os.environ, CUDA_VISIBLE_DEVICES=gpu, TOKENIZERS_PARALLELISM="false",
               HF_HUB_OFFLINE="1", TRANSFORMERS_OFFLINE="1")
    for run in mine:
        out = run["out_dir"]
        if is_complete(out):
            print(f"[{now()}] {run['id']}: already complete", flush=True)
            continue
        lock = out + ".lock"
        if not acquire(lock):
            print(f"[{now()}] {run['id']}: locked by another worker, skipping", flush=True)
            continue
        try:
            if os.path.exists(out):
                os.rename(out, f"{out}.failed-{now()}")
            log = os.path.join(WORK, "logs", f"{run['id']}.log")
            print(f"[{now()}] {run['id']}: start on {box} GPU {gpu}", flush=True)
            with open(log, "w") as handle:
                rc = subprocess.run([plan["python"], EVAL, *run["args"]], cwd=plan["fpga_root"],
                                    env=env, stdout=handle, stderr=subprocess.STDOUT).returncode
            if rc != 0 or not is_complete(out):
                moved = f"{out}.failed-{now()}" if os.path.exists(out) else None
                if moved:
                    os.rename(out, moved)
                with open(os.path.join(WORK, "failures", f"{run['id']}-{now()}.json"), "w") as fh:
                    json.dump({"run": run["id"], "returncode": rc, "log": log,
                               "moved_to": moved, "host": socket.gethostname()}, fh, indent=1)
                print(f"[{now()}] {run['id']}: FAILED (rc={rc}); see {log}", flush=True)
            else:
                print(f"[{now()}] {run['id']}: done", flush=True)
        finally:
            if os.path.exists(lock):
                os.remove(lock)
    print(f"[{now()}] worker {args.worker} finished its queue", flush=True)


def status(_args: argparse.Namespace) -> None:
    plan = load_plan()
    print(f"{'run':14s} {'worker':9s} {'state':9s} correct/draws")
    for run in plan["runs"]:
        out = run["out_dir"]
        if is_complete(out):
            with open(os.path.join(out, "holdout_summary.json")) as handle:
                rows = json.load(handle)[run["id"]].values()
            correct = sum(r["n_correct"] for r in rows)
            total = sum(r["n"] for r in rows)
            state, detail = "done", f"{correct}/{total}"
        elif os.path.exists(out + ".lock"):
            emitted = [f for f in os.listdir(out) if f.endswith(".sv")] if os.path.isdir(out) else []
            state, detail = "running", f"{len(emitted)} correct candidates so far"
        else:
            parent = os.path.dirname(out)
            failed = ([f for f in os.listdir(parent) if f.startswith(run["id"] + ".failed-")]
                      if os.path.isdir(parent) else [])
            state = "failed" if failed else "pending"
            detail = f"{len(failed)} failed attempt(s)" if failed else ""
        print(f"{run['id']:14s} {run['worker']:9s} {state:9s} {detail}")


def main(argv: Optional[Sequence[str]] = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    sub = ap.add_subparsers(dest="command", required=True)
    p = sub.add_parser("prepare")
    p.add_argument("--fpga-root", default="auto",
                   help="previous-project checkout; 'auto' picks the one matching GitHub")
    p.set_defaults(func=prepare)
    w = sub.add_parser("work")
    w.add_argument("--worker", required=True, choices=[f"{b}-{g}" for b, n in BOXES.items()
                                                        for g in range(n)])
    w.set_defaults(func=work)
    s = sub.add_parser("status")
    s.set_defaults(func=status)
    args = ap.parse_args(argv)
    args.func(args)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

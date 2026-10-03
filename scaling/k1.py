#!/usr/bin/env python3
"""Kill test K1: does generated-circuit quality change with model size under one SFT recipe?

    python scaling/k1.py prepare                    # once, on V100a
    python scaling/k1.py work --worker v100a-0      # one per GPU, any box
    python scaling/k1.py status
    python scaling/k1.py collect                    # after all evaluations
    python scaling/eda_vivado.py run --dir k1/vivado --out k1/vivado/ppa.jsonl --jobs 32
    python scaling/k1.py analyze

Implements research/fpga2/K1_PROTOCOL_20261003.md.  ``prepare`` checks the
frozen evaluator, the four base models and the corpus (leak check against the
development and confirmation splits), carves the learning-rate validation designs
out of the corpus, and writes ``k1/plan.json``.  Workers share one dynamic queue
(lock files on the shared filesystem): learning-rate sweep -> automatic selection
-> final SFT per seed -> evaluation on the development split.  A failed job is
moved aside and not retried unless ``--retry-failed`` is given.
"""

from __future__ import annotations

import argparse
import glob
import hashlib
import json
import math
import os
import random
import socket
import statistics
import subprocess
import sys
import time
from collections import defaultdict
from typing import Dict, List, Optional, Sequence, Tuple

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(HERE)
sys.path.insert(0, REPO)

from student import gate0 as G0  # noqa: E402
from student import gate0_physical as GP  # noqa: E402

WORK = os.path.join(REPO, "k1")
SFT = os.path.join(HERE, "sft.py")
EVAL = os.path.join(REPO, "student", "eval_compressed.py")
MAS = G0.MAS

SIZES: List[Tuple[str, str]] = [
    ("0.5B", f"{MAS}/models/Qwen/Qwen2.5-Coder-0.5B"),
    ("1.5B", G0.QWEN15),
    ("3B", f"{MAS}/models/Qwen/Qwen2.5-Coder-3B"),
    ("7B", f"{MAS}/models/Qwen/Qwen2.5-Coder-7B"),
]
SEEDS = {"0.5B": [1, 2, 3], "1.5B": [1, 2, 3], "3B": [1, 2], "7B": [1, 2]}
LRS = [5e-5, 1e-4, 2e-4]
SWEEP_SEED = 1
VAL_FRACTION = 0.15
CORPUS = "sft_corpus.jsonl"
CONFIRMATION_SPLIT = os.path.join(REPO, "scaling_splits", "confirmation_split.json")
GENERATION_SEED = G0.GENERATION_SEED
N_DRAWS = G0.N_DRAWS
RESAMPLES = 10_000
BOOTSTRAP_SEED = 20261003
CEILING_REL = 0.05
SATURATED_Q = 0.95


def tag(size: str) -> str:
    return size.lower().replace(".", "p")


def sha256_text(text: str) -> str:
    return hashlib.sha256(text.encode()).hexdigest()


def load_json(path: str):
    with open(path, encoding="utf-8") as handle:
        return json.load(handle)


def write_json(path: str, data, exclusive: bool = False) -> bool:
    """Write JSON; with exclusive=True only if the file does not exist yet."""
    os.makedirs(os.path.dirname(path), exist_ok=True)
    if exclusive:
        try:
            fd = os.open(path, os.O_CREAT | os.O_EXCL | os.O_WRONLY)
        except FileExistsError:
            return False
        handle = os.fdopen(fd, "w", encoding="utf-8", newline="\n")
    else:
        handle = open(path, "w", encoding="utf-8", newline="\n")
    with handle:
        json.dump(data, handle, indent=1)
        handle.write("\n")
    return True


def read_rows(path: str) -> List[dict]:
    with open(path, encoding="utf-8") as handle:
        return [json.loads(line) for line in handle if line.strip()]


def write_rows(path: str, rows: List[dict]) -> None:
    with open(path, "w", encoding="utf-8", newline="\n") as handle:
        for row in rows:
            handle.write(json.dumps(row, sort_keys=True) + "\n")


# ------------------------------------------------------------------ preparation

def split_validation(rows: List[dict], fraction: float = VAL_FRACTION) -> Tuple[List[dict], List[dict], List[str]]:
    """Hold out whole designs, per family, first by sha256(design); at least one per family
    with three or more designs."""
    by_family: Dict[str, List[str]] = defaultdict(list)
    for row in rows:
        if row["design"] not in by_family[row["family"]]:
            by_family[row["family"]].append(row["design"])
    held = set()
    for family, designs in by_family.items():
        if len(designs) < 3:
            continue
        k = max(1, round(fraction * len(designs)))
        held.update(sorted(designs, key=sha256_text)[:k])
    train = [r for r in rows if r["design"] not in held]
    val = [r for r in rows if r["design"] in held]
    return train, val, sorted(held)


def leak_check(rows: List[dict], split_paths: Sequence[str]) -> None:
    corpus_designs = {r["design"] for r in rows}
    for path in split_paths:
        overlap = corpus_designs & {d["design"] for d in load_json(path)["designs"]}
        if overlap:
            raise SystemExit(f"corpus contains designs of {path}: {sorted(overlap)[:10]}")


def check_base(path: str) -> dict:
    for name in ("config.json", "tokenizer_config.json"):
        if not os.path.isfile(os.path.join(path, name)):
            raise SystemExit(f"base model incomplete: {path} lacks {name}")
    if not glob.glob(os.path.join(path, "*.safetensors")):
        raise SystemExit(f"base model has no safetensors weights: {path}")
    tok_cfg = load_json(os.path.join(path, "tokenizer_config.json"))
    if not tok_cfg.get("chat_template"):
        raise SystemExit(f"{path}: no chat template; prompts would be rendered differently")
    tok_json = os.path.join(path, "tokenizer.json")
    return {"path": path,
            "config_sha256": G0.sha256_file(os.path.join(path, "config.json")),
            "tokenizer_sha256": G0.sha256_file(tok_json) if os.path.isfile(tok_json) else None,
            "chat_template_sha256": sha256_text(tok_cfg["chat_template"])}


def build_jobs(work: str, families: List[str]) -> List[dict]:
    jobs = []
    for size, _ in reversed(SIZES):  # largest first: they bound the wall time
        for lr in LRS:
            jobs.append({"id": f"sweep_{tag(size)}_lr{lr:.0e}", "stage": "sweep", "size": size,
                         "lr": lr, "seed": SWEEP_SEED,
                         "out_dir": os.path.join(work, "adapters", f"sweep_{tag(size)}_lr{lr:.0e}"),
                         "marker": "val_loss.json"})
    for size, _ in reversed(SIZES):
        for seed in SEEDS[size]:
            jobs.append({"id": f"final_{tag(size)}_s{seed}", "stage": "final", "size": size,
                         "seed": seed,
                         "out_dir": os.path.join(work, "adapters", f"final_{tag(size)}_s{seed}"),
                         "marker": "training_record.json"})
    for size, _ in reversed(SIZES):
        for seed in SEEDS[size]:
            jobs.append({"id": f"k1_{tag(size)}_s{seed}", "stage": "eval", "size": size,
                         "seed": seed, "families": families,
                         "adapter": os.path.join(work, "adapters", f"final_{tag(size)}_s{seed}"),
                         "out_dir": os.path.join(work, "runs", f"k1_{tag(size)}_s{seed}"),
                         "marker": "generation_config.json"})
    return jobs


def prepare(args: argparse.Namespace) -> None:
    root = G0.choose_root(args.fpga_root)
    G0.oracle_self_check(root)
    dev = os.path.join(G0.WORK, "dev_split.json")
    if not os.path.isfile(dev):
        raise SystemExit(f"{dev} missing (Gate 0 development split)")
    if not os.path.isfile(CONFIRMATION_SPLIT):
        raise SystemExit(f"{CONFIRMATION_SPLIT} missing: draw it first with "
                         "scaling/make_confirmation_split.py")
    bases = {size: check_base(path) for size, path in SIZES}
    if len({b["tokenizer_sha256"] for b in bases.values()}) != 1:
        print("note: tokenizer.json differs across sizes:",
              {s: (b["tokenizer_sha256"] or "")[:12] for s, b in bases.items()})
    corpus_src = G0.resolve_corpus(CORPUS, root)
    rows = read_rows(corpus_src)
    leak_check(rows, [dev, CONFIRMATION_SPLIT])
    train, val, held = split_validation(rows)

    os.makedirs(os.path.join(WORK, "corpus"), exist_ok=True)
    paths = {"full": os.path.join(WORK, "corpus", "full.jsonl"),
             "sweep_train": os.path.join(WORK, "corpus", "sweep_train.jsonl"),
             "sweep_val": os.path.join(WORK, "corpus", "sweep_val.jsonl")}
    for key, data in (("full", rows), ("sweep_train", train), ("sweep_val", val)):
        if not os.path.isfile(paths[key]):
            write_rows(paths[key], data)
    families = sorted({d["family"] for d in load_json(dev)["designs"]})
    plan = {
        "schema": "k1_plan/1", "fpga_root": root, "python": sys.executable,
        "evaluator_sha256": G0.EXPECTED,
        "dev_split": dev, "dev_split_sha256": G0.sha256_file(dev),
        "confirmation_split": CONFIRMATION_SPLIT,
        "confirmation_split_sha256": G0.sha256_file(CONFIRMATION_SPLIT),
        "families": families,
        "corpus_source": corpus_src, "corpus_source_sha256": G0.sha256_file(corpus_src),
        "corpus": {k: {"path": p, "sha256": G0.sha256_file(p), "n_rows": len(read_rows(p))}
                   for k, p in paths.items()},
        "validation_designs": held,
        "bases": bases, "seeds": SEEDS, "lrs": LRS, "sweep_seed": SWEEP_SEED,
        "generation_seed": GENERATION_SEED, "n_draws": N_DRAWS,
        "jobs": build_jobs(WORK, families),
    }
    plan["runs"] = [{"id": j["id"], "policy": tag(j["size"]), "arm": f"s{j['seed']}",
                     "size": j["size"], "seed": j["seed"], "out_dir": j["out_dir"]}
                    for j in plan["jobs"] if j["stage"] == "eval"]
    path = os.path.join(WORK, "plan.json")
    if os.path.isfile(path):
        old = load_json(path)
        if old["jobs"] != plan["jobs"] or old["corpus"] != plan["corpus"]:
            raise SystemExit(f"{path} exists with a different plan; never change a running campaign")
        print("plan.json already present and identical")
    else:
        write_json(path, plan)
    print(f"corpus {len(rows)} rows; sweep train {len(train)}, validation {len(val)} rows "
          f"({len(held)} designs)")
    print(f"families evaluated: {families}")
    print(f"{len(plan['jobs'])} jobs; plan written: {path}")


# ------------------------------------------------------------------ queue

def load_plan() -> dict:
    path = os.path.join(WORK, "plan.json")
    if not os.path.isfile(path):
        raise SystemExit("k1/plan.json missing: run `k1.py prepare` first")
    return load_json(path)


def acquire(lock: str) -> bool:
    """Atomic lock on the shared filesystem; a lock left by a dead worker on this host is
    cleared.  Two workers clearing the same stale lock at once is harmless."""
    record = f"{socket.gethostname()} {os.getpid()} {G0.now()}\n"
    for _ in range(2):
        try:
            fd = os.open(lock, os.O_CREAT | os.O_EXCL | os.O_WRONLY)
        except FileExistsError:
            try:
                host, pid, _ = open(lock).read().split()
            except (OSError, ValueError):
                return False
            if host == socket.gethostname() and not os.path.exists(f"/proc/{pid}"):
                try:
                    os.remove(lock)
                except FileNotFoundError:
                    pass
                continue
            return False
        with os.fdopen(fd, "w") as handle:
            handle.write(record)
        return True
    return False


def is_complete(job: dict) -> bool:
    return os.path.isfile(os.path.join(job["out_dir"], job["marker"]))


# Failure records older than this (epoch seconds) are ignored; set by ``work --retry-failed``
# to the worker's start time, so a job is retried once per relaunch, never in a loop.
FAILURE_CUTOFF = 0.0


def failure_records(job: dict) -> List[str]:
    paths = glob.glob(os.path.join(WORK, "failures", f"{job['id']}-*.json"))
    return sorted(p for p in paths if os.path.getmtime(p) >= FAILURE_CUTOFF)


def lr_choice_path() -> str:
    return os.path.join(WORK, "lr_choice.json")


def select_learning_rates(plan: dict) -> Optional[dict]:
    """Once every sweep job is complete, pick per size the lr with the lowest held-out
    completion NLL (ties: the smaller lr).  Written once; never changed."""
    path = lr_choice_path()
    if os.path.isfile(path):
        return load_json(path)
    sweeps = [j for j in plan["jobs"] if j["stage"] == "sweep"]
    if not all(is_complete(j) for j in sweeps):
        return None
    table: Dict[str, Dict[str, float]] = defaultdict(dict)
    for j in sweeps:
        table[j["size"]][repr(j["lr"])] = load_json(os.path.join(j["out_dir"], j["marker"]))["nll_per_token"]
    choice = {size: float(min(vals, key=lambda lr: (vals[lr], float(lr))))
              for size, vals in table.items()}
    record = {"schema": "k1_lr_choice/1", "rule": "min held-out completion NLL; ties -> smaller lr",
              "nll": table, "lr": choice, "written": G0.now()}
    write_json(path, record, exclusive=True)
    return load_json(path)


def dependency_state(job: dict, plan: dict) -> str:
    """'ready', 'waiting' or 'blocked' (a dependency failed)."""
    if job["stage"] == "sweep":
        return "ready"
    if job["stage"] == "final":
        if os.path.isfile(lr_choice_path()):
            return "ready"
        sweeps = [j for j in plan["jobs"] if j["stage"] == "sweep"]
        if any(failure_records(j) and not is_complete(j) for j in sweeps):
            return "blocked"
        return "waiting"
    final = next(j for j in plan["jobs"] if j["stage"] == "final"
                 and j["size"] == job["size"] and j["seed"] == job["seed"])
    if is_complete(final):
        return "ready"
    if failure_records(final) and not is_complete(final):
        return "blocked"
    return "waiting"


def base_path(plan: dict, size: str) -> str:
    return plan["bases"][size]["path"]


def job_commands(job: dict, plan: dict) -> List[Tuple[List[str], str]]:
    py = plan["python"]
    root = plan["fpga_root"]
    base = base_path(plan, job["size"])
    if job["stage"] == "sweep":
        corpus = plan["corpus"]
        return [([py, SFT, "train", "--fpga-root", root, "--base", base,
                  "--corpus", corpus["sweep_train"]["path"], "--out", job["out_dir"],
                  "--lr", repr(job["lr"]), "--seed", str(job["seed"])], REPO),
                ([py, SFT, "val-loss", "--fpga-root", root, "--base", base,
                  "--adapter", job["out_dir"], "--corpus", corpus["sweep_val"]["path"],
                  "--out", os.path.join(job["out_dir"], job["marker"])], REPO)]
    if job["stage"] == "final":
        lr = load_json(lr_choice_path())["lr"][job["size"]]
        return [([py, SFT, "train", "--fpga-root", root, "--base", base,
                  "--corpus", plan["corpus"]["full"]["path"], "--out", job["out_dir"],
                  "--lr", repr(lr), "--seed", str(job["seed"])], REPO)]
    return [([py, EVAL, "--fpga-root", root, "--base", base, "--adapter", job["adapter"],
              "--split", plan["dev_split"], "--policy", job["id"],
              "--generation-seed", str(plan["generation_seed"]), "--n", str(plan["n_draws"]),
              "--families", *job["families"], "--out-dir", job["out_dir"], "--bits", "16"], root)]


def run_job(job: dict, plan: dict, gpu: str) -> bool:
    out = job["out_dir"]
    if os.path.exists(out) and job["stage"] == "eval":
        os.rename(out, f"{out}.failed-{G0.now()}")  # evaluations always start fresh
    if os.path.exists(out) and job["stage"] in ("sweep", "final") and \
            not os.path.isfile(os.path.join(out, "training_record.json")):
        os.rename(out, f"{out}.failed-{G0.now()}")  # a half-trained adapter is never resumed
    env = dict(os.environ, CUDA_VISIBLE_DEVICES=gpu, TOKENIZERS_PARALLELISM="false",
               HF_HUB_OFFLINE="1", TRANSFORMERS_OFFLINE="1",
               PYTORCH_CUDA_ALLOC_CONF="expandable_segments:True")
    log = os.path.join(WORK, "logs", f"{job['id']}.log")
    rc = 0
    with open(log, "a") as handle:
        for cmd, cwd in job_commands(job, plan):
            handle.write(f"\n### {G0.now()} {socket.gethostname()} GPU {gpu}: {' '.join(cmd)}\n")
            handle.flush()
            rc = subprocess.run(cmd, cwd=cwd, env=env, stdout=handle, stderr=subprocess.STDOUT).returncode
            if rc != 0:
                break
    if rc == 0 and is_complete(job):
        return True
    moved = None
    if os.path.exists(out):
        moved = f"{out}.failed-{G0.now()}"
        os.rename(out, moved)
    write_json(os.path.join(WORK, "failures", f"{job['id']}-{G0.now()}.json"),
               {"job": job["id"], "returncode": rc, "log": log, "moved_to": moved,
                "host": socket.gethostname(), "gpu": gpu})
    return False


def work(args: argparse.Namespace) -> None:
    global FAILURE_CUTOFF
    if args.retry_failed:
        FAILURE_CUTOFF = time.time()
    plan = load_plan()
    box, gpu = args.worker.split("-")
    for sub in ("logs", "failures", "adapters", "runs"):
        os.makedirs(os.path.join(WORK, sub), exist_ok=True)
    while True:
        select_learning_rates(plan)
        pending = [j for j in plan["jobs"] if not is_complete(j) and not failure_records(j)]
        if not pending:
            print(f"[{G0.now()}] {args.worker}: nothing left to run", flush=True)
            return
        states = {j["id"]: dependency_state(j, plan) for j in pending}
        if all(s == "blocked" for s in states.values()):
            print(f"[{G0.now()}] {args.worker}: remaining jobs blocked by failures", flush=True)
            return
        picked = None
        for j in pending:
            if states[j["id"]] == "ready" and acquire(j["out_dir"] + ".lock"):
                picked = j
                break
        if picked is None:
            time.sleep(args.poll)
            continue
        try:
            print(f"[{G0.now()}] {picked['id']}: start on {box} GPU {gpu}", flush=True)
            ok = run_job(picked, plan, gpu)
            print(f"[{G0.now()}] {picked['id']}: {'done' if ok else 'FAILED, see logs'}", flush=True)
        finally:
            lock = picked["out_dir"] + ".lock"
            if os.path.exists(lock):
                os.remove(lock)


def status(_args: argparse.Namespace) -> None:
    plan = load_plan()
    choice = load_json(lr_choice_path()) if os.path.isfile(lr_choice_path()) else None
    for job in plan["jobs"]:
        if is_complete(job):
            state = "done"
            data = load_json(os.path.join(job["out_dir"], job["marker"]))
            if job["stage"] == "sweep":
                detail = f"val nll {data['nll_per_token']:.4f}"
            elif job["stage"] == "final":
                detail = f"loss {data['first_loss']}->{data['last_loss']} in {data['wall_s']}s on {data['gpu']}"
            else:
                rows = load_json(os.path.join(job["out_dir"], "holdout_summary.json"))[job["id"]].values()
                detail = f"{sum(r['n_correct'] for r in rows)}/{sum(r['n'] for r in rows)} correct"
        elif os.path.exists(job["out_dir"] + ".lock"):
            state, detail = "running", open(job["out_dir"] + ".lock").read().strip()
        elif failure_records(job):
            state, detail = "FAILED", failure_records(job)[-1]
        else:
            state, detail = dependency_state(job, plan), ""
        print(f"{job['id']:22s} {state:8s} {detail}")
    if choice:
        print("learning rates chosen:", choice["lr"])


# ------------------------------------------------------------------ physical step

def collect(args: argparse.Namespace) -> None:
    GP.WORK = WORK
    GP.collect(argparse.Namespace(out=args.out, allow_partial=args.allow_partial))


# ------------------------------------------------------------------ analysis

def size_tables(plan: dict, table: Dict[str, Dict[str, dict]]) -> Dict[str, Dict[int, Dict[str, dict]]]:
    """by_size[size][seed][design] = design row."""
    by_size: Dict[str, Dict[int, Dict[str, dict]]] = defaultdict(dict)
    for run in plan["runs"]:
        if run["id"] in table:
            by_size[run["size"]][run["seed"]] = table[run["id"]]
    return by_size


def size_value(by_size, size: str, seeds: Sequence[int], designs: Sequence[str], metric: str) -> Optional[float]:
    """Mean over designs; per design the seed-mean of q or F, or pooled mu."""
    vals = []
    for d in designs:
        rows = [by_size[size][s][d] for s in seeds]
        if metric == "mu":
            correct = sum(r["correct"] for r in rows)
            if not correct:
                return None
            vals.append(sum(r["sum_cF"] for r in rows) / correct)
        else:
            vals.append(sum(GP.endpoints(r)[metric] for r in rows) / len(rows))
    return sum(vals) / len(vals) if vals else None


def bootstrap(by_size, sizes: List[str], designs_by_metric: Dict[str, List[str]],
              strata: Dict[str, str], n: int = RESAMPLES, seed: int = BOOTSTRAP_SEED) -> dict:
    """Paired design bootstrap within strata, with training seeds resampled within size."""
    rng = random.Random(seed)
    draws: Dict[str, Dict[Tuple[str, str], List[float]]] = {m: defaultdict(list) for m in designs_by_metric}
    seeds_of = {s: sorted(by_size[s]) for s in sizes}
    for _ in range(n):
        seed_pick = {s: [rng.choice(seeds_of[s]) for _ in seeds_of[s]] for s in sizes}
        for metric, designs in designs_by_metric.items():
            groups: Dict[str, List[str]] = defaultdict(list)
            for d in designs:
                groups[strata[d]].append(d)
            picked = [g[rng.randrange(len(g))] for g in groups.values() for _ in g]
            values = {s: size_value(by_size, s, seed_pick[s], picked, metric) for s in sizes}
            for i, a in enumerate(sizes):
                for b in sizes[i + 1:]:
                    if values[a] is not None and values[b] is not None:
                        draws[metric][(a, b)].append(values[b] - values[a])
    out: Dict[str, Dict[str, List[float]]] = {}
    for metric, pairs in draws.items():
        out[metric] = {}
        for (a, b), diffs in pairs.items():
            diffs.sort()
            k = len(diffs)
            out[metric][f"{b} - {a}"] = [diffs[int(0.025 * k)], diffs[int(0.975 * k) - 1]]
    return out


def excludes_zero(ci: Sequence[float]) -> bool:
    return ci[0] > 0 or ci[1] < 0


def trend_holds(points: Dict[str, float], cis: Dict[str, List[float]], sizes: List[str]) -> bool:
    """Largest-minus-smallest interval excludes zero, and the seed-mean sequence is monotone
    in that direction or has one inversion whose own interval includes zero."""
    ci = cis[f"{sizes[-1]} - {sizes[0]}"]
    if not excludes_zero(ci):
        return False
    sign = 1 if ci[0] > 0 else -1
    inversions = [(a, b) for a, b in zip(sizes, sizes[1:]) if sign * (points[b] - points[a]) < 0]
    if not inversions:
        return True
    if len(inversions) > 1:
        return False
    a, b = inversions[0]
    return not excludes_zero(cis[f"{b} - {a}"])


def decide(points: Dict[str, Dict[str, float]], cis: Dict[str, Dict[str, List[float]]],
           seed_sd_within: float, sd_between: float, sizes: List[str]) -> dict:
    q, mu, F = points["q"], points["mu"], points["F"]
    if all(q[s] >= SATURATED_Q for s in sizes):
        outcome = "saturated"
    elif trend_holds(F, cis["F"], sizes):
        outcome = "trend"
    elif (trend_holds(q, cis["q"], sizes) and mu.get(sizes[0])
          and all(abs(mu[s] - mu[sizes[0]]) / mu[sizes[0]] < CEILING_REL for s in sizes)
          and not any(excludes_zero(ci) for ci in cis["mu"].values())):
        outcome = "ceiling"
    elif (not any(excludes_zero(ci) for m in ("q", "mu", "F") for ci in cis[m].values())
          and sd_between <= seed_sd_within):
        outcome = "no signal"
    else:
        outcome = "inconclusive"
    mu_flat = bool(mu.get(sizes[0])) and all(
        abs(mu[s] - mu[sizes[0]]) / mu[sizes[0]] < CEILING_REL for s in sizes)
    return {"outcome": outcome, "mu_flat_descriptive": mu_flat}


def analyze(args: argparse.Namespace) -> None:
    plan = load_plan()
    cmap = load_json(os.path.join(args.vivado, "candidate_map.json"))
    ppa = {}
    with open(os.path.join(args.vivado, "ppa.jsonl"), encoding="utf-8") as handle:
        for line in handle:
            if line.strip():
                rec = json.loads(line)
                ppa[rec["module"]] = rec
    table = GP.design_table(plan, cmap, ppa)
    result = analyze_table(plan, table)
    write_json(os.path.join(WORK, "k1_analysis.json"), result)
    print(f"{'size':6s} {'q':>7s} {'mu (common)':>12s} {'F':>8s}  per-seed F")
    for s in result["sizes"]:
        p = result["points"]
        print(f"{s:6s} {p['q'][s]:7.3f} {p['mu'][s] or 0:12.2f} {p['F'][s]:8.2f}  "
              f"{[round(x, 2) for x in result['per_seed_F'][s]]}")
    for metric in ("q", "mu", "F"):
        for pair, ci in result["intervals"][metric].items():
            print(f"  {metric:3s} {pair:12s} [{ci[0]:+.3f}, {ci[1]:+.3f}]")
    print(f"seed SD within size {result['seed_sd_within']:.3f}; SD between sizes {result['sd_between']:.3f}")
    print(f"common-support designs for mu: {len(result['mu_designs'])}")
    print("K1 decision:", result["decision"])


def analyze_table(plan: dict, table: Dict[str, Dict[str, dict]]) -> dict:
    by_size = size_tables(plan, table)
    sizes = [s for s, _ in SIZES if s in by_size]
    designs = sorted(set.intersection(*(set(rows) for s in sizes for rows in by_size[s].values())))
    any_row = next(iter(by_size[sizes[0]].values()))
    strata = {d: f"{any_row[d]['family']}|{any_row[d]['regime']}" for d in designs}
    mu_designs = [d for d in designs
                  if all(sum(by_size[s][k][d]["correct"] for k in by_size[s]) > 0 for s in sizes)]
    points = {m: {s: size_value(by_size, s, sorted(by_size[s]), designs if m != "mu" else mu_designs, m)
                  for s in sizes} for m in ("q", "F")}
    points["mu"] = {s: (size_value(by_size, s, sorted(by_size[s]), mu_designs, "mu") if mu_designs else None)
                    for s in sizes}
    per_seed_F = {s: [size_value(by_size, s, [k], designs, "F") for k in sorted(by_size[s])] for s in sizes}
    within = [statistics.variance(v) for v in per_seed_F.values() if len(v) > 1]
    seed_sd_within = math.sqrt(sum(within) / len(within)) if within else 0.0
    sd_between = statistics.stdev(points["F"].values()) if len(sizes) > 1 else 0.0
    cis = bootstrap(by_size, sizes, {"q": designs, "F": designs, "mu": mu_designs}, strata)
    decision = decide(points, cis, seed_sd_within, sd_between, sizes)
    return {"schema": "k1_analysis/1", "sizes": sizes, "designs": designs, "mu_designs": mu_designs,
            "points": points, "per_seed_F": per_seed_F, "intervals": cis,
            "seed_sd_within": seed_sd_within, "sd_between": sd_between, "decision": decision}


def main(argv: Optional[Sequence[str]] = None) -> None:
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    sub = ap.add_subparsers(dest="cmd", required=True)
    p = sub.add_parser("prepare")
    p.add_argument("--fpga-root", default="auto")
    w = sub.add_parser("work")
    w.add_argument("--worker", required=True, help="<box>-<gpu>, e.g. v100a-0")
    w.add_argument("--retry-failed", action="store_true",
                   help="ignore failures recorded before this worker started (each is retried once)")
    w.add_argument("--poll", type=int, default=120, help="seconds between queue checks while waiting")
    sub.add_parser("status")
    c = sub.add_parser("collect")
    c.add_argument("--out", default=os.path.join(WORK, "vivado"))
    c.add_argument("--allow-partial", action="store_true")
    a = sub.add_parser("analyze")
    a.add_argument("--vivado", default=os.path.join(WORK, "vivado"))
    args = ap.parse_args(argv)
    {"prepare": prepare, "work": work, "status": status, "collect": collect,
     "analyze": analyze}[args.cmd](args)


if __name__ == "__main__":
    main()

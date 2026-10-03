#!/usr/bin/env python3
"""Seeded SFT with the previous project's frozen trainer, and held-out completion loss.

    python scaling/sft.py train --fpga-root F --base B --corpus C --out O --lr 1e-4 --seed 1
    python scaling/sft.py val-loss --fpga-root F --base B --adapter O --corpus V --out O/val_loss.json

``train`` runs ``sft_train_v2.main`` unchanged (LoRA r=16/alpha=32 on q/k/v/o,
completion-masked loss, 4 epochs, batch 1 x 16 accumulation, cosine schedule,
BF16, max length 4096).  That script has no seed option, so the wrapper adds
exactly two things: ``transformers.set_seed(seed)`` before the LoRA weights are
initialised, and ``seed`` passed to its ``TrainingArguments`` (with ``data_seed``
unset, the Trainer seeds its data sampler from ``seed``; ``data_seed`` itself needs a
newer ``accelerate`` than the frozen environment has).
It then writes ``training_record.json`` (the completion marker).

``val-loss`` scores an adapter by mean completion-token negative log-likelihood
on held-out rows, rendered with the trainer's own ``CorpusDataset``.
"""

from __future__ import annotations

import argparse
import datetime as _dt
import hashlib
import json
import os
import platform
import socket
import sys
import time
from typing import Optional, Sequence


def sha256_file(path: str) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as handle:
        for block in iter(lambda: handle.read(1 << 20), b""):
            h.update(block)
    return h.hexdigest()


def load_rows(path: str) -> list:
    with open(path, encoding="utf-8") as handle:
        return [json.loads(line) for line in handle if line.strip()]


def import_trainer(fpga_root: str):
    sys.path.insert(0, os.path.abspath(fpga_root))
    import sft_train_v2  # noqa: E402  (frozen previous-project trainer)
    return sft_train_v2


def seeded_training_arguments(original, seed: int):
    """Wrap TrainingArguments so every call carries this run's seed."""
    def make(*args, **kwargs):
        kwargs["seed"] = seed
        return original(*args, **kwargs)
    return make


def train(args: argparse.Namespace) -> None:
    record_path = os.path.join(args.out, "training_record.json")
    if os.path.isfile(record_path):
        print(f"{record_path} exists; nothing to do")
        return
    trainer_mod = import_trainer(args.fpga_root)
    import torch
    import transformers
    transformers.set_seed(args.seed)
    trainer_mod.TrainingArguments = seeded_training_arguments(trainer_mod.TrainingArguments, args.seed)
    argv = ["sft_train_v2.py", "--corpus", args.corpus, "--base", args.base, "--out", args.out,
            "--lr", repr(args.lr), "--epochs", str(args.epochs)]
    sys.argv = argv
    start = time.time()
    trainer_mod.main()
    wall = time.time() - start

    state_files = []
    for name in os.listdir(args.out):
        path = os.path.join(args.out, name, "trainer_state.json")
        if name.startswith("checkpoint-") and os.path.isfile(path):
            state_files.append((int(name.split("-")[1]), path))
    losses, steps = [], None
    if state_files:
        with open(max(state_files)[1], encoding="utf-8") as handle:
            state = json.load(handle)
        losses = [h["loss"] for h in state.get("log_history", []) if "loss" in h]
        steps = state.get("global_step")
    record = {
        "schema": "scaling_sft_record/1",
        "finished": _dt.datetime.now().isoformat(timespec="seconds"),
        "host": socket.gethostname(),
        "gpu": torch.cuda.get_device_name(0) if torch.cuda.is_available() else None,
        "base": os.path.abspath(args.base), "corpus": os.path.abspath(args.corpus),
        "corpus_sha256": sha256_file(args.corpus), "n_rows": len(load_rows(args.corpus)),
        "lr": args.lr, "seed": args.seed, "epochs": args.epochs, "argv": argv,
        "trainer_sha256": sha256_file(trainer_mod.__file__),
        "wrapper_sha256": sha256_file(os.path.abspath(__file__)),
        "versions": {"python": platform.python_version(), "torch": torch.__version__,
                     "transformers": transformers.__version__},
        "global_step": steps, "first_loss": losses[0] if losses else None,
        "last_loss": losses[-1] if losses else None, "wall_s": round(wall, 1),
    }
    with open(record_path, "w", encoding="utf-8", newline="\n") as handle:
        json.dump(record, handle, indent=1)
        handle.write("\n")
    print(json.dumps({k: record[k] for k in ("global_step", "first_loss", "last_loss", "wall_s")}))


def val_loss(args: argparse.Namespace) -> None:
    trainer_mod = import_trainer(args.fpga_root)
    import torch
    from peft import PeftModel
    from transformers import AutoModelForCausalLM, AutoTokenizer

    tok = AutoTokenizer.from_pretrained(args.base)
    if tok.pad_token is None:
        tok.pad_token = tok.eos_token
    model = AutoModelForCausalLM.from_pretrained(args.base, torch_dtype=torch.bfloat16,
                                                 device_map={"": 0})
    model = PeftModel.from_pretrained(model, args.adapter).eval()
    rows = load_rows(args.corpus)
    dataset = trainer_mod.CorpusDataset(rows, tok, max_length=args.max_length)
    total, count = 0.0, 0
    with torch.no_grad():
        for i in range(len(dataset)):
            item = dataset[i]
            ids = torch.tensor([item["input_ids"]], device=model.device)
            labels = torch.tensor([item["labels"]], device=model.device)
            n = int((labels[0, 1:] != trainer_mod.IGNORE).sum())
            if n == 0:
                continue
            loss = model(input_ids=ids, labels=labels).loss.float().item()
            total += loss * n
            count += n
    result = {"schema": "scaling_val_loss/1", "adapter": os.path.abspath(args.adapter),
              "corpus_sha256": sha256_file(args.corpus), "n_rows": len(rows),
              "n_tokens": count, "nll_per_token": total / count if count else None}
    with open(args.out, "w", encoding="utf-8", newline="\n") as handle:
        json.dump(result, handle, indent=1)
        handle.write("\n")
    print(json.dumps(result))


def main(argv: Optional[Sequence[str]] = None) -> None:
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    sub = ap.add_subparsers(dest="cmd", required=True)
    t = sub.add_parser("train")
    t.add_argument("--fpga-root", required=True)
    t.add_argument("--base", required=True)
    t.add_argument("--corpus", required=True)
    t.add_argument("--out", required=True)
    t.add_argument("--lr", type=float, required=True)
    t.add_argument("--seed", type=int, required=True)
    t.add_argument("--epochs", type=int, default=4)
    v = sub.add_parser("val-loss")
    v.add_argument("--fpga-root", required=True)
    v.add_argument("--base", required=True)
    v.add_argument("--adapter", required=True)
    v.add_argument("--corpus", required=True)
    v.add_argument("--out", required=True)
    v.add_argument("--max-length", type=int, default=4096)
    args = ap.parse_args(argv)
    {"train": train, "val-loss": val_loss}[args.cmd](args)


if __name__ == "__main__":
    main()

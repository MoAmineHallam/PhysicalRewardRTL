#!/usr/bin/env python3
"""
sft_train_v2.py  -  V2 Stage 1: SFT warm-start on the ORACLE-VERIFIED corpus.

Why this exists (and supersedes sft_train.py): the cross-model probe proved the
base models write these accelerators correctly at ~2%, so GRPO has no foothold
(RL refines competence, it cannot create it). The fix -- and the supervisor's own
roadmap step 1 -- is an SFT warm-start. sft_train.py was the V1 trainer: it read
reward-filtered RTLCoder *generations* (dataset.jsonl) for a handful of toy
designs with hard-coded specs, and computed loss over the prompt too. This reads
gen_sft_corpus.py's output instead: (prompt -> completion) pairs where every
completion is I/O-equivalence-verified correct by the V2 oracle, across the
fir/firr/poly/cordic grid in multiple coding styles. Loss is masked to the
completion only (the model is graded on the RTL it writes, not on echoing the
spec), which is the correct SFT objective.

Output: a LoRA adapter. Probe it afterwards with gen_accel_candidates.py
(--adapter) + the oracle: does correct-rate jump from ~2%? Only then is GRPO
worth running.

Runs on the GPU server (one V100 is plenty for a 7B LoRA at this corpus size):
    python sft_train_v2.py --corpus sft_corpus.jsonl --base rtlcoder --out sft_v2_out
"""

import os
import json
import argparse
from collections import Counter

os.environ.setdefault("TRANSFORMERS_OFFLINE", "1")
os.environ.setdefault("HF_HUB_OFFLINE", "1")
os.environ.setdefault("TOKENIZERS_PARALLELISM", "false")
# Pin to ONE GPU by default: with 2 visible GPUs the HF Trainer auto-wraps the
# model in nn.DataParallel, which replicates the 7B onto GPU0 and OOMs a 32GB
# V100. A 7B LoRA + gradient checkpointing fits on one V100. Override by
# exporting CUDA_VISIBLE_DEVICES before launching if you really want both.
os.environ.setdefault("CUDA_VISIBLE_DEVICES", "0")
os.environ.setdefault("PYTORCH_CUDA_ALLOC_CONF", "expandable_segments:True")

import torch
from torch.utils.data import Dataset
from transformers import (AutoTokenizer, AutoModelForCausalLM,
                          TrainingArguments, Trainer, DataCollatorForSeq2Seq)
from peft import LoraConfig, get_peft_model, TaskType

IGNORE = -100


class CorpusDataset(Dataset):
    """(prompt -> completion) pairs with the prompt tokens masked out of loss."""

    def __init__(self, rows, tokenizer, max_length=1024):
        self.tok = tokenizer
        self.max_length = max_length
        self.rows = rows

    def __len__(self):
        return len(self.rows)

    def _render_prompt(self, prompt):
        # Use the model's chat template when it has one; otherwise feed the raw
        # instruction (base completion models like CodeGen have no template).
        if self.tok.chat_template:
            return self.tok.apply_chat_template(
                [{"role": "user", "content": prompt}],
                tokenize=False, add_generation_prompt=True)
        return prompt + "\n"

    def __getitem__(self, idx):
        row = self.rows[idx]
        prompt = self._render_prompt(row["prompt"])
        completion = row["completion"].rstrip() + self.tok.eos_token

        p_ids = self.tok(prompt, add_special_tokens=False)["input_ids"]
        c_ids = self.tok(completion, add_special_tokens=False)["input_ids"]
        ids = (p_ids + c_ids)[:self.max_length]
        labels = ([IGNORE] * len(p_ids) + c_ids)[:self.max_length]
        # If truncation ate the whole completion, keep at least the tail of it.
        if all(l == IGNORE for l in labels):
            labels = ids.copy()
        return {"input_ids": ids,
                "attention_mask": [1] * len(ids),
                "labels": labels}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--corpus", default="sft_corpus.jsonl")
    ap.add_argument("--base", default=os.environ.get("RTLCODER_PATH", "rtlcoder"),
                    help="base model dir (HF) to warm-start")
    ap.add_argument("--out", default="sft_v2_out")
    ap.add_argument("--epochs", type=int, default=4)
    ap.add_argument("--batch", type=int, default=1)
    ap.add_argument("--grad_accum", type=int, default=16)
    ap.add_argument("--lr", type=float, default=1e-4)
    ap.add_argument("--max_length", type=int, default=4096)
    ap.add_argument("--lora_r", type=int, default=16)
    args = ap.parse_args()

    rows = [json.loads(l) for l in open(args.corpus)]
    if not rows:
        raise SystemExit(f"empty corpus: {args.corpus} (run gen_sft_corpus.py first)")
    print(f"corpus: {len(rows)} oracle-verified pairs from {args.corpus}")
    print("  by family:", dict(Counter(r.get("family", "?") for r in rows)))
    print("  by style :", dict(Counter(r.get("style", "?") for r in rows)))

    tok = AutoTokenizer.from_pretrained(args.base)
    if tok.pad_token is None:
        tok.pad_token = tok.eos_token

    model = AutoModelForCausalLM.from_pretrained(
        args.base, torch_dtype=torch.bfloat16, device_map={"": 0})
    model.config.use_cache = False

    # F4: train at 4096 so the largest transposed FIRs (fir32/firr32 ~750+ tokens
    # of completion, plus the interface prompt) are never truncated mid-module.
    # RTLCoder is deepseek-coder-based (16k context); the tokenizer's 2048 is a
    # misconfigured default. Verify the MODEL actually supports the requested
    # length and clamp with a loud warning rather than silently training on
    # truncated RTL.
    max_pos = getattr(model.config, "max_position_embeddings", None)
    if max_pos and args.max_length > max_pos:
        print(f"[F4][warn] --max_length {args.max_length} > model "
              f"max_position_embeddings {max_pos}; clamping to {max_pos}")
        args.max_length = max_pos
    else:
        print(f"[F4] training at max_length={args.max_length} "
              f"(model supports {max_pos})")

    lora = LoraConfig(
        task_type=TaskType.CAUSAL_LM, r=args.lora_r, lora_alpha=2 * args.lora_r,
        lora_dropout=0.05, bias="none",
        target_modules=["q_proj", "k_proj", "v_proj", "o_proj"])
    model = get_peft_model(model, lora)
    model.enable_input_require_grads()   # required for gradient checkpointing + PEFT
    model.print_trainable_parameters()

    ds = CorpusDataset(rows, tok, max_length=args.max_length)
    collator = DataCollatorForSeq2Seq(tok, model=model, padding=True,
                                      pad_to_multiple_of=8, label_pad_token_id=IGNORE)

    targs = TrainingArguments(
        output_dir=args.out, num_train_epochs=args.epochs,
        per_device_train_batch_size=args.batch,
        gradient_accumulation_steps=args.grad_accum,
        learning_rate=args.lr, lr_scheduler_type="cosine", warmup_ratio=0.05,
        bf16=True, logging_steps=10, save_strategy="epoch", report_to="none",
        gradient_checkpointing=True,
        gradient_checkpointing_kwargs={"use_reentrant": False},
        dataloader_num_workers=0, remove_unused_columns=False)

    trainer = Trainer(model=model, args=targs, train_dataset=ds,
                      data_collator=collator)
    print(f"\nSFT warm-start: {len(ds)} samples, {args.epochs} epochs "
          f"(loss masked to completion only)")
    trainer.train()

    model.save_pretrained(args.out)
    tok.save_pretrained(args.out)
    print(f"\nLoRA adapter -> {args.out}/")
    print("Next: probe competence with the oracle, e.g.\n"
          f"  python gen_accel_candidates.py --adapter {args.out} --n 24\n"
          "  (then score with oracle.score) -> did correct-rate jump from ~2%? "
          "If yes, GRPO on the V2 oracle is worth running.")


if __name__ == "__main__":
    main()

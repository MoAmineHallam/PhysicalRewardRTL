#!/usr/bin/env python3
"""
grpo_train_v2.py  -  Phase 3 GRPO, anti-forgetting recipe.

Changes vs v1:
  - Trains a FRESH LoRA on base RTLCoder (no SFT warm-start) to avoid the
    memorization/forgetting seen with the SFT model.
  - KL reference is the BASE model, obtained by disabling the LoRA adapter
    (no second model loaded -> ~half the memory).
  - Loss is length-normalized (mean per-token log-prob, not sum) for stability.
  - Design sampling weighted toward high-variance designs (the flat ones give
    no gradient, so they are down-weighted).

Usage:
    python grpo_train_v2.py [--out grpo_v2] [--steps 500] [--group_size 6]
                            [--lr 1e-5] [--kl_coef 0.1]
"""

import sys
import os
import json
import argparse
import random
import subprocess
import tempfile
import re

os.environ["TRANSFORMERS_OFFLINE"] = "1"

import torch
import torch.nn.functional as F
from transformers import AutoTokenizer, AutoModelForCausalLM
from peft import LoraConfig, get_peft_model, TaskType

# Reuse the design specs from grpo_train (same prompts)
from grpo_train import DESIGNS, extract_verilog, score_verilog

# Sampling weights: down-weight designs that score flat (no gradient signal).
#   edge_detector(0) some variance | alu_mux(1) flat | comb_always(2) high var
#   bcd_counter(3) high var | bit_manip(4) high var | dff_array(5) flat | shift_reg(6) flat
DESIGN_WEIGHTS = {
    0: 1.0,   # edge_detector
    1: 0.2,   # alu_mux   (flat at 0.967)
    2: 2.0,   # comb_always
    3: 2.0,   # bcd_counter
    4: 2.0,   # bit_manip
    5: 0.2,   # dff_array (flat at 1.0)
    6: 0.2,   # shift_reg (flat at 1.0)
}


def gen_token_logprobs(model, tokenizer, prompt_ids, gen_ids, use_adapter=True):
    """
    Mean per-token log-prob of gen_ids under the model.
    If use_adapter=False, disable the LoRA adapter (= base model = KL reference).
    """
    full_ids = torch.cat([prompt_ids, gen_ids.unsqueeze(0)], dim=1)
    ctx = torch.amp.autocast("cuda", dtype=torch.bfloat16)
    if use_adapter:
        with ctx:
            logits = model(full_ids).logits
    else:
        with model.disable_adapter(), torch.no_grad(), ctx:
            logits = model(full_ids).logits
    prompt_len = prompt_ids.shape[1]
    gen_logits = logits[0, prompt_len - 1: prompt_len - 1 + gen_ids.shape[0], :]
    log_probs = F.log_softmax(gen_logits.float(), dim=-1)
    tok_lp = log_probs[torch.arange(gen_ids.shape[0]), gen_ids]
    return tok_lp.mean()   # length-normalized


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--base_model",  default="rtlcoder")
    parser.add_argument("--out",         default="grpo_v2")
    parser.add_argument("--steps",       type=int,   default=500)
    parser.add_argument("--group_size",  type=int,   default=6)
    parser.add_argument("--max_tokens",  type=int,   default=512)
    parser.add_argument("--temperature", type=float, default=1.0)
    parser.add_argument("--lr",          type=float, default=1e-5)
    parser.add_argument("--kl_coef",     type=float, default=0.1)
    parser.add_argument("--log",         default="grpo_v2_log.jsonl")
    args = parser.parse_args()

    os.makedirs(args.out, exist_ok=True)

    print("Loading base model + fresh LoRA...")
    tokenizer = AutoTokenizer.from_pretrained(args.base_model)
    if tokenizer.pad_token is None:
        tokenizer.pad_token = tokenizer.eos_token

    base = AutoModelForCausalLM.from_pretrained(
        args.base_model, torch_dtype=torch.bfloat16, device_map="auto"
    )
    base.config.use_cache = True  # needed for generate

    lora_config = LoraConfig(
        task_type=TaskType.CAUSAL_LM,
        r=16, lora_alpha=32, lora_dropout=0.05,
        target_modules=["q_proj", "v_proj", "k_proj", "o_proj"],
        bias="none",
    )
    model = get_peft_model(base, lora_config)
    model.print_trainable_parameters()

    optimizer = torch.optim.AdamW(
        [p for p in model.parameters() if p.requires_grad], lr=args.lr
    )

    # weighted design pool
    pool = [(s, n, sp) for (s, n, sp) in DESIGNS]
    weights = [DESIGN_WEIGHTS[s] for (s, n, sp) in pool]

    log_file = open(args.log, "a")
    print(f"\nStarting GRPO-v2: {args.steps} steps, group_size={args.group_size}, "
          f"kl_coef={args.kl_coef}, lr={args.lr}\n")

    dev = next(model.parameters()).device

    for step in range(args.steps):
        sel_id, design_name, spec = random.choices(pool, weights=weights, k=1)[0]
        messages = [{"role": "user", "content": spec}]
        prompt_text = tokenizer.apply_chat_template(
            messages, tokenize=False, add_generation_prompt=True
        )
        prompt_ids = tokenizer(
            prompt_text, return_tensors="pt", return_token_type_ids=False
        ).input_ids.to(dev)

        # ── generate group ────────────────────────────────────────────────────
        rewards = []
        gen_ids_list = []
        model.eval()
        for _ in range(args.group_size):
            with torch.no_grad():
                out = model.generate(
                    prompt_ids,
                    max_new_tokens=args.max_tokens,
                    temperature=args.temperature,
                    do_sample=True,
                    pad_token_id=tokenizer.eos_token_id,
                )
            gen_ids = out[0, prompt_ids.shape[1]:]
            text = tokenizer.decode(gen_ids, skip_special_tokens=True)
            verilog = extract_verilog(text, design_name)
            reward = score_verilog(verilog, sel_id) if verilog else 0.0
            rewards.append(reward)
            gen_ids_list.append(gen_ids)
        model.train()

        r = torch.tensor(rewards, dtype=torch.float32)
        if r.std() < 1e-6:
            print(f"[{step:4d}] {design_name:15s}  "
                  f"rewards={[f'{x:.3f}' for x in rewards]}  (skipped)", flush=True)
            log_file.write(json.dumps({"step": step, "design": design_name,
                                       "rewards": rewards, "loss": None}) + "\n")
            log_file.flush()
            continue

        advantages = (r - r.mean()) / (r.std() + 1e-8)

        # ── policy gradient + KL-to-base ──────────────────────────────────────
        optimizer.zero_grad()
        total_loss_val = 0.0
        for gen_ids, adv in zip(gen_ids_list, advantages.tolist()):
            lp     = gen_token_logprobs(model, tokenizer, prompt_ids, gen_ids, use_adapter=True)
            base_lp = gen_token_logprobs(model, tokenizer, prompt_ids, gen_ids, use_adapter=False)
            kl = lp - base_lp.detach()
            loss = (-adv * lp + args.kl_coef * kl) / args.group_size
            loss.backward()
            total_loss_val += loss.item()

        torch.nn.utils.clip_grad_norm_(
            [p for p in model.parameters() if p.requires_grad], 1.0
        )
        optimizer.step()

        mean_r = r.mean().item()
        print(f"[{step:4d}] {design_name:15s}  "
              f"rewards={[f'{x:.3f}' for x in rewards]}  "
              f"mean={mean_r:.3f}  loss={total_loss_val:.4f}", flush=True)

        log_file.write(json.dumps({
            "step": step, "design": design_name, "rewards": rewards,
            "mean_r": mean_r, "max_r": r.max().item(), "loss": total_loss_val,
        }) + "\n")
        log_file.flush()

        if (step + 1) % 100 == 0:
            ckpt = os.path.join(args.out, f"step_{step+1}")
            model.save_pretrained(ckpt)
            print(f"  -> checkpoint: {ckpt}", flush=True)

    model.save_pretrained(args.out)
    tokenizer.save_pretrained(args.out)
    log_file.close()
    print(f"\nGRPO-v2 done. Model saved to {args.out}/")


if __name__ == "__main__":
    main()

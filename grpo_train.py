#!/usr/bin/env python3
"""
grpo_train.py  -  Phase 3 GRPO online RL training against hardware reward.

Loads the SFT-warmed LoRA model, then runs Group Relative Policy Optimization:
  - Sample K candidates per prompt from current policy
  - Score each with score_candidate.py (hardware reward)
  - Normalize rewards within group → advantages
  - Policy gradient update on LoRA parameters

Usage:
    python grpo_train.py [--sft_model sft_out] [--out grpo_out]
                         [--steps 200] [--group_size 4] [--lr 1e-5]
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
from peft import PeftModel

# ── design specs (same as build_dataset.py) ───────────────────────────────────
DESIGNS = [
    (0, "edge_detector", """\
Please write a Verilog module named `edge_detector` that detects rising edges.

Ports:
  input  clk    - clock
  input  rst_n  - active-low synchronous reset
  input  in     - single-bit signal to monitor
  output rise   - goes high for exactly one clock cycle on each 0->1 transition of `in`

Behavior:
  - Registered (clocked) design; all outputs update on posedge clk.
  - On !rst_n: rise <= 0.
  - rise is 1 when in==1 and the previous registered value of in==0, else 0.
"""),
    (1, "alu_mux", """\
Please write a Verilog module named `alu_mux` implementing a registered ALU with op-select mux.

Ports:
  input  clk         - clock
  input  rst_n       - active-low synchronous reset
  input  [3:0] a     - operand A
  input  [3:0] b     - operand B
  input  [2:0] op    - operation select
  output reg [3:0] result

Operations (op):
  0 -> result = a + b
  1 -> result = ~a
  2 -> result = a
  3 -> result = b
  4 -> result = a ^ b
  5 -> result = ~a
  6 -> result = a
  7 -> result = b

Behavior:
  - Registered: result updates on posedge clk.
  - On !rst_n: result <= 0.
"""),
    (2, "comb_always", """\
Please write a Verilog module named `comb_always` that implements a priority encoder.

Ports:
  input  clk         - clock
  input  rst_n       - active-low synchronous reset
  input  [7:0] in    - 8-bit input
  output [2:0] out   - index of highest set bit (priority: bit 7 > bit 0)
  output valid       - 1 if any bit of `in` is set, else 0

Behavior:
  - Registered: out and valid update on posedge clk.
  - On !rst_n: out <= 0, valid <= 0.
  - Priority: highest-index set bit wins.
  - valid=1 iff in != 0.
"""),
    (3, "bcd_counter", """\
Please write a Verilog module named `bcd_counter` that counts 0-99 in BCD.

Ports:
  input  clk         - clock
  input  rst_n       - active-low synchronous reset
  input  en          - count enable
  output [3:0] ones  - BCD ones digit (0-9)
  output [3:0] tens  - BCD tens digit (0-9)

Behavior:
  - Registered: ones and tens update on posedge clk.
  - On !rst_n: ones <= 0, tens <= 0.
  - When en=1: increment; ones wraps 9->0 and tens increments; at 99->00.
  - When en=0: hold.
"""),
    (4, "bit_manip", """\
Please write a Verilog module named `bit_manip` that reverses bits and counts population.

Ports:
  input  clk           - clock
  input  rst_n         - active-low synchronous reset
  input  [7:0] in      - 8-bit input
  output [7:0] reversed
  output [3:0] popcount

Behavior:
  - Registered: outputs update on posedge clk.
  - On !rst_n: reversed <= 0, popcount <= 0.
  - reversed[i] = in[7-i].
  - popcount = number of 1-bits in in.
"""),
    (5, "dff_array", """\
Please write a Verilog module named `dff_array` implementing an 8-bit enabled D flip-flop array.

Ports:
  input  clk, rst_n, en
  input  [7:0] d
  output [7:0] q

Behavior:
  - On !rst_n: q <= 0. When en=1: q <= d. When en=0: hold.
"""),
    (6, "shift_reg", """\
Please write a Verilog module named `shift_reg` implementing an 8-bit SIPO shift register.

Ports:
  input  clk, rst_n, en, sin
  output [7:0] q

Behavior:
  - On !rst_n: q <= 0. When en=1: q <= {q[6:0], sin}. When en=0: hold.
"""),
]

SCORE_SCRIPT = os.path.join(os.path.dirname(__file__), "score_candidate.py")


def extract_verilog(text: str, module_name: str) -> str | None:
    m = re.search(rf'(?s)(module\s+{re.escape(module_name)}\b.*?endmodule)', text)
    if m:
        return m.group(1)
    m = re.search(r'(?s)(module\s+\w+\b.*?endmodule)', text)
    return m.group(1) if m else None


def score_verilog(verilog: str, sel_id: int) -> float:
    with tempfile.NamedTemporaryFile(suffix='.v', mode='w', delete=False) as f:
        f.write(verilog)
        tmp = f.name
    try:
        cp = subprocess.run(
            [sys.executable, SCORE_SCRIPT, tmp, str(sel_id)],
            capture_output=True, text=True, timeout=180
        )
        return float(cp.stdout.strip()) if cp.returncode == 0 else 0.0
    except Exception:
        return 0.0
    finally:
        os.unlink(tmp)


def generate_candidate(model, tokenizer, prompt_ids, max_new_tokens, temperature):
    """Generate one candidate; return (token_ids, log_probs) for generated tokens only."""
    with torch.no_grad():
        out = model.generate(
            prompt_ids,
            max_new_tokens=max_new_tokens,
            temperature=temperature,
            do_sample=True,
            pad_token_id=tokenizer.eos_token_id,
            return_dict_in_generate=True,
            output_scores=True,
        )
    gen_ids = out.sequences[:, prompt_ids.shape[1]:]  # generated tokens only
    # Stack scores → (seq_len, vocab)
    scores = torch.stack(out.scores, dim=1)           # (1, seq_len, vocab)
    log_probs = F.log_softmax(scores, dim=-1)
    # Gather log-prob of each chosen token
    tok_log_probs = log_probs[0, torch.arange(gen_ids.shape[1]), gen_ids[0]]
    return gen_ids[0], tok_log_probs


def sequence_log_prob(model, tokenizer, prompt_ids, gen_ids):
    """Recompute log-prob of gen_ids under current model (for gradient)."""
    full_ids = torch.cat([prompt_ids, gen_ids.unsqueeze(0)], dim=1)
    with torch.cuda.amp.autocast(dtype=torch.bfloat16):
        logits = model(full_ids).logits  # (1, full_len, vocab)
    prompt_len = prompt_ids.shape[1]
    gen_logits = logits[0, prompt_len - 1: prompt_len - 1 + gen_ids.shape[0], :]
    log_probs = F.log_softmax(gen_logits, dim=-1)
    tok_log_probs = log_probs[torch.arange(gen_ids.shape[0]), gen_ids]
    return tok_log_probs.sum()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--sft_model",   default="sft_out")
    parser.add_argument("--base_model",  default="rtlcoder")
    parser.add_argument("--out",         default="grpo_out")
    parser.add_argument("--steps",       type=int,   default=200)
    parser.add_argument("--group_size",  type=int,   default=4)
    parser.add_argument("--max_tokens",  type=int,   default=512)
    parser.add_argument("--temperature", type=float, default=0.9)
    parser.add_argument("--lr",          type=float, default=1e-5)
    parser.add_argument("--kl_coef",     type=float, default=0.05)
    parser.add_argument("--log",         default="grpo_log.jsonl")
    args = parser.parse_args()

    os.makedirs(args.out, exist_ok=True)

    print("Loading tokenizer and model...")
    tokenizer = AutoTokenizer.from_pretrained(args.sft_model)
    if tokenizer.pad_token is None:
        tokenizer.pad_token = tokenizer.eos_token

    base = AutoModelForCausalLM.from_pretrained(
        args.base_model, torch_dtype=torch.bfloat16, device_map="auto"
    )
    model = PeftModel.from_pretrained(base, args.sft_model, is_trainable=True)
    model.train()

    # Frozen reference model for KL penalty
    ref_base = AutoModelForCausalLM.from_pretrained(
        args.base_model, torch_dtype=torch.bfloat16, device_map="auto"
    )
    ref_model = PeftModel.from_pretrained(ref_base, args.sft_model, is_trainable=False)
    ref_model.eval()

    optimizer = torch.optim.AdamW(
        [p for p in model.parameters() if p.requires_grad], lr=args.lr
    )

    log_file = open(args.log, "a")
    print(f"Starting GRPO: {args.steps} steps, group_size={args.group_size}\n")

    for step in range(args.steps):
        sel_id, design_name, spec = random.choice(DESIGNS)
        messages = [{"role": "user", "content": spec}]
        prompt_text = tokenizer.apply_chat_template(
            messages, tokenize=False, add_generation_prompt=True
        )
        prompt_ids = tokenizer(
            prompt_text, return_tensors="pt", return_token_type_ids=False
        ).input_ids.to(next(model.parameters()).device)

        # ── generate group ────────────────────────────────────────────────────
        candidates = []
        rewards    = []
        gen_ids_list = []

        for _ in range(args.group_size):
            gen_ids, _ = generate_candidate(
                model, tokenizer, prompt_ids, args.max_tokens, args.temperature
            )
            text = tokenizer.decode(gen_ids, skip_special_tokens=True)
            verilog = extract_verilog(text, design_name)
            reward = score_verilog(verilog, sel_id) if verilog else 0.0
            candidates.append(text)
            rewards.append(reward)
            gen_ids_list.append(gen_ids)

        # ── group-relative advantages ─────────────────────────────────────────
        r = torch.tensor(rewards, dtype=torch.float32)
        if r.std() < 1e-6:
            # all same reward — no gradient signal, skip update
            mean_r = r.mean().item()
            print(f"[{step:4d}] {design_name:15s}  rewards={[f'{x:.3f}' for x in rewards]}  (skipped, no variance)", flush=True)
            log_file.write(json.dumps({"step": step, "design": design_name,
                                       "rewards": rewards, "loss": None}) + "\n")
            log_file.flush()
            continue

        advantages = (r - r.mean()) / (r.std() + 1e-8)

        # ── policy gradient loss ──────────────────────────────────────────────
        loss = torch.tensor(0.0, requires_grad=True, device=prompt_ids.device,
                            dtype=torch.bfloat16)
        for gen_ids, adv in zip(gen_ids_list, advantages.tolist()):
            lp = sequence_log_prob(model, tokenizer, prompt_ids, gen_ids)
            kl_lp = sequence_log_prob(ref_model, tokenizer, prompt_ids, gen_ids)
            kl = (lp - kl_lp.detach())
            loss = loss + (-adv * lp + args.kl_coef * kl)

        loss = loss / args.group_size

        optimizer.zero_grad()
        loss.backward()
        torch.nn.utils.clip_grad_norm_(
            [p for p in model.parameters() if p.requires_grad], 1.0
        )
        optimizer.step()

        mean_r = r.mean().item()
        max_r  = r.max().item()
        print(f"[{step:4d}] {design_name:15s}  "
              f"rewards={[f'{x:.3f}' for x in rewards]}  "
              f"mean={mean_r:.3f}  loss={loss.item():.4f}", flush=True)

        log_file.write(json.dumps({
            "step":    step,
            "design":  design_name,
            "rewards": rewards,
            "mean_r":  mean_r,
            "max_r":   max_r,
            "loss":    loss.item(),
        }) + "\n")
        log_file.flush()

        # save checkpoint every 50 steps
        if (step + 1) % 50 == 0:
            ckpt = os.path.join(args.out, f"step_{step+1}")
            model.save_pretrained(ckpt)
            print(f"  → checkpoint saved: {ckpt}", flush=True)

    # final save
    model.save_pretrained(args.out)
    tokenizer.save_pretrained(args.out)
    log_file.close()
    print(f"\nGRPO done. Model saved to {args.out}/")


if __name__ == "__main__":
    main()

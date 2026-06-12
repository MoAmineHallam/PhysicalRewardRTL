#!/usr/bin/env python3
"""
grpo_train_v3.py  -  Stage 8: GRPO on the 966-design hardware-validated pool.

Changes vs grpo_train_v2 (7 hardcoded designs):
  - Pool = manifest designs confirmed on silicon (hw_bad.json["good"], 966),
    with the SAME prompts build_dataset.py uses (spec + exact module
    interface), so the dataset statistics transfer directly.
  - Design sampling weighted by within-design reward std from
    analyze_dataset.py (design_weights.json): saturated designs are barely
    sampled, live designs (graycnt, tccnt, shifters...) carry the gradient.
  - The whole group is sampled in ONE batched generate() call
    (num_return_sequences, stop at 'endmodule') -- the build_dataset fast
    path, ~10-20x faster than v2's sequential loop.
  - Rewards scored in-process with score_candidate.score_rtl (dense masked
    Hamming vs the silicon-certified golden), parallel across the group.
  - Precision picked automatically: bf16 on Ampere+ (the borrowed-2xA100
    plan), fp16 on V100 (no bf16 hardware) with LoRA params upcast to fp32
    + GradScaler so 1e-5-sized updates don't underflow.
  - KL to the base model via adapter-disable (no second model in memory),
    k3 estimator exp(r) - r - 1 with r = base_lp - lp.

Run from /zeng_gk/Amine/mas (so the default rtlcoder path resolves):
    python fpga/grpo_train_v3.py --steps 600 --group_size 8
    python fpga/grpo_train_v3.py --resume grpo_v3/step_200    # continue
Outputs: grpo_v3/ (LoRA adapter checkpoints) + grpo_v3_log.jsonl.
"""

import os
import sys
import json
import time
import random
import argparse
import concurrent.futures as cf

os.environ.setdefault("TRANSFORMERS_OFFLINE", "1")
os.environ.setdefault("HF_HUB_OFFLINE", "1")

import torch
import torch.nn.functional as F
from transformers import AutoTokenizer, AutoModelForCausalLM
from peft import LoraConfig, get_peft_model, PeftModel, TaskType

import score_candidate as SC
from build_dataset import load_pool, extract_verilog, LLM_DIR

HERE = os.path.dirname(os.path.abspath(__file__))
WEIGHT_FLOOR = 0.05  # same floor analyze_dataset uses


def load_design_weights(path, pool):
    """Per-design sampling weights aligned with the pool order."""
    if path and os.path.exists(path):
        w = json.load(open(path))["weights"]
        missing = [rec["name"] for rec, _ in pool if rec["name"] not in w]
        if missing:
            print(f"[warn] {len(missing)} pool designs missing from {path}; "
                  f"floor weight used (e.g. {missing[0]})", file=sys.stderr)
        return [w.get(rec["name"], WEIGHT_FLOOR) for rec, _ in pool]
    print(f"[warn] no weights file at {path}: uniform sampling",
          file=sys.stderr)
    return [1.0] * len(pool)


def pick_dtype(name):
    if name == "bf16":
        return torch.bfloat16
    if name == "fp16":
        return torch.float16
    # auto: bf16 needs compute capability >= 8.0 (Ampere); V100 is 7.0 and
    # PyTorch only emulates bf16 there (the 10-20x generation slowdown)
    major, _ = torch.cuda.get_device_capability(0)
    return torch.bfloat16 if major >= 8 else torch.float16


def upcast_trainable(model, model_dtype):
    """LoRA params to fp32 (Adam updates at lr~1e-5 underflow in fp16).

    Recent peft casts activations to the adapter dtype and the result back,
    so mixed fp16 base / fp32 LoRA works; verified by a smoke forward+backward,
    reverting to the model dtype if this peft version can't handle it.
    """
    trainable = [p for p in model.parameters() if p.requires_grad]
    for p in trainable:
        p.data = p.data.float()
    try:
        dev = next(model.parameters()).device
        ids = torch.tensor([[1, 2, 3, 4]], device=dev)
        model(ids).logits.float().mean().backward()
        model.zero_grad(set_to_none=True)
        print("[dtype] LoRA params upcast to fp32 (smoke test passed)")
    except RuntimeError as e:
        for p in trainable:
            p.data = p.data.to(model_dtype)
        model.zero_grad(set_to_none=True)
        print(f"[dtype] fp32 LoRA upcast failed on this peft version ({e}); "
              f"keeping {model_dtype} params -- consider upgrading peft",
              file=sys.stderr)
    return trainable


def generate_group(model, tok, prompt_ids, k, max_new, temp):
    """k candidates in one batched call; returns list of trimmed token ids."""
    with torch.inference_mode():
        out = model.generate(
            prompt_ids,
            max_new_tokens=max_new,
            do_sample=True,
            temperature=temp,
            num_return_sequences=k,
            stop_strings=["endmodule"],
            tokenizer=tok,
            pad_token_id=tok.eos_token_id)
    plen = prompt_ids.shape[1]
    gens = []
    for seq in out:
        g = seq[plen:]
        nz = (g != tok.eos_token_id).nonzero()
        if nz.numel() == 0:
            continue
        gens.append(g[: int(nz[-1].item()) + 1].clone())
    return gens


def seq_mean_logprob(model, prompt_ids, gen_ids, use_adapter=True):
    """Mean per-token log-prob of gen_ids (length-normalized, fp32 softmax).

    use_adapter=False disables the LoRA adapter = base model = KL reference.
    """
    full = torch.cat([prompt_ids[0], gen_ids]).unsqueeze(0)
    if use_adapter:
        logits = model(full).logits
    else:
        with model.disable_adapter(), torch.no_grad():
            logits = model(full).logits
    plen = prompt_ids.shape[1]
    gl = logits[0, plen - 1: plen - 1 + gen_ids.shape[0], :]
    lp = F.log_softmax(gl.float(), dim=-1)
    return lp[torch.arange(gen_ids.shape[0], device=lp.device), gen_ids].mean()


def score_group(texts, name, cycles, manifest):
    """Dense hardware-grounded reward per candidate (parallel iverilog)."""
    def one(text):
        rtl = extract_verilog(text, name)
        if rtl is None:
            return 0.0
        rtl = rtl.encode("ascii", errors="replace").decode("ascii")
        try:
            return SC.score_rtl(rtl, name, cycles, manifest)
        except RuntimeError:
            return 0.0
    with cf.ThreadPoolExecutor(max_workers=min(8, len(texts))) as ex:
        return list(ex.map(one, texts))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--base_model",
                    default=os.environ.get(
                        "RTLCODER_PATH", os.path.join(LLM_DIR, "rtlcoder")))
    ap.add_argument("--out",         default="grpo_v3")
    ap.add_argument("--resume",      default=None,
                    help="adapter dir to continue from (else fresh LoRA)")
    ap.add_argument("--steps",       type=int,   default=600)
    ap.add_argument("--group_size",  type=int,   default=8)
    ap.add_argument("--max_tokens",  type=int,   default=512)
    ap.add_argument("--temperature", type=float, default=1.0)
    ap.add_argument("--lr",          type=float, default=1e-5)
    ap.add_argument("--kl_coef",     type=float, default=0.05)
    ap.add_argument("--cycles",      type=int,   default=SC.N_CYCLES_DEFAULT)
    ap.add_argument("--weights",
                    default=os.path.join(HERE, "design_weights.json"))
    ap.add_argument("--hw-report",   default=SC.HW_REPORT)
    ap.add_argument("--dtype", choices=["auto", "fp16", "bf16"],
                    default="auto")
    ap.add_argument("--save_every",  type=int,   default=50)
    ap.add_argument("--log",         default="grpo_v3_log.jsonl")
    ap.add_argument("--seed",        type=int,   default=0)
    args = ap.parse_args()

    random.seed(args.seed)
    torch.manual_seed(args.seed)
    os.makedirs(args.out, exist_ok=True)

    pool = load_pool(args.hw_report)
    weights = load_design_weights(args.weights, pool)
    manifest = SC.load_manifest()

    dtype = pick_dtype(args.dtype)
    print(f"Loading {args.base_model} ({dtype}, single GPU)...", flush=True)
    tok = AutoTokenizer.from_pretrained(args.base_model)
    if tok.pad_token is None:
        tok.pad_token = tok.eos_token
    base = AutoModelForCausalLM.from_pretrained(
        args.base_model, torch_dtype=dtype, device_map={"": 0})
    base.config.use_cache = True

    if args.resume:
        model = PeftModel.from_pretrained(base, args.resume,
                                          is_trainable=True)
        print(f"resumed adapter from {args.resume}")
    else:
        # lora_dropout=0: sampling and the gradient pass must see the same
        # policy, or the recomputed log-probs are off-policy noise
        model = get_peft_model(base, LoraConfig(
            task_type=TaskType.CAUSAL_LM,
            r=16, lora_alpha=32, lora_dropout=0.0,
            target_modules=["q_proj", "k_proj", "v_proj", "o_proj"],
            bias="none"))
    model.print_trainable_parameters()
    trainable = upcast_trainable(model, dtype)
    dev = next(model.parameters()).device

    opt = torch.optim.AdamW(trainable, lr=args.lr)
    scaler = torch.cuda.amp.GradScaler(enabled=(dtype == torch.float16))

    log_file = open(args.log, "a")
    recent = []  # rolling mean reward
    print(f"\nGRPO-v3: {len(pool)} designs, {args.steps} steps, "
          f"group={args.group_size}, kl={args.kl_coef}, lr={args.lr}, "
          f"{dtype}\n", flush=True)

    for step in range(args.steps):
        t0 = time.time()
        rec, spec = random.choices(pool, weights=weights, k=1)[0]
        name = rec["name"]
        chat = tok.apply_chat_template(
            [{"role": "user", "content": spec}],
            tokenize=False, add_generation_prompt=True)
        prompt_ids = tok(chat, return_tensors="pt",
                         return_token_type_ids=False).input_ids.to(dev)

        model.eval()
        gens = generate_group(model, tok, prompt_ids, args.group_size,
                              args.max_tokens, args.temperature)
        model.train()
        if not gens:
            continue
        texts = [tok.decode(g, skip_special_tokens=True) for g in gens]
        rewards = score_group(texts, name, args.cycles, manifest)
        recent = (recent + rewards)[-100 * args.group_size:]

        r = torch.tensor(rewards, dtype=torch.float32)
        entry = {"step": step, "design": name, "family": rec["family"],
                 "rewards": rewards, "mean_r": r.mean().item(),
                 "max_r": r.max().item()}
        if r.std() < 1e-6:
            # identical rewards: zero advantage everywhere, skip the update
            # (rare under variance-weighted sampling)
            print(f"[{step:4d}] {name:16s} mean={r.mean():.3f} (flat, skip) "
                  f"roll={sum(recent)/len(recent):.3f}", flush=True)
            entry["loss"] = None
            log_file.write(json.dumps(entry) + "\n")
            log_file.flush()
            continue
        adv = (r - r.mean()) / (r.std() + 1e-8)

        opt.zero_grad(set_to_none=True)
        loss_val, kl_val = 0.0, 0.0
        for g, a in zip(gens, adv.tolist()):
            lp = seq_mean_logprob(model, prompt_ids, g, use_adapter=True)
            base_lp = seq_mean_logprob(model, prompt_ids, g,
                                       use_adapter=False).detach()
            d = base_lp - lp
            kl = torch.exp(d) - d - 1.0          # k3 estimator, >= 0
            loss = (-a * lp + args.kl_coef * kl) / len(gens)
            scaler.scale(loss).backward()
            loss_val += loss.item()
            kl_val += kl.item() / len(gens)
        scaler.unscale_(opt)
        torch.nn.utils.clip_grad_norm_(trainable, 1.0)
        scaler.step(opt)
        scaler.update()

        entry.update(loss=loss_val, kl=kl_val)
        log_file.write(json.dumps(entry) + "\n")
        log_file.flush()
        print(f"[{step:4d}] {name:16s} "
              f"r={[f'{x:.2f}' for x in rewards]} mean={r.mean():.3f} "
              f"loss={loss_val:.4f} kl={kl_val:.4f} "
              f"roll={sum(recent)/len(recent):.3f} {time.time()-t0:.0f}s",
              flush=True)

        if (step + 1) % args.save_every == 0:
            ckpt = os.path.join(args.out, f"step_{step + 1}")
            model.save_pretrained(ckpt)
            print(f"  -> checkpoint: {ckpt}", flush=True)

    model.save_pretrained(args.out)
    tok.save_pretrained(args.out)
    log_file.close()
    print(f"\nGRPO-v3 done. Adapter saved to {args.out}/")


if __name__ == "__main__":
    main()

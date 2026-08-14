#!/usr/bin/env python3
"""
grpo_oracle.py  -  Stage 4: ONLINE correctness-gated Fmax GRPO (V2).

Unlike grpo_train_v5 (offline: reweights a FIXED pool of precomputed candidates),
this samples FRESH completions from the policy each step, so the policy can invent
faster implementations rather than just up-weighting existing ones. Affordable
because the reward needs no Vivado per sample:

  per candidate:  oracle.score (iverilog, ~1-2s)  ->  correct? : not
                  correct   -> reward = surrogate Fmax (RTL-text MLP, instant)
                  incorrect -> reward = 0   (the correctness GATE)
  group-normalise the rewards per design -> advantage; GRPO update with KL to the
  FROZEN SFT policy (F3: load the SFT adapter as both a trainable 'default' and a
  frozen 'ref'; KL anchors to 'ref', so the leash pulls toward SFT competence,
  not the base model).

Because incorrect completions get 0 and correct ones get their (positive) Fmax,
one reward simultaneously (a) keeps correctness and (b) pushes toward the fast
tail. Designs whose sampled group is all-wrong or all-same-reward give no gradient
and are skipped.

Phase-B hardening applied here: F2 (surrogate Fmax clamped to [5,500] so it can't
be gamed to inf), F3 (frozen-SFT KL ref), F4 (max-tokens 1536 so fir32/firr32
transposed fit), F8 (stop+trim at endmodule so the gradient ignores post-module
junk), F10 (train on ALL train-split designs, not the 8 pilot prompts). The
train-split design list is gen_sft_corpus.designs(exclude_holdout=True), and a
hard guard refuses to run if any §5 held-out design leaks in.

Start from sft_v5; validate AFTER on Vivado/silicon (surrogate re-anchored to
real synthesis). Held-out eval is eval_holdout.py (NEVER trained on).

    python grpo_oracle.py --sft sft_v5_out --surrogate surrogate_v2.pt \
        --base /zeng_gk/Amine/mas/rtlcoder --steps 400 --group 8 --out grpo_v7
"""

import os
import re
import json
import time
import random
import hashlib
import argparse

os.environ.setdefault("TRANSFORMERS_OFFLINE", "1")
os.environ.setdefault("HF_HUB_OFFLINE", "1")
os.environ.setdefault("TOKENIZERS_PARALLELISM", "false")
os.environ.setdefault("CUDA_VISIBLE_DEVICES", "0")

import numpy as np
import torch
import torch.nn as nn
import torch.nn.functional as F
from transformers import AutoTokenizer, AutoModelForCausalLM
from peft import PeftModel

import oracle
import gen_sft_corpus as GSC
from build_dataset import extract_verilog
from probe_competence import probe_prompts
from surrogate_train import (extract_features, feature_dict, FEAT_NAMES,
                             LOGF_MIN, LOGF_MAX, clamp_fmax)
from canonicalize import (canonicalize as canon_of, canon_hash,
                          struct_feature_dict, Unsupported)
from grpo_train_v3 import pick_dtype, upcast_trainable


def train_split_designs():
    """F10: GRPO trains on ALL train-split designs (dozens of prompts), not the
    8-design pilot list -- more prompts reduce per-prompt overfitting and cover
    the grid. The train split is exactly gen_sft_corpus.designs(exclude_holdout=
    True), so the frozen §5 held-out designs can NEVER leak into RL. cordic is
    excluded too (invariant #5: documented 7B negative result, stays out of RL --
    its groups are always all-wrong, pure wasted compute)."""
    return [name for name, fam, _, _ in GSC.designs(exclude_holdout=True)
            if fam != "cordic"]


def load_surrogate(path, device):
    ck = torch.load(path, map_location=device)
    nfeat = len(ck["feat_names"])
    net = nn.Sequential(nn.Linear(nfeat, 32), nn.ReLU(),
                        nn.Linear(32, 32), nn.ReLU(), nn.Linear(32, 1))
    net.load_state_dict(ck["state"]); net.eval().to(device)
    mu = torch.tensor(ck["mu"], dtype=torch.float32, device=device)
    sd = torch.tensor(ck["sd"], dtype=torch.float32, device=device)
    log_target = ck.get("log_target", True)

    @torch.no_grad()
    def predict_fmax(rtl_text):
        # pass the CHECKPOINT's feature list: old 9-feature nets keep working,
        # v3 (12-feature) nets get the comparator features (D2)
        x = torch.tensor(extract_features(rtl_text, ck["feat_names"]),
                         dtype=torch.float32, device=device)
        out = net(((x - mu) / sd).unsqueeze(0)).item()
        if log_target:
            # F2: clamp in LOG space BEFORE exp, so an out-of-range MLP head can
            # never overflow to +inf (the poly4 gaming mode). exp(clamped) is
            # then guaranteed in [5, 500]; clamp_fmax is a belt-and-braces cap.
            out = min(max(out, LOGF_MIN), LOGF_MAX)
            return clamp_fmax(float(np.exp(out)))
        return clamp_fmax(float(out))
    return predict_fmax


def load_rf_struct(path):
    """rf_struct reward: RandomForest over CANONICAL structural features.

    Returns predict(rtl) -> (reward_mhz, meta). Three gates, all preregistered:
      1. the raw RTL must already have passed the oracle (caller's job);
      2. the canonicaliser must accept it -- Unsupported => reward 0;
      3. the canonical form must COMPILE -- invalid => reward 0.
    Gate 3 exists because two tokenizer defects once produced canonical text that
    satisfied every byte-level self-check while being invalid Verilog. A reward
    computed on text that is not Verilog is meaningless, so it scores 0 and says
    why in the log rather than silently feeding the optimizer noise.

    Compilation is cached on the canonical hash: candidates repeat constantly
    within and across groups, and the gate is deterministic in the canonical
    text, so the cache changes cost only.
    """
    import joblib
    from canonicalize import (canonicalize, canon_hash, struct_features,
                              compiles, Unsupported, CANON_VERSION,
                              STRUCT_FEATURES)
    ck = joblib.load(path)
    model, feats = ck["model"], ck["features"]
    if list(feats) != list(STRUCT_FEATURES):
        raise SystemExit(f"rf_struct feature mismatch: artifact has {feats}, "
                         f"canonicalize.py has {list(STRUCT_FEATURES)}")
    if ck.get("canon_version") != CANON_VERSION:
        raise SystemExit(f"rf_struct was trained under canonicaliser "
                         f"v{ck.get('canon_version')} but this is "
                         f"v{CANON_VERSION} -- refusing to mix versions")
    compile_cache = {}

    def predict(rtl):
        try:
            canon, _ = canonicalize(rtl, "lexical")
        except Unsupported as e:
            return 0.0, {"gate": "unsupported", "detail": str(e)[:200]}
        h = canon_hash(canon)
        if h not in compile_cache:
            compile_cache[h] = compiles(canon)
        ok, err = compile_cache[h]
        if not ok:
            return 0.0, {"gate": "canon_compile_fail", "canon_hash": h,
                         "detail": err[-200:]}
        x = struct_features(canon)
        lg = float(model.predict([x])[0])
        lg = min(max(lg, LOGF_MIN), LOGF_MAX)     # F2 clamp, in log space
        return clamp_fmax(float(np.exp(lg))), {
            "gate": "ok", "canon_hash": h,
            "struct": {k: float(v) for k, v in zip(STRUCT_FEATURES, x)}}
    return predict


def save_policy(model, path):
    """Save ONLY the trainable policy adapter ('default'); the frozen 'ref' is a
    copy of the SFT adapter we never need to reload. Older peft versions have no
    selected_adapters kwarg -- fall back to saving everything ('ref' lands in a
    subdir; harmless) rather than crashing away a training run at checkpoint time."""
    try:
        model.save_pretrained(path, selected_adapters=["default"])
    except TypeError:
        model.save_pretrained(path)


def seq_logprob_adapter(model, prompt_ids, gen_ids, adapter, grad):
    """Mean per-token log-prob of gen_ids under a NAMED PEFT adapter.

    F3: the KL reference must be the FROZEN SFT policy, not the base model. We
    load the SFT adapter twice -- 'default' (trainable policy) and 'ref' (frozen)
    -- and select which one is active per forward pass. grad=False (the reference
    path) wraps the forward in no_grad; the caller detaches. Length-normalised,
    fp32 softmax (matches grpo_train_v3.seq_mean_logprob, but adapter-selectable)."""
    model.set_adapter(adapter)
    full = torch.cat([prompt_ids[0], gen_ids]).unsqueeze(0)
    if grad:
        logits = model(full).logits
    else:
        with torch.no_grad():
            logits = model(full).logits
    plen = prompt_ids.shape[1]
    gl = logits[0, plen - 1: plen - 1 + gen_ids.shape[0], :]
    lp = F.log_softmax(gl.float(), dim=-1)
    return lp[torch.arange(gen_ids.shape[0], device=lp.device), gen_ids].mean()


def trim_endmodule(gen_ids, tok):
    """F8: cut gen_ids at the end of the FIRST 'endmodule' so the GRPO gradient
    (logprob over the whole sampled sequence) is not diluted by post-endmodule
    junk -- the reward is already computed on the extracted module only. Decode
    incrementally and keep the shortest token prefix whose text contains a
    complete 'endmodule'; fall back to the full (eos-trimmed) sequence."""
    # fast path: trim trailing eos/pad first
    nz = (gen_ids != tok.eos_token_id).nonzero()
    if nz.numel():
        gen_ids = gen_ids[: int(nz[-1].item()) + 1]
    full_txt = tok.decode(gen_ids, skip_special_tokens=True)
    pos = full_txt.find("endmodule")
    if pos < 0:
        return gen_ids, full_txt
    target = full_txt[: pos + len("endmodule")]
    # find the smallest prefix of tokens whose decode already covers `target`
    lo, hi = 1, gen_ids.shape[0]
    while lo < hi:
        mid = (lo + hi) // 2
        if "endmodule" in tok.decode(gen_ids[:mid], skip_special_tokens=True):
            hi = mid
        else:
            lo = mid + 1
    return gen_ids[:lo], target


def sample_group(model, tok, prompt, g, temp, max_tokens, dev, batch=4):
    """Sample g completions; return list of (gen_ids_tensor, text).

    Generation stops at 'endmodule' (stop_strings) so large designs are not
    truncated mid-module by the token cap AND no junk trails the module; each
    sequence is then trimmed to end exactly at its own 'endmodule' (F8)."""
    chat = tok.apply_chat_template([{"role": "user", "content": prompt}],
                                   tokenize=False, add_generation_prompt=True)
    inp = tok(chat, return_tensors="pt", return_token_type_ids=False).to(dev)
    plen = inp["input_ids"].shape[1]
    out = []
    remaining = g
    model.config.use_cache = True
    while remaining > 0:
        k = min(batch, remaining)
        with torch.inference_mode():
            seqs = model.generate(**inp, max_new_tokens=max_tokens,
                                  do_sample=True, temperature=temp,
                                  num_return_sequences=k,
                                  stop_strings=["endmodule"], tokenizer=tok,
                                  pad_token_id=tok.eos_token_id)
        for s in seqs:
            gen, text = trim_endmodule(s[plen:], tok)
            out.append((gen.detach().clone(), text))
        remaining -= k
        torch.cuda.empty_cache()
    return inp["input_ids"], out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--base", default=os.environ.get(
        "RTLCODER_PATH", "/zeng_gk/Amine/mas/rtlcoder"))
    ap.add_argument("--sft", default="sft_v5_out", help="SFT adapter to start from")
    ap.add_argument("--surrogate", default="surrogate_v2.pt")
    ap.add_argument("--out", default="grpo_v7")
    ap.add_argument("--designs", nargs="*", default=None,
                    help="default = ALL train-split designs (F10); pass names to override")
    ap.add_argument("--reward", choices=["mlp", "rf_struct", "correctness"],
                    default="mlp",
                    help="mlp = the DEPLOYED (exploited) surrogate, --surrogate; "
                         "rf_struct = RandomForest over canonical structural "
                         "features, --rf; correctness = 1.0 for every "
                         "oracle-correct candidate (the causal control that "
                         "removes the physical signal while leaving the "
                         "correctness gate and KL anchor untouched)")
    ap.add_argument("--rf", default="rf_struct.joblib",
                    help="rf_struct reward artifact (train_rf_struct.py)")
    ap.add_argument("--steps", type=int, default=400)
    ap.add_argument("--max-groups", type=int, default=0,
                    help="hard ceiling on ATTEMPTED groups. A run that hits this "
                         "before --max-updates ends here and is reported as "
                         "having ended on the attempt ceiling; it is never "
                         "silently extended.")
    ap.add_argument("--save-at-updates", default="",
                    help="comma-separated optimizer-update counts at which to "
                         "checkpoint, e.g. '138,276'. Checkpoints are indexed by "
                         "UPDATE, not attempted step: arms are matched on "
                         "non-flat updates, so a step-indexed checkpoint compares "
                         "different amounts of learning across arms.")
    ap.add_argument("--group-log", default="",
                    help="per-candidate JSONL: raw RTL, canonical hash, both "
                         "feature sets, reward, standardized advantage, "
                         "line/token/statement counts, flat-or-update status. "
                         "Default <out>/group_log.jsonl")
    ap.add_argument("--max-updates", type=int, default=0,
                    help="stop after this many NON-FLAT groups (= actual "
                         "optimizer updates), regardless of --steps. 0 = no "
                         "limit. Needed to compare arms fairly: a group whose "
                         "rewards are all equal is skipped, and under "
                         "--constant-reward ~80%% of groups are unanimous, so "
                         "step-matched arms are NOT update-matched.")
    ap.add_argument("--group", type=int, default=8, help="candidates per step")
    ap.add_argument("--gen-batch", type=int, default=4)
    ap.add_argument("--temp", type=float, default=1.0)
    ap.add_argument("--max-tokens", type=int, default=1536)   # F4: fit fir32/firr32 transposed
    ap.add_argument("--lr", type=float, default=1e-5)
    ap.add_argument("--kl_coef", type=float, default=0.1)
    ap.add_argument("--incorrect-reward", type=float, default=0.0)
    ap.add_argument("--constant-reward", action="store_true",
                    help="deprecated alias for --reward correctness")
    ap.add_argument("--dtype", choices=["auto", "fp16", "bf16"], default="auto")
    ap.add_argument("--save_every", type=int, default=100)
    ap.add_argument("--log", default="grpo_v7_log.jsonl")
    ap.add_argument("--seed", type=int, default=0)
    args = ap.parse_args()

    if args.constant_reward:
        args.reward = "correctness"
    save_at = {int(s) for s in args.save_at_updates.split(",") if s.strip()}
    random.seed(args.seed); torch.manual_seed(args.seed)
    os.makedirs(args.out, exist_ok=True)
    group_log_path = args.group_log or os.path.join(args.out, "group_log.jsonl")
    # A crashed run is DISCARDED and rerun from scratch with the same seed;
    # partial runs are never merged and never resumed. Refusing to append to an
    # existing group log is what makes that policy enforceable rather than
    # aspirational.
    if os.path.exists(group_log_path) and os.path.getsize(group_log_path):
        raise SystemExit(
            f"{group_log_path} already exists and is non-empty.\n"
            f"Preregistered crash policy: a run that dies is discarded and "
            f"restarted from step 0 with the same seed -- partial runs are never "
            f"resumed or merged. Move the old log aside deliberately if this is "
            f"a real restart.")
    want = set(args.designs) if args.designs else set(train_split_designs())
    prompts = probe_prompts(want)                 # F10: dozens of train prompts
    designs = sorted(prompts)
    # hard guard: the frozen §5 held-out designs must NEVER enter the GRPO list
    leaked = [d for d in designs if GSC.is_holdout(d)]
    if leaked:
        raise SystemExit(f"HELD-OUT LEAK into GRPO designs: {leaked} "
                         f"(§5 isolation violated -- refusing to train)")
    print(f"GRPO designs ({len(designs)}, train-split only): "
          f"{', '.join(designs)}", flush=True)

    dtype = pick_dtype(args.dtype)
    tok = AutoTokenizer.from_pretrained(args.base)
    if tok.pad_token is None:
        tok.pad_token = tok.eos_token
    base = AutoModelForCausalLM.from_pretrained(
        args.base, torch_dtype=dtype, device_map={"": 0})
    # F3: load the SFT LoRA TWICE -- 'default' (trainable, the RL policy) and
    # 'ref' (frozen, the KL anchor). Previously KL anchored to the BASE model
    # (disable_adapter), which mildly pulled the policy AWAY from SFT competence.
    # Both adapters are tiny (LoRA r=16 x 4 proj), so this adds no real memory.
    # The trainable adapter keeps the name 'default' so save_pretrained writes it
    # to args.out/ directly (the frozen 'ref' goes to a subdir we never reload),
    # keeping the downstream from_pretrained(base, grpo_v7) convention intact.
    model = PeftModel.from_pretrained(base, args.sft, is_trainable=True)
    model.load_adapter(args.sft, adapter_name="ref", is_trainable=False)
    model.set_adapter("default")                  # 'default' is the trainable policy
    model.print_trainable_parameters()
    trainable = upcast_trainable(model, dtype)
    dev = next(model.parameters()).device
    opt = torch.optim.AdamW(trainable, lr=args.lr)
    scaler = torch.cuda.amp.GradScaler(enabled=(dtype == torch.float16))
    # ---- reward dispatch -------------------------------------------------
    if args.reward == "mlp":
        _mlp = load_surrogate(args.surrogate, dev)
        reward_fn = lambda rtl: (_mlp(rtl), {"gate": "ok"})
        reward_src = os.path.abspath(args.surrogate)
    elif args.reward == "rf_struct":
        reward_fn = load_rf_struct(args.rf)
        reward_src = os.path.abspath(args.rf)
    else:
        reward_fn = lambda rtl: (1.0, {"gate": "ok"})
        reward_src = "constant 1.0 (correctness-only control)"
    print(f"reward: {args.reward}  <- {reward_src}", flush=True)

    log = open(args.log, "a")
    glog = open(group_log_path, "w")

    # ---- the run's own frozen configuration, written beside the adapter ----
    def _sha(p):
        try:
            return hashlib.sha256(open(p, "rb").read().replace(b"\r\n", b"\n")
                                  ).hexdigest()
        except Exception:
            return None
    cfg = {"reward": args.reward, "reward_source": reward_src,
           "reward_sha256": _sha(reward_src) if os.path.exists(reward_src) else None,
           "sft": os.path.abspath(args.sft), "base": os.path.abspath(args.base),
           "seed": args.seed, "group": args.group, "temp": args.temp,
           "max_tokens": args.max_tokens, "lr": args.lr,
           "kl_coef": args.kl_coef, "incorrect_reward": args.incorrect_reward,
           "steps": args.steps, "max_updates": args.max_updates,
           "max_groups": args.max_groups, "save_at_updates": sorted(save_at),
           "dtype": str(dtype), "grad_clip": 1.0,
           "optimizer": "AdamW", "optimizer_defaults": {
               "betas": [0.9, 0.999], "eps": 1e-8, "weight_decay": 0.01},
           "gpu": (torch.cuda.get_device_name(0)
                   if torch.cuda.is_available() else "cpu"),
           "torch": torch.__version__,
           "n_designs": len(designs), "designs": designs,
           "code_sha256": {f: _sha(os.path.join(os.path.dirname(
               os.path.abspath(__file__)), f))
               for f in ("grpo_oracle.py", "oracle.py", "canonicalize.py",
                         "gen_sft_corpus.py", "gen_accelerator_catalog.py")},
           "crash_policy": "discard and rerun from step 0; never resume or merge"}
    json.dump(cfg, open(os.path.join(args.out, "run_config.json"), "w"), indent=1)

    print(f"\nGRPO-oracle: {args.steps} steps, group={args.group}, "
          f"kl={args.kl_coef}, temp={args.temp}\n", flush=True)

    n_updates = n_flat = n_attempted = 0
    ended = "steps exhausted"
    for step in range(args.steps):
        if args.max_groups and n_attempted >= args.max_groups:
            ended = f"attempt ceiling reached ({args.max_groups} groups)"
            print(f"  -> {ended}", flush=True)
            break
        t0 = time.time()
        n_attempted += 1
        d = random.choice(designs)
        _, prompt = prompts[d]
        model.set_adapter("default")             # sample from the current policy
        prompt_ids, group = sample_group(model, tok, prompt, args.group,
                                         args.temp, args.max_tokens, dev,
                                         args.gen_batch)
        rewards, cands, n_correct = [], [], 0
        for gen_ids, text in group:
            rtl = extract_verilog(text, d)
            r = args.incorrect_reward
            meta = {"gate": "no_module"}
            correct = False
            if rtl is not None:
                rtl = rtl.encode("ascii", "replace").decode("ascii")
                try:
                    correct = oracle.score(rtl, d)["correct"]
                    meta = {"gate": "incorrect"}
                except Exception as e:
                    meta = {"gate": "oracle_error", "detail": str(e)[:200]}
                if correct:
                    n_correct += 1
                    r, meta = reward_fn(rtl)
            rewards.append(r)
            # Canonical features are logged for EVERY arm, not just rf_struct:
            # the exploit is only visible by comparing the line-anchored raw
            # features against the layout-blind canonical ones, so both must be
            # recorded even where the reward never looks at them.
            craw = cstruct = None
            if rtl is not None:
                try:
                    canon, _ = canon_of(rtl, "lexical")
                    craw, cstruct = canon_hash(canon), struct_feature_dict(canon)
                except Unsupported:
                    pass
                except Exception:
                    pass
            cands.append({
                "rtl": rtl, "correct": bool(correct), "reward": float(r),
                "gate": meta.get("gate"), "gate_detail": meta.get("detail"),
                "canon_hash": craw, "struct_features": cstruct,
                "raw_features": (feature_dict(rtl) if rtl is not None else None),
                "n_tokens": int(gen_ids.shape[0]),
                "n_lines_raw": (rtl.count("\n") + 1) if rtl else 0,
                "n_stmts_canon": (cstruct or {}).get("n_stmts")})
        r = torch.tensor(rewards, dtype=torch.float32)
        flat = bool(r.std() < 1e-6)             # no gradient signal -> skip
        adv = (None if flat else
               ((r - r.mean()) / (r.std() + 1e-8)))

        for i, c in enumerate(cands):
            c.update({"step": step, "group_index": n_attempted, "design": d,
                      "cand": i, "flat": flat,
                      "update": (None if flat else n_updates + 1),
                      "advantage": (None if flat else float(adv[i]))})
            glog.write(json.dumps(c) + "\n")
        glog.flush()

        if flat:
            n_flat += 1
            print(f"[{step:4d}] {d:10s} correct={n_correct}/{args.group} "
                  f"(flat reward, skip) {time.time()-t0:.0f}s", flush=True)
            continue

        model.config.use_cache = False
        opt.zero_grad(set_to_none=True)
        loss_val = kl_val = 0.0
        for (gen_ids, _), a in zip(group, adv.tolist()):
            gen_ids = gen_ids[:args.max_tokens].to(dev)
            if gen_ids.numel() < 2:
                continue
            # F3: KL anchor is the FROZEN SFT policy ('ref'), not the base model.
            # ref path is no_grad + detached; policy path carries the gradient.
            ref_lp = seq_logprob_adapter(model, prompt_ids, gen_ids,
                                         "ref", grad=False).detach()
            lp = seq_logprob_adapter(model, prompt_ids, gen_ids,
                                     "default", grad=True)
            dd = ref_lp - lp
            kl = torch.exp(dd) - dd - 1.0         # k3 estimator, >= 0
            loss = (-a * lp + args.kl_coef * kl) / len(group)
            scaler.scale(loss).backward()
            loss_val += loss.item(); kl_val += kl.item() / len(group)
        scaler.unscale_(opt)
        torch.nn.utils.clip_grad_norm_(trainable, 1.0)
        scaler.step(opt); scaler.update()

        n_updates += 1
        rec = {"step": step, "design": d, "correct": n_correct,
               "mean_fmax": float(np.mean([x for x in rewards if x > 0]) or 0),
               "max_fmax": float(max(rewards)), "loss": loss_val, "kl": kl_val,
               "update": n_updates, "n_flat": n_flat}
        log.write(json.dumps(rec) + "\n"); log.flush()
        print(f"[{step:4d}] {d:10s} correct={n_correct}/{args.group} "
              f"surrFmax[max={rec['max_fmax']:.0f}] loss={loss_val:.4f} "
              f"kl={kl_val:.4f} {time.time()-t0:.0f}s", flush=True)
        # Checkpoints are indexed by OPTIMIZER UPDATE when --save-at-updates is
        # given: arms are matched on non-flat updates, so a step-indexed
        # checkpoint would compare different amounts of learning across arms.
        if save_at:
            if n_updates in save_at:
                p = os.path.join(args.out, f"upd_{n_updates}")
                save_policy(model, p)
                print(f"  -> checkpoint {p}", flush=True)
        elif args.save_every and (step + 1) % args.save_every == 0:
            save_policy(model, os.path.join(args.out, f"step_{step+1}"))
            print(f"  -> checkpoint {args.out}/step_{step+1}", flush=True)
        if args.max_updates and n_updates >= args.max_updates:
            ended = f"target updates reached ({args.max_updates})"
            print(f"  -> {ended} at step {step}", flush=True)
            break

    print(f"\nbudget: {n_updates} optimizer updates, {n_flat} flat groups "
          f"skipped ({100.0 * n_flat / max(1, n_updates + n_flat):.1f}% of "
          f"attempted steps produced no gradient)", flush=True)
    print(f"ended: {ended}", flush=True)
    missed = sorted(u for u in save_at if u > n_updates)
    if missed:
        print(f"WARNING: never reached update(s) {missed} -- those checkpoints "
              f"do not exist. Report the run as ending at {n_updates} updates; "
              f"do NOT substitute a nearby checkpoint.", flush=True)
    json.dump({"updates": n_updates, "attempted_groups": n_attempted,
               "flat_groups": n_flat, "ended": ended,
               "checkpoints": sorted(u for u in save_at if u <= n_updates),
               "missed_checkpoints": missed},
              open(os.path.join(args.out, "run_summary.json"), "w"), indent=1)
    glog.close()
    save_policy(model, args.out)
    tok.save_pretrained(args.out)
    log.close()
    print(f"\nGRPO-oracle done. Adapter -> {args.out}/\n"
          f"eval: gen_fmax_candidates.py --adapter {args.out} --out-dir "
          f"rtl/grpo_eval, then run_ppa + analyze_accel_spread -- correctness must "
          f"hold and the Fmax distribution should shift UP vs the SFT policy.")


if __name__ == "__main__":
    main()

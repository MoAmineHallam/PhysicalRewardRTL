#!/usr/bin/env python3
"""
eval_ppa_gen.py  -  Generate from a model, keep functionally-CORRECT outputs,
write them for PPA synthesis. The eval for grpo_train_v4: does the model
actually GENERATE leaner/faster correct RTL than base?

Run once per model (base and each grpo_v4 checkpoint), on the server (GPU +
iverilog). Then synthesize each output dir with run_ppa on the laptop and
compare mean LUT/Fmax of the correct generations (analyze_ppa --manifest).

  python fpga/eval_ppa_gen.py --tag base
  python fpga/eval_ppa_gen.py --adapter grpo_v4/step_100 --tag v4_s100
  python fpga/eval_ppa_gen.py --adapter grpo_v4           --tag v4_s400

Default eval designs = the PPA-spread set (the families with headroom). Only
functionally-correct generations (reward >= --min-reward, scored vs the
silicon-certified golden) are written -- PPA of wrong RTL is meaningless.
"""

import os
import re
import json
import argparse

os.environ.setdefault("TRANSFORMERS_OFFLINE", "1")
os.environ.setdefault("HF_HUB_OFFLINE", "1")

import torch
from transformers import AutoTokenizer, AutoModelForCausalLM

import score_candidate as SC
from build_dataset import make_prompt, extract_verilog, LLM_DIR

HERE = os.path.dirname(os.path.abspath(__file__))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--adapter", default=None, help="LoRA dir (omit = base)")
    ap.add_argument("--tag", required=True, help="base / v4_s100 / v4_s400 ...")
    ap.add_argument("--designs", nargs="*", default=None)
    ap.add_argument("--ppa-manifest",
                    default=os.path.join(HERE, "rtl", "ppa_set",
                                         "ppa_set_manifest.json"))
    ap.add_argument("--n", type=int, default=8, help="generations per design")
    ap.add_argument("--temp", type=float, default=0.8)
    ap.add_argument("--max-tokens", type=int, default=512)
    ap.add_argument("--min-reward", type=float, default=0.999)
    ap.add_argument("--out-dir", default=None)
    ap.add_argument("--base_model",
                    default=os.environ.get("RTLCODER_PATH",
                                           os.path.join(LLM_DIR, "rtlcoder")))
    args = ap.parse_args()

    out_dir = args.out_dir or os.path.join(HERE, "rtl", "ppa_eval", args.tag)
    os.makedirs(out_dir, exist_ok=True)
    man = SC.load_manifest()

    if args.designs:
        designs = args.designs
    else:
        pm = json.load(open(args.ppa_manifest))
        designs = sorted(set(v["design"] for v in pm.values()))

    tok = AutoTokenizer.from_pretrained(args.base_model)
    if tok.pad_token is None:
        tok.pad_token = tok.eos_token
    model = AutoModelForCausalLM.from_pretrained(
        args.base_model, torch_dtype=torch.float16, device_map={"": 0})
    if args.adapter:
        from peft import PeftModel
        model = PeftModel.from_pretrained(model, args.adapter,
                                          is_trainable=False)
    model.eval()

    mani = {}
    tot_correct = 0
    for d in designs:
        if d not in man:
            continue
        spec = os.path.join(SC.RTL_LIB, d, "spec.txt")
        if not os.path.exists(spec):
            continue
        prompt = make_prompt(man[d], open(spec).read())
        chat = tok.apply_chat_template(
            [{"role": "user", "content": prompt}],
            tokenize=False, add_generation_prompt=True)
        inp = tok(chat, return_tensors="pt",
                  return_token_type_ids=False).to("cuda:0")
        with torch.inference_mode():
            out = model.generate(
                **inp, max_new_tokens=args.max_tokens, do_sample=True,
                temperature=args.temp, num_return_sequences=args.n,
                stop_strings=["endmodule"], tokenizer=tok,
                pad_token_id=tok.eos_token_id)
        plen = inp["input_ids"].shape[1]
        kept = 0
        for seq in out:
            txt = tok.decode(seq[plen:], skip_special_tokens=True)
            rtl = extract_verilog(txt, d)
            if rtl is None:
                continue
            rtl = rtl.encode("ascii", errors="replace").decode("ascii")
            try:
                if SC.score_rtl(rtl, d, SC.N_CYCLES_DEFAULT, man) < args.min_reward:
                    continue
            except RuntimeError:
                continue
            mod = f"{d}__{args.tag}__{kept}"
            rr = re.sub(r"\bmodule\s+" + re.escape(d) + r"\b",
                        "module " + mod, rtl, count=1)
            with open(os.path.join(out_dir, mod + ".sv"), "w") as f:
                f.write(rr)
            mani[mod] = {"design": d, "family": man[d].get("family", "?")}
            kept += 1
        tot_correct += kept
        print(f"{d}: {kept}/{args.n} correct", flush=True)

    json.dump(mani, open(os.path.join(out_dir, "eval_manifest.json"), "w"),
              indent=1)
    print(f"\n{tot_correct} correct generations across {len(designs)} designs "
          f"-> {out_dir}\nnext: run_ppa on this dir, then analyze_ppa --manifest")


if __name__ == "__main__":
    main()

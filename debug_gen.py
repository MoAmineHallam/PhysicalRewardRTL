#!/usr/bin/env python3
"""
debug_gen.py  -  Inspect ONE model's raw output for one accelerator spec, to
diagnose why correct-rate is low (format? compile error? wrong logic?).

Prints: the chat prompt, the raw decoded generations, the extracted module,
the iverilog compile result (with stderr), and the score. Run on the server:

    python fpga/debug_gen.py /zeng_gk/Amine/mas/qwen2.5-coder-7b-instruct fir16_8b
"""

import os
import sys
import subprocess
import tempfile

os.environ.setdefault("TRANSFORMERS_OFFLINE", "1")
os.environ.setdefault("HF_HUB_OFFLINE", "1")

import torch
from transformers import AutoTokenizer, AutoModelForCausalLM

import score_accel as SA
from build_dataset import make_prompt, extract_verilog

base = sys.argv[1]
design = sys.argv[2] if len(sys.argv) > 2 else "fir16_8b"
n = int(sys.argv[3]) if len(sys.argv) > 3 else 2

spec = open(os.path.join(SA.RTL_LIB, design, "spec.txt")).read()
prompt = make_prompt({"name": design}, spec) + SA.V2001_SUFFIX

tok = AutoTokenizer.from_pretrained(base)
if tok.pad_token is None:
    tok.pad_token = tok.eos_token
_big = any(s in base.lower() for s in ("16b", "30b", "32b", "34b", "35b", "70b",
                                       "verigen", "codegen"))
model = AutoModelForCausalLM.from_pretrained(
    base, torch_dtype=torch.float16,
    device_map=("auto" if _big else {"": 0})).eval()

# CodeGen / base completion models have no chat template -> feed the raw prompt.
chat = (tok.apply_chat_template([{"role": "user", "content": prompt}],
                                tokenize=False, add_generation_prompt=True)
        if tok.chat_template else prompt)
print("=" * 70 + "\nCHAT PROMPT (as fed to the model)\n" + "=" * 70)
print(chat)

inp = tok(chat, return_tensors="pt", return_token_type_ids=False).to("cuda:0")
with torch.inference_mode():
    out = model.generate(**inp, max_new_tokens=512, do_sample=True,
                         temperature=0.8, num_return_sequences=n,
                         pad_token_id=tok.eos_token_id)
plen = inp["input_ids"].shape[1]

for i, seq in enumerate(out):
    txt = tok.decode(seq[plen:], skip_special_tokens=True)
    print("\n" + "=" * 70 + f"\nRAW GENERATION {i}\n" + "=" * 70)
    print(txt)
    rtl = extract_verilog(txt, design)
    print("\n--- extract_verilog ->", "None" if rtl is None else f"{len(rtl)} chars")
    if rtl:
        rtl = rtl.encode("ascii", errors="replace").decode("ascii")
        with tempfile.TemporaryDirectory() as wd:
            cand = os.path.join(wd, "c.v")
            open(cand, "w").write(rtl)
            tb = os.path.join(wd, "tb.v")
            open(tb, "w").write(SA._tb(design, 64))
            c = subprocess.run(["iverilog", "-g2012", "-o", os.path.join(wd, "a"),
                               cand, tb], capture_output=True, text=True)
            print("--- iverilog rc =", c.returncode)
            if c.returncode != 0:
                print("--- iverilog stderr:\n", c.stderr[:800])
        print("--- score_rtl ->", round(SA.score_rtl(rtl, design), 4))

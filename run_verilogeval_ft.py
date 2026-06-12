#!/usr/bin/env python3
"""
run_verilogeval_ft.py  -  Run VerilogEval with the fine-tuned (GRPO) model.

Monkey-patches llm.coder_call to use the LoRA-adapted model before the
eval script imports it.

Usage:
    python run_verilogeval_ft.py [N_problems] [--model grpo_out] [--out run_ft]
"""

import sys
import os
import argparse

os.environ["TRANSFORMERS_OFFLINE"] = "1"
os.environ.setdefault("HF_HUB_OFFLINE", "1")
LLM_DIR = "/zeng_gk/Amine/mas"
sys.path.insert(0, "/zeng_gk/Amine/verilog-eval")
sys.path.insert(0, LLM_DIR)

import torch
from transformers import AutoTokenizer, AutoModelForCausalLM
from peft import PeftModel

BASE_MODEL = os.environ.get("RTLCODER_PATH", os.path.join(LLM_DIR, "rtlcoder"))

def load_ft_model(model_path: str):
    print(f"[FT] Loading fine-tuned model from {model_path}...")
    tokenizer = AutoTokenizer.from_pretrained(model_path)
    if tokenizer.pad_token is None:
        tokenizer.pad_token = tokenizer.eos_token
    base = AutoModelForCausalLM.from_pretrained(
        BASE_MODEL, torch_dtype=torch.bfloat16, device_map="auto"
    )
    model = PeftModel.from_pretrained(base, model_path, is_trainable=False)
    model.eval()
    print("[FT] Model loaded.")
    return tokenizer, model


def make_coder_call(tokenizer, model):
    def coder_call(messages, max_tokens=1024, temperature=0.1):
        prompt = tokenizer.apply_chat_template(
            messages, tokenize=False, add_generation_prompt=True
        )
        inputs = tokenizer(
            prompt, return_tensors="pt", return_token_type_ids=False
        ).to(next(model.parameters()).device)
        with torch.no_grad():
            outputs = model.generate(
                **inputs,
                max_new_tokens=max_tokens,
                temperature=temperature,
                do_sample=temperature > 0.0,
                pad_token_id=tokenizer.eos_token_id,
            )
        response = tokenizer.decode(
            outputs[0][inputs["input_ids"].shape[1]:],
            skip_special_tokens=True,
        )
        if "endmodulemodule" in response:
            response = response.split("endmodulemodule")[0] + "endmodule"
        elif "endmodule" in response:
            idx = response.rfind("endmodule")
            response = response[: idx + len("endmodule")]
        return response
    return coder_call


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("n_problems", nargs="?", type=int, default=None,
                        help="Limit to first N problems (default: all)")
    parser.add_argument("--model", default="grpo_out",
                        help="Path to fine-tuned LoRA adapter")
    parser.add_argument("--out",   default="run_ft",
                        help="Output directory for results")
    args = parser.parse_args()

    tokenizer, model = load_ft_model(args.model)

    # Monkey-patch llm.coder_call before run_verilogeval imports it
    import llm
    llm.coder_call = make_coder_call(tokenizer, model)

    # Patch output directory
    import run_verilogeval as ve
    # Override strip_fences to cut at FIRST endmodule (model appends training
    # examples after endmodule due to SFT overfitting)
    import re as _re
    def _strip_fences(rtl):
        bt = chr(96)
        rtl = rtl.replace(bt*3 + "verilog", "").replace(bt*3, "")
        mm = _re.search(r"\bmodule\s+\w+\s*[(#;]", rtl)
        if mm:
            rtl = rtl[mm.start():]
        rtl = rtl.strip()
        if "endmodule" in rtl:
            rtl = rtl[:rtl.index("endmodule") + len("endmodule")]
        return rtl
    ve.strip_fences = _strip_fences

    ve.OUTDIR = f"/zeng_gk/Amine/verilog-eval/{args.out}"
    os.makedirs(ve.OUTDIR, exist_ok=True)

    # Override sys.argv so ve.main() sees the problem limit correctly
    if args.n_problems is not None:
        sys.argv = [sys.argv[0], str(args.n_problems)]
    else:
        sys.argv = [sys.argv[0]]

    ve.main()


if __name__ == "__main__":
    main()

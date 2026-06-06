#!/usr/bin/env python3
"""
sft_train.py  -  Phase 3 SFT warm-start for RTLCoder.

Filters dataset.jsonl for high-reward candidates (reward >= threshold),
formats as instruction-tuning pairs, and fine-tunes RTLCoder with LoRA.

Usage:
    python sft_train.py [--dataset dataset.jsonl] [--out sft_out]
                        [--min_reward 0.95] [--epochs 3] [--batch 4]
"""

import sys
import os
import json
import argparse

import torch
from transformers import AutoTokenizer, AutoModelForCausalLM, TrainingArguments, Trainer
from transformers import DataCollatorForSeq2Seq
from peft import LoraConfig, get_peft_model, TaskType
from torch.utils.data import Dataset

RTLCODER_PATH = "rtlcoder"

# Specs must match build_dataset.py exactly (same prompts the model was evaluated on)
SPECS = {
    "edge_detector": """\
Please write a Verilog module named `edge_detector` that detects rising edges.

Ports:
  input  clk    - clock
  input  rst_n  - active-low synchronous reset
  input  in     - single-bit signal to monitor
  output rise   - goes high for exactly one clock cycle on each 0→1 transition of `in`

Behavior:
  - Registered (clocked) design; all outputs update on posedge clk.
  - On !rst_n: rise <= 0.
  - rise is 1 when in==1 and the previous registered value of in==0, else 0.
""",
    "alu_mux": """\
Please write a Verilog module named `alu_mux` implementing a registered ALU with op-select mux.

Ports:
  input  clk         - clock
  input  rst_n       - active-low synchronous reset
  input  [3:0] a     - operand A
  input  [3:0] b     - operand B
  input  [2:0] op    - operation select
  output reg [3:0] result

Operations (op):
  0 → result = a + b   (4-bit addition, truncated)
  1 → result = ~a      (bitwise NOT of a)
  2 → result = a       (pass A)
  3 → result = b       (pass B)
  4 → result = a ^ b   (XOR)
  5 → result = ~a
  6 → result = a
  7 → result = b

Behavior:
  - Registered: result updates on posedge clk.
  - On !rst_n: result <= 0.
""",
    "comb_always": """\
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
    in[7]=1 → out=7; in[7]=0, in[6]=1 → out=6; ... in[0]=1 only → out=0.
  - valid=1 iff in != 0.
""",
    "bcd_counter": """\
Please write a Verilog module named `bcd_counter` that counts 0-99 in BCD.

Ports:
  input  clk         - clock
  input  rst_n       - active-low synchronous reset
  input  en          - count enable (count only when en=1)
  output [3:0] ones  - BCD ones digit (0-9)
  output [3:0] tens  - BCD tens digit (0-9)

Behavior:
  - Registered: ones and tens update on posedge clk.
  - On !rst_n: ones <= 0, tens <= 0.
  - When en=1: increment; ones wraps 9->0 and tens increments; at 99->00.
  - When en=0: hold current value.
""",
    "bit_manip": """\
Please write a Verilog module named `bit_manip` that reverses bits and counts population.

Ports:
  input  clk           - clock
  input  rst_n         - active-low synchronous reset
  input  [7:0] in      - 8-bit input
  output [7:0] reversed  - bit-reversed version of in (in[0]->reversed[7], etc.)
  output [3:0] popcount  - number of 1-bits in `in` (0-8)

Behavior:
  - Registered: reversed and popcount update on posedge clk.
  - On !rst_n: reversed <= 0, popcount <= 0.
  - reversed[i] = in[7-i] for i in 0..7.
  - popcount = in[0]+in[1]+...+in[7].
""",
    "dff_array": """\
Please write a Verilog module named `dff_array` implementing an 8-bit enabled D flip-flop array.

Ports:
  input  clk       - clock
  input  rst_n     - active-low synchronous reset
  input  en        - write enable
  input  [7:0] d   - data input
  output [7:0] q   - registered output

Behavior:
  - Registered: q updates on posedge clk.
  - On !rst_n: q <= 0.
  - When en=1: q <= d.
  - When en=0: q holds its current value.
""",
    "shift_reg": """\
Please write a Verilog module named `shift_reg` implementing an 8-bit serial-in parallel-out shift register.

Ports:
  input  clk       - clock
  input  rst_n     - active-low synchronous reset
  input  en        - shift enable
  input  sin       - serial input (shifted into MSB or LSB)
  output [7:0] q   - parallel output

Behavior:
  - Registered: q updates on posedge clk.
  - On !rst_n: q <= 0.
  - When en=1: shift left by 1, sin enters at LSB: q <= {q[6:0], sin}.
  - When en=0: q holds.
""",
}


class RTLDataset(Dataset):
    def __init__(self, records, tokenizer, max_length=1024):
        self.samples = []
        for rec in records:
            spec = SPECS.get(rec["design_name"], "")
            rtl  = rec["rtl"]
            messages = [{"role": "user", "content": spec}]
            prompt = tokenizer.apply_chat_template(
                messages, tokenize=False, add_generation_prompt=True
            )
            full_text = prompt + rtl + tokenizer.eos_token
            self.samples.append(full_text)
        self.tokenizer = tokenizer
        self.max_length = max_length

    def __len__(self):
        return len(self.samples)

    def __getitem__(self, idx):
        enc = self.tokenizer(
            self.samples[idx],
            truncation=True,
            max_length=self.max_length,
            padding=False,
            return_tensors=None,
        )
        enc["labels"] = enc["input_ids"].copy()
        return enc


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--dataset",    default="dataset.jsonl")
    parser.add_argument("--out",        default="sft_out")
    parser.add_argument("--min_reward", type=float, default=0.95)
    parser.add_argument("--epochs",     type=int,   default=3)
    parser.add_argument("--batch",      type=int,   default=2)
    parser.add_argument("--lr",         type=float, default=2e-4)
    parser.add_argument("--max_length", type=int,   default=1024)
    args = parser.parse_args()

    # Load and filter dataset
    records = [json.loads(l) for l in open(args.dataset)]
    filtered = [r for r in records if r["reward"] >= args.min_reward]
    print(f"Dataset: {len(records)} total, {len(filtered)} with reward >= {args.min_reward}")
    if len(filtered) == 0:
        print("No records pass the reward threshold. Exiting.")
        sys.exit(1)

    # Per-design breakdown
    from collections import Counter
    counts = Counter(r["design_name"] for r in filtered)
    for name, n in sorted(counts.items()):
        print(f"  {name:15s}: {n}")

    # Load model and tokenizer
    print("\nLoading RTLCoder...")
    tokenizer = AutoTokenizer.from_pretrained(RTLCODER_PATH)
    if tokenizer.pad_token is None:
        tokenizer.pad_token = tokenizer.eos_token

    model = AutoModelForCausalLM.from_pretrained(
        RTLCODER_PATH,
        torch_dtype=torch.bfloat16,
        device_map="auto",
    )
    model.config.use_cache = False

    # Apply LoRA
    lora_config = LoraConfig(
        task_type=TaskType.CAUSAL_LM,
        r=16,
        lora_alpha=32,
        lora_dropout=0.05,
        target_modules=["q_proj", "v_proj", "k_proj", "o_proj"],
        bias="none",
    )
    model = get_peft_model(model, lora_config)
    model.print_trainable_parameters()

    # Build dataset
    train_dataset = RTLDataset(filtered, tokenizer, max_length=args.max_length)
    print(f"\nTraining samples: {len(train_dataset)}")

    data_collator = DataCollatorForSeq2Seq(
        tokenizer, model=model, padding=True, pad_to_multiple_of=8
    )

    # Training
    training_args = TrainingArguments(
        output_dir=args.out,
        num_train_epochs=args.epochs,
        per_device_train_batch_size=args.batch,
        gradient_accumulation_steps=4,
        learning_rate=args.lr,
        lr_scheduler_type="cosine",
        warmup_ratio=0.05,
        bf16=True,
        logging_steps=10,
        save_strategy="epoch",
        report_to="none",
        dataloader_num_workers=0,
        remove_unused_columns=False,
    )

    trainer = Trainer(
        model=model,
        args=training_args,
        train_dataset=train_dataset,
        data_collator=data_collator,
    )

    print("\nStarting SFT training...")
    trainer.train()

    # Save LoRA adapter
    model.save_pretrained(args.out)
    tokenizer.save_pretrained(args.out)
    print(f"\nLoRA adapter saved to {args.out}/")


if __name__ == "__main__":
    main()

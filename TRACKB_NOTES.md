# Track B - Dataset Expansion Notes

## Batch 1: Datapath designs (drafted, awaiting board capture)

| sel | name         | inputs                       | probe packing                  | period | divides 1024 |
|-----|--------------|------------------------------|--------------------------------|--------|--------------|
| 7   | mult4x4      | a=cnt[3:0], b=cnt[7:4]       | {8'b0, product[7:0]}           | 256    | yes          |
| 8   | comparator4  | a=cnt[3:0], b=cnt[7:4]       | {13'b0, gt, eq, lt}            | 256    | yes          |
| 9   | barrel_shift | data=cnt[7:0], shamt=cnt[9:8]| {8'b0, out[7:0]}               | 1024   | yes          |
| 10  | addsub4      | a=cnt[3:0], b=cnt[7:4], sub=cnt[8] | {11'b0, result[4:0]}     | 512    | yes          |

All periods divide the LA buffer depth (1024), so FFT phase alignment works
without per-design N_COMPARE hacks (unlike bcd_counter).

## IMPORTANT: sel width must grow from 3 to 4 bits

Current `dut_top.v` and `la_axi.v` use a 3-bit `sel` (max 8 designs, sel 0-7).
Adding sel 8,9,10 requires widening `sel` to 4 bits:
  - dut_top.v: `input wire [3:0] sel;`
  - la_axi.v: widen the SEL register field to 4 bits
  - Re-synthesize the bitstream in Vivado.

## Board capture workflow (per design)

1. Add DUT instantiation to dut_top.v (snippets below).
2. Widen sel to 4 bits; extend the probe mux case statement.
3. Synthesize + implement in Vivado, generate bitstream.
4. Program PYNQ-Z2, run the LA capture for each new sel value.
5. Save capture as rtl_library/<name>/waveform.npy (uint16, >= 1024 samples).
6. Validate: `python3 golden.py` produces golden_waveform.npy; compare the
   first ~256 samples (modulo FFT offset) against waveform.npy to confirm the
   hardware matches the golden RTL before trusting the reward.

## dut_top.v instantiation snippets

```verilog
// --- 7: mult4x4 ---
wire [7:0] mul_p;
mult4x4 u_mul (.clk(clk), .rst_n(rst_n),
    .a(cnt[3:0]), .b(cnt[7:4]), .product(mul_p));

// --- 8: comparator4 ---
wire cmp_gt, cmp_eq, cmp_lt;
comparator4 u_cmp (.clk(clk), .rst_n(rst_n),
    .a(cnt[3:0]), .b(cnt[7:4]), .gt(cmp_gt), .eq(cmp_eq), .lt(cmp_lt));

// --- 9: barrel_shift ---
wire [7:0] bs_out;
barrel_shift u_bs (.clk(clk), .rst_n(rst_n),
    .data(cnt[7:0]), .shamt(cnt[9:8]), .out(bs_out));

// --- 10: addsub4 ---
wire [4:0] as_res;
addsub4 u_as (.clk(clk), .rst_n(rst_n),
    .a(cnt[3:0]), .b(cnt[7:4]), .sub(cnt[8]), .result(as_res));
```

Probe mux additions:
```verilog
4'd7:  probe = {8'b0,  mul_p};
4'd8:  probe = {13'b0, cmp_gt, cmp_eq, cmp_lt};
4'd9:  probe = {8'b0,  bs_out};
4'd10: probe = {11'b0, as_res};
```

## score_candidate.py integration snippets

Extend the module-level lists:
```python
DESIGN_NAMES += ["mult4x4", "comparator4", "barrel_shift", "addsub4"]   # 7,8,9,10
PROBE_MASKS  += [0x00FF, 0x0007, 0x00FF, 0x001F]                          # 7,8,9,10
N_COMPARE    += [32768, 32768, 32768, 32768]                             # periods divide 1024
```

Add testbench DUT blocks (sel 7-10) mirroring the dut_top wiring above, e.g.:
```python
7: '''
    wire [7:0] product;
    wire [15:0] probe = {8'b0, product};
    mult4x4 dut (.clk(clk), .rst_n(rst_n),
        .a(cnt[3:0]), .b(cnt[7:4]), .product(product));
''',
# ...comparator4, barrel_shift, addsub4 similarly
```

## After capture: regenerate dataset

```bash
# generate candidates for the new designs only (sel 7-10)
python3 build_dataset.py --sel 7 --n 50 --out dataset.jsonl
python3 build_dataset.py --sel 8 --n 50 --out dataset.jsonl
python3 build_dataset.py --sel 9 --n 50 --out dataset.jsonl
python3 build_dataset.py --sel 10 --n 50 --out dataset.jsonl
```

Then add the new specs/sel ids to grpo_train.py DESIGNS and re-run GRPO-v2.

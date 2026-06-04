"""Golden reference model for alu_mux."""
import numpy as np
from pathlib import Path

def compute_golden(stimulus_path="stimulus.txt"):
    rows = [l.split() for l in Path(stimulus_path).read_text().splitlines()
            if l.strip() and not l.startswith("#")]
    result = 0
    out = []
    for a_s, b_s, op_s in rows:
        a, b, op = int(a_s) & 0xF, int(b_s) & 0xF, int(op_s) & 0x7
        ops = [a+b, a-b, a&b, a|b, a^b, ~a, a, b]
        result = ops[op] & 0xF
        out.append(result)
    return np.array(out, dtype=np.uint16)

if __name__ == "__main__":
    golden = compute_golden()
    rows = [l.split() for l in Path("stimulus.txt").read_text().splitlines()
            if l.strip() and not l.startswith("#")]
    print("cycle |  a  b op | result")
    for i, ((a,b,op), r) in enumerate(zip(rows, golden)):
        print(f"  {i:3d} | {a:2s} {b:2s}  {op} |  {r}")
    np.save("golden_waveform.npy", golden)
    print(f"\nSaved golden_waveform.npy  ({len(golden)} samples)")

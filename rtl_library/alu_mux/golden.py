"""
Golden reference for alu_mux — counter-driven mode.
Inputs: a=cnt[3:0], b=cnt[7:4], op=cnt[10:8]
Probe: {12'b0, result[3:0]}
"""
import numpy as np

def compute_golden(n_cycles: int = 32768) -> np.ndarray:
    result = 0
    out = []
    for c in range(n_cycles):
        a  = c & 0xF
        b  = (c >> 4) & 0xF
        op = (c >> 8) & 0x7
        ops = [a+b, a-b, a&b, a|b, a^b, ~a, a, b]
        result = ops[op] & 0xF
        out.append(result)
    return np.array(out, dtype=np.uint16)

if __name__ == "__main__":
    golden = compute_golden()
    print("cycle |  a  b op | result")
    for i in range(min(20, len(golden))):
        c = i
        a, b, op = c&0xF, (c>>4)&0xF, (c>>8)&0x7
        print(f"  {i:3d} | {a:2d} {b:2d}  {op} |  {golden[i]}")
    np.save("golden_waveform.npy", golden)
    print(f"\nSaved golden_waveform.npy  ({len(golden)} samples)")

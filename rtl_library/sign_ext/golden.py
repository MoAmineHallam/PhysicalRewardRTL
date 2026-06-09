"""
Golden reference for sign_ext.
Input: in4=cnt[3:0]
Probe: {8'b0, out8[7:0]}  Period=16.
out8 = sign_extend(in4) = {{4{in4[3]}}, in4}.
"""
import numpy as np

def compute_golden(n_cycles: int = 32768) -> np.ndarray:
    out = []
    for c in range(n_cycles):
        in4 = c & 0xF
        sign = (in4 >> 3) & 1
        out8 = (0xF0 * sign) | in4
        out.append(out8)
    return np.array(out, dtype=np.uint16)

if __name__ == "__main__":
    g = compute_golden(20)
    print("cycle | in4  | out8")
    for i, v in enumerate(g):
        print(f"  {i:3d} | {i&0xF:04b} | {v:08b}  ({v:#04x})")
    np.save("golden_waveform.npy", compute_golden())
    print("Saved golden_waveform.npy")

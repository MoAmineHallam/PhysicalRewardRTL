"""
Golden reference for abs_val.
Input: in=cnt[3:0]  (treated as 4-bit two's complement)
Probe: {12'b0, out[3:0]}  Period=16.
"""
import numpy as np

def compute_golden(n_cycles: int = 32768) -> np.ndarray:
    out = []
    for c in range(n_cycles):
        in4 = c & 0xF
        if in4 & 0x8:  # negative
            result = (~in4 + 1) & 0xF
        else:
            result = in4
        out.append(result)
    return np.array(out, dtype=np.uint16)

if __name__ == "__main__":
    g = compute_golden(20)
    print("cycle | in   | out")
    for i, v in enumerate(g):
        in4 = i & 0xF
        signed = in4 if not (in4 & 8) else in4 - 16
        print(f"  {i:3d} | {in4:4b} ({signed:+3d}) |  {v}")
    np.save("golden_waveform.npy", compute_golden())
    print("Saved golden_waveform.npy")

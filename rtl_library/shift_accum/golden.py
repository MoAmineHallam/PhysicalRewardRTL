"""
Golden reference for shift_accum.
Input: data=cnt[3:0]
Probe: {8'b0, accum[7:0]}  Period=16 for accum to settle.
accum = (accum + data) >> 1 each cycle (logical shift).
"""
import numpy as np

def compute_golden(n_cycles: int = 32768) -> np.ndarray:
    out = []
    accum = 0
    for c in range(n_cycles):
        data = c & 0xF
        out.append(accum)
        accum = ((accum + data) >> 1) & 0xFF
    return np.array(out, dtype=np.uint16)

if __name__ == "__main__":
    g = compute_golden(20)
    print("cycle | data | accum")
    for i, v in enumerate(g):
        print(f"  {i:3d} |  {i&0xF:2d}  |  {v}")
    np.save("golden_waveform.npy", compute_golden())
    print("Saved golden_waveform.npy")

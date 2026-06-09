"""
Golden reference for gray_encoder.
Input: bin=cnt[3:0]
Probe: {12'b0, gray[3:0]}  Period=16.
gray = bin ^ (bin >> 1).
"""
import numpy as np

def compute_golden(n_cycles: int = 32768) -> np.ndarray:
    out = []
    for c in range(n_cycles):
        b = c & 0xF
        gray = b ^ (b >> 1)
        out.append(gray)
    return np.array(out, dtype=np.uint16)

if __name__ == "__main__":
    g = compute_golden(20)
    print("cycle | bin  | gray")
    for i, v in enumerate(g):
        print(f"  {i:3d} | {i&0xF:04b} | {v:04b}")
    np.save("golden_waveform.npy", compute_golden())
    print("Saved golden_waveform.npy")

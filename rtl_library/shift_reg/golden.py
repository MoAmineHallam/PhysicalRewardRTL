"""
Golden reference for shift_reg — counter-driven mode.
Inputs: en = 1, sin = cnt[0]
Probe: {8'b0, q[7:0]}
"""
import numpy as np

def compute_golden(n_cycles: int = 32768) -> np.ndarray:
    sr = 0
    out = []
    for c in range(n_cycles):
        sin = c & 1
        sr  = ((sr << 1) | sin) & 0xFF
        out.append(sr)
    return np.array(out, dtype=np.uint16)

if __name__ == "__main__":
    golden = compute_golden()
    print("cycle | sin |   q (bin)")
    for i in range(min(20, len(golden))):
        print(f"  {i:3d} |  {i&1}  | {golden[i]:3d}  {golden[i]:08b}")
    np.save("golden_waveform.npy", golden)
    print(f"\nSaved golden_waveform.npy  ({len(golden)} samples)")

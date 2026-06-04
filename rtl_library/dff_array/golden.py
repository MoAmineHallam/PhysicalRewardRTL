"""
Golden reference for dff_array — counter-driven mode.
Inputs: en = cnt[0],  d = cnt[8:1]
Probe: {8'b0, q[7:0]}
"""
import numpy as np

def compute_golden(n_cycles: int = 32768) -> np.ndarray:
    q = 0
    out = []
    for c in range(n_cycles):
        en = c & 1
        d  = (c >> 1) & 0xFF
        if en:
            q = d
        out.append(q)
    return np.array(out, dtype=np.uint16)

if __name__ == "__main__":
    golden = compute_golden()
    print("cycle | en   d  |   q")
    for i in range(min(20, len(golden))):
        en = i & 1
        d  = (i >> 1) & 0xFF
        print(f"  {i:3d} |  {en}  {d:3d}  | {golden[i]:3d}")
    np.save("golden_waveform.npy", golden)
    print(f"\nSaved golden_waveform.npy  ({len(golden)} samples)")

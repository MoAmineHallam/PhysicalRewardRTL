"""
Golden reference for edge_detector — counter-driven mode.
Input: in = cnt[8]  (changes every 256 cycles)
Probe: {14'b0, cnt[8], rise}
"""
import numpy as np

def compute_golden(n_cycles: int = 32768) -> np.ndarray:
    in_prev = 0
    out = []
    for c in range(n_cycles):
        in_val = (c >> 8) & 1
        rise   = int(in_val == 1 and in_prev == 0)
        out.append(((in_val << 1) | rise) & 0xFFFF)
        in_prev = in_val
    return np.array(out, dtype=np.uint16)

if __name__ == "__main__":
    golden = compute_golden()
    print("cycle | cnt[8] | rise")
    for i in range(min(600, len(golden))):
        g = golden[i]
        if g != golden[i-1] or i < 5:
            print(f"  {i:5d} |   {(g>>1)&1}    |   {g&1}")
    np.save("golden_waveform.npy", golden)
    print(f"\nSaved golden_waveform.npy  ({len(golden)} samples)")
    print(f"Rising edges: {int(np.sum(golden & 1))}")

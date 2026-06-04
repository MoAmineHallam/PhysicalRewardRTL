"""
Golden reference for comb_always (priority encoder) — counter-driven mode.
Input: in = cnt[7:0]
Probe: {12'b0, valid, out[2:0]}
"""
import numpy as np

def compute_golden(n_cycles: int = 32768) -> np.ndarray:
    out = []
    for c in range(n_cycles):
        v = c & 0xFF
        enc, vld = 0, 0
        for bit in range(7, -1, -1):
            if (v >> bit) & 1:
                enc, vld = bit, 1
                break
        out.append((vld << 3) | enc)
    return np.array(out, dtype=np.uint16)

if __name__ == "__main__":
    golden = compute_golden()
    print("cycle |  in  | enc valid")
    for i in range(min(20, len(golden))):
        g = golden[i]
        print(f"  {i:3d} | {i&0xFF:3d}  |  {g&7}   {(g>>3)&1}")
    np.save("golden_waveform.npy", golden)
    print(f"\nSaved golden_waveform.npy  ({len(golden)} samples)")

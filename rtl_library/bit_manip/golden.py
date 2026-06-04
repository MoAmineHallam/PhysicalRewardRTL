"""
Golden reference for bit_manip — counter-driven mode.
Input: in = cnt[7:0]
Probe: {4'b0, reversed[7:0], popcount[3:0]}
"""
import numpy as np

def compute_golden(n_cycles: int = 32768) -> np.ndarray:
    out = []
    for c in range(n_cycles):
        v   = c & 0xFF
        rev = int(f"{v:08b}"[::-1], 2)
        cnt = bin(v).count("1")
        out.append((rev << 4) | cnt)
    return np.array(out, dtype=np.uint16)

if __name__ == "__main__":
    golden = compute_golden()
    print("cycle |  in  | reversed popcount")
    for i in range(min(20, len(golden))):
        g = golden[i]
        print(f"  {i:3d} | {i&0xFF:3d}  |  {g>>4:3d}      {g&0xF}")
    np.save("golden_waveform.npy", golden)
    print(f"\nSaved golden_waveform.npy  ({len(golden)} samples)")

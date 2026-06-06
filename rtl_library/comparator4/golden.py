"""
Golden reference for comparator4 - counter-driven mode.
Inputs: a=cnt[3:0], b=cnt[7:4]
Probe: {13'b0, gt, eq, lt}  (gt=bit2, eq=bit1, lt=bit0)
"""
import numpy as np

def compute_golden(n_cycles: int = 32768) -> np.ndarray:
    out = []
    for c in range(n_cycles):
        a = c & 0xF
        b = (c >> 4) & 0xF
        gt = 1 if a > b else 0
        eq = 1 if a == b else 0
        lt = 1 if a < b else 0
        out.append(((gt << 2) | (eq << 1) | lt) & 0xFFFF)
    return np.array(out, dtype=np.uint16)

if __name__ == "__main__":
    golden = compute_golden()
    print("cycle |  a  b | gt eq lt")
    for i in range(min(20, len(golden))):
        a, b = i & 0xF, (i >> 4) & 0xF
        g = golden[i]
        print(f"  {i:3d} | {a:2d} {b:2d} |  {(g>>2)&1}  {(g>>1)&1}  {g&1}")
    np.save("golden_waveform.npy", golden)
    print(f"\nSaved golden_waveform.npy  ({len(golden)} samples)")

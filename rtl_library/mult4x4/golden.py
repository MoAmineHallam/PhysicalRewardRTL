"""
Golden reference for mult4x4 - counter-driven mode.
Inputs: a=cnt[3:0], b=cnt[7:4]
Probe: {8'b0, product[7:0]}
"""
import numpy as np

def compute_golden(n_cycles: int = 32768) -> np.ndarray:
    out = []
    for c in range(n_cycles):
        a = c & 0xF
        b = (c >> 4) & 0xF
        out.append((a * b) & 0xFF)
    return np.array(out, dtype=np.uint16)

if __name__ == "__main__":
    golden = compute_golden()
    print("cycle |  a  b | product")
    for i in range(min(20, len(golden))):
        a, b = i & 0xF, (i >> 4) & 0xF
        print(f"  {i:3d} | {a:2d} {b:2d} |  {golden[i]}")
    np.save("golden_waveform.npy", golden)
    print(f"\nSaved golden_waveform.npy  ({len(golden)} samples)")

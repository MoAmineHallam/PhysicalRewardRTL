"""
Golden reference for barrel_shift - counter-driven mode.
Inputs: data=cnt[7:0], shamt=cnt[9:8]
Probe: {8'b0, out[7:0]}
"""
import numpy as np

def compute_golden(n_cycles: int = 32768) -> np.ndarray:
    out = []
    for c in range(n_cycles):
        data  = c & 0xFF
        shamt = (c >> 8) & 0x3
        out.append((data << shamt) & 0xFF)
    return np.array(out, dtype=np.uint16)

if __name__ == "__main__":
    golden = compute_golden()
    print("cycle | data shamt | out")
    for i in range(min(20, len(golden))):
        data, shamt = i & 0xFF, (i >> 8) & 0x3
        print(f"  {i:3d} | {data:3d}   {shamt}   | {golden[i]}")
    np.save("golden_waveform.npy", golden)
    print(f"\nSaved golden_waveform.npy  ({len(golden)} samples)")

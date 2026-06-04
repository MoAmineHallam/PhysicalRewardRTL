"""Golden reference model for bit_manip."""
import numpy as np
from pathlib import Path

def compute_golden(stimulus_path="stimulus.txt"):
    values = [int(l.strip()) for l in Path(stimulus_path).read_text().splitlines()
              if l.strip() and not l.startswith("#")]
    out = []
    for v in values:
        v &= 0xFF
        rev = int(f"{v:08b}"[::-1], 2)
        cnt = bin(v).count("1")
        out.append((rev << 4) | cnt)  # pack reversed[7:0] + popcount[3:0]
    return np.array(out, dtype=np.uint16)

if __name__ == "__main__":
    golden = compute_golden()
    values = [int(l.strip()) for l in Path("stimulus.txt").read_text().splitlines()
              if l.strip() and not l.startswith("#")]
    print("cycle |  in  | reversed popcount")
    for i, (v, g) in enumerate(zip(values, golden)):
        rev, cnt = g >> 4, g & 0xF
        print(f"  {i:3d} | {v:3d}  |  {rev:3d}      {cnt}")
    np.save("golden_waveform.npy", golden)
    print(f"\nSaved golden_waveform.npy  ({len(golden)} samples)")

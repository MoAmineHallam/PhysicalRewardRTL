"""Golden reference model for comb_always (priority encoder)."""
import numpy as np
from pathlib import Path

def compute_golden(stimulus_path="stimulus.txt"):
    values = [int(l.strip()) for l in Path(stimulus_path).read_text().splitlines()
              if l.strip() and not l.startswith("#")]
    out = []
    for v in values:
        v &= 0xFF
        enc, vld = 0, 0
        for bit in range(7, -1, -1):
            if (v >> bit) & 1:
                enc, vld = bit, 1
                break
        out.append((enc << 1) | vld)  # pack enc[2:0] + valid into one word
    return np.array(out, dtype=np.uint16)

if __name__ == "__main__":
    golden = compute_golden()
    values = [int(l.strip()) for l in Path("stimulus.txt").read_text().splitlines()
              if l.strip() and not l.startswith("#")]
    print("cycle |  in  | enc valid")
    for i, (v, g) in enumerate(zip(values, golden)):
        enc, vld = g >> 1, g & 1
        print(f"  {i:3d} | {v:3d}  |  {enc}   {vld}")
    np.save("golden_waveform.npy", golden)
    print(f"\nSaved golden_waveform.npy  ({len(golden)} samples)")

"""Golden reference model for dff_array."""
import numpy as np
from pathlib import Path

def compute_golden(stimulus_path="stimulus.txt"):
    rows = [l.split() for l in Path(stimulus_path).read_text().splitlines()
            if l.strip() and not l.startswith("#")]
    q = 0
    out = []
    for en_s, d_s in rows:
        en, d = int(en_s), int(d_s) & 0xFF
        if en:
            q = d
        out.append(q)
    return np.array(out, dtype=np.uint16)

if __name__ == "__main__":
    golden = compute_golden()
    rows = [l.split() for l in Path("stimulus.txt").read_text().splitlines()
            if l.strip() and not l.startswith("#")]
    print("cycle | en   d  |   q")
    for i, ((en, d), g) in enumerate(zip(rows, golden)):
        print(f"  {i:3d} |  {en} {d:3s}  | {g:3d}")
    np.save("golden_waveform.npy", golden)
    print(f"\nSaved golden_waveform.npy  ({len(golden)} samples)")

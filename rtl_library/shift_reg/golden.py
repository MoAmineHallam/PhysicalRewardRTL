"""Golden reference model for shift_reg."""
import numpy as np
from pathlib import Path

def compute_golden(stimulus_path="stimulus.txt"):
    rows = [l.split() for l in Path(stimulus_path).read_text().splitlines()
            if l.strip() and not l.startswith("#")]
    sr = 0
    out = []
    for en_s, sin_s in rows:
        en, sin = int(en_s), int(sin_s) & 1
        if en:
            sr = ((sr << 1) | sin) & 0xFF
        out.append(sr)
    return np.array(out, dtype=np.uint16)

if __name__ == "__main__":
    golden = compute_golden()
    rows = [l.split() for l in Path("stimulus.txt").read_text().splitlines()
            if l.strip() and not l.startswith("#")]
    print("cycle | en sin |   q (bin)")
    for i, ((en, sin), g) in enumerate(zip(rows, golden)):
        print(f"  {i:3d} |  {en}   {sin} | {g:3d}  {g:08b}")
    np.save("golden_waveform.npy", golden)
    print(f"\nSaved golden_waveform.npy  ({len(golden)} samples)")

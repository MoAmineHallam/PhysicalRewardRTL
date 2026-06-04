"""
Golden reference model for edge_detector.
Computes expected 'rise' output for each cycle given stimulus.txt input sequence.
Reset is active-low; held for 2 cycles before stimulus begins.
"""

import numpy as np
from pathlib import Path

def compute_golden(stimulus_path: str = "stimulus.txt") -> np.ndarray:
    values = [int(l.strip()) for l in Path(stimulus_path).read_text().splitlines()
              if l.strip() and not l.startswith("#")]

    in_prev = 0
    rise_seq = []
    for v in values:
        rise = int(v == 1 and in_prev == 0)
        rise_seq.append(rise)
        in_prev = v

    return np.array(rise_seq, dtype=np.uint16)

if __name__ == "__main__":
    golden = compute_golden()
    print("cycle | in | rise")
    stim = [int(l.strip()) for l in Path("stimulus.txt").read_text().splitlines()
            if l.strip() and not l.startswith("#")]
    for i, (s, r) in enumerate(zip(stim, golden)):
        print(f"  {i:3d} |  {s} |  {r}")
    np.save("golden_waveform.npy", golden)
    print(f"\nSaved golden_waveform.npy  ({len(golden)} samples)")

"""Golden reference model for bcd_counter."""
import numpy as np
from pathlib import Path

def compute_golden(stimulus_path="stimulus.txt"):
    values = [int(l.strip()) for l in Path(stimulus_path).read_text().splitlines()
              if l.strip() and not l.startswith("#")]
    ones, tens = 0, 0
    out = []
    for en in values:
        if en:
            if ones == 9:
                ones = 0
                tens = 0 if tens == 9 else tens + 1
            else:
                ones += 1
        out.append((tens << 4) | ones)  # pack tens[3:0] + ones[3:0]
    return np.array(out, dtype=np.uint16)

if __name__ == "__main__":
    golden = compute_golden()
    values = [int(l.strip()) for l in Path("stimulus.txt").read_text().splitlines()
              if l.strip() and not l.startswith("#")]
    print("cycle | en | tens ones")
    for i, (en, g) in enumerate(zip(values, golden)):
        print(f"  {i:3d} |  {en} |   {g>>4}    {g&0xF}")
    np.save("golden_waveform.npy", golden)
    print(f"\nSaved golden_waveform.npy  ({len(golden)} samples)")

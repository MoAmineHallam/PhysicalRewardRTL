"""
Golden reference for bcd_counter — counter-driven mode.
Input: en = 1 (always enabled, free-running)
Probe: {8'b0, tens[3:0], ones[3:0]}
"""
import numpy as np

def compute_golden(n_cycles: int = 32768) -> np.ndarray:
    ones, tens = 0, 0
    out = []
    for _ in range(n_cycles):
        if ones == 9:
            ones = 0
            tens = 0 if tens == 9 else tens + 1
        else:
            ones += 1
        out.append((tens << 4) | ones)
    return np.array(out, dtype=np.uint16)

if __name__ == "__main__":
    golden = compute_golden()
    print("cycle | tens ones")
    for i in range(min(25, len(golden))):
        g = golden[i]
        print(f"  {i:3d} |   {g>>4}    {g&0xF}")
    np.save("golden_waveform.npy", golden)
    print(f"\nSaved golden_waveform.npy  ({len(golden)} samples)")
    print(f"Full wrap at cycle: {next(i for i,v in enumerate(golden) if v==0 and i>0)}")

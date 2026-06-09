"""
Golden reference for ring_counter - free-running, no inputs.
Probe: {12'b0, count[3:0]}  Period=4.
Reset state: 4'b0001. Each cycle: rotate left.
"""
import numpy as np

def compute_golden(n_cycles: int = 32768) -> np.ndarray:
    out = []
    count = 0b0001
    for _ in range(n_cycles):
        out.append(count)
        count = ((count << 1) | (count >> 3)) & 0xF
    return np.array(out, dtype=np.uint16)

if __name__ == "__main__":
    g = compute_golden(16)
    print("cycle | count")
    for i, v in enumerate(g):
        print(f"  {i:3d} |  {v:04b}")
    np.save("golden_waveform.npy", compute_golden())
    print("Saved golden_waveform.npy")

"""
Golden reference for mod10_counter - counter-driven testbench.
No data inputs; design free-runs.
Probe: {12'b0, count[3:0]}  -> 4-bit count value, period=10.
"""
import numpy as np

def compute_golden(n_cycles: int = 32768) -> np.ndarray:
    out = []
    count = 0
    for _ in range(n_cycles):
        out.append(count)
        count = 0 if count == 9 else count + 1
    return np.array(out, dtype=np.uint16)

if __name__ == "__main__":
    g = compute_golden(40)
    print("cycle | count")
    for i, v in enumerate(g):
        print(f"  {i:3d} |  {v}")
    np.save("golden_waveform.npy", compute_golden())
    print("Saved golden_waveform.npy")

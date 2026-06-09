"""
Golden reference for updown_counter.
Inputs: dir=cnt[0]  (cnt is the testbench counter, separate from DUT count).
Probe: {12'b0, count[3:0]}
dir=0: count up, dir=1: count down. Period=32.
Note: DUT count is internal state; we simulate it cycle by cycle.
"""
import numpy as np

def compute_golden(n_cycles: int = 32768) -> np.ndarray:
    out = []
    count = 0
    for c in range(n_cycles):
        dir_ = c & 1
        out.append(count)
        if dir_:
            count = (count - 1) & 0xF
        else:
            count = (count + 1) & 0xF
    return np.array(out, dtype=np.uint16)

if __name__ == "__main__":
    g = compute_golden(64)
    print("cycle | dir | count")
    for i, v in enumerate(g):
        print(f"  {i:3d} |  {i&1}  |  {v}")
    np.save("golden_waveform.npy", compute_golden())
    print("Saved golden_waveform.npy")

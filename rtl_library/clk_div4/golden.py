"""
Golden reference for clk_div4 - free-running, no inputs.
Probe: {13'b0, en, cnt[1:0]}  (3-bit: en is bit2, cnt is bits[1:0])
en[t] = 1 when cnt[t-1] == 3, i.e., registered pulse. Period=4.
"""
import numpy as np

def compute_golden(n_cycles: int = 32768) -> np.ndarray:
    out = []
    cnt = 0
    en = 0
    for _ in range(n_cycles):
        out.append((en << 2) | cnt)
        en = 1 if (cnt == 3) else 0
        cnt = (cnt + 1) & 3
    return np.array(out, dtype=np.uint16)

if __name__ == "__main__":
    g = compute_golden(16)
    print("cycle | en | cnt")
    for i, v in enumerate(g):
        print(f"  {i:3d} |  {(v>>2)&1} |  {v&3}")
    np.save("golden_waveform.npy", compute_golden())
    print("Saved golden_waveform.npy")

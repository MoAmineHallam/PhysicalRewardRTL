"""Golden for a streaming median-of-19 (family=med), 8-bit samples
x[c]=c&0xFF, window = current + previous 18 (init 0). Output {y[15:0]}
mask=0xFFFF. Pipeline latency absorbed by the score shift."""
import numpy as np


def compute_golden(n_cycles: int = 32768) -> np.ndarray:
    out = []
    win = [0] * 19
    for c in range(n_cycles):
        win = [c & 0xFF] + win[:-1]
        out.append(sorted(win)[9])
    return np.array(out, dtype=np.uint16)


if __name__ == "__main__":
    g = compute_golden()
    for i in range(min(20, len(g))):
        print(f"{i:4d}  {g[i]:#06x}  {g[i]}")
    np.save("golden_waveform.npy", g)

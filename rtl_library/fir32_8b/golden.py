"""Golden for a 32-tap direct-form FIR (family=fir), 8-bit samples
x[c]=c&0xFF, fixed coefficients [3, 5, 7, 9, 11, 13, 15, 17, 19, 21, 23, 25, 27, 29, 31, 33, 33, 31, 29, 27, 25, 23, 21, 19, 17, 15, 13, 11, 9, 7, 5, 3]. Output {y[15:0]} mask=0xFFFF.
Hardware output is this stream delayed by pipeline latency; the sweep/score
two-sided registration shift absorbs that, so this is the un-delayed ideal."""
import numpy as np

H = [3, 5, 7, 9, 11, 13, 15, 17, 19, 21, 23, 25, 27, 29, 31, 33, 33, 31, 29, 27, 25, 23, 21, 19, 17, 15, 13, 11, 9, 7, 5, 3]


def compute_golden(n_cycles: int = 32768) -> np.ndarray:
    out = []
    xline = [0] * 32
    for c in range(n_cycles):
        x = c & 0xFF
        xline = [x] + xline[:31]
        out.append(sum(H[k] * xline[k] for k in range(32)) & 0xFFFF)
    return np.array(out, dtype=np.uint16)


if __name__ == "__main__":
    g = compute_golden()
    for i in range(min(20, len(g))):
        print(f"{i:4d}  {g[i]:#06x}  {g[i]}")
    np.save("golden_waveform.npy", g)

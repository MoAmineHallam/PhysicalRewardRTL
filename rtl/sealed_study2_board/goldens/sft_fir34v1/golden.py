"""Golden for a 34-tap direct-form FIR (family=fir), 8-bit samples
x[c]=c&0xFF, fixed coefficients [59, 41, 24, 13, 56, 5, 31, 61, 44, 42, 13, 1, 7, 58, 21, 7, 19, 28, 23, 26, 39, 33, 5, 57, 28, 11, 18, 34, 5, 11, 53, 14, 1, 48]. Output {y[15:0]} mask=0xFFFF.
Hardware output is this stream delayed by pipeline latency; the sweep/score
two-sided registration shift absorbs that, so this is the un-delayed ideal."""
import numpy as np

H = [59, 41, 24, 13, 56, 5, 31, 61, 44, 42, 13, 1, 7, 58, 21, 7, 19, 28, 23, 26, 39, 33, 5, 57, 28, 11, 18, 34, 5, 11, 53, 14, 1, 48]


def compute_golden(n_cycles: int = 32768) -> np.ndarray:
    out = []
    xline = [0] * 34
    for c in range(n_cycles):
        x = c & 0xFF
        xline = [x] + xline[:33]
        out.append(sum(H[k] * xline[k] for k in range(34)) & 0xFFFF)
    return np.array(out, dtype=np.uint16)


if __name__ == "__main__":
    g = compute_golden()
    for i in range(min(20, len(g))):
        print(f"{i:4d}  {g[i]:#06x}  {g[i]}")
    np.save("golden_waveform.npy", g)

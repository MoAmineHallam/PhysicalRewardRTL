"""Golden for a 20-tap direct-form FIR (family=fir), 8-bit samples
x[c]=c&0xFF, fixed coefficients [4, 8, 12, 16, 20, 24, 28, 32, 36, 40, 44, 48, 52, 56, 60, 64, 68, 72, 76, 80]. Output {y[15:0]} mask=0xFFFF.
Hardware output is this stream delayed by pipeline latency; the sweep/score
two-sided registration shift absorbs that, so this is the un-delayed ideal."""
import numpy as np

H = [4, 8, 12, 16, 20, 24, 28, 32, 36, 40, 44, 48, 52, 56, 60, 64, 68, 72, 76, 80]


def compute_golden(n_cycles: int = 32768) -> np.ndarray:
    out = []
    xline = [0] * 20
    for c in range(n_cycles):
        x = c & 0xFF
        xline = [x] + xline[:19]
        out.append(sum(H[k] * xline[k] for k in range(20)) & 0xFFFF)
    return np.array(out, dtype=np.uint16)


if __name__ == "__main__":
    g = compute_golden()
    for i in range(min(20, len(g))):
        print(f"{i:4d}  {g[i]:#06x}  {g[i]}")
    np.save("golden_waveform.npy", g)

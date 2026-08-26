"""Golden for an order-18 IIR (family=iir), 8-bit samples x[c]=c&0xFF,
feedforward B=[25, 26, 46, 49, 16, 8, 15, 31, 37, 52, 6, 54, 60, 33, 33, 62, 48, 18, 56], feedback ((9*y1)>>4)+((5*y2)>>4), mod 2^16. Output
{y[15:0]} mask=0xFFFF. Pipeline latency absorbed by the score shift."""
import numpy as np

B = [25, 26, 46, 49, 16, 8, 15, 31, 37, 52, 6, 54, 60, 33, 33, 62, 48, 18, 56]


def compute_golden(n_cycles: int = 32768) -> np.ndarray:
    out = []
    xd = [0] * 18
    y1 = y2 = 0
    for c in range(n_cycles):
        x = c & 0xFF
        acc = B[0] * x + sum(B[k] * xd[k - 1] for k in range(1, 19))
        acc += (9 * y1) >> 4
        acc += (5 * y2) >> 4
        ynew = acc & 0xFFFF
        y2, y1 = y1, ynew
        xd = [x] + xd[:-1]
        out.append(ynew)
    return np.array(out, dtype=np.uint16)


if __name__ == "__main__":
    g = compute_golden()
    for i in range(min(20, len(g))):
        print(f"{i:4d}  {g[i]:#06x}  {g[i]}")
    np.save("golden_waveform.npy", g)

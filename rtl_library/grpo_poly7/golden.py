"""Golden for a degree-7 Horner polynomial (family=poly), mod 2^16.
x[c]=c&0xFF, coefficients [1, 3, 5, 7, 9, 11, 13, 15]: y = (((c0*x+c1)*x+c2)...+cD) & 0xFFFF.
Output {y[15:0]} mask=0xFFFF. Pipeline latency absorbed by the score shift."""
import numpy as np

C = [1, 3, 5, 7, 9, 11, 13, 15]


def compute_golden(n_cycles: int = 32768) -> np.ndarray:
    out = []
    for c in range(n_cycles):
        x = c & 0xFF
        acc = C[0]
        for k in range(1, len(C)):
            acc = (acc * x + C[k]) & 0xFFFF
        out.append(acc & 0xFFFF)
    return np.array(out, dtype=np.uint16)


if __name__ == "__main__":
    g = compute_golden()
    for i in range(min(20, len(g))):
        print(f"{i:4d}  {g[i]:#06x}  {g[i]}")
    np.save("golden_waveform.npy", g)

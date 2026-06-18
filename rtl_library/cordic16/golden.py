"""Golden for an 16-iteration rotation-mode CORDIC (family=cordic).
Angle x[c]=c&0xFF (unit: 90deg=256); pure integer shift-add, so exact. Output
is the low 16 bits of the x (cos-scaled) result. Pipeline latency absorbed by
the score shift."""
import numpy as np

ATAN = [128, 76, 40, 20, 10, 5, 3, 1, 1, 0, 0, 0, 0, 0, 0, 0]
X0 = 9949


def compute_golden(n_cycles: int = 32768) -> np.ndarray:
    out = []
    for c in range(n_cycles):
        x = X0; y = 0; z = c & 0xFF
        for i in range(16):
            dx = x >> i
            dy = y >> i
            if z >= 0:
                x = x - dy; y = y + dx; z = z - ATAN[i]
            else:
                x = x + dy; y = y - dx; z = z + ATAN[i]
        out.append(x & 0xFFFF)
    return np.array(out, dtype=np.uint16)


if __name__ == "__main__":
    g = compute_golden()
    for i in range(min(20, len(g))):
        print(f"{i:4d}  {g[i]:#06x}  {g[i]}")
    np.save("golden_waveform.npy", g)

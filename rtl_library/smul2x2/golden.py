"""
Golden reference for smul2x2 (family=smul).
signed 2x2 multiply.
Probe packing: {12'b0, product}   mask=0x000f   period=16
Counter-driven: inputs are slices of free-running cnt.
"""
import numpy as np


def compute_golden(n_cycles: int = 32768) -> np.ndarray:
    out = []
    for c in range(n_cycles):
        a = c & 3
        b = (c >> 2) & 3
        a = a - 4 if a >= 2 else a
        b = b - 4 if b >= 2 else b
        val = (a * b) & 15
        out.append(val & 0xFFFF)
    return np.array(out, dtype=np.uint16)


if __name__ == "__main__":
    g = compute_golden()
    for i in range(min(20, len(g))):
        print(f"{i:4d}  {g[i]:#06x}  {g[i]}")
    np.save("golden_waveform.npy", g)
    print(f"Saved golden_waveform.npy ({len(g)} samples)")

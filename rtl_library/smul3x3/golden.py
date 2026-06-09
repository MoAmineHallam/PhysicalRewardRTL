"""
Golden reference for smul3x3 (family=smul).
signed 3x3 multiply.
Probe packing: {10'b0, product}   mask=0x003f   period=64
Counter-driven: inputs are slices of free-running cnt.
"""
import numpy as np


def compute_golden(n_cycles: int = 32768) -> np.ndarray:
    out = []
    for c in range(n_cycles):
        a = c & 7
        b = (c >> 3) & 7
        a = a - 8 if a >= 4 else a
        b = b - 8 if b >= 4 else b
        val = (a * b) & 63
        out.append(val & 0xFFFF)
    return np.array(out, dtype=np.uint16)


if __name__ == "__main__":
    g = compute_golden()
    for i in range(min(20, len(g))):
        print(f"{i:4d}  {g[i]:#06x}  {g[i]}")
    np.save("golden_waveform.npy", g)
    print(f"Saved golden_waveform.npy ({len(g)} samples)")

"""
Golden reference for smul6x6 (family=smul).
signed 6x6 multiply.
Probe packing: {4'b0, product}   mask=0x0fff   period=4096
Counter-driven: inputs are slices of free-running cnt.
"""
import numpy as np


def compute_golden(n_cycles: int = 32768) -> np.ndarray:
    out = []
    for c in range(n_cycles):
        a = c & 63
        b = (c >> 6) & 63
        a = a - 64 if a >= 32 else a
        b = b - 64 if b >= 32 else b
        val = (a * b) & 4095
        out.append(val & 0xFFFF)
    return np.array(out, dtype=np.uint16)


if __name__ == "__main__":
    g = compute_golden()
    for i in range(min(20, len(g))):
        print(f"{i:4d}  {g[i]:#06x}  {g[i]}")
    np.save("golden_waveform.npy", g)
    print(f"Saved golden_waveform.npy ({len(g)} samples)")

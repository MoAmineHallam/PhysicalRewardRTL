"""
Golden reference for smul5x5 (family=smul).
signed 5x5 multiply.
Probe packing: {6'b0, product}   mask=0x03ff   period=1024
Counter-driven: inputs are slices of free-running cnt.
"""
import numpy as np


def compute_golden(n_cycles: int = 32768) -> np.ndarray:
    out = []
    for c in range(n_cycles):
        a = c & 31
        b = (c >> 5) & 31
        a = a - 32 if a >= 16 else a
        b = b - 32 if b >= 16 else b
        val = (a * b) & 1023
        out.append(val & 0xFFFF)
    return np.array(out, dtype=np.uint16)


if __name__ == "__main__":
    g = compute_golden()
    for i in range(min(20, len(g))):
        print(f"{i:4d}  {g[i]:#06x}  {g[i]}")
    np.save("golden_waveform.npy", g)
    print(f"Saved golden_waveform.npy ({len(g)} samples)")

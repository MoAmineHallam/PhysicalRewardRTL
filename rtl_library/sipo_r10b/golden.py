"""
Golden reference for sipo_r10b (family=shiftreg).
10-bit SIPO right.
Probe packing: {6'b0, q}   mask=0x03ff   period=2048
Counter-driven: inputs are slices of free-running cnt.
"""
import numpy as np


def compute_golden(n_cycles: int = 32768) -> np.ndarray:
    out = []
    for c in range(n_cycles):
        if c == 0:
            st = 0
        val = st & 1023
        sin = c & 1
        st = ((st >> 1) | (sin << 9)) & 1023
        out.append(val & 0xFFFF)
    return np.array(out, dtype=np.uint16)


if __name__ == "__main__":
    g = compute_golden()
    for i in range(min(20, len(g))):
        print(f"{i:4d}  {g[i]:#06x}  {g[i]}")
    np.save("golden_waveform.npy", g)
    print(f"Saved golden_waveform.npy ({len(g)} samples)")

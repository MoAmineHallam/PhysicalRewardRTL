"""
Golden reference for rotate_rsh7 (family=shift).
7-bit right rotate shift.
Probe packing: {9'b0, out}   mask=0x007f   period=1024
Counter-driven: inputs are slices of free-running cnt.
"""
import numpy as np


def compute_golden(n_cycles: int = 32768) -> np.ndarray:
    out = []
    for c in range(n_cycles):
        d = c & 127
        s = (c >> 7) & 7
        val = (((d >> s) | (d << (7-s))) & 127 if s else d) & 127
        out.append(val & 0xFFFF)
    return np.array(out, dtype=np.uint16)


if __name__ == "__main__":
    g = compute_golden()
    for i in range(min(20, len(g))):
        print(f"{i:4d}  {g[i]:#06x}  {g[i]}")
    np.save("golden_waveform.npy", g)
    print(f"Saved golden_waveform.npy ({len(g)} samples)")

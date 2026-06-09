"""
Golden reference for gray2bin7 (family=gray2bin).
7-bit gray->binary.
Probe packing: {9'b0, bin}   mask=0x007f   period=128
Counter-driven: inputs are slices of free-running cnt.
"""
import numpy as np


def compute_golden(n_cycles: int = 32768) -> np.ndarray:
    out = []
    for c in range(n_cycles):
        g = c & 127
        b = 0
        for i in range(6, -1, -1):
            b ^= (g >> i)
        val = b & 127
        out.append(val & 0xFFFF)
    return np.array(out, dtype=np.uint16)


if __name__ == "__main__":
    g = compute_golden()
    for i in range(min(20, len(g))):
        print(f"{i:4d}  {g[i]:#06x}  {g[i]}")
    np.save("golden_waveform.npy", g)
    print(f"Saved golden_waveform.npy ({len(g)} samples)")

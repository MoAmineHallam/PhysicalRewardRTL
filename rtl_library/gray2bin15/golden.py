"""
Golden reference for gray2bin15 (family=gray2bin).
15-bit gray->binary.
Probe packing: {1'b0, bin}   mask=0x7fff   period=32768
Counter-driven: inputs are slices of free-running cnt.
"""
import numpy as np


def compute_golden(n_cycles: int = 32768) -> np.ndarray:
    out = []
    for c in range(n_cycles):
        g = c & 32767
        b = 0
        for i in range(14, -1, -1):
            b ^= (g >> i)
        val = b & 32767
        out.append(val & 0xFFFF)
    return np.array(out, dtype=np.uint16)


if __name__ == "__main__":
    g = compute_golden()
    for i in range(min(20, len(g))):
        print(f"{i:4d}  {g[i]:#06x}  {g[i]}")
    np.save("golden_waveform.npy", g)
    print(f"Saved golden_waveform.npy ({len(g)} samples)")

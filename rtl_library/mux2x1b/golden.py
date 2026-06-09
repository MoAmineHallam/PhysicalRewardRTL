"""
Golden reference for mux2x1b (family=mux).
2-to-1 mux, 1-bit.
Probe packing: {15'b0, out}   mask=0x0001   period=8
Counter-driven: inputs are slices of free-running cnt.
"""
import numpy as np


def compute_golden(n_cycles: int = 32768) -> np.ndarray:
    out = []
    for c in range(n_cycles):
        sel = c & 1
        d0 = (c >> 1) & 1
        d1 = (c >> 2) & 1
        val = [d0, d1][sel]
        out.append(val & 0xFFFF)
    return np.array(out, dtype=np.uint16)


if __name__ == "__main__":
    g = compute_golden()
    for i in range(min(20, len(g))):
        print(f"{i:4d}  {g[i]:#06x}  {g[i]}")
    np.save("golden_waveform.npy", g)
    print(f"Saved golden_waveform.npy ({len(g)} samples)")

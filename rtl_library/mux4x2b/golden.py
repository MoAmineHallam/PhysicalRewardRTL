"""
Golden reference for mux4x2b (family=mux).
4-to-1 mux, 2-bit.
Probe packing: {14'b0, out}   mask=0x0003   period=1024
Counter-driven: inputs are slices of free-running cnt.
"""
import numpy as np


def compute_golden(n_cycles: int = 32768) -> np.ndarray:
    out = []
    for c in range(n_cycles):
        sel = c & 3
        d0 = (c >> 2) & 3
        d1 = (c >> 4) & 3
        d2 = (c >> 6) & 3
        d3 = (c >> 8) & 3
        val = [d0, d1, d2, d3][sel]
        out.append(val & 0xFFFF)
    return np.array(out, dtype=np.uint16)


if __name__ == "__main__":
    g = compute_golden()
    for i in range(min(20, len(g))):
        print(f"{i:4d}  {g[i]:#06x}  {g[i]}")
    np.save("golden_waveform.npy", g)
    print(f"Saved golden_waveform.npy ({len(g)} samples)")

"""
Golden reference for mux8x3b (family=mux).
8-to-1 mux, 3-bit.
Probe packing: {13'b0, out}   mask=0x0007   period=134217728
Counter-driven: inputs are slices of free-running cnt.
"""
import numpy as np


def compute_golden(n_cycles: int = 32768) -> np.ndarray:
    out = []
    for c in range(n_cycles):
        sel = c & 7
        d0 = (c >> 3) & 7
        d1 = (c >> 6) & 7
        d2 = (c >> 9) & 7
        d3 = (c >> 12) & 7
        d4 = (c >> 15) & 7
        d5 = (c >> 18) & 7
        d6 = (c >> 21) & 7
        d7 = (c >> 24) & 7
        val = [d0, d1, d2, d3, d4, d5, d6, d7][sel]
        out.append(val & 0xFFFF)
    return np.array(out, dtype=np.uint16)


if __name__ == "__main__":
    g = compute_golden()
    for i in range(min(20, len(g))):
        print(f"{i:4d}  {g[i]:#06x}  {g[i]}")
    np.save("golden_waveform.npy", g)
    print(f"Saved golden_waveform.npy ({len(g)} samples)")

"""
Golden reference for mux16x1b (family=mux).
16-to-1 mux, 1-bit.
Probe packing: {15'b0, out}   mask=0x0001   period=1048576
Counter-driven: inputs are slices of free-running cnt.
"""
import numpy as np


def compute_golden(n_cycles: int = 32768) -> np.ndarray:
    out = []
    for c in range(n_cycles):
        sel = c & 15
        d0 = (c >> 4) & 1
        d1 = (c >> 5) & 1
        d2 = (c >> 6) & 1
        d3 = (c >> 7) & 1
        d4 = (c >> 8) & 1
        d5 = (c >> 9) & 1
        d6 = (c >> 10) & 1
        d7 = (c >> 11) & 1
        d8 = (c >> 12) & 1
        d9 = (c >> 13) & 1
        d10 = (c >> 14) & 1
        d11 = (c >> 15) & 1
        d12 = (c >> 16) & 1
        d13 = (c >> 17) & 1
        d14 = (c >> 18) & 1
        d15 = (c >> 19) & 1
        val = [d0, d1, d2, d3, d4, d5, d6, d7, d8, d9, d10, d11, d12, d13, d14, d15][sel]
        out.append(val & 0xFFFF)
    return np.array(out, dtype=np.uint16)


if __name__ == "__main__":
    g = compute_golden()
    for i in range(min(20, len(g))):
        print(f"{i:4d}  {g[i]:#06x}  {g[i]}")
    np.save("golden_waveform.npy", g)
    print(f"Saved golden_waveform.npy ({len(g)} samples)")

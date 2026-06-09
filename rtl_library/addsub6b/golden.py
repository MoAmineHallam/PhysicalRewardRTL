"""
Golden reference for addsub6b (family=addsub).
6-bit addsub.
Probe packing: {9'b0, result}   mask=0x007f   period=8192
Counter-driven: inputs are slices of free-running cnt.
"""
import numpy as np


def compute_golden(n_cycles: int = 32768) -> np.ndarray:
    out = []
    for c in range(n_cycles):
        a = c & 63
        b = (c >> 6) & 63
        s = (c >> 12) & 1
        val = ((a - b) if s else (a + b)) & 127
        out.append(val & 0xFFFF)
    return np.array(out, dtype=np.uint16)


if __name__ == "__main__":
    g = compute_golden()
    for i in range(min(20, len(g))):
        print(f"{i:4d}  {g[i]:#06x}  {g[i]}")
    np.save("golden_waveform.npy", g)
    print(f"Saved golden_waveform.npy ({len(g)} samples)")

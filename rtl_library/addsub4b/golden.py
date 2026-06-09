"""
Golden reference for addsub4b (family=addsub).
4-bit addsub.
Probe packing: {11'b0, result}   mask=0x001f   period=512
Counter-driven: inputs are slices of free-running cnt.
"""
import numpy as np


def compute_golden(n_cycles: int = 32768) -> np.ndarray:
    out = []
    for c in range(n_cycles):
        a = c & 15
        b = (c >> 4) & 15
        s = (c >> 8) & 1
        val = ((a - b) if s else (a + b)) & 31
        out.append(val & 0xFFFF)
    return np.array(out, dtype=np.uint16)


if __name__ == "__main__":
    g = compute_golden()
    for i in range(min(20, len(g))):
        print(f"{i:4d}  {g[i]:#06x}  {g[i]}")
    np.save("golden_waveform.npy", g)
    print(f"Saved golden_waveform.npy ({len(g)} samples)")

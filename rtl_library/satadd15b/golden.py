"""
Golden reference for satadd15b (family=satadd).
15-bit saturating add.
Probe packing: {1'b0, sum}   mask=0x7fff   period=1073741824
Counter-driven: inputs are slices of free-running cnt.
"""
import numpy as np


def compute_golden(n_cycles: int = 32768) -> np.ndarray:
    out = []
    for c in range(n_cycles):
        a = c & 32767
        b = (c >> 15) & 32767
        s = a + b
        val = 32767 if s > 32767 else s
        out.append(val & 0xFFFF)
    return np.array(out, dtype=np.uint16)


if __name__ == "__main__":
    g = compute_golden()
    for i in range(min(20, len(g))):
        print(f"{i:4d}  {g[i]:#06x}  {g[i]}")
    np.save("golden_waveform.npy", g)
    print(f"Saved golden_waveform.npy ({len(g)} samples)")

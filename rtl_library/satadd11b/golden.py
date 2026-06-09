"""
Golden reference for satadd11b (family=satadd).
11-bit saturating add.
Probe packing: {5'b0, sum}   mask=0x07ff   period=4194304
Counter-driven: inputs are slices of free-running cnt.
"""
import numpy as np


def compute_golden(n_cycles: int = 32768) -> np.ndarray:
    out = []
    for c in range(n_cycles):
        a = c & 2047
        b = (c >> 11) & 2047
        s = a + b
        val = 2047 if s > 2047 else s
        out.append(val & 0xFFFF)
    return np.array(out, dtype=np.uint16)


if __name__ == "__main__":
    g = compute_golden()
    for i in range(min(20, len(g))):
        print(f"{i:4d}  {g[i]:#06x}  {g[i]}")
    np.save("golden_waveform.npy", g)
    print(f"Saved golden_waveform.npy ({len(g)} samples)")

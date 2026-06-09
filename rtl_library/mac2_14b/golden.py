"""
Golden reference for mac2_14b (family=mac).
14-bit MAC, 2-bit operands.
Probe packing: {2'b0, acc}   mask=0x3fff   period=256
Counter-driven: inputs are slices of free-running cnt.
"""
import numpy as np


def compute_golden(n_cycles: int = 32768) -> np.ndarray:
    out = []
    for c in range(n_cycles):
        if c == 0:
            st = 0
        val = st & 16383
        a = c & 3
        b = (c >> 2) & 3
        st = (st + a * b) & 16383
        out.append(val & 0xFFFF)
    return np.array(out, dtype=np.uint16)


if __name__ == "__main__":
    g = compute_golden()
    for i in range(min(20, len(g))):
        print(f"{i:4d}  {g[i]:#06x}  {g[i]}")
    np.save("golden_waveform.npy", g)
    print(f"Saved golden_waveform.npy ({len(g)} samples)")

"""
Golden reference for mac4_8b (family=mac).
8-bit MAC, 4-bit operands.
Probe packing: {8'b0, acc}   mask=0x00ff   period=4096
Counter-driven: inputs are slices of free-running cnt.
"""
import numpy as np


def compute_golden(n_cycles: int = 32768) -> np.ndarray:
    out = []
    for c in range(n_cycles):
        if c == 0:
            st = 0
        val = st & 255
        a = c & 15
        b = (c >> 4) & 15
        st = (st + a * b) & 255
        out.append(val & 0xFFFF)
    return np.array(out, dtype=np.uint16)


if __name__ == "__main__":
    g = compute_golden()
    for i in range(min(20, len(g))):
        print(f"{i:4d}  {g[i]:#06x}  {g[i]}")
    np.save("golden_waveform.npy", g)
    print(f"Saved golden_waveform.npy ({len(g)} samples)")

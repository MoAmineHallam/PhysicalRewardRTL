"""
Golden reference for cmp12b (family=cmp).
12-bit comparator -> {gt,eq,lt}.
Probe packing: {13'b0, gt, eq, lt}   mask=0x0007   period=16777216
Counter-driven: inputs are slices of free-running cnt.
"""
import numpy as np


def compute_golden(n_cycles: int = 32768) -> np.ndarray:
    out = []
    for c in range(n_cycles):
        a = c & 4095
        b = (c >> 12) & 4095
        val = ((1 if a>b else 0)<<2)|((1 if a==b else 0)<<1)|(1 if a<b else 0)
        out.append(val & 0xFFFF)
    return np.array(out, dtype=np.uint16)


if __name__ == "__main__":
    g = compute_golden()
    for i in range(min(20, len(g))):
        print(f"{i:4d}  {g[i]:#06x}  {g[i]}")
    np.save("golden_waveform.npy", g)
    print(f"Saved golden_waveform.npy ({len(g)} samples)")

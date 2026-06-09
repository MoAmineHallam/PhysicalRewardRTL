"""
Golden reference for alu7_4op (family=alu).
7-bit 4-op ALU.
Probe packing: {9'b0, result}   mask=0x007f   period=65536
Counter-driven: inputs are slices of free-running cnt.
"""
import numpy as np


def compute_golden(n_cycles: int = 32768) -> np.ndarray:
    out = []
    for c in range(n_cycles):
        a = c & 127
        b = (c >> 7) & 127
        op = (c >> 14) & 3
        val = 0
        if False:
            pass
        elif op == 0: val = (a + b) & 127
        elif op == 1: val = (a - b) & 127
        elif op == 2: val = (a & b) & 127
        elif op == 3: val = (a | b) & 127
        out.append(val & 0xFFFF)
    return np.array(out, dtype=np.uint16)


if __name__ == "__main__":
    g = compute_golden()
    for i in range(min(20, len(g))):
        print(f"{i:4d}  {g[i]:#06x}  {g[i]}")
    np.save("golden_waveform.npy", g)
    print(f"Saved golden_waveform.npy ({len(g)} samples)")

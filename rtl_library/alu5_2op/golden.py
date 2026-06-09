"""
Golden reference for alu5_2op (family=alu).
5-bit 2-op ALU.
Probe packing: {11'b0, result}   mask=0x001f   period=2048
Counter-driven: inputs are slices of free-running cnt.
"""
import numpy as np


def compute_golden(n_cycles: int = 32768) -> np.ndarray:
    out = []
    for c in range(n_cycles):
        a = c & 31
        b = (c >> 5) & 31
        op = (c >> 10) & 1
        val = 0
        if False:
            pass
        elif op == 0: val = (a + b) & 31
        elif op == 1: val = (a - b) & 31
        out.append(val & 0xFFFF)
    return np.array(out, dtype=np.uint16)


if __name__ == "__main__":
    g = compute_golden()
    for i in range(min(20, len(g))):
        print(f"{i:4d}  {g[i]:#06x}  {g[i]}")
    np.save("golden_waveform.npy", g)
    print(f"Saved golden_waveform.npy ({len(g)} samples)")

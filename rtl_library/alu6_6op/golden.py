"""
Golden reference for alu6_6op (family=alu).
6-bit 6-op ALU.
Probe packing: {10'b0, result}   mask=0x003f   period=32768
Counter-driven: inputs are slices of free-running cnt.
"""
import numpy as np


def compute_golden(n_cycles: int = 32768) -> np.ndarray:
    out = []
    for c in range(n_cycles):
        a = c & 63
        b = (c >> 6) & 63
        op = (c >> 12) & 7
        val = 0
        if False:
            pass
        elif op == 0: val = (a + b) & 63
        elif op == 1: val = (a - b) & 63
        elif op == 2: val = (a & b) & 63
        elif op == 3: val = (a | b) & 63
        elif op == 4: val = (a ^ b) & 63
        elif op == 5: val = (~a) & 63
        out.append(val & 0xFFFF)
    return np.array(out, dtype=np.uint16)


if __name__ == "__main__":
    g = compute_golden()
    for i in range(min(20, len(g))):
        print(f"{i:4d}  {g[i]:#06x}  {g[i]}")
    np.save("golden_waveform.npy", g)
    print(f"Saved golden_waveform.npy ({len(g)} samples)")

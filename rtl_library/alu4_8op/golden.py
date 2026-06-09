"""
Golden reference for alu4_8op (family=alu).
4-bit 8-op ALU.
Probe packing: {12'b0, result}   mask=0x000f   period=2048
Counter-driven: inputs are slices of free-running cnt.
"""
import numpy as np


def compute_golden(n_cycles: int = 32768) -> np.ndarray:
    out = []
    for c in range(n_cycles):
        a = c & 15
        b = (c >> 4) & 15
        op = (c >> 8) & 7
        val = 0
        if False:
            pass
        elif op == 0: val = (a + b) & 15
        elif op == 1: val = (a - b) & 15
        elif op == 2: val = (a & b) & 15
        elif op == 3: val = (a | b) & 15
        elif op == 4: val = (a ^ b) & 15
        elif op == 5: val = (~a) & 15
        elif op == 6: val = (a << 1) & 15
        elif op == 7: val = (a >> 1) & 15
        out.append(val & 0xFFFF)
    return np.array(out, dtype=np.uint16)


if __name__ == "__main__":
    g = compute_golden()
    for i in range(min(20, len(g))):
        print(f"{i:4d}  {g[i]:#06x}  {g[i]}")
    np.save("golden_waveform.npy", g)
    print(f"Saved golden_waveform.npy ({len(g)} samples)")

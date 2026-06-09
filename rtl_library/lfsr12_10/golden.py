"""
Golden reference for lfsr12_10 (family=lfsr).
12-bit LFSR taps=0x829.
Probe packing: {4'b0, state}   mask=0x0fff   period=4095
Counter-driven: inputs are slices of free-running cnt.
"""
import numpy as np


def compute_golden(n_cycles: int = 32768) -> np.ndarray:
    out = []
    for c in range(n_cycles):
        if c == 0:
            st = 2748
        val = st
        fb = st & 1
        st = st >> 1
        if fb: st ^= 2089
        st &= 4095
        out.append(val & 0xFFFF)
    return np.array(out, dtype=np.uint16)


if __name__ == "__main__":
    g = compute_golden()
    for i in range(min(20, len(g))):
        print(f"{i:4d}  {g[i]:#06x}  {g[i]}")
    np.save("golden_waveform.npy", g)
    print(f"Saved golden_waveform.npy ({len(g)} samples)")

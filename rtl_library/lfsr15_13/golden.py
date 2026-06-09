"""
Golden reference for lfsr15_13 (family=lfsr).
15-bit LFSR taps=0x6000.
Probe packing: {1'b0, state}   mask=0x7fff   period=32767
Counter-driven: inputs are slices of free-running cnt.
"""
import numpy as np


def compute_golden(n_cycles: int = 32768) -> np.ndarray:
    out = []
    for c in range(n_cycles):
        if c == 0:
            st = 32767
        val = st
        fb = st & 1
        st = st >> 1
        if fb: st ^= 24576
        st &= 32767
        out.append(val & 0xFFFF)
    return np.array(out, dtype=np.uint16)


if __name__ == "__main__":
    g = compute_golden()
    for i in range(min(20, len(g))):
        print(f"{i:4d}  {g[i]:#06x}  {g[i]}")
    np.save("golden_waveform.npy", g)
    print(f"Saved golden_waveform.npy ({len(g)} samples)")

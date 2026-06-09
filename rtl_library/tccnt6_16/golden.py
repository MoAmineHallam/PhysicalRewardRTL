"""
Golden reference for tccnt6_16 (family=terminal_counter).
6-bit counter wrap 16 + tc.
Probe packing: {9'b0, tc, count}   mask=0x007f   period=17
Counter-driven: inputs are slices of free-running cnt.
"""
import numpy as np


def compute_golden(n_cycles: int = 32768) -> np.ndarray:
    out = []
    for c in range(n_cycles):
        if c == 0:
            st = 0; prev = 0
        val = (st & 63) | ((1 if prev == 16 else 0) << 6)
        prev = st
        st = 0 if st == 16 else (st + 1)
        out.append(val & 0xFFFF)
    return np.array(out, dtype=np.uint16)


if __name__ == "__main__":
    g = compute_golden()
    for i in range(min(20, len(g))):
        print(f"{i:4d}  {g[i]:#06x}  {g[i]}")
    np.save("golden_waveform.npy", g)
    print(f"Saved golden_waveform.npy ({len(g)} samples)")

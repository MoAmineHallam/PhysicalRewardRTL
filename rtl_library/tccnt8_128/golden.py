"""
Golden reference for tccnt8_128 (family=terminal_counter).
8-bit counter wrap 128 + tc.
Probe packing: {7'b0, tc, count}   mask=0x01ff   period=129
Counter-driven: inputs are slices of free-running cnt.
"""
import numpy as np


def compute_golden(n_cycles: int = 32768) -> np.ndarray:
    out = []
    for c in range(n_cycles):
        if c == 0:
            st = 0; prev = 0
        val = (st & 255) | ((1 if prev == 128 else 0) << 8)
        prev = st
        st = 0 if st == 128 else (st + 1)
        out.append(val & 0xFFFF)
    return np.array(out, dtype=np.uint16)


if __name__ == "__main__":
    g = compute_golden()
    for i in range(min(20, len(g))):
        print(f"{i:4d}  {g[i]:#06x}  {g[i]}")
    np.save("golden_waveform.npy", g)
    print(f"Saved golden_waveform.npy ({len(g)} samples)")

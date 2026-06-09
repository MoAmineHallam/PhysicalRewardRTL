"""
Golden reference for updown6b (family=updown).
6-bit up/down counter (dir=cnt[8]).
Probe packing: {10'b0, count}   mask=0x003f   period=512
Counter-driven: inputs are slices of free-running cnt.
"""
import numpy as np


def compute_golden(n_cycles: int = 32768) -> np.ndarray:
    out = []
    for c in range(n_cycles):
        if c == 0:
            st = 0
        d = (c >> 8) & 1
        val = st & 63
        st = (st - 1) if d else (st + 1)
        st &= 63
        out.append(val & 0xFFFF)
    return np.array(out, dtype=np.uint16)


if __name__ == "__main__":
    g = compute_golden()
    for i in range(min(20, len(g))):
        print(f"{i:4d}  {g[i]:#06x}  {g[i]}")
    np.save("golden_waveform.npy", g)
    print(f"Saved golden_waveform.npy ({len(g)} samples)")

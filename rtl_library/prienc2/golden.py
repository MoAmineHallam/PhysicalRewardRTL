"""
Golden reference for prienc2 (family=prienc).
2-input priority encoder.
Probe packing: {14'b0, valid, enc}   mask=0x0003   period=4
Counter-driven: inputs are slices of free-running cnt.
"""
import numpy as np


def compute_golden(n_cycles: int = 32768) -> np.ndarray:
    out = []
    for c in range(n_cycles):
        req = c & 3
        enc = 0
        for i in range(1, -1, -1):
            if req & (1<<i):
                enc = i; break
        val = ((1 if req else 0)<<1)|enc
        out.append(val & 0xFFFF)
    return np.array(out, dtype=np.uint16)


if __name__ == "__main__":
    g = compute_golden()
    for i in range(min(20, len(g))):
        print(f"{i:4d}  {g[i]:#06x}  {g[i]}")
    np.save("golden_waveform.npy", g)
    print(f"Saved golden_waveform.npy ({len(g)} samples)")

"""
Golden reference for prienc3 (family=prienc).
3-input priority encoder.
Probe packing: {13'b0, valid, enc}   mask=0x0007   period=8
Counter-driven: inputs are slices of free-running cnt.
"""
import numpy as np


def compute_golden(n_cycles: int = 32768) -> np.ndarray:
    out = []
    for c in range(n_cycles):
        req = c & 7
        enc = 0
        for i in range(2, -1, -1):
            if req & (1<<i):
                enc = i; break
        val = ((1 if req else 0)<<2)|enc
        out.append(val & 0xFFFF)
    return np.array(out, dtype=np.uint16)


if __name__ == "__main__":
    g = compute_golden()
    for i in range(min(20, len(g))):
        print(f"{i:4d}  {g[i]:#06x}  {g[i]}")
    np.save("golden_waveform.npy", g)
    print(f"Saved golden_waveform.npy ({len(g)} samples)")

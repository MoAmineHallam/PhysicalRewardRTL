"""
Golden reference for echo8b (family=canary).

A 3-deep flip-flop echo of x[c]=c&0xFF (dut_top wires .x(cnt[7:0])).  Output
packing: {8'b0, x_delayed}  mask=0xFFFF (only low 8 bits ever set).  The fixed
pipeline delay is absorbed by the sweep scorer's two-sided registration shift,
so this golden is the un-delayed ideal stream.
"""
import numpy as np


def compute_golden(n_cycles: int = 32768) -> np.ndarray:
    return np.array([c & 0xFF for c in range(n_cycles)], dtype=np.uint16)


if __name__ == "__main__":
    g = compute_golden()
    for i in range(min(24, len(g))):
        print(f"{i:4d}  {g[i]:#06x}  {g[i]}")
    np.save("golden_waveform.npy", g)
    print(f"Saved golden_waveform.npy ({len(g)} samples)")

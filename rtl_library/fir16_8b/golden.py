"""
Golden reference for fir16_8b (family=fir).

16-tap direct-form FIR, 8-bit unsigned samples, fixed 8-bit symmetric
coefficients.  Stimulus is the free-running cycle counter low byte: x[c]=c&0xFF
(the dut_top wires .x(cnt[7:0])).  Output packing: {y[15:0]}  mask=0xFFFF.

The hardware output is this ideal stream delayed by the delay-line + output
register latency; the silicon-Fmax sweep scorer absorbs that with a small
two-sided registration shift, so this golden is the un-delayed ideal sequence.
"""
import numpy as np

H = [3, 7, 12, 19, 27, 34, 40, 43, 43, 40, 34, 27, 19, 12, 7, 3]


def compute_golden(n_cycles: int = 32768) -> np.ndarray:
    out = []
    xline = [0] * 16
    for c in range(n_cycles):
        x = c & 0xFF
        xline = [x] + xline[:15]          # shift in newest sample
        y = sum(H[k] * xline[k] for k in range(16)) & 0xFFFF
        out.append(y)
    return np.array(out, dtype=np.uint16)


if __name__ == "__main__":
    g = compute_golden()
    for i in range(min(24, len(g))):
        print(f"{i:4d}  {g[i]:#06x}  {g[i]}")
    np.save("golden_waveform.npy", g)
    print(f"Saved golden_waveform.npy ({len(g)} samples)")

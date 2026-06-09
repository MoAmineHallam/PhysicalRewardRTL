"""
Golden reference for mux4to1.
Inputs: sel=cnt[1:0], d0=cnt[5:2], d1=cnt[9:6], d2=cnt[13:10], d3=cnt[17:14]
Probe: {12'b0, out[3:0]}
Period divides: the full address space cycles through sel every 4 counts.
"""
import numpy as np

def compute_golden(n_cycles: int = 32768) -> np.ndarray:
    out = []
    for c in range(n_cycles):
        sel = c & 0x3
        d0  = (c >> 2)  & 0xF
        d1  = (c >> 6)  & 0xF
        d2  = (c >> 10) & 0xF
        d3  = (c >> 14) & 0xF
        data = [d0, d1, d2, d3]
        out.append(data[sel])
    return np.array(out, dtype=np.uint16)

if __name__ == "__main__":
    g = compute_golden(20)
    print("cycle | sel | out")
    for i, v in enumerate(g):
        print(f"  {i:3d} |  {i&3}  |  {v}")
    np.save("golden_waveform.npy", compute_golden())
    print("Saved golden_waveform.npy")

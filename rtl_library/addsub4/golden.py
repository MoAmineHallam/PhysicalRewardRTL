"""
Golden reference for addsub4 - counter-driven mode.
Inputs: a=cnt[3:0], b=cnt[7:4], sub=cnt[8]
Probe: {11'b0, result[4:0]}
sub=0: result = a + b  (bit4 = carry-out)
sub=1: result = a - b  (bit4 = borrow when a < b)
"""
import numpy as np

def compute_golden(n_cycles: int = 32768) -> np.ndarray:
    out = []
    for c in range(n_cycles):
        a   = c & 0xF
        b   = (c >> 4) & 0xF
        sub = (c >> 8) & 0x1
        if sub:
            res = (a - b) & 0x1F   # 5-bit two's complement; bit4=borrow
        else:
            res = (a + b) & 0x1F   # bit4 = carry
        out.append(res)
    return np.array(out, dtype=np.uint16)

if __name__ == "__main__":
    golden = compute_golden()
    print("cycle |  a  b sub | result[4:0]")
    for i in range(min(20, len(golden))):
        a, b, sub = i & 0xF, (i >> 4) & 0xF, (i >> 8) & 0x1
        print(f"  {i:3d} | {a:2d} {b:2d}  {sub}  |  {golden[i]:05b}")
    np.save("golden_waveform.npy", golden)
    print(f"\nSaved golden_waveform.npy  ({len(golden)} samples)")

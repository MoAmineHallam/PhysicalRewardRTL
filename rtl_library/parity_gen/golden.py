"""
Golden reference for parity_gen.
Input: data=cnt[7:0]
Probe: {14'b0, even_par, odd_par}  (2-bit output)
even_par = ^data, odd_par = ~even_par. Period=256.
"""
import numpy as np

def compute_golden(n_cycles: int = 32768) -> np.ndarray:
    out = []
    for c in range(n_cycles):
        data = c & 0xFF
        even = bin(data).count('1') % 2
        odd = 1 - even
        out.append((even << 1) | odd)
    return np.array(out, dtype=np.uint16)

if __name__ == "__main__":
    g = compute_golden(20)
    print("cycle | data | even odd")
    for i, v in enumerate(g):
        data = i & 0xFF
        print(f"  {i:3d} | {data:08b} |  {(v>>1)&1}    {v&1}")
    np.save("golden_waveform.npy", compute_golden())
    print("Saved golden_waveform.npy")

"""
Golden reference for priority_enc4.
Input: req=cnt[3:0]
Probe: {13'b0, valid, enc[1:0]}  (3-bit output)
Priority: req[3]>req[2]>req[1]>req[0]. Period=16.
"""
import numpy as np

def compute_golden(n_cycles: int = 32768) -> np.ndarray:
    out = []
    for c in range(n_cycles):
        req = c & 0xF
        valid = 1 if req else 0
        if   req & 0x8: enc = 3
        elif req & 0x4: enc = 2
        elif req & 0x2: enc = 1
        else:           enc = 0
        out.append((valid << 2) | enc)
    return np.array(out, dtype=np.uint16)

if __name__ == "__main__":
    g = compute_golden(20)
    print("cycle | req  | valid enc")
    for i, v in enumerate(g):
        print(f"  {i:3d} | {i&0xF:04b} |   {(v>>2)&1}    {v&3}")
    np.save("golden_waveform.npy", compute_golden())
    print("Saved golden_waveform.npy")

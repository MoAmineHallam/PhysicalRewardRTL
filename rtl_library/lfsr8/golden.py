"""
Golden reference for lfsr8 - free-running Galois LFSR.
No data inputs. Probe: {8'b0, state[7:0]}  Period=255.
Polynomial: x^8+x^6+x^5+x^4+1, tap mask=0x70, seed=0xAC.
"""
import numpy as np

def compute_golden(n_cycles: int = 32768) -> np.ndarray:
    out = []
    state = 0xAC
    for _ in range(n_cycles):
        out.append(state)
        feedback = state & 1
        state = state >> 1
        if feedback:
            state ^= 0x70
    return np.array(out, dtype=np.uint16)

if __name__ == "__main__":
    g = compute_golden(260)
    print("cycle | state")
    for i, v in enumerate(g[:20]):
        print(f"  {i:3d} | {v:08b}  ({v:#04x})")
    np.save("golden_waveform.npy", compute_golden())
    print("Saved golden_waveform.npy")

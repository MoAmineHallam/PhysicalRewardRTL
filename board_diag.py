#!/usr/bin/env python3
"""board_diag.py - figure out why all sels read the same. Runs ON the board."""
import numpy as np
import pynq.pl_server.embedded_device as _ed
from pynq.pl_server.device import Device
Device.active_device = _ed.EmbeddedDevice()
from pynq import Overlay, MMIO

BIT = "/home/xilinx/cap/out_b0/system_b0.bit"
LA_BASE = 0x40000000
CTRL, STATUS, RADDR, RDATA = 0x00, 0x04, 0x08, 0x0C


def arm(mmio, sel):
    mmio.write(CTRL, (sel << 2) | 0x1)
    for _ in range(100000):
        if mmio.read(STATUS) & 0x1:
            return True
    return False


def read_n(mmio, n):
    out = []
    for i in range(n):
        mmio.write(RADDR, i)
        out.append(mmio.read(RDATA) & 0xFFFF)
    return out


def main():
    Overlay(BIT)
    mmio = MMIO(LA_BASE, 0x10000)

    # A) does output depend on sel?
    for sel in (26, 18, 12, 6):
        done = arm(mmio, sel)
        s = read_n(mmio, 24)
        print(f"sel={sel:2d} done={done} status=0x{mmio.read(STATUS):x}")
        print("   ", s)

    # B) read stability: re-read index 5 ten times (should be constant)
    arm(mmio, 26)
    reps = []
    for _ in range(10):
        mmio.write(RADDR, 5)
        reps.append(mmio.read(RDATA) & 0xFFFF)
    print("re-read idx5 x10:", reps)

    # C) does rd_index actually move? read idx 0,0,1,1,2,2
    arm(mmio, 26)
    seq = []
    for i in [0, 0, 1, 1, 2, 2, 3, 3]:
        mmio.write(RADDR, i)
        seq.append(mmio.read(RDATA) & 0xFFFF)
    print("idx 0,0,1,1,2,2,3,3 ->", seq)


if __name__ == "__main__":
    main()

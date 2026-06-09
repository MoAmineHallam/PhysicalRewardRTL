#!/usr/bin/env python3
"""
board_test.py  -  Minimal end-to-end hardware sanity check (runs ON the board).

Loads batch-0 bitstream, captures a couple of DUTs whose output is trivial to
eyeball, and prints the first samples. If mod2 reads 0,1,0,1... and mod4 reads
0,1,2,3... the whole loop (synthesis -> bitstream -> LA capture over AXI) works.

Run on the board:
    sudo python3 board_test.py
"""
import time
import numpy as np

# This board is embedded Zynq with no XRT card. PYNQ's normal device
# enumeration probes the XRT backend first and pyxrt.device(0) raises, which
# aborts discovery before the embedded device is reached. So we construct the
# EmbeddedDevice directly and set it active, bypassing enumeration.
import pynq.pl_server.embedded_device as _ed
from pynq.pl_server.device import Device
Device.active_device = _ed.EmbeddedDevice()

from pynq import Overlay, MMIO

BIT   = "/home/xilinx/cap/out_b0/system_b0.bit"
LA_BASE = 0x40000000          # from the Vivado address map for this build
CTRL, STATUS, RADDR, RDATA = 0x00, 0x04, 0x08, 0x0C

# local_sel of a few easy designs in batch 0 (see build_b0 file order)
CASES = {24: ("mod2_counter", [0, 1, 0, 1, 0, 1, 0, 1]),
         25: ("mod3_counter", [0, 1, 2, 0, 1, 2, 0, 1]),
         26: ("mod4_counter", [0, 1, 2, 3, 0, 1, 2, 3])}


def capture(mmio, sel, n):
    mmio.write(CTRL, (sel << 2) | 0x1)        # arm, sw-start, select DUT
    for _ in range(100000):
        if mmio.read(STATUS) & 0x1:           # wait for done
            break
    else:
        raise TimeoutError("capture never completed (done bit stuck)")
    out = np.empty(n, dtype=np.uint16)
    for i in range(n):
        mmio.write(RADDR, i)
        out[i] = mmio.read(RDATA) & 0xFFFF
    return out


def main():
    print("Loading overlay:", BIT)
    Overlay(BIT)                              # programs the FPGA
    mmio = MMIO(LA_BASE, 0x10000)
    print("LA mapped at", hex(LA_BASE))

    for sel, (name, expect) in CASES.items():
        s = capture(mmio, sel, 16)
        print(f"\nsel={sel:2d} {name}")
        print("  captured:", list(int(x) for x in s))
        print("  expected:", expect, "(modulo, possibly phase-shifted)")
    print("\nIf the captured streams are repeating ramps matching the modulus,"
          "\nthe hardware capture path works end to end.")


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""
capture_waveforms.py  -  Automated hardware golden capture (runs ON the PYNQ-Z2).

For every batch bitstream this:
  1. loads the overlay (system_b{K}.bit)
  2. for each DUT in the batch: writes sel + arm to CTRL, polls STATUS.done,
     reads the capture buffer over AXI, and saves
     rtl_library/<name>/waveform.npy  (uint16, DEPTH samples)

This is the "real silicon reward" data source: each waveform is the design
running on actual fabric. The scorer later compares LLM candidates (in
simulation) against these hardware captures.

Run on the board (PYNQ image, as root):
    sudo python3 capture_waveforms.py --bit-dir rtl/batches \
        --manifest rtl/batches/batch_manifest.json --rtl-lib rtl_library

Requires: pynq (Overlay, MMIO). Adjust LA_BASE / register offsets to match your
block design address map if they differ.
"""

import os
import json
import time
import argparse

import numpy as np

# AXI register offsets (bytes) -- must match la_axi_wide.v register map.
CTRL, STATUS, RADDR, RDATA = 0x00, 0x04, 0x08, 0x0C
DEPTH_DEFAULT = 32768


def _init_pynq():
    """Work around XRT probe crash on Zynq (PYNQ 3.x)."""
    import pynq.pl_server.embedded_device as _ed
    from pynq.pl_server.device import Device
    if not isinstance(Device.active_device, _ed.EmbeddedDevice):
        Device.active_device = _ed.EmbeddedDevice()


def capture_one(mmio, local_sel, depth):
    """Arm the LA for one DUT and read back the capture buffer."""
    # CTRL: bit0=arm, bit1=trig_mode(0=sw start), sel at bits[2+]
    mmio.write(CTRL, (local_sel << 2) | 0x1)
    # poll done
    for _ in range(100000):
        if mmio.read(STATUS) & 0x1:
            break
    else:
        raise TimeoutError(f"capture timeout (sel={local_sel})")
    samples = np.empty(depth, dtype=np.uint16)
    for i in range(depth):
        mmio.write(RADDR, i)
        samples[i] = mmio.read(RDATA) & 0xFFFF
    return samples


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--bit-dir", default="rtl/batches")
    ap.add_argument("--manifest", default="rtl/batches/batch_manifest.json")
    ap.add_argument("--rtl-lib", default="rtl_library")
    ap.add_argument("--la-base", type=lambda x: int(x, 0), default=0x40000000,
                    help="AXI base address of la_axi_wide (from your address map)")
    ap.add_argument("--depth", type=int, default=DEPTH_DEFAULT)
    args = ap.parse_args()

    _init_pynq()
    from pynq import Overlay, MMIO  # noqa: import here so script imports off-board

    man = json.load(open(args.manifest))
    by_batch = {}
    for d in man["designs"]:
        by_batch.setdefault(d["batch"], []).append(d)

    total, ok = 0, 0
    for batch_id in sorted(by_batch):
        bit = os.path.join(args.bit_dir, f"out_b{batch_id}",
                           f"system_b{batch_id}.bit")
        if not os.path.exists(bit):
            print(f"[batch {batch_id}] bitstream missing: {bit} -- SKIP")
            continue
        print(f"[batch {batch_id}] loading {bit}")
        Overlay(bit)                      # program the FPGA
        mmio = MMIO(args.la_base, 0x10000)
        for d in sorted(by_batch[batch_id], key=lambda x: x["local_sel"]):
            total += 1
            try:
                wave = capture_one(mmio, d["local_sel"], args.depth)
            except Exception as e:
                print(f"   [{d['name']}] FAIL: {e}")
                continue
            out = os.path.join(args.rtl_lib, d["name"], "waveform.npy")
            os.makedirs(os.path.dirname(out), exist_ok=True)
            np.save(out, wave)
            ok += 1
            if ok % 25 == 0:
                print(f"   captured {ok}/{total} ...")
    print(f"\nDONE: captured {ok}/{total} hardware waveforms.")


if __name__ == "__main__":
    main()

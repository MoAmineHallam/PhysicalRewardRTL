# Reproducibility guide

## What can be reproduced locally

`verify_repository.py` validates the two paper PDFs against the retained
submission record and then runs `artifact/run_demo.py`. The artifact verifies
its own SHA-256 manifest, checks the identity and denominator of every included
draw, joins passing draws to their terminal physical records, recomputes both
policy means, reconstructs the paired family-by-regime bootstrap interval, and
recomputes the measured best-of-N curves.

With `--simulate`, the same command also invokes the unchanged shared functional
gate on `artifact/demo/sft.sv` and `artifact/demo/rf.sv`. Each implementation is
tested on two 1,024-sample streams, with reset repeated between episodes and a
common accepted latency required across streams and episodes. This is simulation
coverage, not formal equivalence.

## Environment

The delivered package was validated with Python 3.12 and NumPy 2.2.6 on
Windows. NumPy is pinned in `artifact/requirements.txt`. Icarus Verilog is only
needed for `--simulate`. The Python and temporary-directory flow is designed to
be portable, but the retained validation record covers the stated Windows
environment.

The manuscript sources use IEEEtran and were validated with Tectonic 0.17.0.
From `paper/source-package`, create a build directory and run:

```text
tectonic --outdir build paper/main.tex
tectonic --outdir build paper/supplement.tex
```

## Evidence included

The artifact includes all 1,920 SFT and RF draws used in the new comparison,
including extraction and functional failures; 192 content-deduplicated terminal
physical records, including three retained physical failures; the sealed design
specifications and prompts; the exact functional checker and reference oracle;
the two worked-example RTL modules; selected passing-boundary implementation
reports for the example; the original protocol and campaign manifest; and a
SHA-256 manifest covering every packaged input.

## Evidence outside this repository snapshot

Model weights and the complete training environment are not distributed here.
The artifact therefore does not reproduce training. It also does not contain
every intermediate Vivado trial directory or start new licensed-tool jobs. The
terminal records needed for the RF versus SFT analysis and the passing-boundary
reports for the worked example are included. The main paper's earlier primary
study uses a different measurement contract and is not recomputed by this
supplementary package.

The full three-arm campaign also evaluated a DPO diagnostic. This reviewer
package contains the requested RF versus SFT contrast and does not present the
DPO diagnostic as a matched implementation of an external method.

## Integrity and expected output

`artifact/SHA256SUMS.json` detects modified or omitted packaged inputs. It is an
integrity manifest, not a digital signature or independent certification. A
successful numerical run prints `PASS`, the two policy rows, and the paired
interval. A successful simulation run additionally reports that both RTL
implementations passed the shared simulation and reset gate.

The retained clean-environment run completed numerical replay and both RTL
simulations in approximately 1.6 seconds after dependency installation.

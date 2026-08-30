# V5 outcome

V5 is permanently **FAIL**.  Six fresh first-attempt synthetic
synth/place/route processes were valid.  Run 7 then failed during synthesis
after launching Vivado's helper process; Vivado reported the existing
`scripts/rt/data/unimacro/unimacro_vhdl.tcl` file as unreadable with the message
`No error`.  The complete raw dependency guards before and after the process
matched the frozen baseline.

The restart hypothesis is therefore rejected.  No Study-2 candidate RTL was
exposed, and V5 must not be rerun or amended into a pass.  The raw attestation
SHA-256 is
`6dcb03bf4ec0ba575f4d2908d991f3d6a65d4bccb9c9a8340a9f9847e71a46e6`.
